# Publications

Every publication on the site comes from a `.bib` file in this folder. The contents
of each `<ul class="pub-list" data-generated="...">` in `index.html` are produced by
`build.py` and **should not be edited by hand** — the next build overwrites them.

## Adding a paper

1. Download the `.bib` from the publisher (Wiley, IOP, Springer, Nature all offer
   "Export citation → BibTeX"). Google Scholar also works: the quote icon → BibTeX.
2. Drop it in the right folder:

   | Folder | Section on the site |
   |---|---|
   | `bib/journal/` | Selected Journal Articles |
   | `bib/conference/` | Selected Conference Papers & Abstracts |
   | `bib/workshop/` | Workshop Papers |

3. Add the fields the publisher doesn't provide (see below).
4. Regenerate and publish:

   ```bash
   python3 build.py
   git diff                        # check it looks right
   git add -A
   git commit -m "Add <paper>"
   git push                        # deploys automatically
   ```

## Fields

Standard BibTeX fields used: `title`, `author`, `journal` (or `booktitle`), `year`,
`doi`, `url`.

These are extra — publishers never include them, so add them yourself:

| Field | Effect | Required |
|---|---|---|
| `kind` | The grey label: `Journal`, `Paper`, `Poster`, `E-poster`, `Oral`, `Workshop` | yes |
| `note` | One-line plain-English summary under the entry | recommended |
| `highlight` | `{true}` gives the entry the featured styling | no |
| `award` | Award text shown above the note | no |
| `code` | URL for a `code` link | no |
| `abstract` | URL for an `abstract` link | no |
| `order` | Position within its year, **higher first**. See below. | recommended |

`pdf`, `slides`, `video`, and `data` also render as links if present.

## Example

```bibtex
@article{li2026lowdose,
  title   = {Low-dose {CT} imaging using a regularization-enhanced efficient diffusion probabilistic model},
  author  = {Li, Qiang and Safari, Mojtaba and Wang, Shansong and Xie, Huiqiao and Ding, Jie and Wang, Tonghe and Yang, Xiaofeng},
  journal = {Medical Physics},
  year    = {2026},
  doi     = {10.1002/mp.70626},
  kind    = {Journal},
  note    = {A regularization-enhanced diffusion probabilistic model for low-dose {CT} reconstruction.}
}
```

Notes on formatting:

- Authors work in either `Last, First and Last, First` or `First Last and First Last`
  form. `Mojtaba Safari` is bolded automatically.
- Wrap acronyms in braces — `{CT}`, `{MRI}` — so other BibTeX tools don't lowercase
  them. `build.py` strips the braces when rendering.
- LaTeX escapes (`\&`, `\%`, `{\"o}`) are converted for you.
- Entries sort by year descending, then by `order` descending, then by citation key.

## Ordering

Newest year always comes first. Within a year, **higher `order` wins**.

Existing entries are numbered in steps of 10 (`100, 90, 80, …`) so there is always
room between any two neighbours — you never have to renumber.

`build.py` prints the number to beat every time it runs:

```
journal       20 entries   top of 2026 is order 100 - use 110 to go above it
```

So to put a new paper at the very top, give it `order = {110}`.

| You want | You write |
|---|---|
| Top of its year | the number `build.py` tells you |
| Between 80 and 90 | `order = {85}` |
| Bottom of its year | omit `order`, or `order = {0}` |

A missing `order` counts as 0, so it sinks to the bottom of its year. Two entries
with the same `order` fall back to alphabetical citation key — which is arbitrary,
so give each paper its own number if you care where it sits.

## The `bib` link

Every entry automatically gets a `bib` link next to `doi`. It points at this file on
GitHub, which renders the BibTeX with syntax highlighting and a copy button, and opens
in a new tab. You don't add anything — `build.py` derives the URL from the file's
location.

One consequence: the link targets the `main` branch on github.com, so a brand-new
paper's `bib` link 404s until you `git push`. Build and push in the same session and
you'll never notice.

To change the target or turn the links off, edit `REPO_BLOB_BASE` near the top of
`build.py` (set it to `None` to disable).

## Checking without writing

```bash
python3 build.py --check
```

Exits 1 if `index.html` doesn't match the `.bib` files — useful before committing.
