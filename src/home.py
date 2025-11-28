import streamlit as st
import os

from helpers import extract
from helpers import process


st.text("Welcome to the Home Page!")

imap_server = st.selectbox("Select E-Mail Server", ["imap.gmail.com", "imap.mail.yahoo.com", "outlook.office365.com"])

email_address = st.text_input("Enter your E-Mail Address")
password = st.text_input("Enter your E-Mail Password (or App Password)", type="password")

FILTER_EMAIL = "ebon@mailing.rewe.de"

attachment_dir = st.text_input("Attachment Directory", value="attachments")
if st.button("Set Attachment Directory") and not os.path.exists(attachment_dir):
        os.makedirs(attachment_dir)

disabled_extract = True
disabled_process = True

if email_address and password:
        disabled_extract = False

if st.button("Start Extraction", disabled=disabled_extract):
        extract(imap_server, email_address, password, FILTER_EMAIL, attachment_dir)
        disabled_process = False

if st.button("Start Processing", disabled=disabled_process):
        process(attachment_dir, 'monthly_euros.csv', 'processed_emails.csv')