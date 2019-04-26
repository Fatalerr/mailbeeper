# -*- coding: utf-8 -*-
"""Module for receiving the mails and attachements from the mail server.

"""
import poplib
import email
import base64
import re,os,logging
from email.Header import decode_header

logger = logging.getLogger('ezmail.pop3')
#logger.setLevel('INFO')

DEFAULT_ENCODING = 'gbk'
MAIL_DELIMITER = "---MAIL---"

def _save_msg(msgtxts,filename):
    with open(filename,'a+') as fp:
        for msg in msgtxts:
            fp.write('\n%s\n' % MAIL_DELIMITER)
            fp.write(msg)
    logger.info('save msg to file.')

def to_unicode(msg,encoding=None):
    if encoding:
        return unicode(msg,encoding)
    else:
        return unicode(msg,DEFAULT_ENCODING)
        #return msg.decode('utf-8')

def read_blocks(lines,delimiter=None):
    if not delimiter:
        delimiter=MAIL_DELIMITER
        
    msg = []
    msgblock = []
    start_flag = False
    for line in lines:
        if line.startswith(delimiter):
            if not start_flag:
                start_flag = True
                continue
            else:
                msg.append("".join(msgblock))
                msgblock = []
        else:
            msgblock.append(line)
            
    #add the last msgblock        
    msg.append("".join(msgblock))
    return msg

class POPLoginFailure(Exception):
    pass

class MailMessage(object):
    def __init__(self,msgobj, msgid=None,header_only=False):
        self.msgobj    = msgobj
        self.cclist    = msgobj.get('cc',None)
        self.tolist    = self.get_content('to')
        self.msgid     = msgid

        self.subject = self.get_content('subject')
        self.body = self.get_body()
        
        if not header_only:
            self.attached_data = self.get_attachments()       
        #self.attached_filenames = [data['filename'] for data in self.attached_data]
        
    def get_content(self,key):
        contents = []
        for cnt,encode in decode_header(self.msgobj[key]):
            contents.append(to_unicode(cnt,encode))
            
        return " ".join(contents)
    
    def info(self,key):
        """return the decode info of the key
        """
        return self.get_content(key)
    
    def msginfo(self,**kwargs):
        _info = {}
        _info.update(kwargs)

        _info['from_addr'] = self.get_addr('from')
        _info['to_addr'] = self.get_addr('to')
        _info['cc_addr'] = self.get_addr('cc')
        _info['attachment_files'] = self.attached_data.keys()

        return _info

    def get_addr(self,key):
        """return the email address from contents
        """
        contents = self.msgobj.get(key,'')
        address = re.findall("<(\S+@\S+)>",contents)
        return address
    
    def get_body(self,msgobj=None):
        msgobj = msgobj or (not msgobj and self.msgobj)
        
        return None
        
    def get_attachments(self,msgobj=None):
        msgobj = msgobj or (not msgobj and self.msgobj)
            
        attached_files = {}
        for part in msgobj.walk():
            content_type = part.get_content_type()
            filename = part.get_filename()
            logger.debug("get_attachments: filename:%s, type:%s" % (filename,content_type))
            if filename and content_type.startswith('application'):
                payload = base64.decodestring(part.get_payload())
                attached_files[filename]=payload

        return attached_files
 
    def save_attachments(self,todir="./",filenames=None,content_type='application'):
        if not filenames:
            filenames = self.attached_data.keys()
            
        for filename in filenames:
            payload = self.attached_data[filename]
            pathfilename = os.path.join(todir,filename)
            with open(pathfilename,'wb') as fp:
                fp.write(payload)
            logger.debug("Save attachment to: %s" % pathfilename)
            
    def __repr__(self):
        #return u"MailMessage(from:%s, subject:%s)" % (self.get_addr('from'),self.info('subject'))
        return unicode("MailMessage(subject:%s)" % self.get_content('subject'),'utf-8')

