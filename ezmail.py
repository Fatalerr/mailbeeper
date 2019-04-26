# -*- coding: utf-8 -*-
"""This module simplize receiving the mails and attachements from the mail server.

Usage:
   from ezmail import init_mail_server, ReplyMail
   from netaccount import account

   account = AccountFile('accounts_info.yml').account(account_name)

   popsrv = init_mail_server('POP3',account)
   msgids = popsrv.search_messages()
   for msg in popsrv.fetch_messages(msgids):
        mail=MailMessage(msg)
        replymail = ReplyMail(mail)
        replymail.set_subject("a brand new python module")
        replyMail.add_to_addr('Mr Zhang')

        smtpsrv = init_mail_server('SMTP',account)

        result = replymail.send(smtpsrv)
"""
import logging
from simplepop3 import POPServer, MailMessage,POPLoginFailure
from simplesmtp import SMTPServer, MailCreator,SMTPLoginFailure
from envelopes import Envelope
from envelopes import SMTP as ezSMTP

SERVER_TYPE = {'POP3': POPServer, 'SMTP': SMTPServer,'ezSMTP': ezSMTP }

logger = logging.getLogger('ezmail')
#logger.setLevel('INFO')

class LoginFailure(Exception):
    pass

class ReplyMail(object):
    """An Envelope Object wrapper used to reply a mail easily. 
    """
    def __init__(self,orimail,from_name=None,charset='utf-8'):
        self.charset=charset

        from_addr = orimail.get_addr('to')[0]
        to_addr = orimail.get_addr('from')
        cc_addr = orimail.get_addr('cc')

        if not from_name:
            from_name = from_addr

        self.envelope = Envelope(
            from_addr = (from_addr,from_name),
            to_addr  = to_addr,
            subject = "RE:" + orimail.subject,
            )

        self.add_addr(cc_addr=cc_addr)

    def add_attachment(self,attfile):
        self.envelope.add_attachment(attfile)

    def set_subject(self,subject):
        self.envelope._subject = subject

    def set_body(self, text_body=None, html_body=None,charset='utf-8'):
        if text_body:
            self.envelope._parts.append(('text/plain', text_body, charset))

        if html_body:
            self.envelope._parts.append(('text/html', html_body, charset))

    def add_addr(self,to_addr=None,cc_addr=None,bcc_addr=None):
        if to_addr:
            for addr in to_addr:
                self.envelope.add_to_addr(addr)
        if cc_addr:
            for addr in cc_addr:
                self.envelope.add_cc_addr(addr)
        if bcc_addr:
            for addr in bcc_addr:
                self.envelope.add_bcc_addr(addr)

    def send(self,smtpserver=None,account=None):
        if smtpserver:
            smtpserver.send(self.msg)
        elif account:
            self.envelope.send(account.smtp,login=account.username,password=account.decrypt_password())
        else:
            logger.error("A SMTP server or mail account must be provided!.")
            return False

        return True

    def __repr__(self):
        return self.envelope.__repr__

def init_mail_server(server_type,account):
    if server_type not in SERVER_TYPE:
        logger.error("No such server type: %s" % server_type)
        sys.exit(1)

    # if server_type == 'ezSMTP':
    #     server = ezSMTP(host=account.smtp,  )
    server = SERVER_TYPE[server_type](account=account)

    return server

