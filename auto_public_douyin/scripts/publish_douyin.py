#!/usr/bin/env python3
"""
Douyin Creator Platform - 图文自动发布
用法示例：
    python publish_douyin.py --login                 # 首次登录
    python publish_douyin.py                         # 使用默认参数发布
    python publish_douyin.py --image a.png --title "标题" --content "描述"
    python publish_douyin.py --dry-run               # 走流程但不真正点发布

脚本使用 Playwright 驱动 Chromium，并通过独立的 user_data/ 目录保持登录态。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from playwright.sync_api import (
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

# ---------- 常量 ----------

DEFAULT_IMAGE_NAME = "GPTImage2.png"
DEFAULT_TITLE = "GPT Image2 使用教程"
DEFAULT_CONTENT = (
    "GPT Image 2 提供了完整的图像生成与编辑能力，核心使用流程分为四大模块：\n"
    "文本生成图像：通过输入描述提示词（如风格、构图、比例要求），即可生成目标图像，支持比例控制与文本渲染，快速实现创意落地。\n"
    "精确图像编辑：支持局部修改、元素调整等精细化编辑，可对原图指定区域添加特效、替换元素，轻松完成图像二次创作。\n"
    "“思维” 模式推理：生成过程会解析提示词、验证信息、生成执行计划并自查结果，让图像生成更贴合需求、减少偏差。\n"
    "高级功能拓展：支持风格一致性控制、多任务并行处理与 API 集成，可批量生成图像，适配批量创作、自动化工作流等场景。"
)
PUBLISH_ENTRY_URL = (
    "https://creator.douyin.com/creator-micro/content/manage?enter_from=publish"
)
PUBLISH_IMAGE_URL = "https://creator.douyin.com/creator-micro/content/upload?type=image"

SKILL_DIR = Path(__file__).resolve().parent.parent  # auto_public_douyin/
USER_DATA_DIR = SKILL_DIR / "user_data"
LOGS_DIR = SKILL_DIR / "logs"
ASSETS_DIR = SKILL_DIR / "assets"

STEP_TIMEOUT_MS = 30_000  # 单步 30s


# ---------- 工具函数 ----------


def log(msg: str) -> None:
    print(f"[douyin-publish] {msg}", flush=True)


def resolve_image_path(raw: str) -> Path:
    """找到图片文件绝对路径：
    1) 绝对/相对路径直接存在
    2) auto_public_douyin/assets/<raw>
    3) ~/Desktop/<raw>, ~/Downloads/<raw>
    """
    p = Path(raw).expanduser()
    if p.is_file():
        return p.resolve()

    candidates = [
        ASSETS_DIR / raw,
        Path.home() / raw,
        Path.home() / "Desktop" / raw,
        Path.home() / "Downloads" / raw,
        SKILL_DIR / raw,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    raise FileNotFoundError(
        f"未找到图片 {raw!r}。请用 --image 指定绝对路径，或将图片放到 {ASSETS_DIR}"
    )


def take_screenshot(page: Page, name: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / f"{int(time.time())}_{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        log(f"📸 截图已保存: {path}")
    except Exception as e:  # noqa: BLE001
        log(f"截图失败: {e}")


# ---------- 核心流程 ----------


def launch_context(p, headless: bool) -> BrowserContext:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    log(f"使用 Chrome profile: {USER_DATA_DIR}")
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR),
        headless=headless,
        viewport={"width": 1440, "height": 900},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-default-browser-check",
        ],
        locale="zh-CN",
    )
    return ctx


def login_only(headless: bool) -> None:
    """仅打开登录页，供首次扫码登录。"""
    log("打开登录页面，请在浏览器中完成扫码登录后关闭窗口…")
    with sync_playwright() as p:
        ctx = launch_context(p, headless=False)  # 登录必须有界面
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://creator.douyin.com/", wait_until="domcontentloaded")
        # 等待用户手动关闭窗口
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:  # noqa: BLE001
            pass
        finally:
            ctx.close()
    log("登录流程结束。下次可直接调用发布脚本。")


def click_by_text_any(page: Page, texts: List[str], timeout: int = STEP_TIMEOUT_MS) -> bool:
    """按给定的文本列表依次尝试点击第一个可见元素。"""
    deadline = time.time() + timeout / 1000
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        for t in texts:
            try:
                loc = page.get_by_text(t, exact=False).first
                if loc.is_visible():
                    loc.click(timeout=3_000)
                    log(f"✅ 点击文本: {t!r}")
                    return True
            except Exception as e:  # noqa: BLE001
                last_err = e
        page.wait_for_timeout(500)
    if last_err:
        log(f"⚠️ 点击失败 last_err: {last_err}")
    return False


def find_file_input(page: Page, timeout: int = STEP_TIMEOUT_MS):
    """寻找文件上传 input[type=file]（可能藏在 iframe 内）。"""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        # 主 frame
        for f in [page] + list(page.frames):
            try:
                inp = f.locator("input[type='file']").first
                if inp.count() > 0:
                    return inp
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(500)
    raise PlaywrightTimeoutError("未找到 input[type=file] 上传控件")


def publish(
    images: List[Path],
    title: str,
    content: str,
    headless: bool,
    dry_run: bool,
) -> None:
    with sync_playwright() as p:
        ctx = launch_context(p, headless=headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(STEP_TIMEOUT_MS)

        try:
            # Step 1: 打开发布入口
            log(f"🌐 打开 {PUBLISH_ENTRY_URL}")
            try:
                page.goto(PUBLISH_ENTRY_URL, wait_until="domcontentloaded", timeout=60_000)
            except PlaywrightTimeoutError:
                log("⚠️ 页面加载超时，继续尝试...")
            page.wait_for_timeout(5_000)

            # 检查登录
            if "login" in page.url or page.get_by_text("扫码登录").count() > 0:
                take_screenshot(page, "need_login")
                raise RuntimeError("未登录。请先运行: python publish_douyin.py --login")

            # Step 2-3: 进入文章发布页
            log("➡️ 进入文章发布页")
            if "upload" not in page.url:
                if not click_by_text_any(page, ["高清发布", "发布作品"]):
                    take_screenshot(page, "step2_hd_publish_fail")
                    raise RuntimeError("找不到「高清发布」按钮")
                page.wait_for_timeout(2_000)

            # 先尝试点击左侧展开菜单里的「发布文章」项
            log("➡️ 点击左侧菜单「发布文章」")
            menu_clicked = page.evaluate("""() => {
                const all = Array.from(document.querySelectorAll('*'));
                // 找左侧菜单里的「发布文章」：x 坐标较小（左侧），y 坐标 > 100（菜单区域）
                const candidates = all.filter(e => {
                    const t = (e.textContent || '').trim();
                    return t === '发布文章';
                }).filter(e => {
                    const r = e.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && r.left < 200 && r.top > 80;
                });
                if (candidates.length === 0) return false;
                // 找最上面的那个（y 最小）
                candidates.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
                const target = candidates[0];
                target.click();
                target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                // 同时尝试找到其父级 a 或 div 再点击一次
                let p = target.parentElement;
                for (let i = 0; i < 3 && p; i++, p = p.parentElement) {
                    p.click();
                    p.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                }
                return true;
            }""")
            if menu_clicked:
                log("✅ 已点击左侧菜单「发布文章」")
            else:
                log("⚠️ 左侧菜单未找到，尝试顶部标签...")
                page.evaluate("""() => {
                    const all = Array.from(document.querySelectorAll('*'));
                    const el = all.find(e => (e.textContent || '').trim() === '发布文章');
                    if (el) {
                        el.click();
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        let p = el.parentElement;
                        for (let i = 0; i < 3 && p; i++, p = p.parentElement) {
                            p.click();
                            p.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        }
                    }
                }""")
            page.wait_for_timeout(4_000)

            # Step 4: 文章发布页 - 处理提示并进入编辑器
            log("➡️ 进入文章编辑器")
            # 用 JS 点击「继续编辑」或「我要发文」
            editor_opened = page.evaluate("""() => {
                const all = Array.from(document.querySelectorAll('*'));
                // 先尝试「继续编辑」
                const continueEdit = all.find(e => (e.textContent || '').trim() === '继续编辑');
                if (continueEdit) {
                    continueEdit.click();
                    continueEdit.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    return 'continue_edit';
                }
                // 否则尝试「我要发文」
                const startBtn = all.find(e => {
                    const t = (e.textContent || '').trim();
                    return t === '我要发文' || t === '开始创作';
                });
                if (startBtn) {
                    startBtn.click();
                    startBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    return 'start_create';
                }
                return 'not_found';
            }""")
            log(f"✅ JS 点击编辑器入口: {editor_opened}")
            page.wait_for_timeout(4_000)

            # 如果仍在文章首页，再次尝试点击「我要发文」
            if page.locator("text=抖音等你大作文章").count() > 0:
                log("⚠️ 仍在文章首页，再次点击「我要发文」")
                click_by_text_any(page, ["我要发文"], timeout=3_000)
                page.wait_for_timeout(3_000)
            
            # Step 5: 填入标题
            log(f"✍️ 填入标题: {title}")
            title_filled = False
            for sel in [
                "input[placeholder*='标题']",
                "textarea[placeholder*='标题']",
                "input[placeholder*='请输入']",
                "input[type='text']",
            ]:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.click()
                    loc.fill("")
                    loc.type(title, delay=20)
                    title_filled = True
                    log(f"✅ 通过 selector 填入标题: {sel}")
                    break
            if not title_filled:
                take_screenshot(page, "step5_title_fail")
                raise RuntimeError("找不到标题输入框")
            
            # Step 6: 填入正文（文章编辑器通常是 contenteditable）
            if content:
                log("✍️ 填入正文")
                body = page.locator("div[contenteditable='true']").first
                if body.count() > 0 and body.is_visible():
                    body.click()
                    # 先清空
                    page.keyboard.press("Control+a")
                    page.keyboard.press("Delete")
                    # 分段输入
                    for paragraph in content.split("\n"):
                        if paragraph.strip():
                            body.type(paragraph.strip(), delay=10)
                            page.keyboard.press("Enter")
                    log("✅ 正文已填入")
                else:
                    log("⚠️ 未找到正文编辑区域")
            
            # Step 7: 在文章中插入图片
            log("➡️ 插入图片到文章")
            abs_paths = [str(p_.resolve()) for p_ in images]
            # 先点击正文区域，然后找插入图片按钮
            body = page.locator("div[contenteditable='true']").first
            if body.count() > 0:
                body.click()
            page.wait_for_timeout(500)
            
            upload_success = False
            # 策略1: 找编辑器工具栏的「图片」按钮
            for img_label in ["图片", "插入图片", "上传图片"]:
                try:
                    img_btn = page.get_by_text(img_label, exact=False).first
                    if img_btn.count() > 0 and img_btn.is_visible():
                        with page.expect_file_chooser(timeout=5_000) as fc_info:
                            img_btn.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(abs_paths)
                        log(f"📎 通过编辑器图片按钮上传: {abs_paths}")
                        upload_success = True
                        break
                except Exception:  # noqa: BLE001
                    continue
            
            # 策略2: 直接拖拽图片到编辑器
            if not upload_success and body.count() > 0:
                log("📎 通过拖拽上传图片到编辑器")
                for p_ in abs_paths:
                    with open(p_, "rb") as f:
                        data = f.read()
                    import base64
                    b64 = base64.b64encode(data).decode()
                    page.evaluate(
                        """([editor, dataUrl, fileName]) => {
                            const dropEvent = new DragEvent('drop', {
                                bubbles: true,
                                cancelable: true,
                                dataTransfer: new DataTransfer()
                            });
                            const blob = new Blob([Uint8Array.from(atob(dataUrl), c => c.charCodeAt(0))]);
                            const file = new File([blob], fileName, { type: 'image/png' });
                            dropEvent.dataTransfer.items.add(file);
                            (editor || document.body).dispatchEvent(dropEvent);
                        }""",
                        [body.element_handle(), b64, Path(p_).name],
                    )
                    page.wait_for_timeout(1_000)
                upload_success = True
            
            if not upload_success:
                log("⚠️ 图片插入未成功，继续执行...")
            
            page.wait_for_timeout(3_000)
            
            # Step 8: 处理图片编辑弹窗并发布
            log("⬇️ 滚动到底部")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1_000)
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(500)
            
            # 关闭可能的图片编辑弹窗
            for btn_text in ["确定", "完成", "确认"]:
                try:
                    modal_btn = page.get_by_role("button", name=btn_text).first
                    if modal_btn.count() > 0 and modal_btn.is_visible():
                        modal_btn.click()
                        log(f"✅ 关闭弹窗: {btn_text}")
                        page.wait_for_timeout(1_000)
                        break
                except Exception:  # noqa: BLE001
                    pass
            
            if dry_run:
                take_screenshot(page, "dry_run_before_publish")
                log("🧪 --dry-run 模式，准备好但不点击「发布」。")
                log("请检查浏览器内容，10 秒后关闭。")
                page.wait_for_timeout(10_000)
                return
            
            log("🚀 点击「发布」")
            publish_clicked = False
            # 优先用 JS 点击，避免弹窗遮挡
            publish_clicked = page.evaluate("""() => {
                const all = Array.from(document.querySelectorAll('button, div, span'));
                const btn = all.find(e => (e.textContent || '').trim() === '发布');
                if (btn) { btn.click(); btn.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }
                const btn2 = all.find(e => (e.textContent || '').trim() === '立即发布');
                if (btn2) { btn2.click(); btn2.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }
                return false;
            }""")
            if publish_clicked:
                log("✅ 通过 JS 点击发布")
            
            if not publish_clicked:
                take_screenshot(page, "step7_publish_fail")
                raise RuntimeError("找不到「发布」按钮")
            
            page.wait_for_timeout(6_000)
            take_screenshot(page, "after_publish")
            log("🎉 发布流程已触发，请在浏览器确认结果。")

        except Exception as e:  # noqa: BLE001
            take_screenshot(page, "error")
            log(f"❌ 发布失败: {e}")
            raise
        finally:
            # 留几秒便于观察
            if not headless:
                page.wait_for_timeout(3_000)
            ctx.close()


# ---------- CLI ----------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抖音创作者中心图文自动发布")
    parser.add_argument(
        "--image",
        action="append",
        default=None,
        help=f"要上传的图片路径，可多次指定。默认: {DEFAULT_IMAGE_NAME}",
    )
    parser.add_argument("--title", default=DEFAULT_TITLE, help="图文标题")
    parser.add_argument("--content", default=DEFAULT_CONTENT, help="正文描述（可选）")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--login", action="store_true", help="仅打开登录页")
    parser.add_argument("--dry-run", action="store_true", help="走完流程但不点发布")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.login:
        login_only(headless=False)
        return 0

    raw_images = args.image or [DEFAULT_IMAGE_NAME]
    try:
        images = [resolve_image_path(x) for x in raw_images]
    except FileNotFoundError as e:
        log(str(e))
        return 2

    log(f"图片: {[str(i) for i in images]}")
    log(f"标题: {args.title}")
    log(f"正文: {args.content or '(空)'}")

    try:
        publish(
            images=images,
            title=args.title,
            content=args.content,
            headless=args.headless,
            dry_run=args.dry_run,
        )
    except Exception as e:  # noqa: BLE001
        log(f"终止: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
