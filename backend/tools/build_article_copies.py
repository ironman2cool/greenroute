"""Build the per-platform copies of the article from docs/article.md (the one file to edit).

    python tools/build_article_copies.py

- Unwraps docs/article.md so each paragraph is one line. Medium turns hard line breaks inside a
  paragraph into visible breaks; DEV and GitHub look the same either way.
- docs/publish/dev.md: DEV settings block + the article (DEV shows the title itself).
- docs/publish/medium.html: open in a browser, select all, copy, paste into a new Medium story.
  Tables become lists (Medium has no tables) and images are absolute URLs, so they paste in.
"""
import html
import os
import re

import markdown

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs")
DEV_FRONT = """---
title: "Should this prompt leave your laptop? Building a local-first AI router and doing the honest math"
published: true
tags: ai, llm, sustainability, python
cover_image: https://raw.githubusercontent.com/ironman2cool/greenroute/main/docs/images/hero.png
---

"""
_BLOCK_START = re.compile(r"^(#|\||!\[|```|<)")
_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s")


def unwrap(md: str) -> str:
    """Join soft-wrapped lines: paragraphs, list items and blockquotes become one line each."""
    out, in_code = [], False
    for line in md.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        prev = out[-1] if out else ""
        joinable = (not in_code and line.strip() and prev.strip() and not _BLOCK_START.match(line)
                    and not _BLOCK_START.match(prev) and not _ITEM.match(line))
        if joinable and line.startswith(">") and prev.startswith(">"):
            out[-1] = prev.rstrip() + " " + line[1:].strip()
        elif joinable and not line.startswith(">") and not prev.startswith(">"):
            out[-1] = prev.rstrip() + " " + line.strip()
        else:
            out.append(line)
    return "\n".join(out)


def tables_to_lists(md: str) -> str:
    """'| a | b |' rows -> '- **a**: b' (Medium can't render tables)."""
    out, rows = [], []
    for line in md.split("\n") + [""]:
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip("|").split("|")])
            continue
        if rows:
            body = [r for r in rows[1:] if not set("".join(r)) <= set("-: ")]
            out += [f"- **{r[0]}**: {' · '.join(r[1:])}" for r in body]
            rows = []
        out.append(line)
    return "\n".join(out[:-1])


def main():
    src = os.path.join(DOCS, "article.md")
    with open(src, encoding="utf-8") as f:
        article = unwrap(f.read().strip()) + "\n"
    with open(src, "w", encoding="utf-8") as f:
        f.write(article)

    body = article.split("\n", 1)[1].lstrip("\n")  # without the "# Title" line
    os.makedirs(os.path.join(DOCS, "publish"), exist_ok=True)
    with open(os.path.join(DOCS, "publish", "dev.md"), "w", encoding="utf-8") as f:
        f.write(DEV_FRONT + body)

    title = article.split("\n", 1)[0].lstrip("# ").strip()
    content = markdown.markdown(tables_to_lists(article), extensions=["fenced_code"])
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{max-width:720px;margin:40px auto;padding:0 20px;font:18px/1.6 Georgia,serif;color:#222;background:#fff}}
img{{max-width:100%}} blockquote{{border-left:3px solid #ccc;margin:0;padding-left:16px;color:#555}}
code{{font-family:Menlo,Consolas,monospace;font-size:.9em}}</style></head>
<body>
{content}
</body></html>
"""
    with open(os.path.join(DOCS, "publish", "medium.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("Updated docs/article.md, docs/publish/dev.md, docs/publish/medium.html")


if __name__ == "__main__":
    main()
