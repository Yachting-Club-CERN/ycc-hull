from datetime import datetime
from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.email import EmailMessageBuilder
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskType


def get_helper_task_url(task: HelperTaskDto) -> str:
    return f"{CONFIG.ycc_app_base_url}/helpers/tasks/{task.id}"


def format_date(date: datetime | None) -> str | None:
    return date.strftime("%d/%m/%Y") if date else None


def format_date_with_day(date: datetime | None) -> str | None:
    return date.strftime("%A, %d %B %Y") if date else None


def format_time(date: datetime | None) -> str | None:
    return date.strftime("%H:%M") if date else None


def format_date_time(date: datetime | None) -> str | None:
    return date.strftime("%d/%m/%Y, %H:%M") if date else None


# TODO format better: https://pypi.org/project/phonenumbers/


def format_phone_numbers(member: MemberPublicInfoDto) -> str:
    phones = []
    if member.mobile_phone:
        phones.append(f"Mobile: {member.mobile_phone}")
    if member.home_phone:
        phones.append(f"Home: {member.home_phone}")
    if member.work_phone:
        phones.append(f"Work: {member.work_phone}")


def format_timing(task: HelperTaskDto) -> str:
    if task.type == HelperTaskType.SHIFT:
        same_day_end = task.starts_at.date() == task.ends_at.date()
        if same_day_end:
            return f"Shift: {format_date_with_day(task.starts_at)} {format_time(task.starts_at)} - {format_time(task.ends_at)}"
        else:
            return f"Multi-Day Shift: {format_date_time(task.starts_at)} - {format_date_time(task.ends_at)}"
    elif task.type == HelperTaskType.DEADLINE:
        return f"Deadline: {format_date_with_day(task.deadline)} {format_time(task.deadline)}"
    else:
        return f"Start: {format_date_time(task.starts_at)} End: {format_date_time(task.ends_at)} Deadline: {format_date_time(task.deadline)}"


async def send_helper_task_helper_sign_up_confirmation(
    task: HelperTaskDto, member: MemberPublicInfoDto
):
    message = (
        EmailMessageBuilder()
        .to(member.full_name, member.email)
        .cc(task.contact.full_name, task.contact.email)
        .subject(f"YCC Task Sign Up Confirmation ({task.title}, ID: {task.id})")
        .reply_to(task.contact.full_name, task.contact.email)
        .content(
            f"""
<html>
<body>
Dear {member.full_name},
<p>
Thank you for signing up for the task as helper:

<ul>
  <li><a href="{get_helper_task_url(task)}">{task.title}</a>
  <li>{format_timing(task)}
  <li>Contact: {task.contact.full_name}, {task.contact.email}, {task.contact.cell_phone}
</ul>

If you cannot take your shift, please find a replacement.
<p>
HTML TEST
<p><strong>STRONG</strong> <em>EM</em> <u>U</u> <s>S</s> <a href="https://cern.ch">A</a>
<p>
<b>BOLD</b> <i>ITALIC</i> <u>UNDERLINE</u> <s>STRIKETHROUGH</s>
<p>
<span style="color: red;">RED</span> <span style="color: green;">GREEN</span> <span style="color: blue;">BLUE</span>
<p>
<span style = "font-size: 20px;">20px</span> <span style = "font-size: 30px;">30px</span> <span style = "font-size: 40px;">40px</span>
<p>
<span style = "font-family: Arial;">Arial</span> <span style = "font-family: Courier;">Courier</span> <span style = "font-family: Georgia;">Georgia</span>
<p>
<span style = "font-weight: bold;">BOLD</span> <span style = "font-style: italic;">ITALIC</span> <span style = "text-decoration: underline;">UNDERLINE</span>
<p>
Kind wishes,
YCC Maintenance & Surveillance Teams"""
        )
    )

    if task.captain:
        message.cc(task.captain.full_name, task.captain.email)

    async with SmtpConnection(CONFIG.email) as smtp:
        await smtp.send_message(message.build())


# def send_reminder_task(task):

#     task_title = task.title
#     task_start_date = task.starts_at
#     task_end_date = task.ends_at
#     task_deadline = task.deadline
#     task_short_description = task.short_description
#     task_long_description = task.long_description

#     captain = task.captain
#     crew = task.helpers

#     crew_list = ""
#     for i in range(0, len(crew)):
#         crew_list += (
#             crew[i].firstname
#             + " "
#             + crew[i].name
#             + ", Phone number: "
#             + crew[i].cell_phone
#             + " / "
#             + crew[i].work_phone
#             + "<br>"
#         )

#     import smtplib
#     from email.message import EmailMessage
#     from email.utils import make_msgid

#     msg = EmailMessage()
#     test_text = make_msgid()

#     for i in range(0, len(crew)):
#         helper = crew[i]

#         msg.set_content(
#             """\
#             <html>
#             <head></head>
#             <body>
#                 <p>Dear """
#             + helper.firstname
#             + """,<p>

