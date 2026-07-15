from pathlib import Path

from edgar import Company, set_identity

set_identity("Navin kumar slayergod1729@gmail.com")


def download_10k(ticker: str, year: int):
    company = Company(ticker)
    filings = company.get_filings(form="10-K")

    filing = next(
        f for f in filings
        if f.filing_date.year == year
    )

    folder = Path(__file__).parent / "Knowledge-base" / "finance_reports"
    folder.mkdir(parents=True, exist_ok=True)


    markdown = filing.markdown()
    md_path = folder / f"{ticker}_{year}_10K.md"
    md_path.write_text(markdown, encoding="utf-8")


    html = filing.html()
    html_path = folder / f"{ticker}_{year}_10K.html"
    html_path.write_text(html, encoding="utf-8")

    print(f"Saved Markdown: {md_path}")
    print(f"Saved HTML: {html_path}")


download_10k("GS", 2023)