from pypdf import PdfReader, PdfWriter
from pathlib import Path


def pad(input_path: Path, count: int):
    input_file = PdfWriter(input_path)
