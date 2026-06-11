# 📝 WeChat Publisher

微信公众号文章自动发布工具。Markdown 写作 → 一键排版 → 推送草稿/发布。

## ✨ 特性

- **Markdown → 微信排版 HTML**：自动转换，内联样式，兼容微信编辑器
- **4 套排版模板**：极简黑白灰、红色标题、暖色文艺、暗黑高级
- **`==强调==` 语法**：高亮重要句子，背景色跟随模板自动适配
- **代码块美化**：浅灰背景 + 顶部装饰线 + 圆角
- **一键发布**：草稿箱 / 直接发布，支持封面图上传
- **多工具支持**：Claude Code、Cursor、Copilot 等 Agent 集成

## 📦 安装

```bash
pip install markdown2
```

## 🚀 快速开始

### 仅排版

```bash
python scripts/format_wechat.py article.md -t default -o output.html
```

### 排版 + 推送草稿

```bash
python scripts/publish.py --draft output.html --title "文章标题" --cover cover.jpg
```

### 从 Markdown 一键发布

```bash
python scripts/publish.py --from-md article.md --title "文章标题" --cover cover.jpg
```

## 🎨 排版模板

| 模板 | 命令 | 风格 |
|------|------|------|
| 极简黑白灰 | `-t default` | 黑白灰、底线标题、强调句灰底 |
| 红色标题极简 | `-t red-minimal` | 红色标题、无装饰、科技感 |
| 暖色文艺 | `-t warm-literary` | 衬线字体、暖棕色调、文学风 |
| 暗黑高级 | `-t dark-elegant` | 深色背景、金色点缀、极客风 |

### 模板预览

在 `templates/` 目录下有对应的 JSON 文件，可自由修改颜色、字体、间距等参数。

## 📝 排版语法

### 强调文字

用 `==文字==` 标记需要高亮的句子，背景色自动适配模板：

```markdown
这是一个==重要观点==，需要特别注意。
```

### 代码块

标准 Markdown 代码块，自动渲染为浅灰背景 + 顶部装饰线：

````markdown
```bash
echo "Hello World"
```
````

## ⚙️ 配置

首次使用需配置公众号凭证，编辑 `scripts/config.json`：

```json
{
    "app_id": "你的AppID",
    "app_secret": "你的AppSecret",
    "author": "作者名"
}
```

### IP 白名单

登录 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 设置与开发 → 基本配置 → IP白名单，添加你的公网 IP。

## 📁 项目结构

```
wechat-publisher/
├── SKILL.md                  # Hermes Skill 配置
├── scripts/
│   ├── format_wechat.py      # 排版引擎
│   ├── publish.py            # 发布脚本
│   └── config.json           # 凭证配置（git忽略）
├── templates/
│   ├── default.json          # 极简黑白灰
│   ├── red-minimal.json      # 红色标题极简
│   ├── warm-literary.json    # 暖色文艺
│   └── dark-elegant.json     # 暗黑高级
├── references/
│   └── setup_guide.md        # 配置指南
└── output/                   # 生成文件（git忽略）
```

## 📄 License

MIT
