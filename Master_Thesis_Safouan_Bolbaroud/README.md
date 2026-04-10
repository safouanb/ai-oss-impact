# Thesis Manuscript Source

This folder contains the LaTeX source for the final manuscript of this thesis.

## What belongs here

- `main.tex`: thesis entrypoint
- `setup.tex`: document formatting and package setup
- `title.tex`: title page layout
- `sections/`: manuscript chapters
- `appendix/`: appendix chapters
- `images/`: static assets used by the manuscript
- `figures/`: exported figures included in the manuscript
- `tables/`: exported tables included in the manuscript
- `references.bib`: BibTeX database for the manuscript

## What does not belong here

- Raw research data
- Processed pipeline outputs that already live under `data/` or `results/`
- Build artifacts such as `main.pdf`, `.aux`, `.log`, `.toc`, and similar files
- Legacy appendix datasets from unrelated projects

## Editing flow

1. Draft and validate research content in the root-level research workspace.
2. Move polished chapter text into `sections/`.
3. Export final thesis figures and tables into `figures/` and `tables/`.
4. Keep citations in `references.bib`.

## Build

```bash
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
