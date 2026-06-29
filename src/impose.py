import sys

from pypdf import PageObject, PdfReader, PdfWriter
from pathlib import Path


PAGES_PER_SHEET = 4 # Folio
A4 = {                  # in points, where 72 points = 1 inch
    "width":  595.276,  # 210 mm
    "height": 841.890,  # 297 mm
}


def impose(input_path: Path, output_dir: Path, split_sides: bool, signature_size: int | None, aggregate_signatures: bool):
    reader = PdfReader(input_path)
    num_pages = len(reader.pages)
    validate_number_of_pages(num_pages, input_path, signature_size=signature_size)

    if signature_size is None:
        impose_nosignatures(reader, output_dir, split_sides)
    else:
        impose_signatures(reader, output_dir, split_sides, signature_size, aggregate_signatures)


def impose_nosignatures(reader: PdfReader, output_dir: Path, split_sides: bool):
    num_pages = len(reader.pages)
    if not split_sides:
        output_path = output_dir / "aggregate.pdf"
        impose_aggregate(reader, output_path, 1, num_pages)
        print(f"[*] Finished imposing PDF: {output_path}")
    else:
        output_path_back = output_dir / "aggregate_back.pdf"
        output_path_front = output_dir / "aggregate_front.pdf"
        impose_split(reader, output_path_back, output_path_front, 1, num_pages)
        print(f"[*] Finished imposing PDF (back): {output_path_back}")
        print(f"[*] Finished imposing PDF (front): {output_path_front}")


def impose_signatures(reader: PdfReader, output_dir: Path, split_sides: bool, signature_size: int, aggregate_signatures: bool):
    num_pages = len(reader.pages)
    pages_per_signature = PAGES_PER_SHEET * signature_size
    num_signatures = num_pages // pages_per_signature

    for signature_index in range(num_signatures):
        signature_number = signature_index + 1
        first_page = signature_index*pages_per_signature + 1
        last_page = (signature_index+1)*pages_per_signature

        if not split_sides:
            output_path = output_dir / f"signature_{signature_number}.pdf"
            impose_aggregate(reader, output_path, first_page, last_page)
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures}: {output_path}")
        else:
            output_path_back = output_dir / f"signature_{signature_number}_back.pdf"
            output_path_front = output_dir / f"signature_{signature_number}_front.pdf"
            impose_split(reader, output_path_back, output_path_front, first_page, last_page)
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures} (back): {output_path_back}")
            print(f"[+] Finished imposing signature {signature_number}/{num_signatures} (front): {output_path_front}")
    
    print("[*] Finished imposing PDF")
    if not aggregate_signatures:
        return
    
    if not split_sides:
        writer = PdfWriter()
        for signature_index in range(num_signatures):
            signature_number = signature_index + 1
            writer.append(output_dir / f"signature_{signature_number}.pdf")

        output_path = output_dir / "aggregate.pdf"
        writer.write(output_path)
        print(f"[*] Aggregated signatures into PDF: {output_path}")

    else:
        writer_back = PdfWriter()
        writer_front = PdfWriter()
        for signature_index in range(num_signatures):
            signature_number = signature_index + 1
            writer_back.append(output_dir / f"signature_{signature_number}_back.pdf")
            writer_front.append(output_dir / f"signature_{signature_number}_front.pdf")

        output_path_back = output_dir / "aggregate_back.pdf"
        output_path_front = output_dir / "aggregate_front.pdf"
        writer_back.write(output_path_back)
        writer_back.write(output_path_front)
        print(f"[*] Aggregated signatures into PDF (back): {output_path_back}")
        print(f"[*] Aggregated signatures into PDF (front): {output_path_front}")
        

def impose_aggregate(reader: PdfReader, output_path: Path, first_page: int, last_page: int):
    writer = PdfWriter()
    total_num_leaves = len(reader.pages) // 2
    
    num_leaves_per_signature = (last_page - first_page) // 2
    for leaf_index in range(num_leaves_per_signature+1):
        leaf_number = (first_page // 2) + leaf_index + 1
        leaf = impose_leaf(reader, leaf_index, first_page, last_page)
        writer.add_page(leaf)
        print(f"[-] Imposed leaf {leaf_number}/{total_num_leaves}")

    writer.write(output_path)


def impose_split(reader: PdfReader, output_path_back: Path, output_path_front: Path, first_page: int, last_page: int):
    writer_back = PdfWriter()
    writer_front = PdfWriter()
    total_num_leaves = len(reader.pages) // 2

    num_leaves_per_signature = (last_page - first_page) // 2
    for leaf_index in range(num_leaves_per_signature+1):
        leaf_number = (first_page // 2) + leaf_index + 1
        leaf = impose_leaf(reader, leaf_index, first_page, last_page)
        if leaf_index % 2 == 0:
            writer_back.add_page(leaf)
        else:
            writer_front.add_page(leaf)
        print(f"[-] Imposed leaf {leaf_number}/{total_num_leaves}")

    writer_back.write(output_path_back)
    writer_front.write(output_path_front)


def impose_leaf(reader: PdfReader, leaf_index: int, first_page, last_page) -> PageObject:
    if leaf_index % 2 == 0:
        # back side
        leaf_page_indices = (last_page - leaf_index, first_page + leaf_index)
    else:
        # front side
        leaf_page_indices = (first_page + leaf_index, last_page - leaf_index)

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


def validate_number_of_pages(num_pages: int, input_path: Path, signature_size: int | None = None):
    if signature_size is None:
        pages_per_signature = PAGES_PER_SHEET
    else:
        pages_per_signature = PAGES_PER_SHEET * signature_size

    if num_pages % pages_per_signature != 0:
        needed_padding = pages_per_signature - (num_pages % pages_per_signature)
        print(f"[!] Error: The PDF must be a multiple of {pages_per_signature}. An extra {needed_padding} pages of padding are needed.", file=sys.stderr)
        print(f"           Use: pamphlet-tool pad {input_path} {needed_padding}", file=sys.stderr)
        sys.exit(1)
