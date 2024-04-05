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
                <p>Dear """ + member_firstname + """, <p>
                
                Thank you for signing up for the task: <p>
        
                &emsp; &emsp;""" + task_short_description +"""<br>
                &emsp; &emsp from """ + task_start_date + """to""" + task_end_date + """
        
                <p>If you cannot take your shift, please find a replacement. <p>
        
                The YCC Surveillance Team</p>
            
            </body>
            </html>
            """.format(test_text = test_text[1:-1]), subtype='html')

        

    msg['Subject'] = 'YCC Task enrolment confirmation'
    msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
    msg['To'] = member_email

    s = smtplib.SMTP('smtp.gmail.com',587)  
    s.starttls()
    s.login("yccapptest", "")
    s.send_message(msg)
    s.quit()
    
    
def send_reminder_task(task):

    task_title = task.title
    task_start_date = task.starts_at
    task_end_date = task.ends_at
    task_deadline = task.deadline
    task_short_description = task.short_description
    task_long_description = task.long_description
    
    captain = task.captain
    crew = task.helpers

    crew_list =''
    for i in range(0, len(crew)):
        crew_list += crew[i].firstname + ' ' + crew[i].name + ', Phone number: ' + crew[i].cell_phone + ' / ' + crew[i].work_phone + '<br>'


    import smtplib
    from email.message import EmailMessage
    from email.utils import make_msgid

    msg = EmailMessage()
    test_text = make_msgid()
    
    for i in range(0, len(crew)):
        helper = crew[i]

        msg.set_content("""\
            <html>
            <head></head>
            <body>
                <p>Dear """ + helper.firstname + """,<p>
                
                This is a reminder for the following task as crew: <p>
                
                &emsp; &emsp; Task: """ + task.title +""" <br>
                &emsp; &emsp; Start: """ + task_start_date + """ <br>
                &emsp; &emsp; End: """ + task_end_date + """ </p>
                
                &emsp; &emsp; Captain: """ + captain.firstname + """ """ + captain.name + """ <br>
                &emsp; &emsp; Email: """ + captain.email + """<br>
                &emsp; &emsp; Phone: """ + captain.cell_phone + """ / """ + captain.work_phone +""" <p>
                
                In case you are not available anymore to do this task, please find a replacement and then contact the Captain. <p>
                
                The YCC Maintenance Team <p>
                
            </body>
            </html>
            """.format(test_text = test_text[1:-1]), subtype='html')

        msg['Subject'] = "YCC Task reminder"
        msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
        msg['To'] = helper.email

        s = smtplib.SMTP('smtp.gmail.com',587)  
        s.starttls()
        s.login("yccapptest", "")
        s.send_message(msgcrew)
        s.quit()
            
        
    msg.set_content("""\
        <html>
        <head></head>
        <body>
            <p>Dear """ + captain.firstname + """,</p>
                
            This is a reminder for the following task as Captain: <p>
                
            &emsp; &emsp; Task: """ + task.title +""" <br>
            &emsp; &emsp; Start: """ + task_start_date + """ <br>
            &emsp; &emsp; End: """ + task_end_date + """ </p>
                
            Your crew for this task is: <br>
            """ + crew_list + """
                
            <p> Thank you for coordinating this task!
                
            The YCC Maintenance Team <p>
                
        </body>
        </html>
        """.format(test_text = test_text[1:-1]), subtype='html')
    
    msg['Subject'] = "YCC Task reminder"
    msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
    msg['To'] = captain.email

    s = smtplib.SMTP('smtp.gmail.com',587)  
    s.starttls()
    s.login("yccapptest", "")
    s.send_message(msg)
    s.quit()
    
    
    
def send_reminder_surveillance(task):

    task_title = task.title
    task_start_date = task.starts_at
    task_end_date = task.ends_at
    task_deadline = task.deadline
    task_short_description = task.short_description
    task_long_description = task.long_description
    
    captain = task.captain
    crew = task.helpers

    crew_list =''
    for i in range(0, len(crew)):
        crew_list += crew[i].firstname + ' ' + crew[i].name + '<br>' + 'E-mail: ' + crew[i].email + '<br>' + ', Phone number: ' + crew[i].cell_phone + ' / ' + crew[i].work_phone + '<p>'


    import smtplib
    from email.message import EmailMessage
    from email.utils import make_msgid

    msg = EmailMessage()
    test_text = make_msgid()
    
    for i in range(0, len(crew)):
        helper = crew[i]

        msg.set_content("""\
            <html>
            <head></head>
            <body>
                <p>Dear """ + helper.firstname + """,<p>
                
                This is a reminder for the following surveillance shift as crew: <p>
                
                &emsp; &emsp; Start: """ + task_start_date + """ <br>
                &emsp; &emsp; End: """ + task_end_date + """ </p>
                
                &emsp; &emsp; Captain: """ + captain.firstname + """ """ + captain.name + """ <br>
                &emsp; &emsp; Email: """ + captain.email + """<br>
                &emsp; &emsp; Phone: """ + captain.cell_phone + """ / """ + captain.work_phone +""" <p>
                
                Please do not miss it and be in Port Choiseul at the mooring of the Q-boat in time! /p>
                
                In case you are not available anymore to do this task, please find a replacement and then contact the Captain. <p>
                
                The YCC Surveillance Team <p>
                
            </body>
            </html>
            """.format(test_text = test_text[1:-1]), subtype='html')

        msg['Subject'] = "YCC Surveillance reminder"
        msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
        msg['To'] = helper.email

        s = smtplib.SMTP('smtp.gmail.com',587)  
        s.starttls()
        s.login("yccapptest", "")
        s.send_message(msgcrew)
        s.quit()
            
        
    msg.set_content("""\
        <html>
        <head></head>
        <body>
            <p>Dear """ + captain.firstname + """,</p>
                
            This is a reminder for the following surveillance shift as Captain: <p>
                
            &emsp; &emsp; Start: """ + task_start_date + """ <br>
            &emsp; &emsp; End: """ + task_end_date + """ </p>
                
            Your crew for this surveillance shift is: <br>
            """ + crew_list + """
                
            <p> Thank you!
                
            The YCC Surveillance Team <p>
                
        </body>
        </html>
        """.format(test_text = test_text[1:-1]), subtype='html')
    
    msg['Subject'] = "YCC Surveillance reminder"
    msg['From'] = "ycc-noreply@cern.ch" #ycc-noreply@cern.ch
    msg['To'] = captain.email

    s = smtplib.SMTP('smtp.gmail.com',587)  
    s.starttls()
    s.login("yccapptest", "")
    s.send_message(msg)
    s.quit()