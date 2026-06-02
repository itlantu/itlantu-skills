"""通过 OpenAI 兼容 API 调用视觉语言模型分析图片。"""

import base64
import os
import sys

from openai import OpenAI

# 支持的图片格式与 MIME 类型映射
SUPPORTED_EXTENSIONS = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "gif": "image/gif",
}


def resolve_image_url(image_input):
    """将本地文件路径或 URL 转换为 API 所需的图片 URL。

    参数:
        image_input: 本地文件路径或 HTTP(S) 链接。

    返回:
        str: 本地文件返回 base64 编码的 Data URI，URL 则原样返回。
    """
    if image_input.startswith("http://") or image_input.startswith("https://"):
        return image_input

    with open(image_input, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = image_input.rsplit(".", 1)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的图片格式: {ext}")

    mime = SUPPORTED_EXTENSIONS[ext]
    return f"data:{mime};base64,{image_b64}"


def analyze_image(image_input, prompt, model=None, api_key=None,
                  base_url=None):
    """使用视觉语言模型分析图片。

    参数:
        image_input: 本地文件路径或图片 URL。
        prompt: 分析的提示词。
        model: 模型名称，未提供时使用环境变量 ITLANTU-IMAGE-MODEL。
        api_key: API 密钥，未提供时使用环境变量 ITLANTU-IMAGE-API-KEY。
        base_url: API 基础地址，未提供时使用环境变量 ITLANTU-IMAGE-BASE-URL。

    返回:
        str: 模型返回的分析内容。
    """
    api_key = api_key or os.environ["ITLANTU-IMAGE-API-KEY"]
    base_url = base_url or os.environ["ITLANTU-IMAGE-BASE-URL"]
    model = model or os.environ["ITLANTU-IMAGE-MODEL"]

    image_url = resolve_image_url(image_input)

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt},
            ],
        }],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_image.py <图片路径或URL> [提示词]")
        sys.exit(1)

    image_input = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请描述这张图片的内容。"

    try:
        result = analyze_image(image_input, prompt)
        print(result)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
