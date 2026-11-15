# Report build

The current report is LaTeX, compiled with LuaLaTeX (TeX Live 2025).

```sh
latexmk -lualatex -interaction=nonstopmode -halt-on-error writeup.tex
```

Only writeup.tex and the built writeup.pdf are distributed; compilation auxiliaries are not. The AI-use disclosure is in the AI-assistance section of the PDF. Building the report does not execute Agda.
