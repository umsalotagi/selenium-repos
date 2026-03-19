# -*- coding: utf-8 -*-
"""
Created on Sat Mar 14 22:58:43 2026

@author: usalotagi
"""



import pandas as pd
import time
from kiteconnect import KiteConnect
from kiteconnect.exceptions import NetworkException
import datetime as dt
import datetime
from abc import ABC, abstractmethod
import logging


class StockBroker(ABC):
    
    @abstractmethod
    def same(self):
        pass
    

class HistoryBroker(ABC):
    pass
    

class MyOrder:
    
    def __init__(self, logger, symbol, enter_order):
        self.symbol = symbol # this is tradingsymbol, can be different for topions
        self.ticker = symbol # this is ticker we use for history
        self.logger = logger
        self.enter_order = enter_order
        self.is_trade_exited = False
        self.sl_order = None
        self.target_order = None
        self.exit_order = None
        self.target_price = None
        self.sl_price = None
        # following is to execute option trades on stock price, so when stock prices cross above enter_price
        # place option trade of type CALL buy, we are expecting prices to rise
        self.enter_price = None
        self.enter_type = "CALL"
        
    def is_sl_executed(self):
        if not self.sl_order:
            self.logger("KITE1001: SL order does not exit")
            return False
        if self.sl_order['Status'].lower() == 'completed':
            self.is_trade_exited = True
            return True
        else:
            return False
        
    def is_target_executed(self):
        if not self.target_order:
            self.logger("KITE1002: SL order does not exit")
            return False
        if self.target_order['Status'] == 'COMPLETE':
            self.is_trade_exited = True
            return True
        else:
            return False
    
    
