import imaplib
import email
from email.header import decode_header
import os
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