import pytest
from doc_translator.translator import split_markdown_by_paragraph

def test_split_simple_paragraphs():
    md = "문단1입니다.\n\n문단2입니다.\n\n문단3입니다."
    chunks = split_markdown_by_paragraph(md)
    assert len(chunks) == 3
    assert chunks[0].strip() == "문단1입니다."
    assert chunks[1].strip() == "문단2입니다."
    assert chunks[2].strip() == "문단3입니다."

def test_split_with_codeblock():
    md = "문단1입니다.\n\n```python\nprint('hello')\n```\n\n문단2입니다."
    chunks = split_markdown_by_paragraph(md)
    assert len(chunks) == 3
    assert "```python" in chunks[1]

def test_split_with_header():
    md = "# 제목\n\n문단1\n\n## 소제목\n\n문단2"
    chunks = split_markdown_by_paragraph(md)
    assert len(chunks) == 5
    assert chunks[0].startswith("# 제목")
    assert chunks[2].startswith("## 소제목")
