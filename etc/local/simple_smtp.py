#!/usr/bin/env python3
"""
Simple SMTP server for local testing that writes emails to LaikaBOSS submission queue.
Uses Python's built-in smtpd module (no external dependencies).
"""
import asyncore
import os
import sys
import json
import uuid
import base64
import datetime
import smtpd

SUBMISSION_DIR = os.environ.get('SUBMISSION_DIR', '/var/laikaboss/submission-queue/email')
SOURCE = os.environ.get('SOURCE', 'email-localhost')

class LaikaMailServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Handle incoming email and write to submission queue."""
        try:
            # Generate unique ID
            submit_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%SZ')

            # data is bytes in Python 3
            if isinstance(data, str):
                data = data.encode('utf-8')

            # Create the submission structure matching ExternalObject.encode() format
            submission = {
                'buffer': base64.standard_b64encode(data).decode('utf-8'),  # base64 encoded
                'externalVars': {
                    'source': SOURCE,
                    'submitID': submit_id,
                    'ephID': submit_id,
                    'filename': f'{submit_id}.eml',
                    'contentType': ['message/rfc822'],
                    'sourceModule': '',
                    'parentModules': [],
                    'charset': '',
                    'uniqID': '',
                    'timestamp': timestamp,
                    'flags': [],
                    'parent': '',
                    'parent_order': 0,
                    'depth': 0,
                    'origRootUID': '',
                    'comment': '',
                    'submitter': '',
                    'extArgs': {},
                },
                'level': 0,
                'ver': 2,
            }

            # Write to submission queue
            os.makedirs(SUBMISSION_DIR, exist_ok=True)
            filename = f'{timestamp}-{submit_id}.submit'
            filepath = os.path.join(SUBMISSION_DIR, filename)

            # Write JSON (not gzipped - collector expects plain JSON)
            with open(filepath, 'w') as f:
                json.dump(submission, f)

            print(f"[{timestamp}] Email queued: {submit_id}")
            print(f"  From: {mailfrom}")
            print(f"  To: {rcpttos}")
            print(f"  Size: {len(data)} bytes")
            print(f"  Saved to: {filepath}")
            sys.stdout.flush()

        except Exception as e:
            print(f"Error handling message: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()

        return None  # Accept the message

def main():
    host = os.environ.get('SMTP_HOST', '0.0.0.0')
    port = int(os.environ.get('SMTP_PORT', '2525'))

    print(f"Starting simple SMTP server on {host}:{port}")
    print(f"Submission directory: {SUBMISSION_DIR}")
    print(f"Source: {SOURCE}")
    print()
    print("Send test emails using:")
    print(f"  python3 -c \"import smtplib; s=smtplib.SMTP('localhost',{port}); s.sendmail('test@example.com',['scan@localhost'],'Subject: Test\\n\\nTest body'); s.quit()\"")
    print()
    sys.stdout.flush()

    server = LaikaMailServer((host, port), None)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
