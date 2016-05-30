# -*- coding: utf-8 -*-
"""
"""
import os,re,logging
from configobject import ConfigObject
from ezmail import ReplyMail
from logarchiver import decompress_archived_files, compress_to_zipfile
from mailaction import MailAction, execute_cmd

CONFIG = ConfigObject('mailbeeper.conf')
logger = logging.getLogger('MailBeeper.smartcheck')


TEMPDIR = {
    'attachments' : "attachments/",
    'logfiles'    : "logfiles/",
    'reports'     : "reports/",
    }

REPORT_NAME = CONFIG.get('report_filename','R:/report.zip')
TEMPDIR = CONFIG.get('temp_dir',TEMPDIR)

def clearn_tempfiles(tempdirs=None,tempfiles=None):
    "Clean all the temporary directories before the work."
    if tempdirs:
        for name,tmpdir in tempdirs.items():
            status, _ = execute_cmd("rm -rf %s/*" % tmpdir)
            if status !=0:
                logger.error("Error happened when clearn the temp dir: %s" % tmpdir)

    if tempfiles:
        for filename in tempfiles:
            status, _ = execute_cmd("rm -rf %s" % filename)

    logger.info("clean_tempfiles: Temporary directories had been cleaned.")
    return

def extract_attachments(mail,tempdir):
    """extract the attachments to temporary attachments directory"""
    logger.info("Extract the attachments...")

    logger.debug("Clean the temporary directories...")
    clearn_tempfiles(tempdir)

    if mail.attached_data:
        logger.info("Save the attachments to %s" % tempdir['attachments'])
        mail.save_attachments(todir=tempdir['attachments'])
    else:
        logger.info("No attachment found.")
        return False

    logger.debug("decompress the attachments files to logfiles directory.")
    decompress_archived_files(tempdir['attachments'],tempdir['logfiles'])
    #logger.info("Extract the log files to %s" % tempdir['logfiles']) 
    
    return True
   
class Action(MailAction):
    name = 'SmartChecker'
    subject_pattern = re.compile("(check_n[g|s]_tn.ckl)")

    actions = ['check_log','reports_handler']
    reply_content ="""\
    Log files analysis completed. Please check the attached report.

    below reports were generated:
    
%(_completed_reports)s


    ..Smartchecker..
    """

    def check_log(self,args):
        """check the logfile"""
        os.chdir("/home/smartchecker/smtchk")
        cmdstr = "/home/smartchecker/smtchk/smartchecker.py -r %(checklist)s %(logfiles)s --saveto=%(reports)s -l"
        logger.info("Running `check_log` command: " + cmdstr % args)
        
        status, output = execute_cmd(cmdstr % args)
        if status !=0:
            logger.error("Running `check_log` failed! ErrorMsg:%s" % output)
            return "Failed"            
        else:
            _code, report_files = execute_cmd("ls %s" % args['reports'])
            if _code == 0:
                self._completed_reports = report_files
            return "Success"

    def reports_handler(self,args):
        ## zip the reports and sendback to user
        report_zipfile = REPORT_NAME
        if os.path.exists(report_zipfile):
            logger.debug("remvoe the old reports.zip file.")
            clearn_tempfiles(tempfiles=[report_zipfile])
        try:
            result = compress_to_zipfile(args['reports'],report_zipfile)
            self.attachment_files=[report_zipfile]
        except Exception, e:
            logger.error("Report handler error: %s" % e)
            return "Failed"

        return "Success"

    def send_report(self,account=None,smtp=None):
        msg=ReplyMail(self.mail,from_name=self.name)
        msg.set_body(text_body=self.reply_content % self.__dict__)
        msg.set_subject("Check Report for %s " % self.args['checklist'])

        for filename in self.attachment_files:
            msg.add_attachment(filename)

        r = msg.send(account=account,smtpserver=smtp)
        
        return r and "Success" or 'Failed'
        #return 'Success' if r else 'Failed'

    def run(self):
        """run the necessary actions"""
        args = {}
        extract_attachments(self.mail,TEMPDIR)
        args['checklist'] = self.parse_subject(self.mail.subject).groups()[0]
        args['logfiles'] = TEMPDIR['logfiles']
        args['reports'] = TEMPDIR['reports']
        self.args = args
        
        logger.debug('Do the actions: %s' % self.actions)
        result=self.do_actions(args,self.actions)
        logger.debug("all actions done.")

        # result = self.check_log(args) 
        # if result != 'Success':
        #     return result

        # result = self.reports_handler(args)

        return result


if __name__ == "__main__":
    action = Action()
