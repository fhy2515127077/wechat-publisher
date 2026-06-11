#!/usr/bin/env python3
"""
微信公众号发布脚本（基于 wechatpy）

用法:
    # 存草稿
    python publish.py --draft article.html --title "标题"

    # 直接发布
    python publish.py --publish article.html --title "标题"

    # 从 Markdown 一键排版+发布
    python publish.py --from-md input.md --title "标题"

功能:
    - 自动获取 access_token 并缓存
    - 上传封面图
    - 上传正文中的图片到微信素材库
    - 创建草稿 / 直接发布
"""

import argparse
import json
import os
import re
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATES_DIR = os.path.join(SKILL_DIR, 'templates')


def load_config() -> dict:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


# ============================================================
# 微信 API 封装（不依赖 wechatpy 的轻量备选）
# ============================================================

class WeChatAPI:
    """轻量级微信公众号 API 封装"""

    BASE = 'https://api.weixin.qq.com/cgi-bin'

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expires = 0
        self.cache_path = os.path.join(SCRIPT_DIR, 'token_cache.json')
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                if data.get('expires', 0) > time.time() + 300:
                    self._token = data['token']
                    self._token_expires = data['expires']
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump({'token': self._token, 'expires': self._token_expires}, f)

    def get_access_token(self) -> str:
        if self._token and time.time() < self._token_expires - 300:
            return self._token

        url = f'{self.BASE}/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}'
        resp = self._request(url)
        if 'access_token' not in resp:
            raise Exception(f'获取 access_token 失败: {resp}')

        self._token = resp['access_token']
        self._token_expires = time.time() + resp.get('expires_in', 7200)
        self._save_cache()
        return self._token

    def _request(self, url: str, data: bytes = None, method='GET') -> dict:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except URLError as e:
            raise Exception(f'网络请求失败: {e}')

    def upload_image(self, image_path: str, media_type: str = 'image') -> str:
        """上传临时/永久素材，返回 media_id"""
        import mimetypes
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

        with open(image_path, 'rb') as f:
            file_data = f.read()

        filename = os.path.basename(image_path)
        content_type = mimetypes.guess_type(image_path)[0] or 'image/jpeg'

        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        token = self.get_access_token()
        # 永久素材
        url = f'{self.BASE}/material/add_material?access_token={token}&type={media_type}'
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        }
        req = Request(url, data=body, headers=headers, method='POST')
        resp_data = json.loads(urlopen(req, timeout=30).read().decode('utf-8'))

        if 'media_id' not in resp_data:
            raise Exception(f'上传素材失败: {resp_data}')
        return resp_data['media_id']

    def upload_image_for_content(self, image_path: str) -> str:
        """上传正文内图片，返回 url"""
        import mimetypes
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

        with open(image_path, 'rb') as f:
            file_data = f.read()

        filename = os.path.basename(image_path)
        content_type = mimetypes.guess_type(image_path)[0] or 'image/jpeg'

        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        token = self.get_access_token()
        url = f'{self.BASE}/media/uploadimg?access_token={token}'
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        }
        req = Request(url, data=body, headers=headers, method='POST')
        resp_data = json.loads(urlopen(req, timeout=30).read().decode('utf-8'))

        if 'url' not in resp_data:
            raise Exception(f'上传正文图片失败: {resp_data}')
        return resp_data['url']

    def upload_content_images(self, html: str) -> str:
        """扫描 HTML 中的本地图片，上传到微信并替换 URL"""
        def replace_img(match):
            full_tag = match.group(0)
            src = match.group(1)
            # 只处理本地文件路径
            if src.startswith('http://') or src.startswith('https://'):
                return full_tag
            img_path = os.path.abspath(src)
            if not os.path.exists(img_path):
                print(f'⚠️ 图片不存在: {img_path}，跳过')
                return full_tag
            try:
                wx_url = self.upload_image_for_content(img_path)
                print(f'  📷 已上传: {os.path.basename(img_path)} → {wx_url[:60]}...')
                return full_tag.replace(src, wx_url)
            except Exception as e:
                print(f'  ❌ 上传失败: {img_path} - {e}')
                return full_tag

        return re.sub(r'<img[^>]+src="([^"]+)"', replace_img, html)

    def create_draft(self, title: str, content: str, thumb_media_id: str,
                     author: str = '', digest: str = '', content_source_url: str = '') -> str:
        """创建草稿，返回 media_id"""
        article = {
            "title": title,
            "author": author,
            "digest": digest or title,
            "content": content,
            "content_source_url": content_source_url,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }

        token = self.get_access_token()
        url = f'{self.BASE}/draft/add?access_token={token}'
        data = json.dumps({"articles": [article]}, ensure_ascii=False).encode('utf-8')
        resp = self._request(url, data=data, method='POST')

        if 'media_id' not in resp:
            raise Exception(f'创建草稿失败: {resp}')
        return resp['media_id']

    def publish(self, media_id: str) -> dict:
        """发布草稿"""
        token = self.get_access_token()
        url = f'{self.BASE}/freepublish/submit?access_token={token}'
        data = json.dumps({"media_id": media_id}).encode('utf-8')
        resp = self._request(url, data=data, method='POST')

        if resp.get('errcode', 0) != 0:
            raise Exception(f'发布失败: {resp}')
        return resp

    def get_publish_status(self, publish_id: str) -> dict:
        """查询发布状态"""
        token = self.get_access_token()
        url = f'{self.BASE}/freepublish/get?access_token={token}'
        data = json.dumps({"publish_id": publish_id}).encode('utf-8')
        return self._request(url, data=data, method='POST')


