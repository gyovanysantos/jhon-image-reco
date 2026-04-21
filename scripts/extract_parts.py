"""
Phase 1: Extract part numbers from the Johnstone Supply PDF catalog.

Parses Cat_220_linked_p1.pdf using pdfplumber. The most reliable source of
part numbers is the embedded hyperlinks (annotations) in the PDF which point
to product-view URLs with ?pID= query parameters.

Outputs a CSV with 100 unique parts.
"""

import csv
import os
import re
from pathlib import Path

import pdfplumber

PDF_PATH = Path(__file__).resolve().parent.parent / "Cat_220_linked_p1.pdf"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_CSV = OUTPUT_DIR / "parts_catalog.csv"
# The live site uses this URL format (the PDF uses a legacy /storefront/ path
# but both resolve to the same product page).
BASE_URL = "https://www.johnstonesupply.com/product-view?pID="
TARGET_PARTS = 100


def extract_parts_from_pdf(pdf_path: str, target_count: int = TARGET_PARTS) -> list[dict]:
    """
    Extract part numbers from the catalog PDF by scanning annotation hyperlinks.

    The PDF embeds links like:
      https://www.johnstonesupply.com/storefront/product-view.ep?pID=X82-169
    We extract the pID value and build the canonical product URL.
    """
    parts = []
    seen_part_numbers = set()

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF has {total_pages} pages. Scanning for product links...")

        for page_num, page in enumerate(pdf.pages, start=1):
            if len(parts) >= target_count:
                break

            if not page.annots:
                continue

            # Get page text for description extraction
            text = page.extract_text() or ""

            for annot in page.annots:
                if len(parts) >= target_count:
                    break

                uri = annot.get("uri")
                if not uri or "pID=" not in uri:
                    continue

                # Extract part number from URL query parameter
                pid = uri.split("pID=")[-1].split("&")[0].strip()
                if not pid or pid in seen_part_numbers:
                    continue

                seen_part_numbers.add(pid)

                # Try to find description context near this part number in the page text
                description = _extract_description(text, pid)

                parts.append({
                    "part_number": pid,
                    "url": f"{BASE_URL}{pid}",
                    "description": description,
                    "catalog_page": page_num,
                })

            if page_num % 100 == 0:
                print(f"  Scanned {page_num}/{total_pages} pages, found {len(parts)} parts so far...")

    return parts


def _extract_description(page_text: str, part_number: str) -> str:
    """Try to extract a meaningful description from the page text near the part number."""
    lines = page_text.split("\n")
    for i, line in enumerate(lines):
        if part_number in line:
            # Use the line itself, cleaned of the part number
            desc = line.replace(part_number, "").strip()
            desc = re.sub(r'\s+', ' ', desc).strip()
            if len(desc) > 200:
                desc = desc[:200].rsplit(' ', 1)[0] + "..."
            return desc
    return ""


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
