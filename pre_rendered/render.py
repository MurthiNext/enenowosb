#!/usr/bin/env python3
"""
render.py — 将 pre_rendered/index.html 中的 {{z|注释内容}} 渲染为带编号脚注的 HTML

用法：
    python pre_rendered/render.py
    # 输出到项目根目录 index.html

工作流程：
  1. 读取 pre_rendered/index.html
  2. 提取所有 {{z|注释内容}} 并替换为 <sup class="footnote"><a href="#fn-N">[N]</a></sup>
  3. 在 <!-- {{z-footnotes}} --> 处自动生成脚注列表
  4. 输出到 ../index.html
"""

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "index.html"
DST = Path(__file__).resolve().parent.parent / "index.html"

# 匹配 {{z|任意内容}}，非贪婪，支持 DOTALL 以匹配含 HTML 标签的内容
Z_PATTERN = re.compile(r'\{\{z\|(.*?)\}\}', re.DOTALL)


def render(src_path: Path, dst_path: Path) -> None:
    src = src_path.read_text(encoding="utf-8")
    content = src

    # --- 第 1 步：收集并替换 {{z|...}} ---
    footnotes: list[tuple[int, str]] = []
    order: list[int] = []  # 记录每个 {{z|...}} 实际出现的序号，用于脚注列表

    def replace_z(match: re.Match) -> str:
        text = match.group(1).strip()
        idx = len(footnotes) + 1
        footnotes.append((idx, text))
        # 内联注释浮窗，保留原始 HTML（含链接）
        return (f'<span class="fn-wrap">'
                f'<sup class="footnote"><a href="#fn-{idx}">[{idx}]</a></sup>'
                f'<span class="fn-tip">{text}</span>'
                f'</span>')

    content = Z_PATTERN.sub(replace_z, content)

    # --- 第 2 步：生成脚注列表 HTML ---
    if footnotes:
        lines = ["<ol>"]
        for idx, text in footnotes:
            # text 中可能含 HTML（如 <a> 标签），直接插入
            lines.append(f'  <li id="fn-{idx}"><a href="#fn-{idx}">↑</a> {text}</li>')
        lines.append("</ol>")
        footnotes_html = "\n".join(lines)

        # 替换占位标记
        placeholder = "<!-- {{z-footnotes}} -->"
        if placeholder not in content:
            print("错误：未找到 {{z-footnotes}} 占位标记", file=sys.stderr)
            sys.exit(1)
        content = content.replace(placeholder, footnotes_html, 1)

    # --- 第 3 步：写出 ---
    dst_path.write_text(content, encoding="utf-8")
    print(f"✓ 已生成 {dst_path}")
    print(f"  共 {len(footnotes)} 条脚注")


if __name__ == "__main__":
    render(SRC, DST)
