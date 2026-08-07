# Publications

Every publication on the site comes from a `.bib` file in this folder. The HTML in
`index.html` between the `<!-- generated ... -->` markers is produced by `build.py`
and **should not be edited by hand** — the next build overwrites it.

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
| `order` | Position within its year, lower first. Omit for new papers and they sort to the top of their year. | no |

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
- Entries sort by year descending, then by `order`, then by citation key.

## Checking without writing

```bash
python3 build.py --check
```

Exits 1 if `index.html` doesn't match the `.bib` files — useful before committing.
