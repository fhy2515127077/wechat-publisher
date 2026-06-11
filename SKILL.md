---
name: wechat-publisher
description: |
  公众号文章自动化发布 pipeline：Markdown 写作 → 微信排版 HTML → wechatpy 发布。
  触发词：发布公众号、发文章、排版文章、公众号发布、自动推送。
  配合 khazix-writer 生成内容后，用本 skill 完成排版和发布。
---

# 公众号自动发布 Pipeline

## 流程概览

```
khazix-writer（生成Markdown）
    ↓
format_wechat.py（Markdown → 微信排版HTML）
    ↓
publish.py（wechatpy → 公众号草稿/发布）
```

## 文件结构

```
~/.hermes/skills/wechat-publisher/
├── SKILL.md                  # 本文件
├── scripts/
│   ├── format_wechat.py      # 排版引擎：Markdown → 微信HTML
│   ├── publish.py            # 发布脚本：wechatpy API
│   ├── pipeline.py           # 主控脚本：串联全流程
│   └── config.json           # 凭证配置（appid/appsecret等）
├── templates/
│   ├── default.json          # 默认排版模板（蓝色调科技风）
│   └── minimal.json          # 极简模板（衬线字体散文风）
├── references/
│   ├── setup_guide.md        # 首次配置指南（凭证、白名单、权限）
│   ├── template_guide.md     # 模板自定义指南
│   └── wechat_api_errcodes.md # API错误码参考
└── output/                   # 生成的HTML输出目录
```

## 使用方式

### 1. 首次配置
```bash
# 安装依赖
pip install wechatpy markdown2 yattag

# 编辑配置填入凭证
# 修改 scripts/config.json
```

### 2. 手动发布
```bash
# 仅排版（不发布）— 不传 --title 则正文不插入标题
python scripts/format_wechat.py input.md -t default -o output/article.html

# 排版 + 指定标题（标题会插入正文顶部居中显示）
python scripts/format_wechat.py input.md -t default --title "文章标题" -o output/article.html

# 排版 + 发布到草稿箱
python scripts/publish.py --draft output/article.html --title "文章标题"

# 排版 + 直接发布
python scripts/publish.py --publish output/article.html --title "文章标题"

# 一键流水线：从Markdown到发布
python scripts/pipeline.py input.md --title "文章标题" --author "作者"
```

### Markdown 强调语法

`format_wechat.py` 支持 `==文字==` 语法，渲染为 `#e9e8e8` 灰色背景高亮，用于标记需要强调的句子。这是用户的首选强调方式（替代加粗+背景色）。

```markdown
==这是需要强调的句子，会显示灰色背景==
```

### 3. Cron 定时发布
配合 Hermes cron，实现定时自动生成+发布。

## 排版模板

模板定义在 `templates/` 目录，用 `-t 模板名` 指定。当前可用模板：

| 模板 | 文件名 | 风格 | 适用场景 |
|------|--------|------|---------|
| 极简黑白灰 | `default` | 黑白灰、底线标题、强调句灰底 | 技术/观点类（用户首选） |
| 红色标题极简 | `red-minimal` | 红色标题、无装饰线、参考赛博禅心 | 科技产品/深度分析 |
| 暖色文艺 | `warm-literary` | 衬线字体、暖棕色调、首行缩进 | 人文/情感/散文类 |
| 暗黑高级 | `dark-elegant` | 深色背景、金色标题、极客风 | 产品发布/技术文档 |

模板支持：自定义字体、颜色、间距、标题样式、引用框、代码块、文末引导模块等。

### 用户首选排版风格（default.json — 极简黑白灰）

default.json 已按用户偏好定制为极简风格，核心参数：
- **字号** 15px，**行高** 1.6，**字间距** 0.5px
- **两端对齐** (text-align: justify)
- **段后距** 24px（margin: 0 0 24px 0）
- **两端缩进** 8px（padding: 0 8px）
- **图片圆角** 8px
- **色调** 纯黑白灰，无彩色元素
- **加粗** 无背景色，纯文字加粗（strong 背景 transparent）
- **强调高亮** 用 `==文字==` 语法，渲染为 `background: #e9e8e8` 的 span（不用加粗）
- **代码块** 浅灰背景 #f5f5f5，非深色主题
- **标题** 左对齐，无居中。H2 有 1px #cccccc 底线装饰，H3 无底线
- 标题层级：H1 20px / H2 18px / H3 16px
- **正文不放标题** 文章正文区不插入居中大标题，直接从内容开始

参考风格来源：AIGCLAB 公众号文章排版。新建模板时以此为基准调整。

## 排版语法扩展

### ==强调== 语法
在 Markdown 中用 `==文字==` 标记需要高亮的句子，排版后渲染为带背景色的 span，不加粗。**背景色和文字颜色跟随模板自动适配**（通过模板 JSON 中的 `emphasis` 字段配置）。

各模板默认强调色：
- default / red-minimal：浅灰底 `#e9e8e8`
- warm-literary：暖棕底 `#f5e6d0` + 棕色字
- dark-elegant：深灰底 `#333333` + 金色字 `#d4a843`

模板中添加 `emphasis` 字段即可自定义：
```json
"emphasis": {"background": "#e9e8e8", "padding": "2px 4px", "color": ""}
```
`color` 为空则不设置文字颜色，继承正文色。

```markdown
==这是一句需要强调的话==
```

