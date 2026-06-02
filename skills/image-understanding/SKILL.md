---
name: image-understanding
description: "图片理解技能。当用户需要对图片/图像/照片进行内容分析时主动调用。关键词包括但不限于：图片分析、图片识别、物体检测、场景理解、图片描述、图片标签、图片分类、OCR文字识别、截图分析、照片内容。即使用户未明确说'分析图片'，只要涉及图片内容理解即应使用此技能。"
---

# 图片理解

## 工具简介

图片理解技能使用支持图片输入的视觉语言模型，通过 `openai` 兼容 API 分析用户提供的图片内容并返回分析结果。

## 工具配置

技能依赖以下 Path 环境变量，调用前需确认均已正确设置：

| Path 环境名 | 作用 |
|---|---|
| `ITLANTU-IMAGE-API-KEY` | 图片理解模型的 API Key |
| `ITLANTU-IMAGE-BASE-URL` | 图片理解模型的 BASE URL |
| `ITLANTU-IMAGE-MODEL` | 图片理解模型的名称 |

### 环境变量检查

逐个检查环境变量，明确指出缺少的变量名。

**Windows (PowerShell)：**

```powershell
$missing = @()
if (-not ${env:ITLANTU-IMAGE-API-KEY}) { $missing += 'ITLANTU-IMAGE-API-KEY' }
if (-not ${env:ITLANTU-IMAGE-BASE-URL}) { $missing += 'ITLANTU-IMAGE-BASE-URL' }
if (-not ${env:ITLANTU-IMAGE-MODEL}) { $missing += 'ITLANTU-IMAGE-MODEL' }
if ($missing.Count -gt 0) {
    Write-Host "错误: 以下环境变量未配置："
    $missing | ForEach-Object { Write-Host "  $_" }
    exit 1
}
Write-Host "所有环境变量已配置"
```

**Linux (bash)：**

```bash
missing=""
printenv ITLANTU-IMAGE-API-KEY > /dev/null 2>&1 || missing="$missing ITLANTU-IMAGE-API-KEY"
printenv ITLANTU-IMAGE-BASE-URL > /dev/null 2>&1 || missing="$missing ITLANTU-IMAGE-BASE-URL"
printenv ITLANTU-IMAGE-MODEL > /dev/null 2>&1 || missing="$missing ITLANTU-IMAGE-MODEL"
if [ -n "$missing" ]; then
    echo "错误: 以下环境变量未配置："
    for var in $missing; do echo "  $var"; done
    exit 1
fi
echo "所有环境变量已配置"
```

## 调用方式

基于 `Python` + `openai` 库调用图片理解模型，直接在终端执行，**不生成代码文件**。

### 调用模板

```
python -c "
import os, sys, base64
from openai import OpenAI

image_path = '<图片路径>'
with open(image_path, 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')
ext = image_path.rsplit('.', 1)[-1].lower()
if ext in ('jpg', 'jpeg'):
    mime = 'image/jpeg'
elif ext == 'png':
    mime = 'image/png'
elif ext in ('webp', 'bmp', 'gif'):
    mime = f'image/{ext}'
else:
    print(f'不支持的图片格式: {ext}')
    sys.exit(1)

client = OpenAI(
    api_key=os.environ['ITLANTU-IMAGE-API-KEY'],
    base_url=os.environ['ITLANTU-IMAGE-BASE-URL']
)

response = client.chat.completions.create(
    model=os.environ['ITLANTU-IMAGE-MODEL'],
    messages=[{
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{image_b64}'}},
            {'type': 'text', 'text': '<提示词>'}
        ]
    }]
)
print(response.choices[0].message.content)
"
```

## 输出格式

分析结果以纯文本形式输出，包含以下结构：

```
=== 图片分析结果 ===
[模型返回的分析内容]
====================
```

## 执行步骤

1. 确认用户提供了图片（文件路径或已粘贴的图片），如未提供则提示用户提供
2. 检查 `ITLANTU-IMAGE-API-KEY`、`ITLANTU-IMAGE-BASE-URL`、`ITLANTU-IMAGE-MODEL` 三个环境变量是否已设置，未设置则提示用户配置
3. 根据用户需求设计提示词，明确告知模型需要分析的内容（如：描述图片、识别物体、提取文字、判断场景等）
4. 使用上述 Python 调用模板执行分析，将 `<图片路径>` 替换为实际路径，`<提示词>` 替换为实际提示词
5. 将模型返回的分析结果按输出格式展示给用户