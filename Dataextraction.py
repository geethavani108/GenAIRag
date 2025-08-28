# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys
sys.path.append(r'C:\Users\My PC\AppData\Roaming\Python\Python313\site-packages')


import pdfplumber
sys.path.append(r'C:\Users\My PC\AppData\Roaming\Python\Python313\site-packages')
import fitz
sys.path.append(r'C:\Users\My PC\AppData\Roaming\Python\Python313\site-packages')
import re
import os
import json

def extract_text(pdf_path):
    """Extract all text from PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text

def extract_fields(text):
    """Extract structured fields using regex"""
    data = {}
    data["customer_name"] = re.search(r"Customer Name[:\-]\s*(.*)", text)
    data["plan_type"]     = re.search(r"Plan Type[:\-]\s*(.*)", text)
    data["pricing"]       = re.search(r"(?:Price|Pricing|Amount)[:\-]\s*(.*)", text)
    data["duration"]      = re.search(r"(?:Duration|Validity|Tenure)[:\-]\s*(.*)", text)

    # Clean results
    for k, v in data.items():
        data[k] = v.group(1).strip() if v else None
    return data

def extract_sections(text):
    """Extract terms, clauses, and legal terms"""
    sections = {}
    patterns = {
        "terms": r"(Terms(?: and Conditions)?[:\s].*?)(?=Clauses|Legal|$)",
        "clauses": r"(Clauses[:\s].*?)(?=Terms|Legal|$)",
        "legal_terms": r"(Legal(?: Terms)?[:\s].*?)(?=Terms|Clauses|$)",
    }
    for key, pat in patterns.items():
        match = re.search(pat, text, re.S | re.I)
        sections[key] = match.group(1).strip() if match else None
    return sections

def extract_images(pdf_path, out_dir="images"):
    """Extract images and their captions"""
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        text = page.get_text()

        for i, img in enumerate(images):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            img_path = os.path.join(out_dir, f"page{page_num+1}_img{i+1}.png")
            if pix.n - pix.alpha >= 4:  # CMYK
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(img_path)
            pix = None

            # Simple caption detection: find text near "image"
            caption_match = re.search(r"(?:Photo|Image|Customer)\s*[:\-]?\s*(.*)", text, re.I)
            caption = caption_match.group(1).strip() if caption_match else None

            results.append({"image": img_path, "caption": caption})
    return results

def extract_pdf(pdf_path, out_dir="output"):
    text = extract_text(pdf_path)
    fields = extract_fields(text)
    sections = extract_sections(text)
    images = extract_images(pdf_path, os.path.join(out_dir, "images"))

    result = {**fields, **sections, "images": images}

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result

# ---- Example usage ----
if __name__ == "__main__":
    pdf_file = "C:/Users/My PC/Downloads/phone_contract_synthetic.pdf"   # <--- your PDF here
    data = extract_pdf(pdf_file)
    print(json.dumps(data, indent=2))
