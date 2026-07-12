from docling.document_converter import DocumentConverter
from pathlib import Path


def convert_pdf_to_markdown(pdf_path: str, output_md_path: str):
    print(f"📄 Reading PDF: {pdf_path}")
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    markdown_content = result.document.export_to_markdown()
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"✅ Success! Markdown saved to: {output_md_path}")

if __name__ == "__main__":
    input_pdf = "f25_AAPL_copy.pdf"
    output_markdown = "apple_finance_2025_clean.md"
    if Path(input_pdf).exists():
        convert_pdf_to_markdown(input_pdf, output_markdown)
    else:
        print(f"❌ Error: Could not find {input_pdf}. Make sure the PDF is in the same folder.")