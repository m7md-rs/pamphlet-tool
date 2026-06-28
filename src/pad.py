from pypdf import PdfReader, PdfWriter
from pathlib import Path


def pad(input_path: Path, count: int):
    reader = PdfReader(input_path)
    writer = PdfWriter(reader)

    dimensions = reader.pages[-1].cropbox
    for _ in range(count):
        writer.add_blank_page(width=dimensions.width, height=dimensions.height)

    writer.write(input_path)
    print(f"[*] Padded file with {count} blank pages: {input_path}")
