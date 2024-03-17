# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage

from email.utils import make_msgid


msg = EmailMessage()
test_text = make_msgid()

email_type = "notification"

if email_type == "notification":

    msg.set_content("""\
    <html>
    <head></head>
    <body>
        <p>Dear João,</p>
        
        <p>Thank you for signing up for the following surveillance shift as Crew2: </p>
        
        <p> &emsp; &emsp; Thursday, April 19 <br> &emsp; &emsp; from 18:00 to 20:30 </p>
        
        <p>If you cannot take your shift, please find a replacement and then contact by phone X Y(+41 XXXXXXX) or - if absent - X Y (+41 XXXXXXX). </p>
        
        <p>The YCC Surveillance Team</p>
    </body>
    </html>
    """.format(
            test_text=test_text[1:-1]
        ),
        subtype="html",
    )

elif email_type == "reminder":

    msg.set_content(
        """\
    <html>
    <head></head>
    <body>
        <p>Dear João,</p>
        
        <p>this is an automatic reminder for the following surveillance shift as CREW: </p>
        
        <p> &emsp; &emsp; Thursday, April 19 <br> &emsp; &emsp; from 18:00 to 20:30 </p>
        
        <p> Please do not miss it and be in Port Choiseul at the mooring of the Q-boat in time! </p>
        <p> If you cannot take your shift, please find a replacement and then contact by phone X Y(+41 XXXXXXX) or - if absent - X Y (+41 XXXXXXX). </p>
        
        <p>The YCC Surveillance Team</p>
        
        <p> The surveillance crew consists of the following members: <br>
        Crew  : X Y <br>
        &emsp; &emsp; eMail XXXX@XX.XX <br>
        &emsp; &emsp; Phone XXX(work) <br>
        &emsp; &emsp; Phone XXX(home) 
        
    </body>
    </html>
    """.format(
            test_text=test_text[1:-1]
        ),
        subtype="html",
    )
# me == the sender's email address
# you == the recipient's email address
# msg['Subject'] = 'Test sending emails'
# msg['From'] = "xxxxx@cern.ch" ycc-noreply@cern.ch
# msg['To'] = #recipient e-mail

msg["Subject"] = "Test sending emails"
msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
msg["To"] = "joao@mailinator.com"


# with open('tuto4.pdf', 'rb') as content_file:
#    content = content_file.read()
#    msg.add_attachment(content, maintype='application', subtype='pdf', filename='tuto4.pdf')

# Send the message via our own SMTP server.

s = smtplib.SMTP("smtp.gmail.com", 587)
s.starttls()
s.login("yccapptest", "xnbc zjtk zfsg uato")
s.send_message(msg)
s.quit()
