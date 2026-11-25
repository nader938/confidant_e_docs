"""Builds the public support site from the project's own text.

    python3 store/site/build.py

Reads docs/user-guide.md, the worked examples in docs/tutorials/, and the
files in src/ beside this script, and writes index.html, guide.html,
tutorials.html, privacy.html and media.json. All pages share site.css.
Guide sections listed in MEDIA get a player when their file is here. Nothing
is uploaded: publishing is a separate commit and push of this folder.
"""

import html
import json
import re
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parent
DOCS = SITE.parent.parent / "docs"
CONTACT = (SITE / "src" / "contact.txt").read_text().strip()

PAGES = [
    ("index.html", "Home"),
    ("guide.html", "User guide"),
    ("tutorials.html", "Tutorials"),
    ("privacy.html", "Privacy"),
]

# Simple line icons, drawn at 24 by 24.
ICONS = {
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "cloud": '<path d="M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17.2 9.1 4.5 4.5 0 0 1 17.5 18H7z"/><path d="M12 16v-5m0 0-2 2m2-2 2 2"/>',
    "wand": '<path d="m4 20 11-11"/><path d="m14 6 4 4"/><path d="M18 3v3m-1.5-1.5h3M6 4v2M5 5h2m12 9v2m-1-1h2"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M6 11a6 6 0 0 0 12 0M12 17v4"/>',
    "chat": '<path d="M4 5h12v9H8l-4 3z"/><path d="M8 17h8l4 3V9h-2"/>',
    "scale": '<path d="M12 4v16M7 20h10M5 8h14"/><path d="m5 8-3 6a3 3 0 0 0 6 0zm14 0-3 6a3 3 0 0 0 6 0z"/>',
    "note": '<path d="M5 4h14v11l-5 5H5z"/><path d="M14 20v-5h5M8 9h8M8 13h4"/>',
    "wifi-off": '<path d="M3 3l18 18"/><path d="M5 12.5a10 10 0 0 1 3.5-2.3M2 9a15 15 0 0 1 4-2.6M10.7 5.1A15 15 0 0 1 22 9M14.5 9.7A10 10 0 0 1 19 12.5M8.5 16a5 5 0 0 1 5-1.3"/><circle cx="12" cy="19" r="1"/>',
}


def icon(name: str) -> str:
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{ICONS[name]}</svg>'
    )