class MailReceiver(object):
    """Receive the mails from multi sources. POP3 server or files
    """
    def connect(self):
        "Connect to the server or file"
        pass

    def get_msgseq(self):
        """Return the  message id range.
        """
        pass

    def search_messages(self,mfilter):
        """return the message IDs which match the mfilter.
        only below fields in message header are support:

        subject, from, cc

        search_messages(subject="smartcheck.*")

        """
        for mid in self.msgid:
            pass

    def fetch_messages(self,msgid_list):
        pass
    

class MailFiler(MailReceiver):
    """This class is used to read mails from a file.
    """
    delimiter_pattrn = re.compile("---MAIL---")
    def __init__(self,filename=None):
        self.filename = filename
        self.msgtxts = None
        self.msgseq_list = []

        if filename:
            self.connect(filename)

    def connect(self,filename=None):
        if not filename:
            filename = self.filename
        self.connection = file(filename)
        
        mailines = self.connection.readlines()
        self.flatmsg_blocks=read_blocks(mailines)
        self.msgseq_list = range(len(self.flatmsg_blocks))
        return self.connection

    def search_messages(self, **kwargs):
        """return the a list of the msg_id which match the mfilter.
        """    
        filtered_msgseq = []
#        self.connection.seek(0)

        for msgseq in self.get_msgseq():
            msgblock = self.flatmsg_blocks[msgseq]
            msg=MailMessage(email.message_from_string(msgblock),header_only=True)
            _result = [re.search(value,msg.info(key)) is not None for key,value in kwargs.items()]
            if sum(_result) == len(_result): #all values are True
                filtered_msgseq.append(msgseq)

        return filtered_msgseq
        
    def generate_rawmsg(self):
        pass

    def get_msgseq(self):
        """Return the seq range of the mails. [0,1,2...]
        """
        return self.msgseq_list
        
    def fetch_messages(self,msgid_list):
        if not self.connection:
            self.connect()
            
        msgs = [email.message_from_string(txt) for txt in self.flatmsg_blocks]
        if msgid_list:
            return [msgs[idx] for idx in msgid_list]
        else:
            return msgs        

