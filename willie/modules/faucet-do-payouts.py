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
import sys
import time
import fcntl
import logging
import bitcoinrpc
from willie.tools import Nick
from willie.module import rule, priority, rate
from ConfigParser import RawConfigParser

conf = RawConfigParser()
conf.read('/home/kunwon1/faucet/faucet.conf')

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG, \
                    filename=conf.get('main', 'basedir') + \
                             conf.get('main', 'logfile') )

lib_path = os.path.abspath(conf.get('main', 'basedir'))
sys.path.append(lib_path)
from faucetUtil import readFile

payouts = {}
addys = {}
semaphore = 0

@rule('^\!?donate$')
@rule('^\!?balance$')
@priority('low')
@rate(120)
def balmsg(bot, trigger):
    if not trigger.sender.startswith('#'):
        return
    bal = getBalance()
    bot.reply(conf.get('main', 'balancetext') % bal)

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

def getBalance():
    rpc = conf._sections['rpc']
    conn = bitcoinrpc.connect_to_remote(rpc['user'], rpc['pass'], \
                                        rpc['host'], rpc['port'])
    return conn.getbalance()

def sendCoins(address, amount):
    rpc = conf._sections['rpc']
    conn = bitcoinrpc.connect_to_remote(rpc['user'], rpc['pass'], \
                                        rpc['host'], rpc['port'])
    rv = conn.validateaddress(address)
    if rv.isvalid:
        conn.sendtoaddress(address, amount)
        logging.info("sent %f to %s" % (amount, address))
    else:
        logging.warning("The address that you provided is invalid, please correct %s" % address)

def updatePayouts():
    global payouts
    newpay = {}
    fn = conf.get('main', 'basedir') + conf.get('main', 'payoutsfile')
    if os.path.isfile(fn):
        content = readFile(fn)
        for line in content:
            (timestamp, nick, amount) = line.split()
            newpay[nick] = "%s %s" % (timestamp, amount)
        payouts = newpay

@rule('(.*)')
@priority('low')
def msg(bot, trigger):
    global semaphore
    global addys
    if not semaphore == 0:
        return
    else:
        semaphore = 1
    global payouts
    updatePayouts()
    curtime = float(time.time())
    cutoff = curtime - conf.getfloat('main', 'payoutDelay')
    flag = 0
    populateAddresses()
    for nick in payouts.keys():
        (ts, amount) = payouts[nick].split()
        amount = float(amount)
        if float(ts) < cutoff or flag == 1:
            flag = 1
            if not nick in addys:
                logging.info("%s missed out on %s coins, no address on file!" % \
                            (nick, amount))
                continue
            else:
                balance = getBalance()
                # print "%s %s" % (balance, conf.getfloat('main', 'minbalance'))
                if not balance > conf.getfloat('main', 'minbalance'):
                    logging.critical("insufficient coins in wallet! no payment processed")
                else:
                    logging.info("Calling API to pay %s %s" % (nick, amount))
                    sendCoins(addys[nick], amount)
    if flag == 1:
        clearPendingPayouts()
    semaphore = 0

def clearPendingPayouts():
    with open(conf.get('main', 'basedir') + \
              conf.get('main', 'payoutsfile'), 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.close()