def page(title: str, body: str, here: str, description: str) -> str:
    links = "".join(
        f'<a href="{"./" if file == "index.html" else file}"'
        f'{" class=here" if file == here else ""}>{label}</a>'
        for file, label in PAGES
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="site.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="./">confidant<span>·e</span></a>
<nav>{links}</nav>
</div></header>
{body}
<footer><div class="wrap">
<span>confidant·e · made by Nader Amir</span>
<a href="mailto:{CONTACT}">{CONTACT}</a>
<a href="privacy.html">Privacy policy</a>
</div></footer>
</body>
</html>
"""


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


# Recordings and videos that go with sections of the guide. Each entry is
# (section number, anchor on the web page, title, kind, file under this
# folder). The website shows them in the guide, and the app reads the same
# list from media.json and plays them from here, so adding one needs no new
# version of the app. kind is "audio" or "video".
MEDIA = [
    ("1", "1-why-use-it", "An introduction", "audio", "audio/00-intro.m4a"),
    ("3", "3-getting-started", "Getting started", "audio", "audio/02-getting-started.m4a"),
    ("10", "10-compare-ais", "Comparing AIs", "audio", "audio/09-comparing-ais.m4a"),
]


def media() -> str:
    """The list the app fetches: only files that are really here."""
    return json.dumps(
        {
            "version": 1,
            "guide": [
                {"section": section, "title": title, "kind": kind, "file": file}
                for section, _, title, kind, file in MEDIA
                if (SITE / file).exists()
            ],
        },
        indent=2,
    )


def home() -> str:
    features = [
        ("wand", "Clean up your writing", "Paste or dictate rough text and get a clean version beside it, with every change shaded so you can see what was done."),
        ("chat", "Ask in private", "Hold a conversation with the AI you choose. Earlier conversations stay on your Mac, ready to pick up again."),
        ("mic", "Dictate instead of typing", "Speak and the words appear. With Whisper, your voice is recognised on your Mac and goes nowhere."),
        ("scale", "Compare AIs fairly", "Put one question to two AIs with the names hidden, pick the better answer, and see which wins on your own questions."),
        ("note", "Memory you control", "Notes that carry from one conversation to the next. You read, edit and approve them before anything is kept."),
        ("wifi-off", "Offline mode", "One switch, and the app makes no internet connections at all. The AIs on your Mac carry on working."),
    ]
    cards = "\n".join(
        f'<div class="card"><div class="icon">{icon(name)}</div>'
        f"<h3>{title}</h3><p>{text}</p></div>"
        for name, title, text in features
    )
    needs = [
        ("The built-in AI", "A Mac with macOS 14, 16 GB of memory and 2.5 GB of free space. One download, nothing else to install."),
        ("Larger local AIs", "The free Ollama app and more memory: 32 to 64 GB for mid-sized models, 128 GB recommended for the most powerful."),
        ("An online AI, if you want one", "Your own Anthropic API key for Claude. Optional, and never chosen for you."),
    ]
    need_cards = "\n".join(
        f'<div class="card"><h3 style="margin-top:0">{title}</h3><p>{text}</p></div>'
        for title, text in needs
    )
    listen = ""
    if (SITE / "audio" / "00-intro.m4a").exists():
        listen = """
<section><div class="wrap">
<div class="listen">
<h2>Hear it from the author</h2>
<p>Nader Amir on what confidant·e is and why he uses it. About three and a half minutes.</p>
<audio controls preload="none" src="audio/00-intro.m4a"></audio>
</div>
</div></section>"""
    body = f"""
<div class="hero"><div class="wrap">
{icon("lock")}
<h1>Your own AI, on your own Mac.</h1>
<p class="lead">confidant·e helps you write and answers your questions with an AI that runs on your computer. What you type stays with you.</p>
<div class="buttons">
<a class="button solid" href="guide.html">Read the guide</a>
<a class="button line" href="tutorials.html">See worked examples</a>
</div>
<p class="soon">Coming to the Mac App Store.</p>
</div></div>
<div class="shot"><img src="img/01-clean-up.jpg" width="1800" height="1125" alt="confidant·e cleaning up a rough letter, with the changed words shaded and a green Private bar across the top"></div>

<section class="center"><div class="wrap">
<h2>You always know where your words are going</h2>
<p class="intro">A bar across the top of the app says it plainly, and changes the moment you choose a different AI.</p>
<div class="bars">
<div class="bar private">{icon("lock")}<span><b>Private</b>&ensp;Running on this computer. Nothing you write leaves it.</span></div>
<div class="bar online">{icon("cloud")}<span><b>Online</b>&ensp;What you write here is sent to Anthropic.</span></div>
</div>
</div></section>

<section class="center"><div class="wrap">
<h2>Everything a writing assistant does, kept to yourself</h2>
<p class="intro">For the letter to your doctor, the note about a client, the question you would not type into a website.</p>
<div class="grid">
{cards}
</div>
</div></section>

<section class="center"><div class="wrap">
<h2>See it at work</h2>
<p class="intro">&nbsp;</p>
<div class="gallery">
<figure><img loading="lazy" src="img/02-ask.jpg" width="1800" height="1125" alt="A conversation in Ask mode with a rated answer"><figcaption>Ask a question and follow up. Rate the answers as you go.</figcaption></figure>
<figure><img loading="lazy" src="img/03-compare-blind.jpg" width="1800" height="1125" alt="Two unnamed answers to the same question, with buttons to pick the better one"><figcaption>Two AIs, names hidden. You pick the better answer.</figcaption></figure>
<figure><img loading="lazy" src="img/05-offline-mode.jpg" width="1800" height="1125" alt="The app with Offline mode switched on"><figcaption>Offline mode: no connections, and it still works.</figcaption></figure>
</div>
</div></section>
{listen}
<section class="center"><div class="wrap">
<h2>What you need</h2>
<p class="intro">A small AI is good at tidying your writing. To get close to a commercial AI in private, you need a large model and a Mac with the memory to hold it.</p>
<div class="grid">
{need_cards}
</div>
</div></section>
"""
    return page(
        "confidant·e: your own AI, on your own Mac",
        body,
        "index.html",
        "A private writing and AI assistant for the Mac. The AI runs on your "
        "own computer, so what you type stays with you.",
    )


def guide() -> str:
    text = (DOCS / "user-guide.md").read_text()
    text = text.replace("](videos/README.md)", "](tutorials.html)")
    # The page has its own list of sections down the side.
    text = re.sub(r"Contents:\n\n(?:\d+\. [^\n]*\n)+\n", "", text)
    body = pandoc(text)
    for _, anchor, title, kind, file in MEDIA:
        if not (SITE / file).exists():
            continue
        heading = re.search(rf'<h2 id="{anchor}">.*?</h2>', body, flags=re.S)
        if heading:
            tag = "video" if kind == "video" else "audio"
            verb = "Watch" if kind == "video" else "Listen"
            player = (
                f'\n<{tag} controls preload="none" src="{file}"></{tag}>'
                f'\n<p class="note">{verb}: {html.escape(title)}, '
                "recorded by Nader Amir.</p>"
            )
            body = body[: heading.end()] + player + body[heading.end() :]
    sections = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body, flags=re.S)
    toc = "".join(
        f'<a href="#{anchor}">{re.sub("<[^>]+>", "", title)}</a>'
        for anchor, title in sections
    )
    content = (
        '<div class="wrap page"><div class="with-toc">'
        f'<aside class="toc"><p>In this guide</p>{toc}</aside>'
        f"<main>{body}</main></div></div>"
    )
    return page(
        "confidant·e user guide",
        content,
        "guide.html",
        "Everything confidant·e does, section by section.",
    )


def tutorials() -> str:
    """The worked examples in docs/tutorials, one after another."""
    entries, cards = [], []
    sources = sorted((DOCS / "tutorials").glob("[0-9][0-9]-*.md"))
    for number, source in enumerate(sources, start=1):
        text = source.read_text()
        title = text.splitlines()[0].lstrip("# ").strip()
        aim = re.search(r"\*\*You will:\*\*\s*(.+?)\s*$", text, flags=re.M)
        slug = source.stem
        cards.append(
            f'<a href="#{slug}"><span class="n">{number}</span><span>'
            f"<b>{html.escape(title)}</b>"
            f'<small>{html.escape(aim.group(1)) if aim else ""}</small>'
            "</span></a>"
        )
        # The page has one title; each tutorial's headings sit a level down.
        lowered = re.sub(r"^(#{1,5}) ", r"#\1 ", text, flags=re.M)
        entries.append(
            f'<section class="tutorial" id="{slug}" style="padding:0">\n'
            f"{pandoc(lowered)}</section>"
        )
    body = (
        '<div class="wrap narrow page" style="max-width:52rem">'
        "<h1>Tutorials</h1>\n"
        '<p class="sub">Worked examples: real tasks from start to finish, '
        "with text to type and what to expect. For a description of every "
        'feature, see the <a href="guide.html">user guide</a>.</p>\n'
        f'<div class="tutorial-list">{"".join(cards)}</div>\n'
        + "\n".join(entries)
        + "</div>"
    )
    return page(
        "confidant·e tutorials",
        body,
        "tutorials.html",
        "Worked examples for confidant·e: real tasks from start to finish.",
    )


def privacy() -> str:
    body = (SITE / "src" / "privacy.body.html").read_text()
    return page(
        "confidant·e privacy policy",
        f'<div class="wrap narrow page">{body}</div>',
        "privacy.html",
        "What happens to your information when you use confidant·e.",
    )


if __name__ == "__main__":
    for name, build in [
        ("index.html", home),
        ("guide.html", guide),
        ("tutorials.html", tutorials),
        ("privacy.html", privacy),
    ]:
        (SITE / name).write_text(build())
    (SITE / "media.json").write_text(media() + "\n")
    print("wrote index, guide, tutorials, privacy and media.json (not uploaded)")
