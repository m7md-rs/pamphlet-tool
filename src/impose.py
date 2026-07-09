import sys
from dataclasses import dataclass
from typing import Optional
from io import BytesIO

import pdf2image
from PIL import ImageDraw
from pypdf import PageObject, PdfReader, PdfWriter
from pathlib import Path


STANDARD_PDF_DPI = 72
PAGES_PER_SHEET = 4 # Folio
A4 = {                  # in points, where 72 points = 1 inch
    "width":  595.276,  # 210 mm
    "height": 841.890,  # 297 mm
}
GUTTER_MARGIN = 28.35 # 10 mm on each side


@dataclass
class OutputOptions:
    output_dir: Path
    split_sides: bool


@dataclass
class DrawOptions:
    fold_marks: bool
    hole_count: Optional[int]

    def any(self):
        return self.fold_marks or self.use_hole_marks()

    def use_hole_marks(self) -> bool:
        return self.hole_count is not None


@dataclass
class SignatureOptions:
    signature_size: Optional[int]
    aggregate_signatures: bool

    def use_signatures(self) -> bool:
        return self.signature_size is not None

    def get_pages_per_signature(self) -> int:
        size = self.signature_size if self.signature_size is not None else 1
        return size * PAGES_PER_SHEET


class PageImage:
    def __init__(self, page: PageObject, dpi=STANDARD_PDF_DPI):
        writer = PdfWriter()
        output = BytesIO()

        writer.add_page(page)
        writer.write(output)
        output.seek(0)

        page_bytes = output.getvalue()

        self.image = pdf2image.convert_from_bytes(page_bytes, dpi=dpi)[0]
        self.draw = ImageDraw.Draw(self.image)

    # SAFETY: Object is invalid after this call
    def to_page(self) -> PageObject:
        output = BytesIO()
        self.image.convert("RGB").save(output, format="PDF")
        output.seek(0)
        page_bytes = output.getvalue()

        reader = PdfReader(BytesIO(page_bytes))
        return reader.pages[0]

    def add_fold_mark(self):
        center_y_px = self.image.height // 2
        self.draw.line([(0, center_y_px), (self.image.width, center_y_px)], fill="black", width=1)

    def add_hole_marks(self, hole_count: int):
        center_y_px = self.image.height // 2
        hole_spacing_px = self.image.width // (hole_count + 1)
        for hole_number in range(1, hole_count+1):
            center = (hole_number * hole_spacing_px, center_y_px)
            self.draw.circle(center, radius=4, fill="black", width=1)


def impose(input_path: Path, output_options: OutputOptions, 
           draw_options: DrawOptions, signature_options: SignatureOptions):
    reader = PdfReader(input_path)
    num_pages = len(reader.pages)
    validate_number_of_pages(num_pages, input_path, pages_per_signature=signature_options.get_pages_per_signature())

    if not signature_options.use_signatures():
        impose_nosignatures(reader, output_options, draw_options)
    else:
        impose_signatures(reader, output_options, draw_options, signature_options)


def impose_nosignatures(reader: PdfReader, output_options: OutputOptions, draw_options: DrawOptions):
    num_pages = len(reader.pages)
    if not output_options.split_sides:
        output_path = output_options.output_dir / "aggregate.pdf"
        impose_aggregate(reader, output_path, 1, num_pages, draw_options)
        print(f"[*] Finished imposing PDF: {output_path}")
    else:
        output_path_back = output_options.output_dir / "aggregate_back.pdf"
        output_path_front = output_options.output_dir / "aggregate_front.pdf"
        impose_split(reader, output_path_back, output_path_front, 1, num_pages, draw_options)
        print(f"[*] Finished imposing PDF (back): {output_path_back}")
        print(f"[*] Finished imposing PDF (front): {output_path_front}")


