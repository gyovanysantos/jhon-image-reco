"""
Phase 1: Extract part numbers from the Johnstone Supply PDF catalog.

Parses Cat_220_linked_p1.pdf using pdfplumber, extracts part numbers,
descriptions, catalog page numbers, and builds product URLs.
Outputs a CSV with 100 parts.
"""

import csv
import os
import re
from pathlib import Path

import pdfplumber

PDF_PATH = Path(__file__).resolve().parent.parent / "Cat_220_linked_p1.pdf"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_CSV = OUTPUT_DIR / "parts_catalog.csv"
BASE_URL = "https://www.johnstonesupply.com/product-view?pID="
TARGET_PARTS = 100


def extract_parts_from_pdf(pdf_path: str, target_count: int = TARGET_PARTS) -> list[dict]:
    """
    Extract part numbers, descriptions, and page numbers from the catalog PDF.

    Looks for Johnstone Supply order numbers (e.g., S81-007, L58-502, G21-930)
    by scanning text and hyperlinks on each page.
    """
    parts = []
    seen_part_numbers = set()

    # Common Johnstone Supply part number patterns:
    # Letter(s) + digits + hyphen + digits (e.g., S81-007, L58-502, SA55-462)
    part_pattern = re.compile(r'\b([A-Z]{1,3}\d{1,3}-\d{2,4})\b')

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            if len(parts) >= target_count:
                break

            text = page.extract_text() or ""
            lines = text.split('\n')

            # Extract part numbers from text
            for line in lines:
                matches = part_pattern.findall(line)
                for part_number in matches:
                    if part_number in seen_part_numbers:
                        continue
                    if len(parts) >= target_count:
                        break

                    seen_part_numbers.add(part_number)

                    # Try to get description from the same line or surrounding context
                    description = _extract_description(line, part_number)

                    parts.append({
                        "part_number": part_number,
                        "url": f"{BASE_URL}{part_number}",
                        "description": description,
                        "catalog_page": page_num,
                    })

            # Also check hyperlinks/annotations for part numbers in URLs
            if page.annots:
                for annot in page.annots:
                    uri = annot.get("uri", "")
                    if "pID=" in uri:
                        pid = uri.split("pID=")[-1].split("&")[0]
                        if pid and pid not in seen_part_numbers:
                            if len(parts) >= target_count:
                                break
                            seen_part_numbers.add(pid)
                            parts.append({
                                "part_number": pid,
                                "url": f"{BASE_URL}{pid}",
                                "description": "",
                                "catalog_page": page_num,
                            })

    return parts


def _extract_description(line: str, part_number: str) -> str:
    """Try to extract a meaningful description from the line containing the part number."""
    # Remove the part number itself and clean up
    desc = line.replace(part_number, "").strip()
    # Remove excessive whitespace
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Truncate if too long
    if len(desc) > 200:
        desc = desc[:200].rsplit(' ', 1)[0] + "..."
    return desc


def write_csv(parts: list[dict], output_path: str) -> None:
    """Write extracted parts to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["part_number", "url", "description", "catalog_page"])
        writer.writeheader()
        writer.writerows(parts)

    print(f"Wrote {len(parts)} parts to {output_path}")


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF catalog not found at {PDF_PATH}")

    print(f"Extracting parts from {PDF_PATH}...")
    parts = extract_parts_from_pdf(str(PDF_PATH), TARGET_PARTS)
    print(f"Found {len(parts)} unique parts")

    write_csv(parts, str(OUTPUT_CSV))
    print(f"CSV saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
