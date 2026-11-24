"""Builds the public documentation pages from the project's own text.

    python3 store/site/build.py

Reads docs/user-guide.md and the worked examples in docs/tutorials/, and
writes guide.html and tutorials.html beside this file. Guide sections listed
in RECORDINGS get an audio player when their recording is in audio/. Nothing
is uploaded: publishing is a separate commit and push of this folder.
"""

import html
import re
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parent
DOCS = SITE.parent.parent / "docs"

STYLE = """<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{color-scheme:light dark}
body{font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:44rem;margin:0 auto;padding:1.5rem 1.25rem 4rem;color:#1b1b21;background:#fbf8ff}
nav{display:flex;flex-wrap:wrap;gap:.25rem 1.25rem;padding-bottom:.9rem;margin-bottom:2rem;border-bottom:1px solid #c7c5d0;font-size:.95rem}
nav strong{margin-right:auto}
h1{font-size:1.9rem;line-height:1.2;margin:0 0 .5rem}
h2{font-size:1.3rem;margin:2.5rem 0 .5rem}h3{font-size:1.05rem;margin:1.5rem 0 .3rem}
.sub{color:#5b5d72;margin:0 0 1.5rem}a{color:#4b53a8}li{margin:.35rem 0}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.95rem;margin:1rem 0}
th,td{text-align:left;vertical-align:top;padding:.5rem .75rem;border-bottom:1px solid #c7c5d0}
pre{background:rgba(120,120,140,.14);padding:.75rem 1rem;border-radius:8px;overflow-x:auto;font-size:.9rem;line-height:1.5;white-space:pre-wrap}blockquote{margin:1rem 0;padding:.1rem 1rem;border-left:3px solid #c7c5d0;color:#5b5d72}.tutorial{border-top:1px solid #c7c5d0;margin-top:2.5rem}.tutorial h2{margin-top:1.75rem}
audio{width:100%;margin:.5rem 0 0}.note{font-size:.85rem;color:#5b5d72;margin:.25rem 0 1rem}
.tutorial{padding-top:.5rem}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #c7c5d0;font-size:.9rem;color:#5b5d72}
@media (prefers-color-scheme:dark){body{color:#e4e1e9;background:#131318}.sub,footer{color:#c7c5d0}a{color:#bdc2ff}nav,th,td,footer{border-color:#46464f}}
</style>"""

NAV = """<nav><strong>confidant·e</strong>
<a href="./">Support</a><a href="guide.html">User guide</a>
<a href="tutorials.html">Tutorials</a><a href="privacy.html">Privacy</a></nav>"""


def page(title: str, body: str) -> str:
    return (
        f'<!doctype html><html lang="en"><head><title>{html.escape(title)}'
        f"</title>{STYLE}</head><body>\n{NAV}\n{body}\n"
        "<footer>confidant·e · Nader Amir</footer>\n</body></html>\n"
    )


def pandoc(markdown: str) -> str:
    body = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "html", "--no-highlight"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # Wide tables scroll inside themselves on a phone.
    return body.replace("<table>", '<div class="table"><table>').replace(
        "</table>", "</table></div>"
    )


# Guide sections that open with a recording of the author talking about them.
RECORDINGS = {
    "1-why-use-it": ("00-intro", "An introduction"),
    "3-getting-started": ("02-getting-started", "Getting started"),
    "10-compare-ais": ("09-comparing-ais", "Comparing AIs"),
}


def guide() -> str:
    text = (DOCS / "user-guide.md").read_text()
    text = text.replace("](videos/README.md)", "](tutorials.html)")
    body = pandoc(text)
    for section, (name, title) in RECORDINGS.items():
        if not (SITE / "audio" / f"{name}.m4a").exists():
            continue
        heading = re.search(rf'<h2 id="{section}">.*?</h2>', body, flags=re.S)
        if heading:
            player = (
                f'\n<audio controls preload="none" src="audio/{name}.m4a">'
                f'</audio>\n<p class="note">Listen: {html.escape(title)}, '
                "recorded by Nader Amir.</p>"
            )
            body = body[: heading.end()] + player + body[heading.end() :]
    return page("confidant·e User Guide", body)


def tutorials() -> str:
    """The worked examples in docs/tutorials, one after another."""
    entries, contents = [], []
    for source in sorted((DOCS / "tutorials").glob("[0-9][0-9]-*.md")):
        text = source.read_text()
        title = text.splitlines()[0].lstrip("# ").strip()
        slug = source.stem
        contents.append(f'<li><a href="#{slug}">{html.escape(title)}</a></li>')
        # The page has one title; each tutorial's headings sit a level down.
        lowered = re.sub(r"^(#{1,5}) ", r"#\1 ", text, flags=re.M)
        entries.append(
            f'<section class="tutorial" id="{slug}">\n{pandoc(lowered)}</section>'
        )
    body = (
        "<h1>Tutorials</h1>\n"
        '<p class="sub">Worked examples: real tasks from start to finish, '
        "with text to type and what to expect. For a description of every "
        'feature, see the <a href="guide.html">user guide</a>.</p>\n'
        f"<ol>\n{chr(10).join(contents)}\n</ol>\n" + "\n".join(entries)
    )
    return page("confidant·e Tutorials", body)


if __name__ == "__main__":
    (SITE / "guide.html").write_text(guide())
    (SITE / "tutorials.html").write_text(tutorials())
    print("wrote guide.html and tutorials.html (not uploaded)")
