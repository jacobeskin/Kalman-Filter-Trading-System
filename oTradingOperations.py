
"""
Library of all the methods for interacting with Oanda API, probably will end 
up being a two classes, maybe some auxiliary methods...will see...
"""
import time
import numpy as np

import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.contrib.requests import MarketOrderRequest

import requests # Also for error handling

class oPositionManager:

    def __init__(self, Account_ID, Account_Token, Instruments, I_types):

        #self.a_id, self.a_t = Account_ID, Account_Token
        self.instruments = Instruments
        self.I_types = I_types
        self.ID = Account_ID
        
        self.existing_positions = [] # List of exisitng positions ticket #'s
        self.long_short = '' # String noting the type of open trades 
        self.std_away = [] # In order not to have duplicate trades...
        
        self.client = oandapyV20.API(access_token=Account_Token)

        

    # Method for getting the closing prices of the last candles
    def oLastPrice(self):

        # In case of errors
        Trade = True # For determining if trading is allowed with new prices
        ERR = False  # For determining if new prices were even recieved on time
        
        i = 0
        H = np.empty((1,len(self.instruments)))
        H[0][-1] = 1.0
        Z = np.empty((1,1))

        # For error handling
        error = 0
        waits = 0

        # Go through all instruments
        while i<len(self.instruments):

            # Basic syntax
            data = {'price':'M', 'granularity':'H1', 'count':2}
            request = instruments.InstrumentsCandles(self.instruments[i],data)

            # Get prices
            try:
                r = self.client.request(request)
                print 'Price request succesfull for', self.instruments[i]
                if i==0:
                    Z[0] = float(r['candles'][0]['mid']['c'])
                else:
                    H[0][i-1] = float(r['candles'][0]['mid']['c'])
                error = 0
                waits = 0
                i += 1
            except oandapyV20.exceptions.V20Error as err:
                print 'Price request failed for',  self.instruments[i]
                error +=1
                print 'Error reason V20 API\n', error
            # Other connection errors
            except requests.exceptions.RequestExceptions as err:
                print 'Price request failed for',  self.instruments[i]
                error +=1
                print 'Error reason\n', err

            # In case there is a problem getting the prices
            if (error>5) and (waits<=50):
                print '\n Trouble getting data, waiting a minute...\n'
                waits += 1
                Trade = False
                time.sleep(60)
            elif (error>5) and (waits>50):
                print ' Unable to get data for over 50 minutes!\n'
                ERR = True
                break
                

        return Z, H, Trade, ERR

    # Method for opening positions
    def oOpenPosition(self, lots):

        OK = True
        opening_positions = []
        # Start opening positions
        for i in xrange(len(self.instruments)):
            order = MarketOrderRequest(instrument=self.instruments[i],
                                               units=lots[i])
            request = orders.OrderCreate(self.ID, data=order.data)

            # Again for error handling
            print '\n Opening on', self.instruments[i]
            try:
                trd = self.client.request(request)
                opening_positions.append(trd['orderFillTransaction']['id'])
		print 'Success!\n'
                
            except (oandapyV20.exceptions.V20Error) as err:
                print 'Error in opening position! Cancelling trade!'
                OK = False
                if len(opening_positions)>0:
                    i = 0
                    while i<len(opening_positions):
                        request = trades.TradeClose(accountID=self.ID,
                                                tradeID=opening_positions[i])
                        try:
                            _ = self.client.request(request)
                            print 'Closed ', opening_positions[i]
                            i += 1
                        except oandapyV20.exceptions.V20Error as err:
                            print 'Close failing as well....'
                            print 'Trying again...perkele perkele...'

        # Adding succesfully opened positions to the all positions list
        if OK:
            for i in opening_positions:
               self.existing_positions.append(i)
            print 'Position IDs:', self.existing_positions, '\n' 
               
        return OK
                        
        
    # Method for opening and closing positions
    def oManage(self, x_pri, z, H, Z, Z_mean, Z_std):

        opening_positions = [] # Positions opened in the middle of a trade
	closing_positions = [] # Positions to be closed

        # Always first check if there are positions to be closed
        if len(self.existing_positions)>0:

            # If we have open trades that need to be closed
            if (((self.long_short=='short') and (Z<=Z_mean-0.5*Z_std))
                or ((self.long_short=='long') and (Z>=Z_mean+0.5*Z_std))):

                # Cycle through the ticket numbers and close the positions
                i = 0
                num_positions = len(self.existing_positions)
                while i<num_positions:

                    request = trades.TradeClose(accountID=self.ID,
                                            tradeID=self.existing_positions[i])

                    # Close position, with error handling
                    try:
                        _ = self.client.request(request)
                        print 'Closed', self.existing_positions[i]
                        closing_positions.apend(self.existing_positions[i])
                        i += 1
                    except oandapyV20.exceptions.V20Error as err:
                        print 'Close failed for', self.existing_positions[i]
                        print '\n Trying again...perkele...\n'

                self.long_short = ''
                self.std_away = []
		for k in closing_positions:
			self.existing_positions.remove(k)

        # Otherwise look for possibly opening trades
                        
        # Get balance of the account
        request = accounts.AccountDetails(self.ID)
        request = self.client.request(request)
        balance = float(request['account']['balance'])
                        
        # Long trade
        if (Z<=Z_mean-2.0*Z_std) and (self.long_short!='short'):

            # Calculate first the lot sizes
            lots = [0]*len(self.instruments)
            for i in xrange(len(self.instruments)):
                if i==0:
                    if self.I_types[i]==1:
                        lots[i] = int(np.around(balance/z,0))
                    else: lots[i] = int(np.around(balance,0))
                else:
                    if self.I_types[i]==1:
                        lots[i] = int(np.around(balance*x_pri[i-1]/H[0][i-1],0))
                    else: lots[i] = int(np.around(balance*x_pri[i-1],0))
                    lots[i] = -1*lots[i]

            p2 = Z_mean-2.0*Z_std
            p3 = Z_mean-3.0*Z_std
            p4 = Z_mean-4.0*Z_std

            # If can open a position 2 std's away
            if (2 not in self.std_away) and ((Z<=p2) and (Z>p3)):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(2) # Trade at 2 std's open
                    self.long_short = 'long'
                    print '\n Opened long positions 2 std\'s away!\n'

            # If can open a position 3 std's away
            if (3 not in self.std_away) and ((Z<=p3) and (Z>p4)):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(3) # Trade at 4 std's open
                    self.long_short = 'long'
                    print '\n Opened long positions 3 std\'s away!\n'

            # If can open a position 2 std's away
            if (4 not in self.std_away) and (Z<=p4):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(4) # Trade at 4 std's open
                    self.long_short = 'long'
                    print '\n Opened long positions 4 std\'s away!\n'

        # Short trade
        if (Z>=Z_mean+2.0*Z_std) and (self.long_short!='long'):

            # Calculate first the lot sizes
	    lots = [0]*len(self.instruments)
            for i in xrange(len(self.instruments)):
                if i==0:
                    if self.I_types[i]==1:
                        lots[i] = int(np.around(balance/z,0))
                    else: lots[i] = int(np.around(balance,0))
                    lots[i] = -1*lots[i]
                else:
                    if self.I_types[i]==1:
                        lots[i] = int(np.around(balance*x_pri[i-1]/H[0][i-1],0))
                    else: lots[i] = int(np.around(balance*x_pri[i-1],0))

            p2 = Z_mean+2.0*Z_std
            p3 = Z_mean+3.0*Z_std
            p4 = Z_mean+4.0*Z_std

            # If can open a position 2 std's away
            if (2 not in self.std_away) and ((Z>=p2) and (Z<p3)):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(2) # Trade at 2 std's open
                    self.long_short = 'short'
                    print '\n Opened short positions 2 std\'s away!\n'

            # If can open a position 3 std's away
            if (3 not in self.std_away) and ((Z>=p3) and (Z<p4)):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(3) # Trade at 4 std's open
                    self.long_short = 'short'
                    print '\n Opened short positions 3 std\'s away!\n'

            # If can open a position 2 std's away
            if (4 not in self.std_away) and (Z>=p4):

                OK = self.oOpenPosition(lots)
                if OK:
                    self.std_away.append(4) # Trade at 4 std's open
                    self.long_short = 'short'
                    print '\n Opened short positions 4 std\'s away!\n'
                            
    # Method for getting data for burnin, WILL DO ERROR HANDLING LATER
    def oGetData(self, candles):

        z = np.empty((candles-1, 1))
        h = np.empty((candles-1, len(self.instruments)))
        for i in xrange(len(self.instruments)+1):
            if i<len(self.instruments):
                data = {'price':'M', 'granularity':'H1', 'count':candles} 
                request = instruments.InstrumentsCandles(self.instruments[i],
                                                         data)
                prices = self.client.request(request)

            for j in xrange(candles-1):
                if i==0:
                    z[j] = float(prices['candles'][j]['mid']['c'])
                elif (i>0) and (i<len(self.instruments)):
                    h[j][i-1] = float(prices['candles'][j]['mid']['c'])
                else:
                    h[j][i-1] = 1.0
        return z, h
                                                     

            
            

            

            

            
    
