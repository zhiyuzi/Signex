---
name: extract-content
description: HTML 正文提取工具。当分析阶段发现某 item 的 content 不足时，用此工具提取完整正文。支持 BeautifulSoup（免费）和 Firecrawl API（可选，需 FIRECRAWL_API_KEY）。
---

# extract-content

从 stdin 读取 URL 列表，提取网页正文内容：

```bash
echo '{"urls": ["https://example.com/article"]}' | uv run python .claude/skills/extract-content/scripts/extract.py
```

参数：
- `urls`: 要提取内容的 URL 数组

可选环境变量 `FIRECRAWL_API_KEY`：设置后优先使用 Firecrawl API 获取 LLM-ready Markdown，未设置则使用 BeautifulSoup 本地提取。

输出格式（与 sensor 不同）：
```json
{"success": true, "results": [{"url": "...", "title": "...", "content": "...", "word_count": 1234, "extractor": "firecrawl"}], "error": ""}
```

`extractor` 字段仅在 Firecrawl 路径返回，BS4 fallback 时不包含此字段。

注意：这不是 sensor，不存入 items 表。用于分析阶段补充内容深度。
