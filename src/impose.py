import sys

from pypdf import PdfReader, PdfWriter
from pathlib import Path


PAGES_PER_SHEET = 4 # Two leaves (front and back) per sheet; and two pages per leaf (left and right)


def impose(input_path: Path, output_path: Path):
    input_file = PdfReader(input_path)
    output_file = PdfWriter(output_path)

    num_pages = len(input_file.pages)
    if num_pages % PAGES_PER_SHEET != 0:
        needed_padding = PAGES_PER_SHEET - (num_pages % PAGES_PER_SHEET)
        print(f"[!] Error: The PDF must be a multiple of {PAGES_PER_SHEET}. An extra {needed_padding} pages of padding are needed.", file=sys.stderr)
        print(f"           Use: pamphlet-tool pad {input_path} {needed_padding}")

