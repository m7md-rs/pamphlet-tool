import sys
import argparse

from pypdf import PdfReader, PdfWriter
from pathlib import Path

from impose import impose
from pad import pad


def main():
    parser = argparse.ArgumentParser(
        prog="pamphlet-tool",
        description="Prepare PDF for printing"
    )

    subparsers = parser.add_subparsers(required=True, help="subcommands")

    impose = subparsers.add_parser("impose", help="Impose a PDF before printing")
    impose.set_defaults(func=handle_impose)

    impose.add_argument(
        "input_path",
        metavar="input",
        type=Path,
        help="Path for the input PDF that will be imposed"
    )

    impose.add_argument(
        "-s", "--signature-size",
        dest="signature_size",
        type=int,
        default=None,
        help="The number of sheets/booklets per signature (default: no signatures)"
    )

    impose.add_argument(
        "-a", "--aggregate",
        dest="aggregate_signatures",
        action="store_true",
        help="If signatures are enabled (see -s), then aggregate all signatures into a single PDF"
    )

    impose.add_argument(
        "-k", "--split-sides",
        dest="split_sides",
        action="store_true",
        help="Create a seperate PDF for the front & back side"
    )

    impose.add_argument(
        "-m", "--fold-mark",
        dest="fold_mark",
        action="store_true",
        help="Add a fold mark to each leaf"
    )

    impose.add_argument(
        "-o", "--output",
        dest="output_dir",
        type=Path,
        default="output",
        help="Output directory for the new imposed PDFs. (Default: output)"
    )

    pad = subparsers.add_parser("pad", help="Insert blank padding pages to the end of a PDF") 
    pad.set_defaults(func=handle_pad)

    pad.add_argument(
        "input_path",
        metavar="input",
        type=Path,
        help="Path for the input PDF that will be padded"
    )

    pad.add_argument(
        "needed_padding",
        metavar="count",
        type=int,
        help="The number of padding pages to be inserted",
    )

    pad.add_argument(
        "-y", "--yes",
        dest="skip_confirmation",
        action="store_true",
        help="Skip the confirmation for overwriting the file"
    )

    pad.add_argument(
        "-o", "--output",
        dest="output_path",
        type=Path,
        default=None,
        help="Output padded PDF to this path instead of overwriting"
    )

    args = parser.parse_args()
    args.func(args)


def handle_impose(args: argparse.Namespace):
    validate_input_file(args.input_path)
    args.output_dir.mkdir(exist_ok=True)
    impose(
        args.input_path, args.output_dir, 
        args.split_sides, args.fold_mark, 
        args.signature_size, args.aggregate_signatures
    )


def handle_pad(args: argparse.Namespace):
    validate_input_file(args.input_path)

    if args.output_path is None and not args.skip_confirmation:
        print(f"This will overwrite the input file: {args.input_path}")
        answer = input("Do you want to continue? [y/N] ")
        if answer.lower() not in ["y", "yes"]:
            return

    if args.output_path is None:
        pad(args.input_path, args.needed_padding, args.input_path)
    else:
        pad(args.input_path, args.needed_padding, args.output_path)


def validate_input_file(input_path: Path):
    if not input_path.exists():
        print(f"[!] Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        PdfReader(input_path)
        PdfWriter(input_path)
    except Exception:
        print(f"[!] Error: Input file must be a valid PDF: {input_path}", file=sys.stderr) 
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
