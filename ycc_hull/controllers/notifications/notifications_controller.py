def send_task_confirmation(task, member):

    task_title = task.title
    task_start_date = task.starts_at
    task_end_date = task.ends_at
    task_deadline = task.deadline
    task_short_description = task.short_description
    task_long_description = task.long_description
    
    member_firstname = member.firstname
    member_name = member.name
    member_email = member.email


    import smtplib
    from email.message import EmailMessage
    from email.utils import make_msgid

    msg = EmailMessage()
    test_text = make_msgid()

    msg.set_content("""\
            <html>
            <head></head>
            <body>
                <p>Dear """ + member_firstname + """,</p>
                
                <p>Thank you for signing up for the task: </p>
        
                <p> &emsp; &emsp;""" + task_short_description +"""<br>
                &emsp; &emsp from """ + task_start_date + """to""" + task_end_date + """
        
                <p>If you cannot take your shift, please find a replacement. </p>
        
                <p>The YCC Surveillance Team</p>
            
            </body>
            </html>
            """.format(test_text = test_text[1:-1]), subtype='html')

        
    
    # me == the sender's email address
    # you == the recipient's email address
    #msg['Subject'] = 'Test sending emails'
    #msg['From'] = "xxxxx@cern.ch" ycc-noreply@cern.ch
    #msg['To'] = #recipient e-mail

    msg['Subject'] = 'YCC Task enrolment confirmation'
    msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
    msg['To'] = member_email

    s = smtplib.SMTP('smtp.gmail.com',587)  
    s.starttls()
    s.login("yccapptest", "")
    s.send_message(msg)
    s.quit()