### 不输出标题
调用 `format_wechat.py` 时不传 `--title`，文章直接从正文开始，不会在顶部渲染居中标题。

## markdown2 兼容性 Pitfalls

- **codehilite div**：markdown2 的 `fenced-code-blocks` + `code-friendly` extras 会生成 `<div class="codehilite">` 而非 `<pre><code>`。`format_wechat.py` 已内置转换逻辑，将 codehilite div 提取内容后转为单个 `<pre>` 标签。
- **嵌套标签导致微信崩溃**：微信编辑器对 `<pre><code>` 嵌套结构解析不稳定，可能导致内容折叠或编辑器崩溃。解决办法：合并为单个 `<pre>` 标签，样式全部内联。
- **overflow: hidden 导致内容裁切**：`<pre>` 或 `<code>` 上的 `overflow: hidden` 会隐藏代码内容。避免使用。
- **span 语法高亮标签**：markdown2 会给代码加 `<span class="c1">` 等高亮标签，微信不支持。`format_wechat.py` 会自动清理这些 span。

## 注意事项

详见 `references/setup_and_pitfalls.md`，包含：
- IP白名单配置
- 订阅号/服务号权限差异
- Windows Python超时问题
- execute_code凭证审查绕过
- Grsai图片API使用方法

详见 `references/wechat_html_compat.md`，包含：
- 微信编辑器支持的 CSS 属性
- markdown2 输出的 HTML 结构
- 微信文章图片规则

## 开源仓库

GitHub: https://github.com/fhy2515127077/wechat-publisher (MIT)

## Pitfalls

`wechat-mp-publish` 是本 skill 的早期版本，侧重 API 代码示例。本 skill（wechat-publisher）已包含完整的排版引擎、模板系统和发布脚本，是当前主力 skill。如需合并，请将 wechat-mp-publish 中的 wechatpy API 细节（access_token 刷新、素材上传、freepublish 异步轮询）迁移到本 skill 的 references/ 下后删除旧 skill。

## 排版调试流程

修改模板后，用以下流程验证：
1. 写一个测试 `.md` 文件（含标题/段落/加粗/引用/代码块/图片/列表）
2. `python scripts/format_wechat.py test.md -t default --title "测试" -o output/test.html`
3. 浏览器打开生成的 HTML 文件，截图检查各项样式
4. 确认无误后再用于正式文章

## Pitfalls

- **IP 白名单**：首次使用必须在公众号后台添加服务器公网 IP 到白名单，否则 API 返回 errcode 40164。详见 `references/setup_guide.md`。
- **标题重复**：如果 Markdown 文件里有 H1 标题，又通过 `--title` 传了标题，排版时会自动移除 Markdown 中的第一个 H1 避免重复。这是 `format_wechat.py` 的内置行为。
- **封面图必须有**：发布接口要求 `thumb_media_id`，没有封面图会报错。可先用 `--draft` 存草稿，后台手动加封面后再发布。
- **订阅号权限不足**：未认证的订阅号没有草稿/发布 API 权限，会返回 errcode 48001。需升级为认证服务号或确认已开通接口权限。
- **标题底线层级**：用户要求只有 H2（大标题/章节标题）有底线装饰，H3（小标题）不要底线。修改模板时注意 H3 的 `border_bottom` 应为 `"none"`。
- **强调用 == 语法不用加粗**：用户明确要求加粗（strong）不加背景色，需要高亮的句子用 `==文字==` 语法。不要用 `**文字**` 做强调高亮。
- **正文不放标题**：用户要求文章正文区不插入居中大标题，直接从正文内容开始。排版时不传 `--title` 参数，标题在公众号后台单独设置。
- **markdown2 codehilite 导致代码块空白**：markdown2 使用 `code-friendly` extra 时，代码块会生成 `<div class="codehilite"><p ...re><code>...</code></pre></div>` 结构，而非标准的 `<pre><code>`。WeChat 渲染器无法正确显示这种结构，导致代码块显示为空白。**已修复**：`format_wechat.py` 的 `inject_styles` 函数会先将 `codehilite` div 转换为带样式的 `<pre><code>` 块，再清理内部的 span 标签。如果未来 markdown2 版本变化导致代码块再次异常，检查生成的 HTML 中代码块的 DOM 结构。

## 常见问题与 Pitfalls

### IP 白名单（最常见）
首次调用微信 API 会报 `errcode: 40164, "invalid ip xxx, not in whitelist"`。
**解决**：登录 mp.weixin.qq.com → 设置与开发 → 基本配置 → IP白名单 → 添加当前公网 IP。
可以用 `curl -s https://httpbin.org/ip` 或 `curl -s https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=APPID&secret=SECRET` 看到当前 IP。

### 排版 H1 去重
`format_wechat.py` 会在传入 `--title` 时自动移除 Markdown 中的第一个 H1 标题，避免标题重复显示。如果你的 Markdown 本身没有 H1，不受影响。

### 模板自定义
模板是 JSON 文件（`templates/*.json`），每个元素对应一组 CSS 属性（key 用下划线，输出转连字符）。
修改后立即生效，无需重启。可新增模板文件，用 `-t 模板名` 指定。
参考 `references/template_guide.md` 了解全部可调参数。

### 网络问题排查
Python `urllib` 在 Windows Git Bash 环境下有时会超时（即使 curl 正常）。
优先用 `curl` 做 API 连通性测试，确认 IP 白名单和凭证正确后再用 Python 脚本。
