import pytesseract
from PIL import Image
import os
from pdf2image import convert_from_path
import re

digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
a = "14068"
b = "13400"
pdf_path = f'/Users/markus/Projects/receipts/attachments/{a}.pdf'
output_text = ""

try:
    images = convert_from_path(pdf_path, first_page=1, last_page=1)

    if images:
        first_page_image = images[0]

        output_text = pytesseract.image_to_string(first_page_image)
    else:
         output_text = f"Fehler: Keine Bilder konnten aus der PDF extrahiert werden: {pdf_path}"

except Exception as e:
    output_text = f"Fehler bei der Verarbeitung von {pdf_path}: {e}"


pattern_items = r"^([A-Z.\s\d]+?)\s(\d+,\d{2})\s([A-Z])(?:\s\d+\sStk\sx\s\d+,\d{2})?$"

matches = re.finditer(pattern_items, output_text, re.MULTILINE)
for match in matches:
    # The rest of your code is the same!
    item_name = match.group(1).strip()
    item_price = match.group(2).strip()
    print(f"Item: {item_name}, Price: {item_price}")

pattern_date = r"datum:\s*(\d{2}[.\-/]\d{2}[.\-/]\d{4})"

# Search for the pattern in the text
match = re.search(pattern_date, output_text, re.IGNORECASE)

# Always check if a match was found before trying to access it
if match:
    # match.group(0) would be the full match -> "datum:  10-10-2025"
    # match.group(1) is our first (and only) capturing group -> "10-10-2025"
    extracted_date = match.group(1)
    print(f"Date: {extracted_date}")
else:
    print("Date not found.")