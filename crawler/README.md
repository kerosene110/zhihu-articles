# Zhihu Crawler

Download all articles from `https://www.zhihu.com/column/wontfallinyourlap` and
export each article to its own PDF.

Working as a module to the RAG application and also a stand-alone command-line tool.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd crawler
python zhihu_column_to_pdf.py --out ../output
```

PDFs will be written to `output/wontfallinyourlap/`.

## Metadata-only mode

If you already have metadata and only want to generate PDFs:

```bash
cd crawler
python zhihu_column_to_pdf.py --out ../output --from-metadata
```

If you want to provide a specific metadata file:

```bash
cd crawler
python zhihu_column_to_pdf.py --out ../output --metadata-path /path/to/articles.json
```

If your metadata path is a directory containing multiple page JSON files, pass the directory path:

```bash
cd crawler
python zhihu_column_to_pdf.py --out ../output --metadata-path /path/to/metadata-pages/
```

The script loads all `*.json` files in that directory in sorted order and merges them.

## Notes

- This script is hard-coded to `https://www.zhihu.com/column/wontfallinyourlap`.
- This script uses the public column API and does **not** log in.
- Be polite: use `--sleep` to reduce request rate.
- The script prints progress while paging and converting articles so stalled requests are visible.
- Existing PDFs and HTML fallbacks in `output/wontfallinyourlap/` are detected and skipped on reruns.
- If PDF creation fails, the script saves a `.html` file instead and prints a warning.

## Troubleshooting PDF

`weasyprint` is the default backend. If it fails on your system:

1. Try installing system dependencies for WeasyPrint (Pango/Cairo).
2. Or install `wkhtmltopdf` and add `pdfkit`:

```bash
pip install pdfkit
```

Then rerun the script.

## Other crawler utilities

Run the MHTML converter and PDF renamer from the crawler directory as well.

```bash
cd crawler
python zhihu_answers_mhtml_to_pdf.py --help
python rename_pdfs_by_created.py --help
```
