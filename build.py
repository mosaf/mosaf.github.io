#!/usr/bin/env python3
"""Regenerate the publication lists in index.html from the .bib files in bib/.

Usage:
    python3 build.py            rewrite index.html in place
    python3 build.py --check    exit 1 if index.html is out of date, change nothing

Add a paper by dropping its .bib into bib/journal, bib/conference or bib/workshop
and re-running this script. See bib/README.md for the fields.

Standard library only - no pip install required.
"""

import argparse
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")
BIB = os.path.join(ROOT, "bib")

# Whose name to bold in author lists.
ME = "Mojtaba Safari"

# Section heading in index.html -> bib/ subfolder.
SECTIONS = [
    ("Selected Journal Articles", "journal"),
    ("Selected Conference Papers &amp; Abstracts", "conference"),
    ("Workshop Papers", "workshop"),
]

# Which link fields to render, and in what order.
LINK_FIELDS = ["code", "abstract", "pdf", "slides", "video", "data"]

# Every entry also gets a "bib" link to its source file on GitHub, which renders
# the BibTeX with syntax highlighting and a copy button. Set to None to disable.
REPO_BLOB_BASE = "https://github.com/mosaf/mosaf.github.io/blob/main/bib"

# Generated regions are identified by the data-generated attribute on the <ul>,
# NOT by HTML comments. Comments cannot nest, so a comment marker written inside
# an already-commented-out section terminates it early and leaks markup onto the
# page. The attribute has no such failure mode and is inert in CSS.


# --------------------------------------------------------------------------
# BibTeX parsing
# --------------------------------------------------------------------------

def parse_bib(text):
    """Parse a .bib file containing one or more entries. Returns list of dicts
    with '_type' and '_key' plus lowercased field names."""
    entries = []
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text[at:])
        if not m:
            i = at + 1
            continue
        entry = {"_type": m.group(1).lower(), "_key": m.group(2)}
        pos = at + m.end()
        depth = 1
        while pos < len(text) and depth > 0:
            fm = re.match(r"\s*([\w-]+)\s*=\s*", text[pos:])
            if not fm:
                # No more fields; skip to the closing brace of the entry.
                while pos < len(text) and depth > 0:
                    if text[pos] == "{":
                        depth += 1
                    elif text[pos] == "}":
                        depth -= 1
                    pos += 1
                break
            name = fm.group(1).lower()
            pos += fm.end()
            value, pos = _read_value(text, pos)
            entry[name] = value
            mm = re.match(r"\s*,", text[pos:])
            if mm:
                pos += mm.end()
            else:
                while pos < len(text) and depth > 0:
                    if text[pos] == "{":
                        depth += 1
                    elif text[pos] == "}":
                        depth -= 1
                    pos += 1
                break
        entries.append(entry)
        i = pos
    return entries


def _read_value(text, pos):
    """Read a field value starting at pos: {braced}, "quoted", or bare."""
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text):
        return "", pos
    if text[pos] == "{":
        depth, start = 0, pos
        while pos < len(text):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    return text[start + 1:pos], pos + 1
            pos += 1
        return text[start + 1:], pos
    if text[pos] == '"':
        start = pos + 1
        pos += 1
        while pos < len(text) and text[pos] != '"':
            pos += 2 if text[pos] == "\\" else 1
        return text[start:pos], pos + 1
    start = pos
    while pos < len(text) and text[pos] not in ",}\n":
        pos += 1
    return text[start:pos].strip(), pos


# --------------------------------------------------------------------------
# LaTeX -> plain text
# --------------------------------------------------------------------------

ACCENTS = {
    '"a': "ä", '"o': "ö", '"u': "ü", '"A': "Ä", '"O': "Ö", '"U': "Ü",
    "'a": "á", "'e": "é", "'i": "í", "'o": "ó", "'u": "ú", "'c": "ć",
    "'A": "Á", "'E": "É", "'I": "Í", "'O": "Ó", "'U": "Ú",
    "`a": "à", "`e": "è", "`i": "ì", "`o": "ò", "`u": "ù",
    "^a": "â", "^e": "ê", "^i": "î", "^o": "ô", "^u": "û",
    "~n": "ñ", "~a": "ã", "~o": "õ", "cc": "ç", "cC": "Ç",
}


