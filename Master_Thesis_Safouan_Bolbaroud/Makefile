PDF=main.pdf

.PHONY: all pdf clean

all: pdf

pdf:
	pdflatex -interaction=nonstopmode main.tex
	bibtex main || true
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

clean:
	rm -f *.aux *.bbl *.bcf *.blg *.fdb_latexmk *.fls *.lof *.log *.lot *.nav *.out *.pdf *.run.xml *.snm *.synctex.gz *.toc
