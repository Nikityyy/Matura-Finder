import fitz
import os
import json
from tqdm import tqdm

PDF_DIRECTORY = "pdfs"
OUTPUT_JSON = "matura_data.json"
TARGET_FONT_SIZE = 14.0
MIN_TITLE_LENGTH = 4
IGNORE_FIRST_PAGE = True
IGNORE_LAST_PAGE = True

def is_potential_title(text, size):
    """checks if text is a potential title"""
    if not text or not text.strip():
        return False
    if size != TARGET_FONT_SIZE:
        return False
    if text == "Hinweise zur Aufgabenbearbeitung":
        return False
    cleaned_text = text.strip()
    if len(cleaned_text) < MIN_TITLE_LENGTH:
        return False
    if cleaned_text.isdigit():
        return False
    if cleaned_text.startswith(("_", "-", "„")):
        return False
    return True

def extract_titles_from_pdf(pdf_path):
    """extracts potential titles from a single pdf file."""
    titles = []
    filename = os.path.basename(pdf_path)
    if not filename.endswith("LO.pdf"):
        os.remove(pdf_path)
        return titles
    try:
        doc = fitz.open(pdf_path)
        num_pages = doc.page_count
        for page_num in range(num_pages):
            if IGNORE_FIRST_PAGE and page_num == 0:
                continue
            if IGNORE_LAST_PAGE and page_num == num_pages - 1:
                continue
            page = doc.load_page(page_num)
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
            for block in blocks:
                if block["type"] == 0:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            size = span["size"]
                            if is_potential_title(text, size):
                                titles.append({
                                    "title": text.strip(),
                                    "source": f"{PDF_DIRECTORY}/{filename}",
                                    "page": page_num + 1,
                                    "filename": filename,
                                })
        doc.close()
    except Exception as e:
        print(f"error processing {filename}: {e}")
    return titles

# main execution
if __name__ == "__main__":
    all_matura_titles = []
    if not os.path.exists(PDF_DIRECTORY):
        print(f"error: pdf directory '{PDF_DIRECTORY}' not found.")
        exit(1)
    pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"no pdf files found in '{PDF_DIRECTORY}'.")
        exit(0)
    print(f"found {len(pdf_files)} pdf files. starting extraction...")
    for pdf_file in tqdm(pdf_files, desc="processing pdfs", unit="file"):
        file_path = os.path.join(PDF_DIRECTORY, pdf_file)
        extracted = extract_titles_from_pdf(file_path)
        all_matura_titles.extend(extracted)
    all_matura_titles.sort(key=lambda x: (x["filename"].lower(), x["page"]))
    unique_titles = []
    seen = set()
    for item in all_matura_titles:
        identifier = item["title"]
        if identifier not in seen:
            unique_titles.append(item)
            seen.add(identifier)
    try:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(unique_titles, f, ensure_ascii=False, indent=2)
        print(f"\nsuccessfully extracted {len(unique_titles)} unique titles.")
        print(f"data saved to {OUTPUT_JSON}")
    except Exception as e:
        print(f"\nerror writing json file {OUTPUT_JSON}: {e}")