def latex_to_text(s):
    """Convert a BibTeX field body to plain Unicode text."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()

    # Accents: {\"o}, \"{o}, \'e
    def _accent(m):
        return ACCENTS.get(m.group(1) + m.group(2), m.group(2))

    s = re.sub(r"\{\\([\"'`^~c])\{?(\w)\}?\}", _accent, s)
    s = re.sub(r"\\([\"'`^~])\{(\w)\}", _accent, s)
    s = re.sub(r"\\([\"'`^~])(\w)", _accent, s)

    s = s.replace(r"\ss", "ß").replace(r"\aa", "å").replace(r"\o", "ø")
    s = s.replace(r"\textbackslash{}", "\\")
    s = re.sub(r"\\([&%#_$])", r"\1", s)
    s = s.replace(r"\emdash", "—")
    s = re.sub(r"(?<!-)---(?!-)", "—", s)
    s = re.sub(r"(?<!-)--(?!-)", "–", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)      # drop leftover commands
    s = s.replace("{", "").replace("}", "")   # drop capitalisation braces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def esc(s):
    """Plain text -> HTML-safe text."""
    return html.escape(s, quote=True)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def format_authors(raw):
    """'Li, Qiang and Safari, Mojtaba' -> 'Qiang Li, <strong>Mojtaba Safari</strong>'"""
    names = []
    for part in re.split(r"\s+and\s+", raw):
        part = latex_to_text(part).strip()
        if not part:
            continue
        if part.lower() in ("others", "et al.", "et al"):
            names.append("et al.")
            continue
        if "," in part:
            last, first = (x.strip() for x in part.split(",", 1))
            part = f"{first} {last}".strip()
        names.append(part)
    out = []
    for n in names:
        out.append(f"<strong>{esc(n)}</strong>" if n == ME else esc(n))
    return ", ".join(out)


def entry_links(e):
    """[(label, url)] in a stable order: doi, extras, then bib."""
    links = []
    if e.get("doi"):
        links.append(("doi", "https://doi.org/" + e["doi"].strip()))
    for field in LINK_FIELDS:
        if e.get(field):
            links.append((field, e[field].strip()))
    if REPO_BLOB_BASE and e.get("_file"):
        links.append(("bib", f"{REPO_BLOB_BASE}/{e['_file'].replace(os.sep, '/')}"))
    return links


def primary_url(e):
    if e.get("doi"):
        return "https://doi.org/" + e["doi"].strip()
    return e.get("url", "").strip()


def sort_key(e):
    """Newest year first; within a year, HIGHER order first.

    Adding a paper to the top of its year means giving it a number above the
    current top - see `top order` in this script's output. A missing order
    counts as 0, so the entry falls to the bottom of its year.
    """
    year = re.sub(r"[^0-9]", "", e.get("year", "")) or "0"
    try:
        order = int(re.sub(r"[^0-9-]", "", e.get("order", "0")) or 0)
    except ValueError:
        order = 0
    return (-int(year), -order, e["_key"])


def render_entry(e):
    cls = "pub-item is-highlight" if e.get("highlight", "").strip().lower() in (
        "true", "yes", "1"
    ) else "pub-item"

    title = esc(latex_to_text(e.get("title", "")))
    url = primary_url(e)
    if url:
        title_html = (
            f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{title}</a>'
        )
    else:
        title_html = title

    venue = esc(latex_to_text(e.get("journal") or e.get("booktitle") or ""))
    kind = esc(latex_to_text(e.get("kind", "")))
    year = esc(latex_to_text(e.get("year", "")))

    link_html = "".join(
        f'<a class="pub-link" href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(l)}</a>'
        for l, u in entry_links(e)
    )

    lines = [
        f'            <li class="{cls}">',
        "              <div class=\"pub-meta\">",
        f'                <span class="pub-year">{year}</span>',
        f'                <span class="pub-kind">{kind}</span>',
        "              </div>",
        "              <div class=\"pub-info\">",
        f'                <h3 class="pub-title">{title_html}</h3>',
        f'                <p class="pub-authors">{format_authors(e.get("author", ""))}</p>',
        f'                <p class="pub-line"><span class="pub-venue">{venue}</span>{link_html}</p>',
    ]
    if e.get("award"):
        lines.append(
            f'                <p class="pub-award">{esc(latex_to_text(e["award"]))}</p>'
        )
    if e.get("note"):
        lines.append(
            f'                <p class="pub-note">{esc(latex_to_text(e["note"]))}</p>'
        )
    lines += ["              </div>", "            </li>"]
    return "\n".join(lines)


def load_section(slug):
    folder = os.path.join(BIB, slug)
    if not os.path.isdir(folder):
        return []
    entries = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".bib"):
            continue
        path = os.path.join(folder, name)
        with open(path, encoding="utf-8") as fh:
            parsed = parse_bib(fh.read())
        if not parsed:
            print(f"  ! {path}: no entry found", file=sys.stderr)
        for e in parsed:
            missing = [f for f in ("title", "author", "year") if not e.get(f)]
            if missing:
                print(
                    f"  ! {os.path.join(slug, name)}: missing {', '.join(missing)}",
                    file=sys.stderr,
                )
            e["_file"] = os.path.join(slug, name)
            entries.append(e)
    entries.sort(key=sort_key)
    return entries


def build_html(slug):
    entries = load_section(slug)
    body = "\n\n".join(render_entry(e) for e in entries)
    return f"\n{body}\n          ", entries


def splice(doc, heading, slug):
    """Replace the contents of <ul class="pub-list" data-generated="slug">."""
    pattern = re.compile(
        r"(<ul class=\"pub-list\" data-generated=\"" + re.escape(slug) + r"\">)"
        r"(.*?)(</ul>)",
        re.S,
    )
    m = pattern.search(doc)
    if not m:
        sys.exit(
            f'could not find <ul class="pub-list" data-generated="{slug}"> '
            "in index.html"
        )
    new_body, entries = build_html(slug)
    return doc[: m.start(2)] + new_body + doc[m.end(2):], entries


def top_hint(entries):
    """'top: order 100 (2026) - use 110 to go above it'"""
    if not entries:
        return "empty"
    top = entries[0]
    year = re.sub(r"[^0-9]", "", top.get("year", "")) or "?"
    try:
        order = int(re.sub(r"[^0-9-]", "", top.get("order", "0")) or 0)
    except ValueError:
        order = 0
    return f"top of {year} is order {order} - use {order + 10} to go above it"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if index.html is out of date")
    args = ap.parse_args()

    with open(INDEX, encoding="utf-8") as fh:
        original = fh.read()

    doc = original
    total = 0
    for heading, slug in SECTIONS:
        doc, entries = splice(doc, heading, slug)
        print(f"{slug:12s} {len(entries):3d} entries   {top_hint(entries)}")
        total += len(entries)

    if args.check:
        if doc != original:
            print("\nindex.html is OUT OF DATE - run: python3 build.py", file=sys.stderr)
            return 1
        print(f"\nindex.html is up to date ({total} entries)")
        return 0

    if doc == original:
        print(f"\nno changes ({total} entries)")
        return 0

    with open(INDEX, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"\nwrote index.html ({total} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
