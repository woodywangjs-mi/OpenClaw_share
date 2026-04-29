# Reference — 抖音图文自动发布

## 目录结构

```
auto_public_douyin/
├── SKILL.md              # Skill 主入口，供 OpenClaw / Qoder 自动发现
├── reference.md          # 本文件：排错与扩展说明
├── requirements.txt      # Python 依赖
├── scripts/
│   └── publish_douyin.py # 主自动化脚本（Playwright）
├── assets/               # 可选：默认图片存放位置
├── user_data/            # Chrome 持久化登录态（自动生成，勿提交 Git）
└── logs/                 # 运行截图日志（自动生成）
```

## 完整环境准备

```bash
cd /Users/woody/Local\ Files/LLMStudy/LLMStudy/AI_project/auto_public_douyin

# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Chromium 浏览器（首次必须）
python -m playwright install chromium
```

## 首次登录（只做一次）

```bash
python scripts/publish_douyin.py --login
```

在弹出的浏览器中扫码登录抖音创作者账号，登录成功后直接关闭浏览器窗口。Cookies 会保存在 `user_data/`，后续调用自动复用。

## 使用示例

```bash
# 使用默认参数（与本次任务一致）
python scripts/publish_douyin.py

# 指定图片和标题
python scripts/publish_douyin.py \
  --image "/Users/woody/Desktop/Gemini_Generated_Image_qgdp0yqgdp0yqgdp.png" \
  --title "GPT Image2 使用教程"

# 多图上传 + 正文
python scripts/publish_douyin.py \
  --image a.png --image b.png \
  --title "教程标题" \
  --content "这是一段图文描述"

# 调试模式：走流程但不真正点「发布」
python scripts/publish_douyin.py --dry-run
```

## OpenClaw 调用

在 OpenClaw 的工具定义里注册一个 shell-type 工具：

```yaml
- name: douyin_auto_publish
  command: python
  args:
    - /Users/woody/Local Files/LLMStudy/LLMStudy/AI_project/auto_public_douyin/scripts/publish_douyin.py
    - --image
    - "{{ image_path }}"
    - --title
    - "{{ title }}"
```

或直接让 LLM 生成 shell 命令调用本脚本。

## 常见问题排查

1. **报错「未登录」** → 先运行 `--login` 扫码登录。
2. **找不到某个按钮** → `logs/` 下有对应步骤截图；如果抖音前端改版，修改 `click_by_text_any()` 传入的候选文本列表即可。
3. **上传控件找不到** → 脚本已遍历主 frame 与所有 iframe 查找 `input[type=file]`。若仍失败，说明点击卡片未触发文件选择框，请手动在 dry-run 模式下观察一次 DOM。
4. **图片不存在** → 把图片放进 `auto_public_douyin/assets/` 目录，或用 `--image` 指定绝对路径。
5. **被风控出现验证码** → 脚本不会绕过验证，请在有界面模式下人工完成，然后脚本会继续运行。

## 设计要点

- **持久化登录**：`launch_persistent_context(user_data_dir=...)`，避免每次扫码。
- **反自动化检测**：启动参数添加 `--disable-blink-features=AutomationControlled`。
- **鲁棒选择器**：使用 `get_by_text` + `get_by_role` 的组合，减少因 class 改变导致的失败。
- **失败可视化**：任一关键步骤失败都会在 `logs/` 目录生成 PNG 截图。
