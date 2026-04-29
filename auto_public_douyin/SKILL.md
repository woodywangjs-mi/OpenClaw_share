---
name: douyin-auto-publish
description: Automate publishing image-text posts to Douyin Creator Platform via Chrome. Opens creator.douyin.com, selects HD publish, chooses image-text mode, uploads a local image, fills in the title, and clicks publish. Use when the user asks to auto-publish, 一键发布, 自动发布抖音图文, douyin automation, or 抖音创作者中心自动上传.
---

# Douyin Auto Publish (抖音图文自动发布)

该 Skill 使用 Playwright 操控本机 Chrome/Chromium，自动完成抖音创作者中心的图文发布流程：

1. 打开 `https://creator.douyin.com/creator-micro/content/manage?enter_from=publish`
2. 点击「高清发布」
3. 点击「发布图文」
4. 点击「上传图文」并选择本地图片
5. 填入标题
6. 滚动到底部并点击「发布」按钮

## 何时调用

当用户出现以下意图时调用本 Skill：

- 自动发布抖音图文 / 一键发布
- 抖音创作者中心上传
- OpenClaw 调度自动化浏览器操作发抖音

## 快速开始

### 1. 首次环境准备

```bash
cd /Users/woody/Local\ Files/LLMStudy/LLMStudy/AI_project/auto_public_douyin
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. 登录抖音（只需做一次）

脚本使用独立的 `user_data/` 作为 Chrome profile，首次需要手动登录一次：

```bash
python scripts/publish_douyin.py --login
```

在弹出的浏览器里扫码登录抖音创作者账号，登录成功后关闭窗口。之后再次调用会自动复用登录态。

### 3. 执行自动发布

```bash
python scripts/publish_douyin.py \
  --image "/absolute/path/to/Gemini_Generated_Image_qgdp0yqgdp0yqgdp.png" \
  --title "GPT Image2 使用教程"
```

如需默认值（本任务固定参数），直接：

```bash
python scripts/publish_douyin.py
```

此时脚本会使用内置默认：图片文件名 `Gemini_Generated_Image_qgdp0yqgdp0yqgdp.png`（优先查找同目录 `assets/`，找不到则查找用户桌面和下载目录），标题 `GPT Image2 使用教程`。

## 参数说明

| 参数 | 说明 | 默认 |
|------|------|------|
| `--image` | 要上传的图片绝对路径，可多次指定上传多张 | `Gemini_Generated_Image_qgdp0yqgdp0yqgdp.png` |
| `--title` | 图文标题 | `GPT Image2 使用教程` |
| `--content` | 正文描述（可选） | 空 |
| `--headless` | 无头模式运行 | False（默认有界面） |
| `--login` | 仅打开登录窗口，用于首次登录 | False |
| `--dry-run` | 到达发布按钮前停下，不真正点击「发布」 | False |

## OpenClaw 调用方式

OpenClaw 可通过 Shell 工具直接调用脚本：

```json
{
  "tool": "shell",
  "command": "python /Users/woody/Local Files/LLMStudy/LLMStudy/AI_project/auto_public_douyin/scripts/publish_douyin.py --image '<img_abs_path>' --title '<title>'"
}
```

或在 Agent 对话里说：「用 douyin-auto-publish 发布 xxx.png，标题 yyy」，Qoder 会自动匹配本 Skill。

## 选择器策略

抖音前端会偶尔调整 DOM，脚本采用「文案优先 + role 选择器兜底」的策略：

- `page.get_by_text("高清发布")` / `page.get_by_role("button", name="发布")`
- 若某一步超时，脚本会截图到 `logs/step_<n>.png` 方便排查

## 其他

- 详细排错与选择器调整，见 [reference.md](reference.md)
- 该脚本不会跳过抖音人机验证，如被风控请在有界面模式下人工完成验证后继续
