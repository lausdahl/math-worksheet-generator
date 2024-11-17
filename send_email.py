import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
# Load SMTP configuration from environment variables
smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # Default to Gmail SMTP server
smtp_port = int(os.getenv("SMTP_PORT", 587))  # Default to port 587
password = os.getenv("SMTP_PASSWORD")  # Email account password
# sender_email = os.getenv("SMTP_EMAIL")  # Sender's email address
# receiver_email = os.getenv("SMTP_RECEIVER")  # Recipient's email address

def send_attachment( receiver_email:str,attachment_path:Path,sender_email:str=os.getenv("SMTP_EMAIL")):


    # Check if required environment variables are set
    if not sender_email or not password or not receiver_email:
        raise ValueError("Missing required environment variables: SMTP_EMAIL, SMTP_PASSWORD, SMTP_RECEIVER")

    # Create the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Exercise"

    # Email body
    body = "Hi there,\n\nPlease find the attached PDF file.\n\nBest regards,\nHome work for you"
    message.attach(MIMEText(body, "plain"))

    # Attach PDF
    pdf_filename = attachment_path  # Replace with your PDF filename
    if os.path.exists(pdf_filename):
        with open(pdf_filename, "rb") as pdf_file:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(pdf_file.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename={pdf_filename.name}",
        )
        message.attach(attachment)
    else:
        print(f"File '{pdf_filename}' not found. Skipping attachment.")

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Start TLS encryption
            server.login(sender_email, password)  # Log in to the SMTP server
            server.send_message(message)  # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
