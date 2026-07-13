from edgar import Company, set_identity
from pathlib import Path
set_identity("Navin kumar slayergod1729@gmail.com")

def download_10k(ticker: str, year: int, output_dir="filings"):
    company = Company(ticker)
    filings = company.get_filings(form="10-K")


    filing = next(
        f for f in filings
        if f.filing_date.year == year
    )



    folder = Path(output_dir) / ticker / str(year)
    folder.mkdir(parents=True, exist_ok=True)

    html = filing.html()
    md = filing.markdown()
    txt = filing.text()


    (folder / "10k.html").write_text(html, encoding="utf-8")
    (folder / "10k.md").write_text(md, encoding="utf-8")
    (folder / "10k.txt").write_text(txt, encoding="utf-8")


    print(f"Saved {ticker} {year} 10-K")


download_10k("AAPL", 2025)