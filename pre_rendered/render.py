#!/usr/bin/env python3
"""
render.py — 渲染 pre_rendered/index.html 到项目根目录 index.html

功能：
  1. 提取 {{z|注释内容}} 替换为带编号脚注
  2. 扫描 h2/h3 标题自动生成目录 ({{TOC目录}})
  3. 在 {{z-footnotes}} 处生成脚注列表

用法：
    python pre_rendered/render.py
"""

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "index.html"
DST = Path(__file__).resolve().parent.parent / "index.html"

Z_PATTERN = re.compile(r'\{\{z\|(.*?)\}\}', re.DOTALL)
HEADING_PATTERN = re.compile(r'<h([23])\s+id="([^"]*)"[^>]*>(.*?)</h\1>', re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')

TOC_PLACEHOLDER = '{{TOC目录}}'
FN_PLACEHOLDER = '<!-- {{z-footnotes}} -->'


def strip_html(text: str) -> str:
    return TAG_RE.sub('', text).strip()


def build_toc(content: str) -> str:
    headings = []
    for m in HEADING_PATTERN.finditer(content):
        level = int(m.group(1))
        hid = m.group(2)
        text = strip_html(m.group(3))
        headings.append((level, hid, text))

    if not headings:
        return ''

    lines = [
        '<nav id="toc">',
        '  <details open>',
        '    <summary>目录</summary>',
        '    <div class="toc-inner">',
        '    <ol>',
    ]
    for level, hid, text in headings:
        cls = 'toc-h2' if level == 2 else 'toc-h3'
        lines.append(f'    <li class="{cls}"><a href="#{hid}">{text}</a></li>')
    lines.extend([
        '  </ol>',
        '    </div>',
        '  </details>',
        '</nav>',
    ])
    return '\n'.join(lines)


def render(src_path: Path, dst_path: Path) -> None:
    src = src_path.read_text(encoding="utf-8")
    content = src

    # --- 第 1 步：生成并替换目录 ---
    toc_html = build_toc(content)
    if TOC_PLACEHOLDER not in content:
        print("错误：未找到 {{TOC目录}} 占位标记", file=sys.stderr)
        sys.exit(1)
    content = content.replace(TOC_PLACEHOLDER, toc_html, 1)
    print(f"  TOC目录: {toc_html.count('<li')} 条")

    # --- 第 2 步：收集并替换 {{z|...}} ---
    footnotes: list[tuple[int, str]] = []

    def replace_z(match: re.Match) -> str:
        text = match.group(1).strip()
        idx = len(footnotes) + 1
        footnotes.append((idx, text))
        return (f'<span class="fn-wrap">'
                f'<sup class="footnote"><a href="#fn-{idx}">[{idx}]</a></sup>'
                f'<span class="fn-tip">{text}</span>'
                f'</span>')

    content = Z_PATTERN.sub(replace_z, content)

    # --- 第 3 步：生成脚注列表 HTML ---
    if footnotes:
        lines = ["<ol>"]
        for idx, text in footnotes:
            lines.append(f'  <li id="fn-{idx}"><a href="#fn-{idx}">↑</a> {text}</li>')
        lines.append("</ol>")
        footnotes_html = "\n".join(lines)

        if FN_PLACEHOLDER not in content:
            print("错误：未找到 {{z-footnotes}} 占位标记", file=sys.stderr)
            sys.exit(1)
        content = content.replace(FN_PLACEHOLDER, footnotes_html, 1)

    # --- 第 4 步：写出 ---
    dst_path.write_text(content, encoding="utf-8")
    print(f"✓ 已生成 {dst_path}")
    print(f"  共 {len(footnotes)} 条脚注")


if __name__ == "__main__":
    render(SRC, DST)
