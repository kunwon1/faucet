# -*- coding: utf8 -*-

# Copyright (c) 2013 David J Moore (kunwon1)
#
# Eiffel Forum License, version 2
#
# 1. Permission is hereby granted to use, copy, modify and/or
#    distribute this package, provided that:
#       * copyright notices are retained unchanged,
#       * any distribution of this package, whether modified or not,
#         includes this license text.
# 2. Permission is hereby also granted to distribute binary programs
#    which depend on this package. If the binary program depends on a
#    modified version of this package, you are encouraged to publicly
#    release the modified version of this package.
#
# THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT WARRANTY. ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE TO ANY PARTY FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS PACKAGE.

import os
import time
import fcntl
import logging
from collections import deque
from willie.tools import Nick
from willie.module import rule, priority, event
from ConfigParser import RawConfigParser

conf = RawConfigParser()
conf.read('/home/kunwon1/faucet/faucet.conf')

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG, \
                    filename=conf.get('main', 'basedir') + \
                             conf.get('main', 'logfile') )

@rule('(.*)')
@priority('low')
def chanmsg(bot, trigger):
    if trigger.sender.startswith('#'):
        writeChannelMessage(trigger)

@rule('(.*)')
@priority('low')
@event('JOIN')
def joinmsg(bot, trigger):
    writeEventMessage(trigger)

@rule('(.*)')
@priority('low')
@event('PART')
def partmsg(bot, trigger):
    writeEventMessage(trigger)
    
@rule('(.*)')
@priority('low')
@event('QUIT')
def quitmsg(bot, trigger):
    writeEventMessage(trigger)
    
@rule('(.*)')
@priority('low')
@event('NICK')
def nickchangemsg(bot, trigger):
    writeNickchangeMessage(trigger)

def prepareMessage(message = ''):
    # prepends timestamp and encodes into utf8
    try:
        message = ("%s %s" % (time.time(), message)).encode('UTF-8', 'ignore')
    except:
        if message == '':
            message = "%s UNICODE ERROR" % time.time()
    return message

def writeNickchangeMessage(trigger):
    nick1 = Nick(trigger.nick)
    nick2 = trigger.sender
    event = trigger.event
    host = trigger.hostmask
    message = prepareMessage("%s %s %s %s" % (nick1, event, nick2, host))
    nick1fn = conf.get('main', 'basedir') + conf.get('main', 'nicksdir') + \
                                            nick1 + '/events'
    nick2fn = conf.get('main', 'basedir') + conf.get('main', 'nicksdir') + \
                                            nick2 + '/events'
    writeLogFile(nick1fn, message)
    writeLogFile(nick2fn, message)    

def writeChannelMessage(trigger):
    # prepares a channel message and calls writeLogFile with it
    nick = Nick(trigger.nick)
    message = prepareMessage(trigger)
    fn = conf.get('main', 'basedir') + conf.get('main', 'nicksdir') + \
                                       nick + '/' + nick
    writeLogFile(fn, message)

def writeEventMessage(trigger):
    # writes join/part/quit messages
    nick = Nick(trigger.nick)
    event = trigger.event
    channel = trigger.sender
    host = trigger.hostmask
    if event == 'QUIT':
        message = prepareMessage("%s %s" % (event, host))
    else:
        message = prepareMessage("%s %s %s" % (event, channel, host))
    fn = conf.get('main', 'basedir') + conf.get('main', 'nicksdir') + \
                                       nick + '/events'
    writeLogFile(fn, message)

def writeLogFile(fn, message):
    # adds a line to a logfile, creating the directory/file if necessary
    message = message.replace('\n', '')
    writedir = os.path.dirname(fn)
    if os.path.isfile(fn):
        with open(fn) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            content = f.readlines()
            f.close()
        d = deque(content, 100)
        d.append(message)
        with open(fn,"w+") as fw:
            fcntl.flock(fw.fileno(), fcntl.LOCK_EX)
            for item in d:
                if item[-1] != "\n":					
                    fw.write(item + "\n")
                else:
                    fw.write(item)
            fw.close()
            return
    else:
        if not os.path.exists(writedir):
            os.makedirs(writedir)
        with open(fn, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(message)
            f.close()
