# 微信公众号 HTML 兼容性备忘

## 微信编辑器支持的 CSS
- ✅ 内联 style（所有样式必须写在 style 属性里）
- ✅ border, border-radius, background, padding, margin
- ✅ font-size, color, line-height, letter-spacing, text-align
- ✅ display: block/inline-block
- ❌ `<style>` 标签（会被剥离）
- ❌ class 选择器
- ❌ ::before / ::after 伪元素
- ❌ box-shadow（部分版本不支持）
- ⚠️ `<table>` 支持有限，建议内联样式
- ⚠️ `<pre><code>` 嵌套可能不稳定，建议用单个 `<pre>`

## markdown2 输出结构
- `fenced-code-blocks` extra → `<div class="codehilite"><pre><code>...</code></pre></div>`
- `tables` extra → 标准 `<table>` 结构
- `header-ids` extra → `<h2 id="...">` 带 id 属性
- 无 extras 时 → `<pre><code>...</code></pre>` 标准结构

## codehilite 转换（format_wechat.py 已内置处理）

markdown2 使用 `fenced-code-blocks` + `code-friendly` extras 时，代码块输出结构为：
```html
<div class="codehilite">
<p ...re><span></span><code><span class="c1"># 注释</span>
命令内容
</code></pre>
</div>
```

**问题**：这个结构会导致：
1. 代码块在微信中显示为空白
2. `<p>` 标签被注入段落样式，与代码样式冲突
3. `<span class="c1">` 等语法高亮标签微信不支持

**format_wechat.py 的处理逻辑**：
1. 用正则匹配 `<div class="codehilite">...</div>`
2. 提取 `<code>` 内容
3. 清理所有 `<span>` 标签（保留纯文本）
4. 输出为单个 `<pre style="...">代码内容</pre>` 标签
5. 样式从模板的 `code_block` + `pre` 配置合并

**关键**：代码块必须用单个 `<pre>` 标签，不要嵌套 `<code>`。微信编辑器对嵌套结构解析不稳定，可能导致内容折叠或编辑器崩溃。

## ==强调== 语法的模板适配

`==文字==` 的背景色和文字颜色从模板的 `emphasis` 配置读取：
```json
{
  "emphasis": {
    "background": "#e9e8e8",
    "padding": "2px 4px",
    "color": ""
  }
}
```

- **浅色模板**（default, red-minimal）：`background: #e9e8e8`，`color` 留空继承正文色
- **暖色模板**（warm-literary）：`background: #f5e6d0`，`color: #8b4513`
- **深色模板**（dark-elegant）：`background: #333333`，`color: #d4a843`

新建深色模板时务必设置 `emphasis.color` 为亮色，否则强调文字在深色背景下不可见。

## 微信文章图片规则
- 正文图片必须通过 `media.upload_image` 上传获得微信 CDN 地址
- 外部图片 URL 会被微信屏蔽
- 封面图必须是永久素材（`material.add`）
- 建议尺寸：封面 900×383（2.35:1）或 1:1
