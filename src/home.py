import streamlit as st
import os

from helpers import extract


st.text("Welcome to the Home Page!")

imap_server = st.selectbox("Select E-Mail Server", ["imap.gmail.com", "imap.mail.yahoo.com", "outlook.office365.com"])

email_address = st.text_input("Enter your E-Mail Address")
password = st.text_input("Enter your E-Mail Password (or App Password)", type="password")

FILTER_EMAIL = "ebon@mailing.rewe.de"

attachment_dir = st.text_input("Attachment Directory", value="*/attachments")
if not os.path.exists(attachment_dir):
        os.makedirs(attachment_dir)

extract(imap_server, email_address, password, FILTER_EMAIL, attachment_dir)