def impose_signatures(reader: PdfReader, output_options: OutputOptions, 
                      draw_options: DrawOptions, signature_options: SignatureOptions):
    num_pages = len(reader.pages)
    pages_per_signature = signature_options.get_pages_per_signature()
    num_signatures = num_pages // pages_per_signature

    for signature_index in range(num_signatures):
        signature_number = signature_index + 1
        first_page = signature_index*pages_per_signature + 1
        last_page = (signature_index+1)*pages_per_signature

        if not output_options.split_sides:
            output_path = output_options.output_dir / f"signature_{signature_number}.pdf"
            impose_aggregate(reader, output_path, first_page, last_page, draw_options)
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures}: {output_path}")
        else:
            output_path_back = output_options.output_dir / f"signature_{signature_number}_back.pdf"
            output_path_front = output_options.output_dir / f"signature_{signature_number}_front.pdf"
            impose_split(reader, output_path_back, output_path_front, first_page, last_page, draw_options)
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures} (back): {output_path_back}")
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures} (front): {output_path_front}")
    
    print("[*] Finished imposing PDF")
    if not signature_options.aggregate_signatures:
        return
    
    if not output_options.split_sides:
        writer = PdfWriter()
        for signature_index in range(num_signatures):
            signature_number = signature_index + 1
            writer.append(output_options.output_dir / f"signature_{signature_number}.pdf")

        output_path = output_options.output_dir / "aggregate.pdf"
        writer.write(output_path)
        print(f"[*] Aggregated signatures into PDF: {output_path}")

    else:
        writer_back = PdfWriter()
        writer_front = PdfWriter()
        for signature_index in range(num_signatures):
            signature_number = signature_index + 1
            writer_back.append(output_options.output_dir / f"signature_{signature_number}_back.pdf")
            writer_front.append(output_options.output_dir / f"signature_{signature_number}_front.pdf")

        output_path_back = output_options.output_dir / "aggregate_back.pdf"
        output_path_front = output_options.output_dir / "aggregate_front.pdf"
        writer_back.write(output_path_back)
        writer_front.write(output_path_front)
        print(f"[*] Aggregated signatures into PDF (back): {output_path_back}")
        print(f"[*] Aggregated signatures into PDF (front): {output_path_front}")
        

def impose_aggregate(reader: PdfReader, output_path: Path, first_page: int, last_page: int, draw_options: DrawOptions):
    writer = PdfWriter()
    total_num_leaves = len(reader.pages) // 2
    
    num_leaves_per_signature = (last_page - first_page) // 2
    for leaf_index in range(num_leaves_per_signature+1):
        leaf_number = (first_page // 2) + leaf_index + 1
        leaf = impose_leaf(reader, leaf_index, first_page, last_page, draw_options)
        writer.add_page(leaf)
        print(f"[-] Imposed leaf {leaf_number}/{total_num_leaves}")

    writer.write(output_path)


def impose_split(reader: PdfReader, output_path_back: Path, output_path_front: Path, 
                 first_page: int, last_page: int, draw_options: DrawOptions):
    writer_back = PdfWriter()
    writer_front = PdfWriter()
    total_num_leaves = len(reader.pages) // 2

    num_leaves_per_signature = (last_page - first_page) // 2
    for leaf_index in range(num_leaves_per_signature+1):
        leaf_number = (first_page // 2) + leaf_index + 1
        leaf = impose_leaf(reader, leaf_index, first_page, last_page, draw_options)
        if leaf_index % 2 == 0:
            writer_back.add_page(leaf)
        else:
            writer_front.add_page(leaf)
        print(f"[-] Imposed leaf {leaf_number}/{total_num_leaves}")

    writer_back.write(output_path_back)
    writer_front.write(output_path_front)


def impose_leaf(reader: PdfReader, leaf_index: int, first_page: int, last_page: int, draw_options: DrawOptions) -> PageObject:
    is_back_leaf  = lambda leaf_index : leaf_index % 2 == 0
    is_front_leaf = lambda leaf_index : leaf_index % 2 != 0

    if is_back_leaf(leaf_index):
        leaf_page_indices = (last_page - leaf_index, first_page + leaf_index)
    else:
        leaf_page_indices = (first_page + leaf_index, last_page - leaf_index)

    leaf_left = reader.pages[leaf_page_indices[0]-1]
    leaf_right = reader.pages[leaf_page_indices[1]-1]

    leaf = PageObject.create_blank_page(width=A4["width"], height=A4["height"])

    if draw_options.any():
        page_image = PageImage(leaf)
        if draw_options.fold_marks and is_front_leaf(leaf_index):
            page_image.add_fold_mark()
        if draw_options.use_hole_marks() and is_front_leaf(leaf_index):
            assert draw_options.hole_count is not None
            page_image.add_hole_marks(draw_options.hole_count)
        leaf = page_image.to_page()

    leaf_left.rotate(90)
    leaf_left.scale_to(A4["height"]/2 - GUTTER_MARGIN, A4["width"])
    leaf_left.transfer_rotation_to_content()
    leaf.merge_translated_page(leaf_left, ty=A4["height"]/2 + GUTTER_MARGIN, tx=0)

    leaf_right.rotate(90)
    leaf_right.scale_to(A4["height"]/2 - GUTTER_MARGIN, A4["width"])
    leaf_right.transfer_rotation_to_content()
    leaf.merge_page(leaf_right)

    return leaf


def validate_number_of_pages(num_pages: int, input_path: Path, pages_per_signature: int = PAGES_PER_SHEET):
    if num_pages % pages_per_signature != 0:
        needed_padding = pages_per_signature - (num_pages % pages_per_signature)
        print(f"[!] Error: The PDF must be a multiple of {pages_per_signature}. An extra {needed_padding} pages of padding are needed.", file=sys.stderr)
        print(f"           Use: pamphlet-tool pad {input_path} {needed_padding}", file=sys.stderr)
        sys.exit(1)