class ZerodhaBroker(StockBroker, HistoryBroker):
    
    def __init__(self, kite, nse_instrument_df, logger, strategy_tag, max_trades=1000, test_mode=True):
        self.kite = kite
        self.nse_instrument_df = nse_instrument_df
        self.logger = logger
        self.max_trades = max_trades
        self.test_mode = test_mode
        self.invalid_token_tickers = []
        self.valid_order_status = ["OPEN", "TRIGGER PENDING", "OPEN PENDING"]
        self.my_orders = {}
        self.strategy_tag = strategy_tag
        pass
    
    def same(self):
        pass
    
    def addObserverOrder(self, symbol, enter_price, enter_type):
        my_new_order = MyOrder(self.logger, symbol, None)
        my_new_order.enter_price = enter_price
        my_new_order.enter_type = enter_type
        fake_order_id = "observer_"+symbol + self.strategy_tag
        self.my_orders[fake_order_id] = my_new_order
    
    def instrumentLookup(self, symbol):
        try:
            return self.nse_instrument_df[self.nse_instrument_df.tradingsymbol==symbol].instrument_token.values[0]
        except:
            return -1
    
    
    def fetchOHLCExtended(self, ticker, interval, period_days, inception_date=None):
        """extracts historical data and outputs in the form of dataframe
           inception date string format - dd-mm-yyyy"""
        instrument = self.instrumentLookup(ticker)
        if inception_date:
            from_date = dt.datetime.strptime(inception_date, '%d-%m-%Y')
        else:
            from_date = dt.date.today() - dt.timedelta(period_days)
        to_date = dt.date.today()
        data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        while True:
            if from_date >= (dt.date.today() - dt.timedelta(100)):
                new_data = pd.DataFrame(self.kite.historical_data(instrument,from_date,dt.date.today(),interval))
                if data.empty:
                    data = new_data
                else:
                    data = pd.concat([data, new_data],ignore_index=True)
                break
            else:
                to_date = from_date + dt.timedelta(100)
                new_data = pd.DataFrame(self.kite.historical_data(instrument,from_date,to_date,interval))
                if data.empty:
                    data = new_data
                else:
                    data = pd.concat([data, new_data],ignore_index=True)
                from_date = to_date + dt.timedelta(1)
        data.set_index("date",inplace=True)
        return data
    
    
    def fetchOHLCExtendedAll(self, tickers, interval, period_days):
        entire_data = {}
        for ticker in tickers:
            try:
                from_date = dt.date.today() - dt.timedelta(period_days)
                entire_data[ticker] = self.fetchOHLC(ticker, interval, from_date, dt.date.today())
                #entire_data[ticker].fillna(method='ffill', inplace=True)
                entire_data[ticker].ffill(inplace=True)
                entire_data[ticker].dropna(inplace=True,how="all")
                
            except NetworkException as e:
                try:
                    print("Possible too many request error, retyring for ", ticker, e)
                    time.sleep(0.05)
                    from_date = dt.date.today() - dt.timedelta(period_days)
                    entire_data[ticker] = self.fetchOHLC(ticker, interval, from_date, dt.date.today())
                    entire_data[ticker].dropna(inplace=True,how="all")
                except Exception as e:
                    print("hell, repeated offender ###", ticker, e)
                    raise
                
            except Exception as e:
                print("Possible invalid token for", ticker, e)
                self.invalid_token_tickers.append(ticker)
        return entire_data
    
    def fetchOHLC(self, ticker, interval, from_date, to_date):
        """extracts historical data and outputs in the form of dataframe
           inception date string format - dd-mm-yyyy"""
        instrument = self.instrumentLookup(ticker)
        #print("fetchOHLC", ticker, instrument, interval, from_date, to_date)
        data = pd.DataFrame(self.kite.historical_data(instrument,from_date,to_date,interval))
        if data.empty:
            self.logger.info("KITE1004: No data found for {}".format(ticker))
            return data
        data.set_index("date",inplace=True)
        return data
    
    
    def modifySLOrder(self,symbol,order_id,price):    
        # Modify order given order id
        self.kite.modify_order(order_id=order_id,
                        trigger_price=price,
                        order_type=self.kite.ORDER_TYPE_SLM,
                        variety=self.kite.VARIETY_REGULAR) 
        self.logger.info("KITE1005: Modiying order for {}, with {} with sl_price {}".format(symbol, order_id, price))
    
    
    def getPositions(self):
        a = 0
        while a < 10:
            try:
                positions = self.kite.positions()["day"]
                positions = [item for item in positions if item["product"] == "MIS"]
                break
            except:
                self.logger.info("KITE1006: can't extract position data..retrying")
                a+=1
        return positions
    
    def getOrders(self):
        a = 0
        while a < 10:
            try:
                orders = self.kite.orders()
                orders = [item for item in orders if item["tag"] == "renko_macd"]
                break
            except:
                self.logger.info("KITE1007: can't extract position data..retrying")
                a+=1
        return orders
    
    # this function is shares and options buy/sell compatible
    def placeMarketOrderSLM(self,symbol,buy_sell,quantity,sl_price,instrument_type="EQ",ticker=None):    
        # Place an intraday market order on NSE
        if buy_sell == "BUY":
            t_type=self.kite.TRANSACTION_TYPE_BUY
            t_type_sl=self.kite.TRANSACTION_TYPE_SELL
        elif buy_sell == "SELL":
            t_type=self.kite.TRANSACTION_TYPE_SELL
            t_type_sl=self.kite.TRANSACTION_TYPE_BUY
        else:
            return None,None
        
        if (len(self.getPositions()) >= self.max_trades):
            self.logger.info("KITE1008: More than {} positions already build, no entering the trade {}".format(self.max_trades, symbol))
            return None,None
        
        if instrument_type == "OPT":
            exchange = self.kite.EXCHANGE_NFO
        else:
            exchange = self.kite.EXCHANGE_NSE
        
        # you can use VARIETY_CO also
        enter_order = self.kite.place_order(tradingsymbol=symbol,
                        exchange=exchange, # NSE, BSE
                        transaction_type=t_type, # buy / sell
                        quantity=quantity,
                        order_type=self.kite.ORDER_TYPE_MARKET, # market price order - will get executed at market value
                        product=self.kite.PRODUCT_MIS, # intraday
                        tag=self.strategy_tag,
                        variety=self.kite.VARIETY_REGULAR) # regular order
        my_new_order = MyOrder(self.logger, symbol, enter_order)
        if ticker:
            my_new_order.ticker = ticker
        self.my_orders[my_new_order.enter_order['order_id']] = my_new_order
        self.logger.info("KITE1009: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
        # for ORDER_TYPE_SLM we only provide trigger price, no price
        if sl_price:
            my_new_order.sl_order = self.kite.place_order(tradingsymbol=symbol,
                            exchange=self.kite.EXCHANGE_NSE,
                            transaction_type=t_type_sl,
                            quantity=quantity,
                            order_type=self.kite.ORDER_TYPE_SLM,
                            trigger_price = sl_price,
                            product=self.kite.PRODUCT_MIS,
                            tag=self.strategy_tag,
                            variety=self.kite.VARIETY_REGULAR)
        return my_new_order
    
    # this function is options and equity square off compatible
    def squareOffOrder(self,symbol,buy_sell,quantity,order_id,instrument_type="EQ"):
        if buy_sell == "BUY":
            t_type=self.kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "SELL":
            t_type=self.kite.TRANSACTION_TYPE_SELL
        else:
            t_type=None
        
        if instrument_type == "OPT":
            exchange = self.kite.EXCHANGE_NFO
        else:
            exchange = self.kite.EXCHANGE_NSE
        response = self.kite.place_order(tradingsymbol=symbol,
                    exchange=exchange,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=self.kite.ORDER_TYPE_MARKET,
                    product=self.kite.PRODUCT_MIS,
                    tag=self.strategy_tag,
                    variety=self.kite.VARIETY_REGULAR)
        
        my_entered_order = self.my_orders[order_id]
        # TODO: check quantity before marking exited, sometimes partial exit is also done
        my_entered_order.is_trade_exited = True
        if my_entered_order.sl_order:
            sl_cancel_response = self.kite.cancel_order(order_id=my_entered_order.sl_order["order_id"], variety=self.kite.VARIETY_REGULAR)  
            self.logger.info("KITE1010: cancel stoploss order for {} response {} ".format(symbol, sl_cancel_response))
            
        if my_entered_order.target_order:
            target_cancel_response = self.kite.cancel_order(order_id=my_entered_order.target_order["order_id"], variety=self.kite.VARIETY_REGULAR)  
            self.logger.info("KITE1011: cancel stoploss order for {} response {} ".format(symbol, target_cancel_response))

        self.logger.info("KITE1012: square off done for {} response {} ".format(symbol, response))    
        self.observe_position(symbol, "exit", buy_sell)
        return
    
    # TODO: create method when we want to enter at limit price, once triggered, stoploss and another target limit
    def placeLimitOrder(self,symbol,buy_sell,quantity,limit_price,order_id):    
        # Place an intraday market order on NSE, target order
        if buy_sell == "BUY":
            t_type=self.kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "SELL":
            t_type=self.kite.TRANSACTION_TYPE_SELL
        else:
            return None
        
        if self.test_mode:
            self.logger.info("KITE1013: test_mode is active : Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
            return None
        # you can use VARIETY_CO also
        response = self.kite.place_order(tradingsymbol=symbol,
                        exchange=self.kite.EXCHANGE_NSE, # NSE, BSE
                        transaction_type=t_type, # buy / sell
                        quantity=quantity,
                        price=limit_price,
                        order_type=self.kite.ORDER_TYPE_LIMIT, 
                        product=self.kite.PRODUCT_MIS, # day trade
                        tag=self.strategy_tag,
                        variety=self.kite.VARIETY_REGULAR) # regular order
        
        if order_id:
            my_entered_order = self.my_orders[order_id]
            my_entered_order.target_order = response
            return my_entered_order
        else:
            my_new_order = MyOrder(self.logger, symbol, response)
            self.my_orders[my_new_order.enter_order['order_id']] = my_new_order
            self.logger.info("KITE1014: Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
            self.observe_position(symbol, "enter", buy_sell)
            return my_new_order
        
    def placeStopLossOrder(self,symbol,buy_sell,quantity,sl_price,order_id):
        if buy_sell == "BUY":
            t_type=self.kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "SELL":
            t_type=self.kite.TRANSACTION_TYPE_SELL
        else:
            return None
        response = self.kite.place_order(tradingsymbol=symbol,
                        exchange=self.kite.EXCHANGE_NSE,
                        transaction_type=t_type,
                        quantity=quantity,
                        order_type=self.kite.ORDER_TYPE_SLM,
                        trigger_price = sl_price,
                        product=self.kite.PRODUCT_MIS,
                        tag=self.strategy_tag,
                        variety=self.kite.VARIETY_REGULAR)
        
        my_entered_order = self.my_orders[order_id]
        my_entered_order.target_order = response
        return my_entered_order
        
    
    
    def observe_position(self, symbol, enter_exit, buy_sell):
        # observe options and future, get option chain and log its data, also get quote of it. log both
        if symbol not in self.nifty_options_stocks:
            self.logger.info("KITE1015: symbol {} not present in options stock".format(symbol))
            return
        ltp = self.kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"] 
        put_call = "PE"
        if buy_sell == "BUY":
            put_call = "CE"
        if enter_exit == "enter":
            #chooseOptionChain(symbol, put_call, ltp)
            pass
        else:
            #chooseOptionChain2(symbol, put_call, ltp)
            pass
        pass
    
    def cancelOrder(self,order_id):
        # Modify order given order id
        self.kite.cancel_order(order_id=order_id, variety=self.kite.VARIETY_REGULAR)  
        
        
    def squareOffEverything(self):
        #fetching orders and position information   
        self.logger.info("KITE1016: Squaring off everything ...")
        positions = self.getPositions()
        
        #closing all open position
        for trade in positions:
            if trade["quantity"] > 0:
                self.squareOffOrderAndSL(trade["tradingsymbol"], "BUY", trade["quantity"])
            if trade["quantity"] < 0:
                self.squareOffOrderAndSL(trade["tradingsymbol"], "SELL", abs(trade["quantity"]))
    
        
        #closing all pending orders
        orders = self.getOrders()
        ord_df = pd.DataFrame(orders)
        drop = []
        pending = ord_df[ord_df['status'].isin(["TRIGGER PENDING","OPEN"])]["order_id"].tolist()
        self.logger.info("KITE1017: pending orders {}".format(pending))
        attempt = 0
        while len(pending)>0 and attempt<5:
            pending = [j for j in pending if j not in drop]
            for order in pending:
                try:
                    self.logger.info("KITE1018: Day end square off cancelling orders {}".format(order))
                    self.cancelOrder(order)
                    drop.append(order)
                except:
                    self.logger.info("unable to delete order id : {}".format(order))
                    attempt+=1
        self.logger.info("KITE1019: Its past 3:10 PM, Successfully square off everything .. ending ")
        pass
    
    def getExistingPosition(self,symbol):
        # check if position exists before squareoff
        positions = self.getPositions()
        qty = [item["quantity"] for item in positions if item["tradingsymbol"]==symbol]
        return qty
    
    def getOrdersMap(self):
        orders = self.getOrders()
        return {t.order_id: t for t in orders}
    
    
    def getExistingOrder(self,symbol):
        # it is more probably used to get stop loss order, to edit it
        orders = self.getOrders()
        order = [item for item in orders if item["tradingsymbol"] == symbol and item["status"] in self.valid_order_status]
        if len(order) == 1:
            return order[0]
        else:
            self.logger.info("KITE1020: More than 1 order found for {} order {}".format(symbol, order))
            return None
    
    def isOrderOrPositionExists(self, symbol):
        # check if order is already in pending or position is already build before entering the trade
        positions = self.getPositions()
        orders = self.getOrders()
        order = [item for item in orders if item["tradingsymbol"] == symbol and item["status"] in self.valid_order_status]
        position = [item for item in positions if item["tradingsymbol"] == symbol and item["quantity"] != 0]
        if len(position) >= 1 or len(order) >= 1:
            self.logger.info("KITE1021: Position/Order already exists for {}".format(symbol))
            return True
        return False
    
    def getQuantityForInvestment(self, lastTradedPrice):
        return abs(int(self.invetment_amount / lastTradedPrice))
    
    # TODO : not yet finished
    def checkOrderStatus(self):
        trades_may_not_exited = [item for item in self.my_orders.values() if item.is_trade_exited == False]
        orders_map = self.getOrdersMap()
        
        for trades in trades_may_not_exited:
            if trades.target_order:
                latest_updates_order = orders_map[trades.target_order['order_id']]
                if latest_updates_order['status'] == 'OPEN':
                    pass
                pass
            if trades.sl_order:
                pass
            
    def observerTradeCheck(self, time_for_next_cycle):
        start_time = time.time()
        check_after_every = 20
        observer_trade_keys = [item for item in self.my_orders.keys() if item.startswith("observer_")]
        if not observer_trade_keys:
            self.logger.info("KITE1024: no trades found")
            time.sleep(time_for_next_cycle)
            return
        while (time.time() - start_time <= (time_for_next_cycle+check_after_every)):
            for key in observer_trade_keys:
                if key in self.my_orders:
                    symbol = self.my_orders[key].symbol
                    self.logger.info("KITE1027: not existing order found for {}".format(symbol))
                    enter_price = self.my_orders[key].enter_price
                    enter_type = self.my_orders[key].enter_type
                    symbol_ohlc = self.fetchOHLCExtendedAll([symbol], "1minute", 1)[symbol]
                    high = max (symbol_ohlc['high'].iloc[-1] , symbol_ohlc['high'].iloc[-2])
                    low = min (symbol_ohlc['low'].iloc[-1] , symbol_ohlc['low'].iloc[-2])
                    if enter_type == "CALL" and high > enter_price:
                        #TODO: add CE order, choose option chain
                        self.logger.info("KITE1027: Can add trade now")
                        self.my_orders.pop(key, None)
                    elif enter_type == "PUT" and low < enter_price:
                        #TODO: add PE order
                        self.logger.info("KITE1027: Can add trade now2")
                        self.my_orders.pop(key, None)
            time.sleep(check_after_every)
        time.sleep(time_for_next_cycle - (time.time() - start_time))
        
    def chooseOptionsChain(self,ticker,instument_type="CE"):
        
        pass
        
                
                
class TradeSetup:
    
    def logger_setup(self, log_file_name, date_strftime_format):
        logger = logging.getLogger("custom_logger")
        logger.setLevel(logging.INFO)  # Set minimum log level
        logger.propagate = False  # IMPORTANT → prevents root duplication
        
        # Clear existing handlers (safe for re-runs)
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(log_file_name, mode="a")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", date_strftime_format))
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", date_strftime_format))
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger
            
            
