#!/usr/bin/env python3
"""
Simple script to send a test email to laikamail for scanning.
Usage: python3 send_test_email.py [host] [port]
"""
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_test_email(host='localhost', port=2525):
    # Create message
    msg = MIMEMultipart()
    msg['From'] = 'test@example.com'
    msg['To'] = 'scan@localhost'
    msg['Subject'] = 'Test Email for LaikaBOSS Scanning'
    
    # Email body
    body = """
    This is a test email for LaikaBOSS malware scanning.
    
    It contains plain text and can include attachments.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Optional: Add a test attachment
    test_content = b"This is a test file attachment for scanning."
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(test_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename='test.txt')
    msg.attach(attachment)
    
    # Send
    try:
        server = smtplib.SMTP(host, port)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()
        print(f"Email sent successfully to {host}:{port}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 2525
    send_test_email(host, port)
