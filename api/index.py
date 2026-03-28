from app import create_app, MailTM

mail_client = MailTM()
app = create_app(mail_client)