class POPServer(MailReceiver):
    """Mail POP Server is used to fetch mails.
    parameters:
       host   host url 
       user     username
       
    server = POPServer(host='pop3.163.com',user='tester')
    server.set_password('xxxx')
    messages = server.fetch_mails()

    for msg in messages:
        print mail.subject
        print mail.body
        if mail.attachements:
            print mail.attachemen
    """      

    def __init__(self,host=None,user=None,password=None,account=None):
        self.host = host
        self.user = user
        self.password = password
        self.connection = None
        self.msgseq_list = None
        
        if account:
            self.init(account)

    def init(self,account):
        self.host = account.pop3
        self.user = account.username
        self.password = account.decrypt_password()

    def connect(self,host=None,user=None,password=None):
        host = host or (not host and self.host)
        user = user or (not user and self.user)
        password = password or (not password and self.password)

        if not password:
            import getpass
            password = getpass.getpass("Input the password for the user %s:" % self.user)
        logger.debug("Connecting to POP Server:%s with user:%s passwd:%s**" % (host,user,password[:3]))
        try:
            self.connection = poplib.POP3_SSL(host)
            self.connection.user(user)
            self.connection.pass_(password)
        except Exception,e:
            logger.critical(" Error happen in connect server:%s" % e)
            raise POPLoginFailure,e
            
        logger.info(self.connection.getwelcome())
        
        return self.connection


    def get_msgseq(self):
        if not self.connection:
            self.connect()
            
        mcounter, _size = self.connection.stat()
        logger.info("You got %s mails" % mcounter)
        self.msgseq_list = range(1,mcounter +1)
        
        return self.msgseq_list
        
    def close(self):
        """Close the POP connection to SERVER or FILE
        """
        if isinstance(self.connection,file):
            self.connection.close()
        else:
            self.connection.quit()

    def fetch_messages(self,msgid_list=None,with_msgid=False):
        if not self.connection:
            self.connect()
        
        logger.debug("fetching messages with 'msgid_list':%s" % msgid_list)    
        msg_generator = self.get_rawmsg_from_pop(msgid_list)
        if with_msgid:
            msgs = ((msgid,email.message_from_string(txt)) for msgid,txt in msg_generator)
        else:
            msgs = (email.message_from_string(txt) for msgid,txt in msg_generator)
        
        return msgs

    
    def save_rawmsg(self,filename,seq=None):
        if not self.connection:
            self.connect_server()
        
        msgid,_rawmsg = self.get_rawmsg_from_pop()
        if seq:
            rawmsg = [_rawmsg[seq]]
        else:
            rawmsg = _rawmsg
            
        _save_msg(rawmsg,filename)
            
    def search_messages(self, **kwargs):
        """return the a list of the msg_id which match the mfilter.
        """   

        filtered_msgid = []

        for msgid in self.get_msgseq():
            _resp,header,_size = self.connection.top(msgid,0)
            msg=MailMessage(email.message_from_string("\n".join(header)),header_only=True)
            _result = [re.search(value,msg.info(key)) is not None for key,value in kwargs.items()]
            if sum(_result) == len(_result): #all values are True
                filtered_msgid.append(msgid)

        return filtered_msgid
            
            
    def get_rawmsg_from_pop(self,msgid_list=None):        
        """A generator fetching the mail messages from server
        if msgid is not provided, all messages were fetched.
        """
        if not msgid_list:
            msgid_list=self.get_msgseq()
        
        #Generator for reading mail from server.
        for msgid in msgid_list:
            logger.debug("fetching the mail content wiht msgid:%s" % msgid)
            mobj = self.connection.retr(msgid)
            yield msgid,"\n".join(mobj[1])

    def delete_messages(self,msgid):
        """Delete the msgids. msgids can be a messageID or a list.
        """
        msgid_list = None
        if isinstance(msgid,list):
            msgid_list = msgid
        else:
            msgid_list = [msgid]

        #print "msgid_list:",msgid_list
        for msgid in msgid_list:
            logger.info("Deleting msgid: %s" % msgid)
            self.connection.dele(msgid)

def get_mails_from(source,**mfilters):
    """A generator get mails which match the mfilter from the server or mailfile.
    
    """
    if isinstance(source,POPServer):
        popsrv = source
    elif isinstance(source,str):
        popsrv=POPServer()
        popsrv.connect_file(source)
    else:
        return
    
    #print "filters:",mfilters
    if mfilters:
        msgseq_list = popsrv.search_messages(**mfilters)
    else:
        msgseq_list = None
    
    logger.debug("msg seq: %s" % msgseq_list)
    
    for msgtxt in popsrv.fetch_messages(msgseq_list):
        yield MailMessage(msgtxt)
        
    #return [MailMessage(msg) for msg in popsrv.fetch_messages()]
    
if __name__ == "__main__":
    import sys
    
    #print "logging level:",logger.getLevel()
    if len(sys.argv)==3:
        logger.setLevel(sys.argv[2])
                
    if sys.argv[1] == "server":
        server = POPServer()
        server.host = 'pop3.163.com'
        server.user = 'test@163.com'
        server.password = "test"
    else:
        server=MailFiler(sys.argv[1])

    msgids=server.search_messages(subject="MME")
    print "found matched msgid:",msgids

    print "fetching message.."

    for msg in server.fetch_messages(msgids):
        m = MailMessage(msg)

        print "From:", m.info('from')
        print "subject:",m.info('subject')
        if m.attached_data:
            print "m.attached_filenames:",m.attached_data.keys()
            for fname,payload in m.attached_data.items():
                print fname
        print "-"*78
        


