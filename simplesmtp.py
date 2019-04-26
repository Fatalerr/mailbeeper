# -*- coding: utf-8 -*-
"""Module for send the mail and attachements with the SMTP server.

"""
import os,re,logging
import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.header import Header 
from email import Encoders

logger = logging.getLogger('ezmail.smtp')
#logger.setLevel('INFO')

MAIL_FORMAT = {'text' : MIMEText, 'multipart': MIMEMultipart }

class SMTPLoginFailure(Exception):
    pass

class SMTPServer(object):
    """Mail SMTP Server is used to fetch mails.
    parameters:
       host   host url 
       user     username
       
    server = SMTPServer(host='smtp.163.com',user='gdgprs')
    server.set_password('xxxx')

    server.send_mail()
    """      

    def __init__(self,host=None,user=None,password=None,account=None):
        self.host = host
        self.user = user
        self.password = password
        self.connection = None
        
        if account:
            self.init(account)

    def init(self,account):
        self.from_name = account.description
        self.host = account.smtp
        self.user = account.username
        self.password = account.decrypt_password()

    def connect(self,host=None,user=None,password=None):
        host = host or (not host and self.host)
        user = user or (not user and self.user)
        password = password or (not password and self.password)

        if not password:
            import getpass
            password = getpass.getpass("Input the password for the user %s:" % self.user)
        logger.debug("Connecting to SMTP Server:%s with user:%s passwd:%s**" % (host,user,password[:3]))
        try:
            self.connection = smtplib.SMTP_SSL(host)
            self.connection.login(user,password)
        except Exception,e:
            logger.critical(" Error happen in connect server:%s" % e)
            raise SMTPLoginFailure,e
            
        logger.info("Connected to SMTPServer!")
        
        return self.connection

    def sendmail(self,to_addrs,msg,**kwargs):
        if not self.connection:
            self.connect()

        self.connection.sendmail(self.user,to_addrs,msg)

class MailCreator(object):
    def __init__(self,mailformat="multipart"):
        if mailformat in MAIL_FORMAT:
            self.msg = MAIL_FORMAT[mailformat]()
        else:
            print "Mail format: %s is not supported, MIMEMultipart was used." % mailformat
            self.msg = MIMEMultipart()

    def add_field(self,field,value):
        self.msg[field] = value
        #sender,to_addrs,cc_addrs,attachements=None

    def add_attachments(self,attached_filenames):
        pass

    def attach(self,type_,part,**kwargs):
        content = MAIL_FORMAT[type_]
        self.msg.attach(content(part),**kwargs)

    def create(self):
        return self.msg

    def as_string(self):
        return self.msg.as_string()

if __name__ == "__main__":

    server = SMTPServer()
    server.host = 'smtp.163.com'
    server.user = 'test@163.com'
    server.password = "password"
    server.from_name = "PSChecker <test@163.com>"
    # msg = MIMEText("This mail is send by Python SMTP sendmail text 1",'plain')
    # msg['From'] = "Robert <%s>" % server.user
    # msg['To'] = 'whom@fake.com'
    # msg['Subject'] = Header("Python SMTP txt1",'utf-8')
    msg = MailCreator()
    msg.add_field('From', server.from_name)
    msg.add_field('To','whom@fake.com')
    msg.add_field('Subject',"Hello from python smtp!")

    server.connect()
    server.sendmail(['whom@fake.com'],msg.as_string())    