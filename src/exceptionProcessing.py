#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Processing of exceptions with lisa. """

import logging
logger = logging.getLogger(__name__)
#print '__name__ = ', __name__
#logger = logging.getLogger()


import traceback
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

logging.debug('Test logování')


def reportException(exception):
    try:
        excstr = traceback.format_exc()
        sendMail(excstr, 'Lisa exception: ' + str(exception))
    except Exception as e:
        print traceback.format_exc()
        print str(e)
        print "Problems with sending exception report"


def sendMail(mailcontent, subject='None'):
    me = 'mjirik@kky.zcu.cz'
    you = 'miroslav.jirik@gmail.com'

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
#fp = open(textfile, 'rb')
## Create a text/plain message
    msg = MIMEText(mailcontent)

# me == the sender's email address
# you == the recipient's email address
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = you

# Send the message via our own SMTP server, but don't include the
# envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(me, [you], msg.as_string())
    s.quit()
    #print mailcontent
    logger.debug('Subject: ', subject)
    logger.warn('Mail content')
    logger.debug(mailcontent)