# ============================================================
# wechatpy 版本（优先使用）
# ============================================================

class WeChatAPIWechatpy:
    """使用 wechatpy 库的实现（更稳定，推荐）"""

    def __init__(self, app_id: str, app_secret: str):
        try:
            from wechatpy import WeChatClient
            self.client = WeChatClient(appid=app_id, secret=app_secret)
        except ImportError:
            raise ImportError('需要安装 wechatpy: pip install wechatpy[requests]')

    def upload_image(self, image_path: str, media_type: str = 'image') -> str:
        with open(image_path, 'rb') as f:
            resp = self.client.material.add(media_type, f)
        return resp['media_id']

    def upload_image_for_content(self, image_path: str) -> str:
        with open(image_path, 'rb') as f:
            resp = self.client.media.upload('image', f)
        return resp['url']

    def upload_content_images(self, html: str) -> str:
        def replace_img(match):
            full_tag = match.group(0)
            src = match.group(1)
            if src.startswith('http://') or src.startswith('https://'):
                return full_tag
            img_path = os.path.abspath(src)
            if not os.path.exists(img_path):
                print(f'⚠️ 图片不存在: {img_path}，跳过')
                return full_tag
            try:
                wx_url = self.upload_image_for_content(img_path)
                print(f'  📷 已上传: {os.path.basename(img_path)}')
                return full_tag.replace(src, wx_url)
            except Exception as e:
                print(f'  ❌ 上传失败: {img_path} - {e}')
                return full_tag
        return re.sub(r'<img[^>]+src="([^"]+)"', replace_img, html)

    def create_draft(self, title, content, thumb_media_id, author='', digest='', content_source_url=''):
        from wechatpy import Article
        article = Article(
            title=title, author=author, digest=digest or title,
            content=content, content_source_url=content_source_url,
            thumb_media_id=thumb_media_id,
        )
        resp = self.client.draft.add([article])
        return resp['media_id']

    def publish(self, media_id: str) -> dict:
        resp = self.client.freepublish.submit(media_id)
        return resp

    def get_publish_status(self, publish_id: str) -> dict:
        return self.client.freepublish.get(publish_id)


# ============================================================
# 工具函数
# ============================================================

def get_api(config: dict):
    """根据依赖情况选择 API 实现"""
    try:
        api = WeChatAPIWechatpy(config['app_id'], config['app_secret'])
        print('✅ 使用 wechatpy 库')
        return api
    except (ImportError, Exception):
        pass

    api = WeChatAPI(config['app_id'], config['app_secret'])
    print('✅ 使用内置 API 封装')
    return api


