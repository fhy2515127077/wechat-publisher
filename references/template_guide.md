# 模板自定义指南

## ==强调文字== 语法

`format_wechat.py` 支持 Markdown 扩展语法 `==文字==`，渲染为带背景色的 `<span>`。这是用户首选的强调方式——不用加粗，纯背景色高亮。

```markdown
==这是需要强调的句子==
```

渲染结果（背景色从模板 emphasis 配置读取）：
```html
<span style="background: #e9e8e8; padding: 2px 4px;">这是需要强调的句子</span>
```

### emphasis 配置

在模板 JSON 中添加 `emphasis` 字段，控制强调文字的样式：

```json
{
  "emphasis": {
    "background": "#e9e8e8",
    "padding": "2px 4px",
    "color": ""
  }
}
```

- `background`：背景色（必填）
- `padding`：内边距（默认 2px 4px）
- `color`：文字颜色（留空则继承正文色）

**深色模板务必设置 `color` 为亮色**，否则强调文字在深色背景下不可见。

各模板的 emphasis 配置参考：

| 模板 | background | color | 说明 |
|------|-----------|-------|------|
| default | #e9e8e8 | （空） | 浅灰底，继承正文色 |
| red-minimal | #e9e8e8 | （空） | 同上 |
| warm-literary | #f5e6d0 | #8b4513 | 暖棕底 + 棕色字 |
| dark-elegant | #333333 | #d4a843 | 深灰底 + 金字 |

## 模板文件结构

每个模板是 `templates/<name>.json`，顶层 key 是元素名，值是 CSS 属性对象（下划线转连字符）。

```json
{
  "name": "模板显示名",
  "description": "模板描述",
  "body": { "font_size": "15px", "color": "#333333", "text_align": "justify", ... },
  "title": { "font_size": "22px", "text_align": "center", ... },
  "h1": { "border_bottom": "2px solid #1e90ff", ... },
  "emphasis": { "background": "#e9e8e8", "padding": "2px 4px", "color": "" },
  ...
}
```

## 全部可调元素

| 元素 | 说明 | 常改属性 |
|------|------|---------|
| `body` | 整体容器 | font_size, color, line_height, font_family, background, letter_spacing, padding, text_align |
| `title` | 文章大标题 | font_size, color, text_align, margin |
| `author` | 作者署名 | font_size, color, text_align |
| `date` | 发布日期 | font_size, color, text_align |
| `h1` | 一级标题 | font_size, color, border_bottom, margin |
| `h2` | 二级标题 | font_size, color, border_bottom, margin |
| `h3` | 三级标题 | font_size, color, margin |
| `p` | 段落 | margin, line_height, text_indent |
| `strong` | 加粗 | color, font_weight, background, padding, border_radius |
| `em` | 斜体 | color, font_style |
| `a` | 链接 | color, text-decoration |
| `blockquote` | 引用块 | border_left, padding, background, color, border_radius |
| `code_inline` | 行内代码 | background, color, padding, border_radius |
| `code_block` | 代码块 | background, color, padding, border_radius, font_size, border_top |
| `pre` | 代码块外层 | margin, padding |
| `img` | 图片 | max_width, border_radius, margin |
| `hr` | 分隔线 | border, margin |
| `ul` / `ol` | 列表 | padding_left, margin |
| `li` | 列表项 | margin, line_height |
| `table` / `th` / `td` | 表格 | border-collapse, border, padding, background |
| `footer` | 文末引导 | text_align, margin, padding, border_top, font_size, color |
| `emphasis` | ==强调== 语法 | background, padding, color |

## 常见风格速查

### 极简黑白灰（当前 default.json）
- 正文：15px / 两端对齐 / 行高1.6 / 字间距0.5px / 段后距24px / 两端缩进8px
- 色调：纯黑白灰，无彩色
- 标题：仅 H2 有底线（`1px solid #cccccc`），H3 无底线（`border_bottom: none`）
- 代码块/引用块：浅灰背景 `#f5f5f5` + 圆角 4px
- 强调：用 `==文字==` 语法，`background: #e9e8e8`，不用加粗
- 图片圆角：8px
- 参考来源：AIGCLAB 公众号

### 红色标题极简（red-minimal.json）
- 标题：红色 `#e74c3c`，无底线装饰
- 代码块顶部边线：红色 `#e74c3c`
- 参考来源：赛博禅心公众号

### 暖色文艺（warm-literary.json）
- 字体：Georgia / Noto Serif SC 衬线字体
- 背景：暖米色 `#fffdf7`
- 标题：暖棕色 `#8b4513`
- 段落首行缩进 2em
- 强调：暖棕底 `#f5e6d0` + 棕色字

### 暗黑高级（dark-elegant.json）
- 背景：深色 `#1a1a1a`
- 标题/强调色：金色 `#d4a843`
- 强调：深灰底 `#333333` + 金字
- 代码块：深灰背景 `#2a2a2a`

### 蓝色科技风
- 引用块左边线：`#1e90ff`
- h1 底线：`2px solid #1e90ff`
- 链接色：`#576b95`

## 新增模板

1. 复制 `templates/default.json` → `templates/mytemplate.json`
2. 修改样式值
3. **深色模板**务必添加 `emphasis` 配置并设置 `color` 为亮色
4. 使用时指定 `-t mytemplate`
