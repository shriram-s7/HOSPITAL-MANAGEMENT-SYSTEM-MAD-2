import os
from celery import Celery
from celery.schedules import crontab
from app import create_app
from models import db, User, Appointment, Treatment
import io
import csv
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'hospitalmanagementsystem79@gmail.com'
SENDER_PASSWORD = os.environ.get("HMS_SENDER_PASSWORD", "")

def send_email(to_email, subject, body_html, attachment_name=None, attachment_data=None):
    if not to_email:
        print(f"Skipping email: no recipient address provided.")
        return
        
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_html, 'html'))
    
    if attachment_name and attachment_data:
        part = MIMEApplication(attachment_data, Name=attachment_name)
        part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
        msg.attach(part)
        
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        clean_password = SENDER_PASSWORD.replace(" ", "")
        server.login(SENDER_EMAIL, clean_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")

flask_app = create_app()

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(flask_app)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        daily_reminders.s(),
        name='daily-reminders-8am'
    )
    sender.add_periodic_task(
        crontab(hour=8, minute=0, day_of_month=1),
        monthly_report.s(),
        name='monthly-report-1st'
    )

@celery.task
def daily_reminders():
    today = datetime.date.today()
    apps = Appointment.query.filter_by(date=today, status='Booked').all()
    if not apps:
        print(f"No appointments today ({today}), no reminders to send.")
        return
    for app in apps:
        recipient = 'hospitalmanagementsystem79@gmail.com'
        body = f"<h3>Appointment Reminder</h3><p>Dear {app.patient.username},</p><p>You have an appointment today with <b>Dr. {app.doctor.username}</b> at <b>{app.time}</b>.</p><p>Please be sure to visit the hospital on time.</p>"
        send_email(to_email=recipient, subject=f'HMS Reminder: {app.patient.username} â†’ Dr. {app.doctor.username}', body_html=body)
        print(f"Reminder sent for {app.patient.username} â†’ Dr. {app.doctor.username} at {app.time}")

@celery.task
def monthly_report():
    doctors = User.query.filter_by(role='Doctor').all()
    today = datetime.date.today()
    start_date = datetime.date(today.year, today.month, 1)
    
    for doc in doctors:
        if not doc.email: continue
        
        apps = Appointment.query.filter(Appointment.doctor_id == doc.id, Appointment.date >= start_date).all()
        html = f"<h2>HMS Monthly Activity Report: {today.strftime('%B %Y')}</h2>"
        html += f"<p>Doctor: <b>{doc.username}</b> ({doc.email})</p>"
        html += "<table border='1' cellpadding='10' cellspacing='0'><tr><th>Date</th><th>Patient</th><th>Status</th><th>Diagnosis</th><th>Treatment Prescribed</th></tr>"
        
        for a in apps:
            diag = a.treatment.diagnosis if a.treatment else 'N/A'
            pres = a.treatment.prescription if a.treatment else 'N/A'
            html += f"<tr><td>{a.date}</td><td>{a.patient.username}</td><td>{a.status}</td><td>{diag}</td><td>{pres}</td></tr>"
            
        html += "</table><br><p>Thank you for your service this month.</p>"
        recipient = 'hospitalmanagementsystem79@gmail.com'
        send_email(to_email=recipient, subject=f'HMS - Monthly Activity Report: {today.strftime("%B %Y")}', body_html=html)
        print(f"Monthly report sent to {recipient} for Dr. {doc.username}")

@celery.task
def export_csv_job(user_id):
    user = User.query.get(user_id)
    apps = Appointment.query.filter_by(patient_id=user_id, status='Completed').all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['User ID', 'Username', 'Consulting Doctor', 'Appointment Date', 'Diagnosis', 'Treatment', 'Next Visit'])
    for a in apps:
        cw.writerow([
            user_id, 
            user.username, 
            a.doctor.username, 
            a.date.strftime('%Y-%m-%d'), 
            a.treatment.diagnosis if a.treatment else '', 
            a.treatment.prescription if a.treatment else '',
            a.treatment.notes if a.treatment else ''
        ])
    
    csv_content = si.getvalue()
    target_email = 'hospitalmanagementsystem79@gmail.com'
    
    body = f"<p>Dear {user.username},</p><p>Please find attached the complete log of your medical treatments and consultation history.</p><p>This export was requested by you from the HMS Patient Dashboard.</p>"
    send_email(
        to_email=target_email,
        subject='HMS - Your Treatment History CSV Export',
        body_html=body,
        attachment_name='treatment_history.csv',
        attachment_data=csv_content.encode('utf-8')
    )
    print(f"Export CSV sent to {target_email} for patient {user.username}.")
    return "Done"
