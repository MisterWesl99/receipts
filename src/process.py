import pytesseract
from PIL import Image
import os
from pdf2image import convert_from_path
import re
import csv

def process():

    file_path = '/Users/markus/Projects/receipts/attachments'
    output_text = ""

    dic = {}
    pattern_date = r"datum:\s*(\d{2}[.\-/]\d{2}[.\-/]\d{4})"
    pattern_price = r"EUR\s*(\d+,\d{2})"
    pattern_items = r"^([A-Z.\s\d]+?)\s(\d+,\d{2})\s([A-Z])(?:\s\d+\sStk\sx\s\d+,\d{2})?$"

    counter = 0

    for file in os.listdir(file_path):
        if file.endswith(".pdf"):
            counter += 1

    print(f"Anzahl der PDF-Dateien im Verzeichnis: {counter}")

    for file in os.listdir(file_path):
        if file.endswith(".pdf"):
            counter -= 1
            if counter % 10 == 0:
                print(counter)
            pdf_path = os.path.join(file_path, file)

            try:
                images = convert_from_path(pdf_path, first_page=1, last_page=1)

                if images:
                    first_page_image = images[0]

                    output_text = pytesseract.image_to_string(first_page_image)
                else:
                    output_text = f"Fehler: Keine Bilder konnten aus der PDF extrahiert werden: {pdf_path}"

            except Exception as e:
                output_text = f"Fehler bei der Verarbeitung von {pdf_path}: {e}"


            #matches = re.finditer(pattern_items, output_text, re.MULTILINE)
            #for match in matches:
            #    # The rest of your code is the same!
            #    item_name = match.group(1).strip()
            #    item_price = match.group(2).strip()
            #    print(f"Item: {item_name}, Price: {item_price}")

            match = re.search(pattern_date, output_text, re.IGNORECASE)
            if match:
                extracted_date = match.group(1)
                extracted_month = extracted_date[3:]

            match = re.search(pattern_price, output_text, re.IGNORECASE)
            if match:
                extracted_price = match.group(1)
                extracted_price = float(extracted_price.replace(',', '.'))

            dic[extracted_month] = dic.get(extracted_month, 0.0) + extracted_price

    dic = dict(sorted(dic.items(), key=lambda item: (int(item[0].split('.')[1]), int(item[0].split('.')[0]))))
    print(dic)

    # Define the headers (column names)
    headers = ["month", "euro"]

    # Define the filename
    filename = "monthly_euros.csv"

    # Writing to the csv file
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Create a csv writer object
            csvwriter = csv.writer(csvfile)

            # Write the headers
            csvwriter.writerow(headers)

            # Write the data rows
            csvwriter.writerows(dic.items())

        print(f"Successfully created the file: {filename}")

    except IOError:
        print(f"Error: Could not write to the file {filename}.")