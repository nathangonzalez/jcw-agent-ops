#!/usr/bin/env python3
"""
OCR weekly photo timesheets into text + CSV for review.
"""

import argparse
import csv
import os
from pathlib import Path

from PIL import Image, ImageOps
import pytesseract


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, help="Folder with photos")
    parser.add_argument("--out-dir", required=True, help="Output folder for OCR files")
    parser.add_argument("--tesseract-cmd", default="", help="Optional tesseract.exe path")
    return parser.parse_args()


def resolve_tesseract(cmd: str) -> str:
    if cmd:
        return cmd
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return ""


def preprocess(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    return gray


def ocr_image(path: Path) -> str:
    img = Image.open(path)
    img = preprocess(img)
    return pytesseract.image_to_string(img)


def avg_confidence(img: Image.Image) -> float:
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    confs = []
    for conf in data.get("conf", []):
        try:
            val = float(conf)
            if val >= 0:
                confs.append(val)
        except Exception:
            continue
    if not confs:
        return 0.0
    return round(sum(confs) / len(confs), 2)


def best_ocr_variant(path: Path):
    img = Image.open(path)
    img = preprocess(img)
    variants = []
    for angle in (0, 90, 180, 270):
        rotated = img.rotate(angle, expand=True)
        conf = avg_confidence(rotated)
        text = pytesseract.image_to_string(rotated)
        variants.append((conf, angle, text))
    variants.sort(key=lambda x: x[0], reverse=True)
    return variants[0]


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tess_cmd = resolve_tesseract(args.tesseract_cmd)
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd

    images = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}])
    if not images:
        raise SystemExit(f"No images found in {input_dir}")

    combined_rows = [["image", "avg_confidence", "text"]]
    line_rows = [["image", "line_no", "line"]]

    for path in images:
        conf, angle, text = best_ocr_variant(path)
        text_path = out_dir / f"{path.stem}.txt"
        text_path.write_text(text, encoding="utf-8")
        combined_rows.append([path.name, conf, text.strip()])
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                line_rows.append([path.name, i, line.strip()])

    with (out_dir / "ocr_combined.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(combined_rows)

    with (out_dir / "ocr_lines.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(line_rows)

    print(f"OCR complete: {len(images)} images")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
