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
import re
import sys
import time
import glob
import fcntl
import random
import logging
from collections import deque
from willie.tools import Nick
from willie.module import rule, priority
from ConfigParser import RawConfigParser

conf = RawConfigParser()
conf.read('/home/kunwon1/faucet/faucet.conf')

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG, \
                    filename=conf.get('main', 'basedir') + \
                             conf.get('main', 'logfile') )

lib_path = os.path.abspath(conf.get('main', 'basedir'))
sys.path.append(lib_path)
from faucetOdds import payoutList
from faucetUtil import readFile

lastHeartbeat = 0
nextPayout = 0
logs = {}
addys = {}

def populateAddresses():
    global addys
    newaddys = {}
    fn = conf.get('main', 'basedir') + conf.get('main', 'addressfile')
    if os.path.isfile(fn):
        content = readFile(fn)
        for line in content:
            (n, a) = line.split()
            newaddys[n] = a
        addys = newaddys

def getPayoutTime():
    floor = conf.getint('main',  'payoutMaxTimeFlux') * -1
    val = conf.getint('main',  'payoutMedianTime') + \
          random.uniform(floor, conf.getint('main',  'payoutMaxTimeFlux'))
    return int(val)

def getPayoutOdds():
    floor = conf.getfloat('main', 'payoutMaxOddsFlux') * -1
    return conf.getfloat('main', 'payoutMedianOdds') + \
           random.uniform(floor, conf.getfloat('main', 'payoutMaxOddsFlux'))

@rule('(.*)')
@priority('low')
def msg(bot, trigger):
    global lastHeartbeat
    global nextPayout
    if time.time() >= nextPayout:
        nextPayout = time.time() + getPayoutTime()
        if not lastHeartbeat == 0:
            doPayout(bot, trigger)
        logging.info('Next payout at %s' % time.ctime(nextPayout))
    lastHeartbeat = time.time()

def doPayout(bot, trigger):
    populateLogs()
    populateAddresses()
    global logs
    global addys
    fLogs = {}
    odds = getPayoutOdds()
    logging.info('Doing payout. Odds are %s' % odds)
    clearPendingPayouts()
    for nick in logs.keys():
        for line in logs[nick]:
            timestamp = float(str.split(line)[0])
            cutoff = float(time.time()) - \
                     conf.getfloat('main', 'timeForConsideration')
            if timestamp < cutoff:
                continue
            if nick in fLogs.keys():
                fLogs[nick].append(line)
            else:
                fLogs[nick] = []
                fLogs[nick].append(line)
    for cNick in fLogs.keys():
        foo = random.random()
        if foo < odds:
            payout = random.choice(payoutList)
            logging.info('adding to pending: %s %s' % (cNick, payout))
            if not cNick in addys:
                continue
            bot.msg(cNick, conf.get('main', 'payoutmessage') % (cNick, payout))
            doSinglePayout(cNick, payout)
        else:
            logging.info("%s didn't make the cut!" % cNick)
        
    
def populateLogs():
    global logs
    for file in glob.glob(conf.get('main', 'basedir') + \
                          conf.get('main', 'nicksdir') + '*'):
        if re.search('\.', file):
            continue
        (head, tail) = os.path.split(file)
        file = file + '/' + tail
        if os.path.isfile(file):
            logs[tail] = readFile(file)

def doSinglePayout(nick, amount):
    nick = str(nick)
    with open(conf.get('main', 'basedir') + \
              conf.get('main', 'payoutsfile'), 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write("%s %s %s\n" % (time.time(), nick, amount))
        f.close()

def clearPendingPayouts():
    with open(conf.get('main', 'basedir') + \
              conf.get('main', 'payoutsfile'), 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.close()
