#!/usr/bin/env python3
"""
Markdown → 微信公众号排版 HTML 转换器

用法:
    python format_wechat.py input.md -t default -o output.html
    python format_wechat.py input.md --template default --title "文章标题" --author "作者"

支持:
    - 标题（h1-h6）
    - 段落、加粗、斜体
    - 引用块
    - 代码块（行内 + 块）
    - 有序/无序列表
    - 图片（自动适配宽度）
    - 分隔线
    - 表格（基础支持）
"""

import argparse
import json
import os
import re
import sys

# --- markdown2 依赖 ---
try:
    import markdown2
except ImportError:
    print("ERROR: 需要安装 markdown2: pip install markdown2", file=sys.stderr)
    sys.exit(1)


# ============================================================
# 排版模板配置
# ============================================================

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')


def load_template(name: str = 'default') -> dict:
    """加载模板配置"""
    path = os.path.join(TEMPLATES_DIR, f'{name}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 返回默认内联配置
    return get_default_config()


def get_default_config() -> dict:
    """默认排版配置"""
    return {
        "name": "默认模板",
        "body": {
            "max_width": "100%",
            "font_size": "16px",
            "color": "#333333",
            "line_height": "1.8",
            "font_family": "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
            "letter_spacing": "0.5px",
            "word_break": "break-word",
            "padding": "0 8px",
            "background": "#ffffff"
        },
        "title": {
            "font_size": "22px",
            "font_weight": "bold",
            "color": "#1a1a1a",
            "text_align": "center",
            "margin": "20px 0 8px 0",
            "line_height": "1.4"
        },
        "author": {
            "font_size": "13px",
            "color": "#999999",
            "text_align": "center",
            "margin": "0 0 24px 0"
        },
        "date": {
            "font_size": "12px",
            "color": "#bbbbbb",
            "text_align": "center",
            "margin": "0 0 20px 0"
        },
        "h1": {
            "font_size": "22px",
            "font_weight": "bold",
            "color": "#1a1a1a",
            "margin": "32px 0 16px 0",
            "padding_bottom": "8px",
            "border_bottom": "2px solid #1e90ff"
        },
        "h2": {
            "font_size": "20px",
            "font_weight": "bold",
            "color": "#1a1a1a",
            "margin": "28px 0 14px 0",
            "padding_bottom": "6px",
            "border_bottom": "1px solid #eee"
        },
        "h3": {
            "font_size": "18px",
            "font_weight": "bold",
            "color": "#1a1a1a",
            "margin": "24px 0 12px 0"
        },
        "p": {
            "margin": "16px 0",
            "line_height": "1.8",
            "text_indent": "0"
        },
        "strong": {
            "color": "#1a1a1a",
            "font_weight": "bold"
        },
        "em": {
            "color": "#666666",
            "font_style": "italic"
        },
        "a": {
            "color": "#576b95",
            "text-decoration": "none"
        },
        "blockquote": {
            "border_left": "4px solid #1e90ff",
            "padding": "12px 16px",
            "background": "#f7f8fa",
            "color": "#666666",
            "margin": "16px 0",
            "font_size": "15px",
            "line_height": "1.7"
        },
        "code_inline": {
            "background": "#f5f5f5",
            "color": "#e74c3c",
            "padding": "2px 6px",
            "border_radius": "3px",
            "font_size": "14px",
            "font_family": "Consolas, Monaco, 'Courier New', monospace"
        },
        "code_block": {
            "background": "#2d2d2d",
            "color": "#ccc",
            "padding": "16px",
            "border_radius": "6px",
            "font_size": "13px",
            "line_height": "1.6",
            "margin": "16px 0",
            "overflow_x": "auto",
            "font_family": "Consolas, Monaco, 'Courier New', monospace",
            "white_space": "pre-wrap",
            "word_break": "break-all"
        },
        "pre": {
            "margin": "16px 0",
            "padding": "0"
        },
        "img": {
            "max_width": "100%",
            "border_radius": "4px",
            "margin": "16px 0",
            "display": "block"
        },
        "hr": {
            "border": "none",
            "border_top": "1px solid #eee",
            "margin": "24px 0"
        },
        "ul": {
            "padding_left": "24px",
            "margin": "12px 0"
        },
        "ol": {
            "padding_left": "24px",
            "margin": "12px 0"
        },
        "li": {
            "margin": "6px 0",
            "line_height": "1.7"
        },
        "table": {
            "border-collapse": "collapse",
            "width": "100%",
            "margin": "16px 0",
            "font_size": "14px"
        },
        "th": {
            "background": "#f5f5f5",
            "border": "1px solid #ddd",
            "padding": "8px 12px",
            "font_weight": "bold",
            "text_align": "left"
        },
        "td": {
            "border": "1px solid #ddd",
            "padding": "8px 12px"
        },
        "footer": {
            "text_align": "center",
            "margin": "40px 0 20px 0",
            "padding": "20px 0 0 0",
            "border_top": "1px solid #eee",
            "font_size": "14px",
            "color": "#999999",
            "line_height": "1.8"
        }
    }


# ============================================================
# HTML 样式生成器
# ============================================================

def css(style_dict: dict) -> str:
    """将样式字典转为 CSS 内联字符串"""
    return '; '.join(f'{k.replace("_", "-")}: {v}' for k, v in style_dict.items())


def build_styles(cfg: dict) -> dict:
    """从配置构建各元素的 style 字符串"""
    styles = {}
    for key, val in cfg.items():
        if isinstance(val, dict):
            styles[key] = css(val)
    return styles


# ============================================================
# Markdown → HTML 转换
# ============================================================

def markdown_to_html(md_text: str, template_name: str = 'default',
                      title: str = '', author: str = '', date: str = '',
                      footer: str = '') -> str:
    """将 Markdown 转换为微信兼容的排版 HTML"""

    # 加载模板配置
    cfg = load_template(template_name)
    styles = build_styles(cfg)

    # 用 markdown2 转换
    extras = [
        'fenced-code-blocks',
        'tables',
        'header-ids',
        'break-on-newline',
        'cuddled-lists',
        'code-friendly',
    ]
    html_body = markdown2.markdown(md_text, extras=extras)

    # 如果指定了 title，移除 Markdown 中的第一个 H1（避免重复）
    if title:
        html_body = re.sub(r'<h1[^>]*>.*?</h1>\s*', '', html_body, count=1, flags=re.DOTALL)

    # 后处理：==强调文字== 转为高亮span（颜色跟随模板）
    emphasis_cfg = cfg.get('emphasis', {})
    emphasis_bg = emphasis_cfg.get('background', '#e9e8e8')
    emphasis_padding = emphasis_cfg.get('padding', '2px 4px')
    emphasis_color = emphasis_cfg.get('color', '')
    emphasis_style = f'background: {emphasis_bg}; padding: {emphasis_padding};'
    if emphasis_color:
        emphasis_style += f' color: {emphasis_color};'
    html_body = re.sub(
        r'==(.+?)==',
        lambda m, s=emphasis_style: f'<span style="{s}">{m.group(1)}</span>',
        html_body
    )

    # 后处理：给各标签注入内联样式
    html_body = inject_styles(html_body, styles)

    # 构建完整 HTML
    parts = []
    parts.append(f'<section style="{css(cfg.get("body", {}))}">')

    # 标题
    if title:
        parts.append(f'<h1 style="{styles.get("title", "")}">{title}</h1>')

    # 作者
    if author:
        parts.append(f'<p style="{styles.get("author", "")}">{author}</p>')

    # 日期
    if date:
        parts.append(f'<p style="{styles.get("date", "")}">{date}</p>')

    # 正文
    parts.append(html_body)

    # 文末引导
    if footer:
        parts.append(f'<section style="{styles.get("footer", "")}">{footer}</section>')

    parts.append('</section>')

    return '\n'.join(parts)


def inject_styles(html: str, styles: dict) -> str:
    """给 HTML 标签注入内联样式"""

    # h1-h3
    for level in ['h1', 'h2', 'h3']:
        tag_style = styles.get(level, '')
        if tag_style:
            html = re.sub(
                rf'<{level}(.*?)>',
                lambda m, s=tag_style, l=level: f'<{l} style="{s}"{m.group(1)}>',
                html
            )

    # 段落
    if 'p' in styles:
        html = re.sub(
            r'<p(.*?)>',
            lambda m: f'<p style="{styles["p"]}"{m.group(1)}>',
            html
        )

    # 加粗
    if 'strong' in styles:
        html = re.sub(
            r'<strong>(.*?)</strong>',
            lambda m: f'<strong style="{styles["strong"]}">{m.group(1)}</strong>',
            html,
            flags=re.DOTALL
        )

    # 斜体
    if 'em' in styles:
        html = re.sub(
            r'<em>(.*?)</em>',
            lambda m: f'<em style="{styles["em"]}">{m.group(1)}</em>',
            html,
            flags=re.DOTALL
        )

    # 链接
    if 'a' in styles:
        html = re.sub(
            r'<a(.*?)>',
            lambda m: f'<a style="{styles["a"]}"{m.group(1)}>',
            html
        )

    # 引用
    if 'blockquote' in styles:
        html = re.sub(
            r'<blockquote(.*?)>',
            lambda m: f'<blockquote style="{styles["blockquote"]}"{m.group(1)}>',
            html
        )

    # 行内代码
    if 'code_inline' in styles:
        html = re.sub(
            r'<code>(?!.*</pre>)(.*?)</code>',
            lambda m: f'<code style="{styles["code_inline"]}">{m.group(1)}</code>',
            html
        )

    # 代码块（markdown2 codehilite div → styled pre）
    if 'code_block' in styles:
        # 合并 pre + code 样式到一个 pre 标签
        combined_style = styles.get('pre', '') + '; ' + styles['code_block'] if styles.get('pre') else styles['code_block']
        def replace_codehilite(m):
            inner = m.group(1)
            # 提取 code 内容
            code_match = re.search(r'<code[^>]*>(.*?)</code>', inner, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
                # 清理 span 标签（markdown2 的语法高亮）
                code_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', code_content)
                code_content = code_content.strip()
                return f'<pre style="{combined_style}">{code_content}</pre>'
            return m.group(0)
        html = re.sub(
            r'<div class="codehilite">(.*?)</div>',
            replace_codehilite,
            html,
            flags=re.DOTALL
        )
        # 标准 pre+code 格式 → 简化为 pre
        def replace_pre_code(m):
            code_content = m.group(2)
            code_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', code_content)
            return f'<pre style="{combined_style}">{code_content}</pre>'
        html = re.sub(
            r'<pre><code[^>]*>(.*?)</code></pre>',
            replace_pre_code,
            html,
            flags=re.DOTALL
        )

    # 图片
    if 'img' in styles:
        html = re.sub(
            r'<img(.*?)>',
            lambda m: f'<img style="{styles["img"]}"{m.group(1)} />',
            html
        )

    # 分隔线
    if 'hr' in styles:
        html = re.sub(
            r'<hr\s*/?>',
            f'<hr style="{styles["hr"]}" />',
            html
        )

    # 列表
    if 'ul' in styles:
        html = re.sub(
            r'<ul(.*?)>',
            lambda m: f'<ul style="{styles["ul"]}"{m.group(1)}>',
            html
        )
    if 'ol' in styles:
        html = re.sub(
            r'<ol(.*?)>',
            lambda m: f'<ol style="{styles["ol"]}"{m.group(1)}>',
            html
        )
    if 'li' in styles:
        html = re.sub(
            r'<li(.*?)>',
            lambda m: f'<li style="{styles["li"]}"{m.group(1)}>',
            html
        )

    # 表格
    if 'table' in styles:
        html = re.sub(
            r'<table(.*?)>',
            lambda m: f'<table style="{styles["table"]}"{m.group(1)}>',
            html
        )
    if 'th' in styles:
        html = re.sub(
            r'<th(.*?)>',
            lambda m: f'<th style="{styles["th"]}"{m.group(1)}>',
            html
        )
    if 'td' in styles:
        html = re.sub(
            r'<td(.*?)>',
            lambda m: f'<td style="{styles["td"]}"{m.group(1)}>',
            html
        )

    return html


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Markdown → 微信公众号排版HTML')
    parser.add_argument('input', help='Markdown 文件路径')
    parser.add_argument('-t', '--template', default='default', help='模板名称 (default/minimal)')
    parser.add_argument('-o', '--output', help='输出 HTML 文件路径')
    parser.add_argument('--title', default='', help='文章标题')
    parser.add_argument('--author', default='', help='作者名')
    parser.add_argument('--date', default='', help='发布日期')
    parser.add_argument('--footer', default='', help='文末引导文字')
    parser.add_argument('--list-templates', action='store_true', help='列出可用模板')

    args = parser.parse_args()

    if args.list_templates:
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        if os.path.exists(templates_dir):
            for f in os.listdir(templates_dir):
                if f.endswith('.json'):
                    print(f'  - {f[:-5]}')
        print('  - default (内置)')
        print('  - minimal (内置)')
        return

    # 读取 Markdown
    with open(args.input, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 转换
    html = markdown_to_html(
        md_text,
        template_name=args.template,
        title=args.title,
        author=args.author,
        date=args.date,
        footer=args.footer
    )

    # 输出
    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'✅ 排版完成，已保存到: {args.output}')
    else:
        print(html)


if __name__ == '__main__':
    main()
