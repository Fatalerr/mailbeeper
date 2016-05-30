# -*- coding: utf-8 -*-
"""collect the config log and extract the data.
"""
import logging,re
from mailaction import MailAction

logger=logging.getLogger('MailBeeper.configcollect')

class Action(MailAction):
    name = 'ConfigCollect'
    subject_pattern = re.compile("\[\w+\](config):.*")

    def run(self):
        logger.info("I'm collecting the config")

        return 'Success'
