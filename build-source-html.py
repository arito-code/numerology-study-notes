#!/usr/bin/env python3
"""Convert source Markdown files to branded HTML pages."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import markdown
    from markdown.extensions import tables
except ImportError:
    raise SystemExit("Run: pip install markdown")

ROOT = Path(__file__).resolve().parent

CSS = """
    :root {
      --green: #1F4D3A; --gold: #C6A85C; --beige: #F5F3E7;
      --navy: #243A5E; --ink: #17352D; --text: #21342F;
      --muted: #6B7A75; --line: #E4E2D8; --white: #fff;
      --radius: 6px; --max: 820px;
    }
    * { box-sizing: border-box; }
    body { margin: 0; }
    .source-text {
      font-family: "Inter", "Zen Kaku Gothic New", system-ui, sans-serif;
      color: var(--text);
      background: linear-gradient(90deg, #fff 0%, #fff 55%, #fbfaf4 100%);
      line-height: 1.85; letter-spacing: 0.02em;
      padding: 48px 24px 96px;
    }
    .wrap { max-width: var(--max); margin: 0 auto; }
    .hero { padding-bottom: 40px; border-bottom: 1px solid var(--line); margin-bottom: 48px; }
    .hero-label { font-size: 12px; font-weight: 800; letter-spacing: 0.28em; color: var(--gold); margin: 0 0 12px; }
    h1 { font-size: clamp(28px, 4vw, 36px); font-weight: 900; color: var(--green); margin: 0 0 16px; line-height: 1.35; }
    .hero-meta { font-size: 14px; color: var(--muted); font-weight: 600; margin: 0; }
    .hero-meta strong { color: var(--ink); }
    .hero-meta a { color: var(--green); }
    .nav-links { display: flex; flex-wrap: wrap; gap: 12px 20px; margin-top: 12px; font-size: 14px; font-weight: 700; }
    .nav-links a { color: var(--green); text-decoration: none; }
    .nav-links a:hover { text-decoration: underline; }
    .content h2 {
      font-size: clamp(20px, 3vw, 26px); font-weight: 900; color: var(--green);
      margin: 48px 0 16px; padding-top: 24px; border-top: 1px solid var(--line);
    }
    .content h2:first-child { margin-top: 0; padding-top: 0; border-top: none; }
    .content h3 { font-size: 17px; font-weight: 800; color: var(--navy); margin: 28px 0 10px; }
    .content p, .content li { font-size: 15px; font-weight: 600; color: #3a4a45; }
    .content p { margin: 0 0 1em; }
    .content ul, .content ol { margin: 0 0 1.2em; padding-left: 1.4em; }
    .content li { margin-bottom: 0.35em; }
    .content blockquote {
      margin: 0 0 24px; padding: 16px 20px;
      background: var(--beige); border-left: 4px solid var(--gold);
      border-radius: 0 var(--radius) var(--radius) 0;
      font-size: 14px; font-weight: 700; color: var(--ink);
    }
    .content blockquote p { margin: 0 0 0.5em; }
    .content blockquote p:last-child { margin-bottom: 0; }
    .content hr { border: none; border-top: 1px solid var(--line); margin: 32px 0; }
    .content table {
      width: 100%; border-collapse: collapse; margin: 16px 0 20px;
      font-size: 13px; font-weight: 700;
    }
    .content th { background: var(--green); color: var(--white); padding: 8px 10px; text-align: left; }
    .content td { padding: 8px 10px; border-bottom: 1px solid var(--line); background: var(--white); }
    .content tr:nth-child(even) td { background: #faf9f4; }
    .content .table-scroll { overflow-x: auto; margin: 16px 0 20px; }
    .content code {
      font-family: "Cambria Math", Consolas, monospace;
      font-size: 0.92em; background: var(--beige);
      padding: 2px 6px; border-radius: 3px;
    }
    .content ul li { list-style: disc; }
    .content ol li { list-style: decimal; }
    .content strong { font-weight: 800; color: var(--ink); }
    .badge {
      display: inline-block; font-size: 11px; font-weight: 800;
      letter-spacing: 0.12em; color: var(--white); background: var(--navy);
      padding: 4px 10px; border-radius: 3px; margin-bottom: 8px;
    }
    footer { margin-top: 48px; font-size: 12px; color: var(--muted); text-align: center; font-weight: 600; }
    .hebrew { font-family: "Times New Roman", serif; direction: rtl; }
"""

PAGES = [
    {
        "md": ROOT / "P146-152_4章.珍しい数と数の型" / "magic-squares-and-unusual-numbers.md",
        "out": ROOT / "chapter-4-source.html",
        "title": "第4章 珍しい数と数の型 — 原文テキスト",
        "label": "SOURCE TEXT — CHAPTER 4",
        "heading": "第4章「珍しい数と数の型」<br>原文テキスト",
        "meta": "出典：<strong>『数秘術』ジョン・キング著</strong>　／　pp.146–159<br>MD要約から生成した原文表示ページ",
        "study_link": "/chapter-4.html",
        "study_label": "学習ノート（解説付き）",
    },
    {
        "md": ROOT / "P162-198_5章.カバラを超えて" / "数秘術-第5章-学習ノート.md",
        "out": ROOT / "chapter-5-source.html",
        "title": "第5章 カバラ、それを超えて — 原文テキスト",
        "label": "SOURCE TEXT — CHAPTER 5",
        "heading": "第5章「カバラ、それを超えて」<br>原文テキスト",
        "meta": "出典：<strong>『数秘術』ジョン・キング著</strong>　／　pp.162–198<br>MD要約から生成した原文表示ページ",
        "study_link": "/chapter-5.html",
        "study_label": "学習ノート（解説付き）",
    },
]


def prepare_md(text: str) -> str:
    """Drop redundant title and MD-only meta blockquote."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    if i < len(lines) and lines[i].startswith("# "):
        i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and lines[i].strip().startswith(">"):
        while i < len(lines) and (lines[i].strip().startswith(">") or lines[i].strip() == ""):
            i += 1
    while i < len(lines) and lines[i].strip() in ("", "---"):
        if lines[i].strip() == "---":
            i += 1
            break
        i += 1
    out.extend(lines[i:])
    return "\n".join(out).lstrip("\n")


def md_to_html(text: str) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "nl2br"])
    html = md.convert(text)
    html = re.sub(
        r"<table>",
        r'<div class="table-scroll"><table>',
        html,
    )
    html = html.replace("</table>", "</table></div>")
    return html


def build_page(cfg: dict) -> None:
    md_text = prepare_md(cfg["md"].read_text(encoding="utf-8"))
    body = md_to_html(md_text)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{cfg["title"]}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="source-text">
<div class="wrap">

<header class="hero">
  <p class="hero-label">{cfg["label"]}</p>
  <span class="badge">原文表示</span>
  <h1>{cfg["heading"]}</h1>
  <p class="hero-meta">
    {cfg["meta"]}<br>
    <span class="nav-links">
      <a href="/">← 目次に戻る</a>
      <a href="{cfg["study_link"]}">→ {cfg["study_label"]}</a>
    </span>
  </p>
</header>

<article class="content">
{body}
</article>

<footer>
  出典：ジョン・キング『数秘術』／ スクール研修用
</footer>

</div>
</div>
</body>
</html>
"""
    cfg["out"].write_text(html, encoding="utf-8")
    print(f"Wrote {cfg['out'].name}")


def main() -> None:
    for cfg in PAGES:
        if not cfg["md"].exists():
            raise SystemExit(f"Missing: {cfg['md']}")
        build_page(cfg)


if __name__ == "__main__":
    main()
