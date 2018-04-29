
# Automatic  trading system with Python(2)

## Description

Simple Kalman filter strategy for trading a portfolio of 5 currency pairs. Will add a proper description at some later point in time. 

## Current status

Code works (or should work as is) a list of tuples denoting Fridays is added manually into the oTradingSystem.py script, this is to be corrected next. Also the Kalman filter "burn-in" has to be specified the same way, this also denotes the window from which rolling average and standard deviation of the portfolio are calculated. 

Since the program skips Friday 5pm EST - Sunday 5pm EST by just waiting a fixed amount of time, the 
oTradingSystem.py should be run only when trading is active.

So to be fixed next are insertion of data from the command line and ability to start the system whenever. Also adding a possibility for pickling the system so that data is not lost if the system is shut down for maintenance for example is on the agenda. All is dependent on time...

Broker used is Oanda, and the API for it is provided by https://github.com/hootnot/oanda-api-v20, it is exellent and easy to use! Thanks hootnot!

### Care must be taken, this strategy is not to be used for trading as is unless you hate money.

