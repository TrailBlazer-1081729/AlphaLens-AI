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


    folder = Path(__file__).parent / "Knowledge-base" / "finance_reports"
    folder.mkdir(parents=True, exist_ok=True)


    md = filing.markdown()

    filename = f"{ticker}_{year}_10K.md"
    output_file = folder / filename
    output_file.write_text(md, encoding="utf-8")


    print(f"Saved {ticker} {year} 10-K")


download_10k("MSFT", 2025)