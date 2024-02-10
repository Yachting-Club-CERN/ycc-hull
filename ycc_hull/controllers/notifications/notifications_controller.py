#print("Hello world")

#ycc-noreply@cern.ch

import smtpd
import asyncore

class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data):
        print(f"Receiving message from: {mailfrom}")
        print(f"Recipients: {rcpttos}")
        print(f"Message length: {len(data)}")
        print(f"Message data:\n{data}\n")

if __name__ == '_main_':
    smtp_server = CustomSMTPServer(('127.0.0.1', 10022), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
        
        
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage

# Open the plain text file whose name is in textfile for reading.
#with open(textfile) as fp:
    # Create a text/plain message
msg = EmailMessage()
msg.set_content('Hello world')

# me == the sender's email address
# you == the recipient's email address
#msg['Subject'] = 'Test sending emails'
#msg['From'] = "xxxxx@cern.ch" ycc-noreply@cern.ch
#msg['To'] = #recipient e-mail

msg['Subject'] = 'Test sending emails'
msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
msg['To'] = ####



#with open('tuto4.pdf', 'rb') as content_file:
#    content = content_file.read()
#    msg.add_attachment(content, maintype='application', subtype='pdf', filename='tuto4.pdf')

# Send the message via our own SMTP server.

s = smtplib.SMTP('localhost',10022)  
s.send_message(msg)
s.quit()