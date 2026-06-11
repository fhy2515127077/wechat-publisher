#!/usr/bin/env python3
"""
公众号发布主控脚本 — 一键流水线

用法:
    # 从 Markdown 一键排版+发布
    python pipeline.py article.md --title "标题"

    # 指定模板和作者
    python pipeline.py article.md --title "标题" --template default --author "卡兹克"

    # 仅排版不发布（调试用）
    python pipeline.py article.md --title "标题" --dry-run

    # 排版后存草稿
    python pipeline.py article.md --title "标题" --draft

流程:
    1. 读取 Markdown
    2. 调用排版引擎转为微信HTML
    3. 上传图片到微信素材库
    4. 创建草稿 / 发布
"""

import argparse
import os
import sys
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(SKILL_DIR, 'output')

sys.path.insert(0, SCRIPT_DIR)


def main():
    parser = argparse.ArgumentParser(description='公众号发布流水线')
    parser.add_argument('input', help='Markdown 文件路径')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--author', default='', help='作者名')
    parser.add_argument('--template', default='default', help='排版模板名')
    parser.add_argument('--cover', default='', help='封面图路径')
    parser.add_argument('--digest', default='', help='文章摘要')
    parser.add_argument('--date', default='', help='发布日期（默认今天）')
    parser.add_argument('--footer', default=None, help='文末引导文字')
    parser.add_argument('--dry-run', action='store_true', help='仅排版，不发布')
    parser.add_argument('--draft', action='store_true', help='排版后存草稿箱')
    parser.add_argument('--publish', action='store_true', help='排版后直接发布')
    parser.add_argument('--output', default='', help='HTML 输出路径（默认自动生成）')

    args = parser.parse_args()

    # 默认日期
    if not args.date:
        args.date = datetime.now().strftime('%Y年%m月%d日')

    # 读取 Markdown
    print(f'📖 读取文件: {args.input}')
    with open(args.input, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 排版
    print(f'🎨 正在排版（模板: {args.template}）...')
    from format_wechat import markdown_to_html
    from publish import load_config

    config = load_config()
    footer = args.footer if args.footer is not None else config.get('default_footer', '')

    html = markdown_to_html(
        md_text,
        template_name=args.template,
        title=args.title,
        author=args.author or config.get('author', ''),
        date=args.date,
        footer=footer
    )

    # 保存 HTML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = args.title[:20].replace(' ', '_').replace('/', '_')
        output_path = os.path.join(OUTPUT_DIR, f'{timestamp}_{safe_title}.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ 排版完成: {output_path}')

    # 如果仅排版，到此结束
    if args.dry_run:
        print('🏁 dry-run 模式，流程结束')
        return

    # 发布
    from publish import get_api, format_article

    api = get_api(config)

    # 上传正文图片
    print('🖼️ 处理正文图片...')
    html = api.upload_content_images(html)

    # 封面图
    cover_path = args.cover or ''
    if cover_path and os.path.exists(cover_path):
        print('🖼️ 上传封面图...')
        thumb_media_id = api.upload_image(cover_path)
        config['draft_media_id'] = thumb_media_id
        # 回写配置
        config_path = os.path.join(SCRIPT_DIR, 'config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    elif config.get('draft_media_id'):
        thumb_media_id = config['draft_media_id']
    else:
        print('❌ 未指定封面图，请用 --cover 提供封面图路径')
        sys.exit(1)

    # 创建草稿
    print('📝 创建草稿...')
    media_id = api.create_draft(
        title=args.title,
        content=html,
        thumb_media_id=thumb_media_id,
        author=args.author or config.get('author', ''),
        digest=args.digest or args.title
    )
    print(f'✅ 草稿创建成功: {media_id}')

    # 发布
    if args.publish:
        print('🚀 发布中...')
        result = api.publish(media_id)
        publish_id = result.get('publish_id', '')
        print(f'✅ 发布成功！publish_id: {publish_id}')
    else:
        print('📋 已存入草稿箱。如需发布请加 --publish 参数')

    print('\n🎉 流程完成！')


if __name__ == '__main__':
    main()
