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
import glob
import fcntl
import hashlib
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
from faucetUtil import readFile, sanitize

nicks = []
passwords = {}
addresses = {}

@rule('^\!?faucet$')
@priority('low')
@rate(120)
def refmsg(bot, trigger):
    if not trigger.sender.startswith('#'):
        return
    bot.reply(conf.get('main', 'refmsgtxt'))

@rule('getstarted')
@priority('low')
@rate(120)
def helpmsg(bot, trigger):
    if trigger.sender.startswith('#'):
        return
    nick = Nick(trigger.sender)
    logging.info('got help command from %s' % nick)
    for r in (conf.get('main', 'help1'), conf.get('main', 'help2'), \
              conf.get('main', 'help3')):
        bot.reply(r)

@rule('wallet\s(\w*)\s(\w{26,35})')
@priority('high')
@rate(30)
def msg(bot, trigger):
    if trigger.sender.startswith('#'):
        return
    nick = Nick(trigger.sender)
    pw_plain = sanitize(trigger.group(1))
    hashed = hashPW(pw_plain)
    address = sanitize(trigger.group(2))
    rpc = conf._sections['rpc']
    conn = bitcoinrpc.connect_to_remote(rpc['user'], rpc['pass'], \
                                        rpc['host'], rpc['port'])
    rv = conn.validateaddress(address)
    if not rv.isvalid:
        bot.reply('invalid address, try again!')
        return
    updatePasswords()
    global passwords
    if nick in passwords:
        if not hashed == passwords[nick]:
            bot.reply('incorrect password.')
            return
    else:
        appendPasswordFile(nick + ' ' + hashPW(pw_plain))
    updateAddresses()
    global addresses
    if nick in addresses:
        if address == addresses[nick]:
            bot.reply(conf.get('main', 'addressexistsreply'))
            return
        else:
            bot.reply('Updating your stored address')            
    updateAddressFile(nick, address)
    logging.info("set address for %s to %s" % (nick, address))
    bot.reply(conf.get('main', 'walletreply') % (nick, address, pw_plain))
    
def populateNicks():
    global nicks
    newnicks = []
    for file in glob.glob(conf.get('main', 'basedir') + \
                          conf.get('main', 'nicksdir') + '*'):
        if re.search('\.', file):
            continue
        (head, tail) = os.path.split(file)
        newnicks.append(tail)
    nicks = newnicks

def hashPW(arg=''):
    m = hashlib.md5()
    m.update(arg)
    return m.hexdigest()

def updateAddressFile(nick, address):
    addys = {}
    fn = conf.get('main', 'basedir') + conf.get('main', 'addressfile')
    writedir = os.path.dirname(fn)
    if os.path.isfile(fn):
        content = readFile(fn)
        for line in content:
            (n, a) = line.split()
            addys[n] = a
        addys[nick] = address
        with open(fn,"w+") as fw:
            fcntl.flock(fw.fileno(), fcntl.LOCK_EX)
            for key, value in addys.iteritems():
                fw.write("%s %s\n" % (key, value))
            fw.close()
    else:
        if not os.path.exists(writedir):
            os.makedirs(writedir)
        with open(fn, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write("%s %s\n" % (nick, address))
            f.close()
        
def updatePasswords():
    global passwords
    newpw = {}
    fn = conf.get('main', 'basedir') + conf.get('main', 'pwfile')
    if os.path.isfile(fn):
        content = readFile(fn)
        for line in content:
            (nick, pw) = line.split()
            newpw[nick] = pw
        passwords = newpw

def updateAddresses():
    global addresses
    newaddy = {}
    fn = conf.get('main', 'basedir') + conf.get('main', 'addressfile')
    if os.path.isfile(fn):
        content = readFile(fn)
        for line in content:
            (nick, addy) = line.split()
            newaddy[nick] = addy
        addresses = newaddy

def appendPasswordFile(line):
    fn = conf.get('main', 'basedir') + conf.get('main', 'pwfile')
    writedir = os.path.dirname(fn)
    if os.path.isfile(fn):
        with open(fn,"a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(line + "\n")
            f.close()
    else:
        if not os.path.exists(writedir):
            os.makedirs(writedir)
        with open(fn, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(line + "\n")
            f.close()