def format_article(html_path: str, template: str = 'default', title: str = '',
                   author: str = '', date: str = '', footer: str = '') -> str:
    """调用 format_wechat.py 排版"""
    config = load_config()

    if footer is None:
        footer = config.get('default_footer', '')

    # 导入排版模块
    sys.path.insert(0, SCRIPT_DIR)
    from format_wechat import markdown_to_html

    if html_path.endswith('.md'):
        with open(html_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        return markdown_to_html(md_text, template_name=template,
                                title=title, author=author or config.get('author', ''),
                                date=date, footer=footer)
    else:
        # 已经是 HTML 文件，直接读取
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='微信公众号发布工具')
    parser.add_argument('input', nargs='?', help='HTML 或 Markdown 文件路径')
    parser.add_argument('--draft', action='store_true', help='仅创建草稿，不发布')
    parser.add_argument('--publish', action='store_true', help='创建草稿并发布')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--author', default='', help='作者名')
    parser.add_argument('--digest', default='', help='摘要（默认取标题）')
    parser.add_argument('--cover', default='', help='封面图路径')
    parser.add_argument('--template', default='default', help='排版模板')
    parser.add_argument('--from-md', action='store_true', help='从 Markdown 源文件排版+发布')
    parser.add_argument('--footer', default=None, help='文末引导文字')
    parser.add_argument('--status', help='查询发布状态（publish_id）')

    args = parser.parse_args()
    config = load_config()

    # 检查凭证
    if config.get('app_id') == 'YOUR_APP_ID':
        print('❌ 请先配置 app_id 和 app_secret！')
        print(f'   编辑配置文件: {CONFIG_PATH}')
        sys.exit(1)

    # 查询发布状态
    if args.status:
        api = get_api(config)
        status = api.get_publish_status(args.status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    if not args.input and not args.draft:
        parser.error('请指定输入文件')

    # 初始化 API
    api = get_api(config)

    # 排版（如果是 Markdown）
    if args.from_md or args.input.endswith('.md'):
        print('📝 正在排版...')
        html_content = format_article(
            args.input,
            template=args.template,
            title=args.title,
            author=args.author or config.get('author', ''),
            footer=args.footer
        )
    else:
        with open(args.input, 'r', encoding='utf-8') as f:
            html_content = f.read()

    # 上传正文中的图片
    print('🖼️ 正在处理正文图片...')
    html_content = api.upload_content_images(html_content)

    # 上传封面图
    cover_path = args.cover or config.get('default_cover', '')
    if cover_path and os.path.exists(cover_path):
        print('🖼️ 正在上传封面图...')
        thumb_media_id = api.upload_image(cover_path)
    else:
        # 如果没有封面图，尝试获取已有的
        if config.get('draft_media_id'):
            thumb_media_id = config['draft_media_id']
            print(f'📋 使用已缓存的封面 media_id: {thumb_media_id[:20]}...')
        else:
            print('⚠️ 未指定封面图，将使用最近上传的永久素材')
            print('   建议通过 --cover 指定封面图路径')
            # 用一个 1x1 透明图作为临时方案
            sys.exit(1)

    # 创建草稿
    print('📝 正在创建草稿...')
    media_id = api.create_draft(
        title=args.title,
        content=html_content,
        thumb_media_id=thumb_media_id,
        author=args.author or config.get('author', ''),
        digest=args.digest
    )
    print(f'✅ 草稿已创建: {media_id}')

    # 发布
    if args.publish:
        print('🚀 正在发布...')
        result = api.publish(media_id)
        publish_id = result.get('publish_id', '')
        print(f'✅ 发布成功！publish_id: {publish_id}')
        print('   可通过 --status 查询发布状态')
    elif args.draft:
        print('📋 已保存到草稿箱，请在公众号后台检查后手动发布')
    else:
        print('📋 默认保存到草稿箱。使用 --publish 直接发布')

    # 保存 media_id 供后续使用
    config['draft_media_id'] = thumb_media_id
    save_config(config)


if __name__ == '__main__':
    main()
