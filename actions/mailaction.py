# -*- coding: utf-8 -*-
"""
"""
import os,re
from collections import OrderedDict
from commands import getstatusoutput

def execute_cmd(cmd,todir=None,shell=False):
    if todir:
        cmd = "cd %s;%s" % (os.path.abspath(todir), cmd)

    status,output = getstatusoutput(cmd)

    return status,output

class MailAction(object):
    """the base Calss for executing actions specified by the mail.
    """
    name = 'MailAction'
    subject_pattern = re.compile("None")
    actions = []

    def __init__(self,mail,**kwargs):
        self.mail = mail
        self.args = {}
        self.results = OrderedDict()

        for key,value in kwargs.items():
            self.__dict__[key] = value

    @classmethod
    def parse_subject(cls,subject):
        """parse the subject and return the result and the command and args.
        """
        result = cls.subject_pattern.search(subject)
        return result

    def do_actions(self,args,actioname_list=None):
        if not actioname_list:
            actioname_list = self.actions

        actions_completed = True
        for action in actioname_list:
            _result = getattr(self,action)(args)
            self.results[action] = _result
            if _result == 'Failed':
                actions_completed=False
                break

        return actions_completed and "Success" or 'Failed'
       
    def run(self):
        print "running: %s with parameter" % self.__class__.__name__
        print "parameters:",self.__dict__

        return "Success!"

class EmptyAction(MailAction):
    name = 'EmptyAction'
    pass