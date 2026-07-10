from dataclasses import dataclass

from pathlib import Path
from pypdf import PdfReader


@dataclass
class Area:
    width: float
    height: float
    unit: str = "mm"

    def __repr__(self) -> str:
        r = lambda val : round(val, 1)
        return f"{r(self.width)}{self.unit} x {r(self.height)}{self.unit}"


A4 = { # in mm
    "width": 210,
    "height": 297,
    "thickness": 0.1, # Standard 80 gsm A4 paper
}

def calculate_cover_size(input_path: Path):
    reader = PdfReader(input_path)
    num_pages = len(reader.pages)
    num_sheets = num_pages // 2

    side = Area(width=A4["height"] / 2, height=A4["width"])

    spine_thickness = num_sheets * A4["thickness"]
    spine = Area(spine_thickness, side.height)
    
    assert side.height == spine.height
    total = Area(2*side.width + spine.width, side.height)

    print(f"[+] Side area: {side}")
    print(f"[+] Spine area: {spine}")
    print(f"[*] Total area: {total}")


