# -*- coding: utf-8 -*-
"""
"""
import smartcheck
import configcollect
import logging

logger = logging.getLogger('Action.init')

AVAIABLE_ACTIONS = {
    'smartcheck' : smartcheck.Action,
    'configinfo' : configcollect.Action,
}

def select_action_by_subject(subject):
    """select the right action accodrding to subject
    """
    for name,action_class in AVAIABLE_ACTIONS.items():
        r = action_class.parse_subject(subject)
        if r:
            logger.debug("Subject matched the action:%s, result: %s" % (name,r.groups()))
            return name, action_class

    return None,None