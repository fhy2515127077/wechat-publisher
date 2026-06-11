#!/usr/bin/env python3
"""
微信公众号文章配图生成器
使用 GPT Image 2 API (via Grsai) 为文章生成上下文相关的配图。

用法:
  python generate_images.py config.json
  python generate_images.py config.json --api-key sk-xxx

配置文件格式 (config.json):
[
  {
    "prompt": "图片描述（英文效果更好）",
    "output": "输出路径，如 output/article-images/img01.jpg",
    "size": "1536x1024",       // 可选，默认 1536x1024
    "model": "gpt-image-2"     // 可选，默认 gpt-image-2
  }
]

环境变量:
  GRSAI_API_KEY: Grsai API 密钥（也可通过 --api-key 参数传入）
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import ssl

# ── 配置 ──────────────────────────────────────────────
DEFAULT_API_BASE = "https://grsaiapi.com"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1536x1024"  # 16:10 横图，适合公众号配图
TIMEOUT = 120  # 秒


def find_api_key():
    """按优先级查找 API Key：环境变量 → gen_cover.py"""
    key = os.environ.get("GRSAI_API_KEY")
    if key:
        return key
    # 从 gen_cover.py 读取
    gen_cover = os.path.join(os.path.dirname(__file__), "gen_cover.py")
    if os.path.exists(gen_cover):
        import re
        with open(gen_cover, "r") as f:
            content = f.read()
        match = re.search(r'API_KEY\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    return None


def generate_image(prompt, output_path, size=DEFAULT_SIZE, model=DEFAULT_MODEL,
                   api_key=None, api_base=DEFAULT_API_BASE):
    """调用 GPT Image 2 API 生成单张图片并保存到本地。"""

    if not api_key:
        api_key = find_api_key()
    if not api_key:
        raise ValueError("未提供 API Key，请通过 --api-key 参数、GRSAI_API_KEY 环境变量或 scripts/gen_cover.py 配置")

    url = f"{api_base}/v1/images/generations"
    body = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "url"
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    # 跳过 SSL 验证（某些中转站证书问题）
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"  ⏳ 正在生成: {prompt[:60]}...")
    start = time.time()

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API 请求失败 [{e.code}]: {error_body}")

    elapsed = time.time() - start

    # 解析响应（兼容 OpenAI 格式和 Grsai 格式）
    image_url = None
    if "data" in result and result["data"]:
        image_url = result["data"][0].get("url")
    elif "results" in result and result["results"]:
        image_url = result["results"][0].get("url")

    if not image_url:
        raise RuntimeError(f"未获取到图片 URL，响应: {json.dumps(result, ensure_ascii=False)[:500]}")

    # 下载图片
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    img_req = urllib.request.Request(image_url)
    with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
        img_data = img_resp.read()

    with open(output_path, "wb") as f:
        f.write(img_data)

    size_kb = len(img_data) / 1024
    print(f"  ✅ 已保存: {output_path} ({size_kb:.0f}KB, {elapsed:.1f}s)")
    return output_path


def process_config(config_path, api_key=None, api_base=None):
    """读取配置文件并批量生成图片。"""

    with open(config_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        items = [items]

    base = api_base or DEFAULT_API_BASE
    total = len(items)
    success = 0
    failed = []

    print(f"📸 开始生成 {total} 张配图...\n")

    for i, item in enumerate(items, 1):
        prompt = item.get("prompt", "")
        output = item.get("output", "")
        size = item.get("size", DEFAULT_SIZE)
        model = item.get("model", DEFAULT_MODEL)

        if not prompt or not output:
            print(f"  ⚠️  [{i}/{total}] 跳过：缺少 prompt 或 output")
            continue

        print(f"[{i}/{total}] {os.path.basename(output)}")
        try:
            generate_image(prompt, output, size=size, model=model,
                          api_key=api_key, api_base=base)
            success += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            failed.append({"output": output, "error": str(e)})

        # 避免 API 限流
        if i < total:
            time.sleep(1)

    print(f"\n{'='*50}")
    print(f"✅ 成功: {success}/{total}")
    if failed:
        print(f"❌ 失败: {len(failed)}")
        for f_item in failed:
            print(f"   - {f_item['output']}: {f_item['error']}")

    return failed


def generate_from_markdown(md_path, output_dir, api_key=None, api_base=None):
    """
    从 Markdown 文件中提取图片引用，为每张图片生成 AI 配图。
    
    Markdown 中的图片引用格式：
      ![alt text](path)
    
    脚本会：
    1. 扫描所有 ![...] 引用
    2. 用 alt text 作为生成提示词的基础
    3. 生成图片并保存到 output_dir
    4. 返回更新后的图片路径映射
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    # 匹配 ![alt](path) 格式
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = list(re.finditer(pattern, content))

    if not matches:
        print("未找到图片引用")
        return {}

    os.makedirs(output_dir, exist_ok=True)
    mapping = {}
    total = len(matches)

    print(f"📸 在 Markdown 中找到 {total} 张图片引用，开始生成...\n")

    for i, match in enumerate(matches, 1):
        alt_text = match.group(1)
        original_path = match.group(2)

        # 从原始路径推断文件名
        ext = os.path.splitext(original_path)[1] or ".jpg"
        filename = os.path.basename(original_path)
        if not filename or filename.startswith("img"):
            filename = f"img{i:02d}{ext}"
        output_path = os.path.join(output_dir, filename)

        # 用 alt text + 上下文作为 prompt
        prompt = f"Editorial illustration for article about: {alt_text}. Clean, modern, professional style suitable for WeChat article. No text overlay."

        print(f"[{i}/{total}] {alt_text}")
        try:
            generate_image(prompt, output_path, api_key=api_key, api_base=api_base or DEFAULT_API_BASE)
            mapping[original_path] = output_path
        except Exception as e:
            print(f"  ❌ 失败: {e}")

        if i < total:
            time.sleep(1)

    return mapping


def main():
    parser = argparse.ArgumentParser(description="微信公众号文章配图生成器")
    parser.add_argument("config", help="配置文件路径 (JSON) 或 Markdown 文件路径")
    parser.add_argument("--api-key", help="Grsai API Key")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API 基础 URL")
    parser.add_argument("--output-dir", help="图片输出目录（配合 --from-markdown 使用）")
    parser.add_argument("--from-markdown", action="store_true",
                       help="从 Markdown 文件提取图片引用并生成")

    args = parser.parse_args()

    if args.from_markdown:
        output_dir = args.output_dir or os.path.join(os.path.dirname(args.config), "article-images")
        mapping = generate_from_markdown(args.config, output_dir,
                                        api_key=args.api_key, api_base=args.api_base)
        if mapping:
            print(f"\n📋 图片路径映射:")
            for orig, new in mapping.items():
                print(f"   {orig} → {new}")
    else:
        process_config(args.config, api_key=args.api_key, api_base=args.api_base)


if __name__ == "__main__":
    main()