#                 This is a reminder for the following task as crew: <p>

#                 &emsp; &emsp; Task: """
#             + task.title
#             + """ <br>
#                 &emsp; &emsp; Start: """
#             + task_start_date
#             + """ <br>
#                 &emsp; &emsp; End: """
#             + task_end_date
#             + """ </p>

#                 &emsp; &emsp; Captain: """
#             + captain.firstname
#             + """ """
#             + captain.name
#             + """ <br>
#                 &emsp; &emsp; Email: """
#             + captain.email
#             + """<br>
#                 &emsp; &emsp; Phone: """
#             + captain.cell_phone
#             + """ / """
#             + captain.work_phone
#             + """ <p>

#                 In case you are not available anymore to do this task, please find a replacement and then contact the Captain. <p>

#                 The YCC Maintenance Team <p>

#             </body>
#             </html>
#             """.format(
#                 test_text=test_text[1:-1]
#             ),
#             subtype="html",
#         )

#         msg["Subject"] = "YCC Task reminder"
#         msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#         msg["To"] = helper.email

#         s = smtplib.SMTP("smtp.gmail.com", 587)
#         s.starttls()
#         s.login("yccapptest", "")
#         s.send_message(msgcrew)
#         s.quit()

#     msg.set_content(
#         """\
#         <html>
#         <head></head>
#         <body>
#             <p>Dear """
#         + captain.firstname
#         + """,</p>

#             This is a reminder for the following task as Captain: <p>

#             &emsp; &emsp; Task: """
#         + task.title
#         + """ <br>
#             &emsp; &emsp; Start: """
#         + task_start_date
#         + """ <br>
#             &emsp; &emsp; End: """
#         + task_end_date
#         + """ </p>

#             Your crew for this task is: <br>
#             """
#         + crew_list
#         + """

#             <p> Thank you for coordinating this task!

#             The YCC Maintenance Team <p>

#         </body>
#         </html>
#         """.format(
#             test_text=test_text[1:-1]
#         ),
#         subtype="html",
#     )

#     msg["Subject"] = "YCC Task reminder"
#     msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#     msg["To"] = captain.email

#     s = smtplib.SMTP("smtp.gmail.com", 587)
#     s.starttls()
#     s.login("yccapptest", "")
#     s.send_message(msg)
#     s.quit()


# def send_reminder_surveillance(task):

#     task_title = task.title
#     task_start_date = task.starts_at
#     task_end_date = task.ends_at
#     task_deadline = task.deadline
#     task_short_description = task.short_description
#     task_long_description = task.long_description

#     captain = task.captain
#     crew = task.helpers

#     crew_list = ""
#     for i in range(0, len(crew)):
#         crew_list += (
#             crew[i].firstname
#             + " "
#             + crew[i].name
#             + "<br>"
#             + "Email: "
#             + crew[i].email
#             + "<br>"
#             + ", Phone number: "
#             + crew[i].cell_phone
#             + " / "
#             + crew[i].work_phone
#             + "<p>"
#         )

#     import smtplib
#     from email.message import EmailMessage
#     from email.utils import make_msgid

#     msg = EmailMessage()
#     test_text = make_msgid()

#     for i in range(0, len(crew)):
#         helper = crew[i]

#         msg.set_content(
#             """\
#             <html>
#             <head></head>
#             <body>
#                 <p>Dear """
#             + helper.firstname
#             + """,<p>

#                 This is a reminder for the following surveillance shift as crew: <p>

#                 &emsp; &emsp; Start: """
#             + task_start_date
#             + """ <br>
#                 &emsp; &emsp; End: """
#             + task_end_date
#             + """ </p>

#                 &emsp; &emsp; Captain: """
#             + captain.firstname
#             + """ """
#             + captain.name
#             + """ <br>
#                 &emsp; &emsp; Email: """
#             + captain.email
#             + """<br>
#                 &emsp; &emsp; Phone: """
#             + captain.cell_phone
#             + """ / """
#             + captain.work_phone
#             + """ <p>

#                 Please do not miss it and be in Port Choiseul at the mooring of the Q-boat in time! /p>

#                 In case you are not available anymore to do this task, please find a replacement and then contact the Captain. <p>

#                 The YCC Surveillance Team <p>

#             </body>
#             </html>
#             """.format(
#                 test_text=test_text[1:-1]
#             ),
#             subtype="html",
#         )

#         msg["Subject"] = "YCC Surveillance reminder"
#         msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#         msg["To"] = helper.email

#         s = smtplib.SMTP("smtp.gmail.com", 587)
#         s.starttls()
#         s.login("yccapptest", "")
#         s.send_message(msgcrew)
#         s.quit()

#     msg.set_content(
#         """\
#         <html>
#         <head></head>
#         <body>
#             <p>Dear """
#         + captain.firstname
#         + """,</p>

#             This is a reminder for the following surveillance shift as Captain: <p>

