import imaplib
import email
from email.header import decode_header
import os
import getpass # Für sichere Passworteingabe
import csv

def extract():
    # --- Konfiguration ---
    IMAP_SERVER = 'imap.gmail.com'
    EMAIL_ADDRESS = input("Geben Sie Ihre E-Mail-Adresse ein: ")
    # Sichere Passworteingabe (oder App-Passwort)
    PASSWORD = getpass.getpass("Geben Sie Ihr E-Mail-Passwort (oder App-Passwort) ein: ")

    # Name und E-Mail-Adresse, nach der gefiltert werden soll
    FILTER_EMAIL = "ebon@mailing.rewe.de"

    # Optional: Ordner zum Speichern von Anhängen
    ATTACHMENT_DIR = '/Users/markus/Projects/receipts/attachments'
    if not os.path.exists(ATTACHMENT_DIR):
        os.makedirs(ATTACHMENT_DIR)
    # --------------------

    def decode_subject(header):
        """Dekodiert E-Mail-Header (z.B. Betreff) korrekt."""
        decoded_parts = decode_header(header)
        subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                subject += part.decode(encoding or 'utf-8', errors='replace')
            else:
                subject += part
        return subject

    try:
        # Verbindung zum Server herstellen (SSL verwenden)
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)

        # Anmelden
        mail.login(EMAIL_ADDRESS, PASSWORD)
        print("Erfolgreich angemeldet.")

        # Postfach auswählen (normalerweise 'inbox')
        status, messages_count = mail.select('inbox')
        if status != 'OK':
            print("Fehler beim Öffnen des Postfachs.")
            exit()

        print(f"Postfach geöffnet. Anzahl Nachrichten: {messages_count[0].decode()}")

        # E-Mails durchsuchen
        search_criteria = f'FROM "{FILTER_EMAIL}"'

        print(f"Suche nach E-Mails mit Kriterium: {search_criteria}...")
        status, search_result = mail.uid("search", None, search_criteria)

        if status != 'OK':
            print("Fehler bei der Suche nach E-Mails.")
            exit()

        email_ids = search_result[0].split()
        print(f"{len(email_ids)} E-Mail(s) gefunden.")

        # Durch gefundene E-Mails iterieren
        for email_id in email_ids:
            print(f"\nVerarbeite E-Mail ID: {email_id.decode()}")

            file = os.path.join(ATTACHMENT_DIR, email_id.decode()+'.pdf')
            if os.path.isfile(file):
                print(f"  E-Mail ID {email_id.decode()} bereits verarbeitet. Überspringe...")
                continue
            else:
                # E-Mail-Daten abrufen (vollständige Nachricht nach RFC822)
                status, msg_data = mail.uid("fetch", email_id, '(RFC822)')
                if status != 'OK':
                    print(f"Fehler beim Abrufen von E-Mail ID {email_id.decode()}.")
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # E-Mail parsen
                        msg = email.message_from_bytes(response_part[1])

                        # Absender und Betreff extrahieren und dekodieren
                        sender = decode_subject(msg.get('From'))
                        subject = decode_subject(msg.get('Subject'))
                        print(f"  Von: {sender}")
                        print(f"  Betreff: {subject}")

                        # --- Anhänge suchen und verarbeiten ---
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_disposition = str(part.get("Content-Disposition"))

                                # Prüfen, ob es sich um einen Anhang handelt
                                if "attachment" in content_disposition:
                                    filename = part.get_filename()
                                    if filename:
                                        filename = decode_subject(filename) # Dateinamen auch dekodieren
                                        print(f"  Anhang gefunden: {filename}")

                                        # Nutzdaten (Inhalt) des Anhangs holen und dekodieren (oft Base64)
                                        payload = part.get_payload(decode=True)

                                        if payload:
                                            #Anhang speichern
                                            filepath = os.path.join(ATTACHMENT_DIR, email_id.decode()+'.pdf')
                                            try:
                                                with open(filepath, 'wb') as f:
                                                    f.write(payload)
                                                print(f"  Anhang gespeichert unter: {filepath}")
                                            except Exception as e_save:
                                                print(f"  Fehler beim Speichern von '{filename}': {e_save}")
                                        else:
                                            print(f"  Anhang '{filename}' hat keinen Inhalt.")
                        else:
                            print("  Keine Anhänge (keine Multipart-Nachricht).")

    except imaplib.IMAP4.error as e:
        print(f"IMAP Fehler: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        # Verbindung immer schließen, auch bei Fehlern
        if 'mail' in locals() and mail.state == 'SELECTED':
            mail.close()
            mail.logout()
            print("\nVerbindung geschlossen.")