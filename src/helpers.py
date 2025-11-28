import csv
import imaplib
import email
from email.header import decode_header
import os
import pytesseract
from PIL import Image
import os
from pdf2image import convert_from_path
import re
import csv
import streamlit as st

def decode_subject(header):
    decoded_parts = decode_header(header)
    subject = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            subject += part.decode(encoding or "utf-8", errors = "replace")
        else:
            subject += part
    return subject

def extract(imap_server, email_address, password, filter_email, attachment_dir):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        st.toast("Successfully logged in.")

        status, messages_count = mail.select("inbox")
        if status != "OK":
            st.error("Error opening mailbox.")
            return
        
        st.toast(f"Mailbox opened. Number of messages: {messages_count[0].decode()}")

        search_criteria = f"FROM \"{filter_email}\""
        
        status, search_result = mail.uid("search", None, search_criteria)
        if status != "OK":
            st.error("Error searching for emails.")
            return
        
        email_ids = search_result[0].split()
        st.toast(f"Found {len(email_ids)} emails from {filter_email}.")

        for email_id in email_ids:

            file = os.path.join(attachment_dir, email_id.decode()+".pdf")
            if os.path.isfile(file):
                continue
            else:
                status, msg_data = mail.uid("fetch", email_id, "(RFC822)")
                if status != "OK":
                    st.error(f"Error when calling E-Mail {email_id.decode()}.")
                    continue

                for response_part in msg_data:

                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        if msg.is_multipart():
                            for part in msg.walk():
                                content_disposition = str(part.get("Content-Disposition"))

                                if "attachment" in content_disposition:
                                    filename = part.get_filename()
                                    if filename:
                                        filename = decode_subject(filename)

                                        payload = part.get_payload(decode=True)

                                        if payload:
                                            filepath = os.path.join(attachment_dir, email_id.decode()+".pdf")
                                            try:
                                                with open(filepath, "wb") as f:
                                                    f.write(payload)
                                            except Exception as e_save:
                                                st.error(f"Error saving \"{filename}\": {e_save}")
                                        else:
                                            st.error(f"No attachment for \"{filename}\".")
                        else:
                            st.error("No attachments found.")

    except imaplib.IMAP4.error as e:
        st.error(f"IMAP Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        if "mail" in locals() and mail.state == "SELECTED":
            mail.close()
            mail.logout()
            st.toast("Logged out from the mail server.")

def process(emails_path, input, output):
    monthly_euros_file = input
    processed_emails_file = output

    # --- Step 1: Load Existing Data ---
    
    # Load already processed email IDs into a set for fast lookups
    processed_emails = set()
    try:
        with open(processed_emails_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row: # Ensure the row is not empty
                    processed_emails.add(row[0])
        print(f"Loaded {len(processed_emails)} previously processed email IDs.")
    except FileNotFoundError:
        print("processed_emails.csv not found. Starting fresh.")

    # Load existing monthly totals into the dictionary
    monthly_euros = {}
    try:
        with open(monthly_euros_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                if row and row[0] != 'avg':
                    month, euro = row
                    monthly_euros[month] = float(euro)
        print(f"Loaded {len(monthly_euros)} existing monthly records.")
    except FileNotFoundError:
        print("monthly_euros.csv not found. Starting fresh.")

    # --- Step 2: Process Only New Files ---
    
    pattern_date = r"datum:\s*(\d{2}[.\-/]\d{2}[.\-/]\d{4})" r"datum:\s*(\d{2}[.\-/]\d{2}[.\-/]\d{4})"
    pattern_price = r"EUR\s*(\d+,\d{2})"
    pattern_items = r"^([A-Z.\s\d]+?)\s(\d+,\d{2})\s([A-Z])(?:\s\d+\sStk\sx\s\d+,\d{2})?$"
    
    # Keep track of emails processed in this run
    newly_processed_emails = []

    all_pdfs = [f for f in os.listdir(emails_path) if f.endswith(".pdf")]
    print(f"Found {len(all_pdfs)} total PDF files in the directory.")

    for file in all_pdfs:
        email_id = file.removesuffix(".pdf")
        
        # Skip if already processed
        if email_id in processed_emails:
            continue

        print(f"Processing new file: {file}")
        pdf_path = os.path.join(emails_path, file)
        output_text = ""
        
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            if images:
                output_text = pytesseract.image_to_string(images[0])
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            continue # Skip to the next file on error

        # Extract data and update totals
        extracted_month = None
        extracted_price = 0.0

        match_date = re.search(pattern_date, output_text, re.IGNORECASE)
        if match_date:
            extracted_date = match_date.group(1)
            extracted_month = extracted_date[3:] # Format MM.YYYY

        match_price = re.search(pattern_price, output_text, re.IGNORECASE)
        if match_price:
            price_str = match_price.group(1).replace(',', '.')
            extracted_price = float(price_str)

        # If we have valid data, update the dictionary
        if extracted_month and extracted_price > 0:
            monthly_euros[extracted_month] = monthly_euros.get(extracted_month, 0.0) + extracted_price
            # Add the ID to our list for this session
            newly_processed_emails.append(email_id)
        else:
            print(f"Could not extract complete data from {file}. Skipping.")
            #print(output_text)  # For debugging purposes
            print(match_date)
            print(extracted_month)
            print(extracted_price)


    # --- Step 3: Save Updated Results ---

    # A) Save the updated monthly totals
    if newly_processed_emails: # Only rewrite if there's new data
        # Sort the dictionary by year, then month before saving
        sorted_totals = dict(sorted(monthly_euros.items(), key=lambda item: (int(item[0].split('.')[1]), int(item[0].split('.')[0]))))
        
        # Calculate the new average
        try:
            avg_value = round(sum(sorted_totals.values()) / len(sorted_totals), 2)
            sorted_totals["avg"] = avg_value
        except ZeroDivisionError:
            sorted_totals["avg"] = 0.0

        try:
            with open(monthly_euros_file, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(["month", "euro"]) # Write header
                csvwriter.writerows(sorted_totals.items())
            print(f"Successfully updated {monthly_euros_file} with new totals.")
        except IOError as e:
            print(f"Error writing to {monthly_euros_file}: {e}")
    else:
        print("No new files to process. Results are unchanged.")

    # B) Append the newly processed IDs to the log file
    if newly_processed_emails:
        try:
            # Use 'a' for append mode
            with open(processed_emails_file, 'a', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                for email_id in newly_processed_emails:
                    csvwriter.writerow([email_id])
            print(f"Successfully appended {len(newly_processed_emails)} new IDs to {processed_emails_file}.")
        except IOError as e:
            print(f"Error writing to {processed_emails_file}: {e}")