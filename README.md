This is a generic IRC based bitcoin/altcoin faucet. If that doesn't make sense to you, you're probably in the wrong place. It will work with any rpc-capable bitcoin/altcoin wallet software, as far as I know. This is currently setup for Quark/QRK, but if you know how to edit text files, you should be able to change everything to work with some other coin.

This faucet bot is written by David J Moore, aka kunwon1
The original faucet bot operates in ##quark on freenode - this is not a faucet support channel
For support questions, join ##faucet on freenode

Released under the Eiffel Public License (Same as willie) - If you find this software useful, please consider donating to me:
BTC 15RAghcMSN2xDFsrfnJEveCwrWM9XNA4o8
QRK QQU9pq8YaZa82xeoGgHm49uifag6FSaZE3

This faucet is a set of modules for willie: https://github.com/embolalia/willie
as such, willie is required.
also required is the python bitcoinrpc module: https://github.com/laanwj/bitcoin-python

Your first order of business is to setup a willie and turn off all the stock modules. I mean, you could probably leave them on, but if they screw anything up, you're on your own :) then, take the modules from the willie/modules directory in the git repo, and install them in the willie modules directory for the bot you've just set up.

Take everything else from the root directory of the repo and put it next to your willie executable (~/faucet in my case)

Edit the module files in willie/modules, you need to point to the .conf file in each of the four module files:

conf.read('/home/kunwon1/faucet/faucet.conf') 

change this to point to your conf file.

Next, edit your conf file. The first section is RPC parameters for your properly configured bitcoind/bitcoin-qt equivalent. My bot is setup to use quarkcoin-qt.

Change the basedir parameter in the next section, everything else can probably stay the same

payoutMedianTime: Unmodified amount of time between payouts, in seconds
payoutMaxTimeFlux: Maximum number of seconds that payout time can fluctuate from payoutMedianTime, up or down.
payoutMedianOdds: Chances of a particular user getting paid out on a given round of payouts. 0.00 - 1.00
payoutMaxOddsFlux: Maximum amount that MedianOdds will fluctuate up or down
timeForConsideration: Time in seconds during which you can be considered for a payout after you stop chatting

# must be float!
payoutDelay: Delay in seconds between picking recipients and actually sending payouts. Set to a high number to audit payouts, but make sure it's smaller than (payoutMedianTime - payoutMaxTimeFlux)
minbalance: If your wallet drops below this balance, no further payouts will be sent

EDIT balancetext - CHANGE THE ADDRESS - otherwise people will be sending me QRK that's meant for you

FINALLY, edit faucetOdds.py - this sets up the min/max payouts and the odds of each

payoutList = [1] * 5 + [0.5] * 20 + [.25] * 75

This will payout 1 QRK 5% of the time, 0.5QRK 20% of the time, and .25QRK 75% of the time.
75+20+5 = 100. You can change this if you want but it won't be as intuitive to determine actual odds.

Another example:

payoutList = [.003] * 3 + [.002] * 5 + [.001] * 90

-003 3% of the time, .002 5% of the time, .001 90% of the time


