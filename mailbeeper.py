#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MailBeeper can fetch and parse the mails from the mail server,then take 
actions according to the commands specified in the SUBJECT.

Author: jun1.liu@nokia.com

Usage: 
    mailbeeper <email_account> [delete]
    
Args:
   email_account,   a email account name which defined in an account file.
                    the account file was specified in 'mailbeeper.conf'
   
   delete,          delete the message in email server.
   
"""
import re,logging
from time import sleep
from configobject import ConfigObject
from netaccount import AccountFile
from ezmail import init_mail_server,MailMessage,POPLoginFailure
from messagelogger import MessageLogger
from actions import select_action_by_subject

CONFIG = ConfigObject('mailbeeper.conf')
logfile = CONFIG.get('logfile','/tmp/mailbeeper.log')

#initilize the root logger
root_logger = MessageLogger()
root_logger.setLevel(CONFIG.get('logging_level','INFO'))
#initilize the applicaiton logger
logger = MessageLogger('MailBeeper')
logger.addFileHandler(logfile,root=True)
#logger.setLevel('DEBUG')

SENDMAIL_INTERVAL = CONFIG.get('sendmail_interval', 5)

def after_work():
    logger.info("mailbeeper sleep...zzzzz\n")

def parse_subject(cmdstr):
    pattern_cmd = re.compile("\[\w+\](\w+):.*")
    pattern_smtchk = re.compile("(check_n[g|s]_tn.ckl)")

    result = pattern_smtchk.search(cmdstr)
    if result:
        return 'smartcheck'

    result = pattern_cmd.search(cmdstr)
    if not result:
        logger.error("Can't recognize the ACTION name in subject:%s" % cmdstr)
        return ''

    return result.groups()[0].lower()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print __doc__
        exit(1)
        
    accounts_file = AccountFile('account_info.yml')
    account_name = sys.argv[1]
    account = accounts_file.account(account_name)

    popsrv = init_mail_server('POP3',account)

    try:
        msgids = popsrv.search_messages()
    except POPLoginFailure,e:
        print "Login failure."
        sys.exit(1)

    if len(sys.argv) == 3 and sys.argv[2] == 'delete':
        popsrv.delete_messages(msgids)
        sys.exit(0)
        
    processed_msgid=[]
    for mid,msgtxt in popsrv.fetch_messages(msgids,with_msgid=True):
        msg = MailMessage(msgtxt)
        from_addr = msg.get_addr('from')
        logger.info("Processing the msgID:%s, From:%s, Subject:%s" % (mid,from_addr,msg.subject))
        

        #parse the subject and execute the command in subject.
        logger.info("Parsing the subject and select the right ACTION and parameters...")
        #action_name = parse_subject(msg.subject)
        action_name, action_class = select_action_by_subject(msg.subject)

        if not action_name:
            logging.info("No action match the subject, Ignore this message.")
            continue
        else:
            action = action_class(msg)

        logger.info("Start to execute the ACTION:%s" % (action.name))
        try:
            result = action.run()
            if result == 'Failed':
                logger.error("Action run with Failed status")
                continue
            
            logger.info("Sending the report to %s" % from_addr)
            result = action.send_report(account=account)
            logger.info("%s on sending the report" % result)

            logger.info("Finish the execution of ACTION: %s, status: %s" % (action.name,result))
            processed_msgid.append(mid)
        except Exception,e:
            logger.error("Failed on executing ACTION:%s, error:%s" % (action_name,e))

        sleep(SENDMAIL_INTERVAL)

    popsrv.delete_messages(processed_msgid)
    after_work()
