import sys

from pypdf import PageObject, PdfReader, PdfWriter
from pathlib import Path


PAGES_PER_SHEET = 4 # Folio
A4 = {                  # in points, where 72 points = 1 inch
    "width":  595.276,  # 210 mm
    "height": 841.890,  # 297 mm
}


def impose(input_path: Path, output_path: Path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    num_pages = len(reader.pages)
    if num_pages % PAGES_PER_SHEET != 0:
        needed_padding = PAGES_PER_SHEET - (num_pages % PAGES_PER_SHEET)
        print(f"[!] Error: The PDF must be a multiple of {PAGES_PER_SHEET}. An extra {needed_padding} pages of padding are needed.", file=sys.stderr)
        print(f"           Use: pamphlet-tool pad {input_path} {needed_padding}", file=sys.stderr)
        sys.exit(1)

    # Guranteed to be a multiple by validate_number_of_pages
    num_leaves = num_pages // PAGES_PER_SHEET * 2
    for leaf_index in range(1, num_leaves + 1):
        leaf = impose_leaf(reader, leaf_index)
        writer.add_page(leaf)
        print(f"[+] Imposed leaf {leaf_index}")

    writer.write(output_path)
    print(f"[*] Finished imposing PDF: {output_path}")


def impose_leaf(reader: PdfReader, leaf_index: int) -> PageObject:
    num_pages = len(reader.pages)

    if leaf_index % 2 != 0:
        # back side
        leaf_page_indices = (num_pages-leaf_index+1, leaf_index)
    else:
        # front side
        leaf_page_indices = (leaf_index, num_pages-leaf_index+1)

    leaf_left = reader.pages[leaf_page_indices[0]-1]
    leaf_right = reader.pages[leaf_page_indices[1]-1]

    leaf = PageObject.create_blank_page(width=A4["width"], height=A4["height"])

    leaf_left.rotate(90)
    leaf_left.scale_to(A4["height"]/2, A4["width"])
    leaf_left.transfer_rotation_to_content()
    leaf.merge_translated_page(leaf_left, ty=A4["height"]/2, tx=0)

    leaf_right.rotate(90)
    leaf_right.scale_to(A4["height"]/2, A4["width"])
    leaf_right.transfer_rotation_to_content()
    leaf.merge_page(leaf_right)

    return leaf