#             &emsp; &emsp; Start: """
#         + task_start_date
#         + """ <br>
#             &emsp; &emsp; End: """
#         + task_end_date
#         + """ </p>

#             Your crew for this surveillance shift is: <br>
#             """
#         + crew_list
#         + """

#             <p> Thank you!

#             The YCC Surveillance Team <p>

#         </body>
#         </html>
#         """.format(
#             test_text=test_text[1:-1]
#         ),
#         subtype="html",
#     )

#     msg["Subject"] = "YCC Surveillance reminder"
#     msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#     msg["To"] = captain.email

#     s = smtplib.SMTP("smtp.gmail.com", 587)
#     s.starttls()
#     s.login("yccapptest", "")
#     s.send_message(msg)
#     s.quit()


# def send_task_marked_as_done(task):

#     task_title = task.title

#     captain = task.captain
#     crew = task.helpers

#     names_list = []
#     emails_list = []
#     names_list.append(captain.firstname)
#     emails_list.append(captain.email)
#     for i in range(0, len(crew)):
#         names_list.append(crew[i].firstname)
#         emails_list.append(crew[i].email)

#     import smtplib
#     from email.message import EmailMessage
#     from email.utils import make_msgid

#     for i in range(0, len(names_list)):

#         msg = EmailMessage()
#         test_text = make_msgid()

#         msg.set_content(
#             """\
#                 <html>
#                 <head></head>
#                 <body>
#                     <p>Dear """
#             + names_list[i]
#             + """, <p>

#                     Thank you for your help with the task: """
#             + task_title
#             + """  <br>
#                     This task has been marked as completed. <p>

#                     The YCC Maintenance Team</p>

#                 </body>
#                 </html>
#                 """.format(
#                 test_text=test_text[1:-1]
#             ),
#             subtype="html",
#         )

#         msg["Subject"] = "YCC Task completed"
#         msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#         msg["To"] = emails_list[i]

#         s = smtplib.SMTP("smtp.gmail.com", 587)
#         s.starttls()
#         s.login("yccapptest", "")
#         s.send_message(msg)
#         s.quit()


# def send_modification_update(old_task, new_task):

#     old_task_title = old_task.title

#     new_task_title = new_task.title
#     new_task_start_date = new_task.starts_at
#     new_task_deadline = new_task.deadline
#     new_task_long_description = new_task.long_description

#     captain = new_task.captain
#     crew = new_task.helpers

#     names_list = []
#     emails_list = []
#     names_list.append(captain.firstname)
#     emails_list.append(captain.email)
#     for i in range(0, len(crew)):
#         names_list.append(crew[i].firstname)
#         emails_list.append(crew[i].email)

#     crew_list = ""
#     for i in range(0, len(crew)):
#         crew_list += (
#             crew[i].firstname
#             + " "
#             + crew[i].name
#             + ", Phone number: "
#             + crew[i].cell_phone
#             + " / "
#             + crew[i].work_phone
#             + "<br>"
#         )

#     import smtplib
#     from email.message import EmailMessage
#     from email.utils import make_msgid

#     for i in range(0, len(names_list)):

#         msg = EmailMessage()
#         test_text = make_msgid()

#         msg.set_content(
#             """\
#                 <html>
#                 <head></head>
#                 <body>
#                     <p>Dear """
#             + names_list[i]
#             + """, <p>

#                     The task """
#             + old_task_title
#             + """, in which you are enrolled in, has been updated. Please find below the updated details:  <p>

#                     &emsp; &emsp; Title: """
#             + new_task_title
#             + """ <br>
#                     &emsp; &emsp; Start date: """
#             + new_task_start_date
#             + """ <br>
#                     &emsp; &emsp; Deadline: """
#             + new_task_deadline
#             + """ </p>

#                     &emsp; &emsp; Deascription """
#             + new_task_long_description
#             + """ </p>

#                     &emsp; &emsp; Captain: """
#             + captain.firstname
#             + """ """
#             + captain.name
#             + """ <br>
#                     &emsp; &emsp; Email: """
#             + captain.email
#             + """<br>
#                     &emsp; &emsp; Phone: """
#             + captain.cell_phone
#             + """ / """
#             + captain.work_phone
#             + """ <p>

#                     Crew: <br>
#                     """
#             + crew_list
#             + """

#                     Thank you again for helping with this task!
#                     The YCC Maintenance Team</p>

#                 </body>
#                 </html>
#                 """.format(
#                 test_text=test_text[1:-1]
#             ),
#             subtype="html",
#         )

#         msg["Subject"] = "YCC Task completed"
#         msg["From"] = "ycc-noreply@cern.ch"  # ycc-noreply@cern.ch
#         msg["To"] = emails_list[i]

#         s = smtplib.SMTP("smtp.gmail.com", 587)
#         s.starttls()
#         s.login("yccapptest", "")
#         s.send_message(msg)
#         s.quit()
