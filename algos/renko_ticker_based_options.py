# -*- coding: utf-8 -*-
"""
Created on Mon May 19 00:53:25 2025

@author: usalotagi

check ichimoku cloud bull for 1 hour - if its in bull go fo renko
-- in renko check continously - if 2nd green candle apear, buy call and  a red candle exit 
-- for second green candle, a red and a previous green need to be checked
-- exit all at end of day 
-- start creating ranko candle with fixed brick - take size from kite everyday
-- start trading after 9:45 only -- but we are  working on tick data - so we can also exxecute at early of the day 
-- or as early as 9:30 **
"""

# -*- coding: utf-8 -*-
"""
Zerodha Kite Connect - Renko implementation using streaming Data

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""


from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
import datetime as dt
import os
import pytz
from kiteconnect.exceptions import NetworkException
import sys
import time
import logging
import locale
import threading
import numpy as np



def now_in_timezone():
    """Returns the current time in the default timezone."""
    return dt.datetime.now(DEFAULT_TIMEZONE)

invalid_token_tickers = []
def fetchOHLCExtendedAll(tickers, interval, period_days):
    entire_data = {}
    for ticker in tickers:
        try:
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except NetworkException as e:
            print("Possible too many request error, retyring for ", ticker, e)
            time.sleep(0.2)
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except Exception as e:
            print("Possible invalid token for", ticker, e)
            invalid_token_tickers.append(ticker)
    return entire_data


def chooseOptionChainATM_ITM(symbol, strike_tic):
    token_list = []
    for symbol in tickers:
        ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]
        #global filtered , sorted_data, option_chosen, latest_expiry_options
        option_name = symbol
        if ticker_options_name[symbol]:
            option_name = ticker_options_name[symbol]
            
        filtered = [item for item in options_expiring_near_future if item["name"]==option_name and item["instrument_type"]=="CE"]
        latest_expiry = min(item['expiry'] for item in filtered)
        
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] < ltp]
        option_chosen_CE_ATM = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
        token_list.appen(option_chosen_CE_ATM)
        
        filtered = [item for item in options_expiring_near_future if item["name"]==option_name and item["instrument_type"]=="PE"]
        latest_expiry = min(item['expiry'] for item in filtered)
        
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] > ltp]
        option_chosen_PE_ATM = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
        token_list.appen(option_chosen_PE_ATM)
        
        for option_chosen in token_list:
            option_chosen_ltp = kite.quote("NFO:" + option_chosen["tradingsymbol"])["NFO:" + option_chosen["tradingsymbol"]]
            lot_size = option_chosen["lot_size"]
            last_price = option_chosen_ltp["last_price"]
            #last_quantity = option_chosen_ltp["last_quantity"]
            last_trade_time = option_chosen_ltp["last_trade_time"]
            instrument_type = option_chosen["instrument_type"]
            asking_price = option_chosen_ltp["depth"]["buy"][0]["price"]
            offer_price = option_chosen_ltp["depth"]["sell"][0]["price"]
            logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, option_chosen["strike"], option_chosen["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
        
    return token_list


def chooseOptionChain(symbol, instrument_type, ltp, opType):
    #global filtered , sorted_data, option_chosen, latest_expiry_options
    option_name = symbol
    if ticker_options_name[symbol]:
        option_name = ticker_options_name[symbol]
        
    filtered = [item for item in options_expiring_near_future if item["name"]==option_name and item["instrument_type"]==instrument_type]
    #sorted_data = sorted(filtered, key=lambda x: x['strike'])
    #sorted_data = sorted(filtered, key=lambda x: (-x['expiry'].toordinal(), x['strike']))
    latest_expiry = min(item['expiry'] for item in filtered)
    
    option_chosen = None
    if opType == 'ATM' and instrument_type == 'CE':
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] < ltp]
        option_chosen = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
    elif opType == 'ATM' and instrument_type == 'PE':
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] > ltp]
        option_chosen = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))

    option_chosen_ltp = kite.quote("NFO:" + option_chosen["tradingsymbol"])["NFO:" + option_chosen["tradingsymbol"]]
    lot_size = option_chosen["lot_size"]
    last_price = option_chosen_ltp["last_price"]
    #last_quantity = option_chosen_ltp["last_quantity"]
    last_trade_time = option_chosen_ltp["last_trade_time"]
    asking_price = option_chosen_ltp["depth"]["buy"][0]["price"]
    offer_price = option_chosen_ltp["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, option_chosen["strike"], option_chosen["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    
    #chosen_options_all[symbol] = option_chosen
    return option_chosen


def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    df['Chikou_span'] = df["close"].shift(-shift_size)
    
entire_data_hr = {}
def checkHourlyBull(ticker):
    df = entire_data_hr[ticker]
    ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26)
    df = df.dropna(subset=["Senkou_span_A", "Senkou_span_B"])
    if df.empty:
        return False
    latest = df.iloc[-1]
    current_price = latest['close']
    span_a = latest['Senkou_span_A']
    span_b = latest['Senkou_span_B']
    cloud_top = max(span_a, span_b)
    cloud_bottom = min(span_a, span_b)
    # Bullish if current price is above the cloud
    is_bull = current_price > cloud_top
    is_bear = current_price < cloud_bottom
    return is_bull, is_bear
        

def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

def tokenLookupOptions(tickers):
    token_list = []
    for symbol in tickers:
        """
        isHourlyBull = checkHourlyBull(symbol)[0]
        isHourlyBear = checkHourlyBull(symbol)[1]
        instrument_type = None
        if isHourlyBull:
            instrument_type = "CE"
        if isHourlyBear:
            instrument_type = "PE"
        if instrument_type == None:
            continue
        """
        symbol_ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]
        op_ch = chooseOptionChain(symbol, "CE", symbol_ltp , "ATM")
        op_ch_2 = chooseOptionChain(symbol, "PE", symbol_ltp , "ATM")
        #ticker_options_name[ticker] = op_ch["name"]
        token_list.append(op_ch)
        token_list.append(op_ch_2)
    return token_list

def getTickerFromInsToken(int_token):
    for option in options_itm:
        if option.get("instrument_token") == int_token:
            for key, value in ticker_options_name.items():
                if value == option["name"]:
                    return key, option.get("instrument_type")
    return None, None  # Return None if not found  


def instrumentLookup(symbol):
    try:
        return nse_instrument_df[nse_instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1
        
def fetchOHLC(ticker, interval, from_date, to_date):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    instrument = instrumentLookup(ticker)
    #print("fetchOHLC", ticker, instrument, interval, from_date, to_date)
    data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
    if data.empty:
        logger.info("RMS109: No data found for ", ticker)
        return data
    data.set_index("date",inplace=True)
    return data

def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR'][-1]

def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a(fast moving average) = 12; 
                      b(slow moving average) =26; 
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

def macd_xover_refresh(macd,ticker):
    global macd_xover
    if macd["MACD"].iloc[-1]>macd["Signal"].iloc[-1]:
        macd_xover[ticker]="bullish"
    elif macd["MACD"].iloc[-1]<macd["Signal"].iloc[-1]:
        macd_xover[ticker]="bearish"
        
def calculate_macd_slope(macd, window=5):
    """
    Calculate slope of MACD using linear regression over the last N points.
    """
    macd_series = macd["MACD"].values
    if len(macd_series) < window:
        return 0.0  # Not enough data
    y = macd_series[-window:]
    x = np.arange(window)
    slope = np.polyfit(x, y, 1)[0]
    return slope
        
def renkoBrickSize(ticker):
    return min(10,max(1,round(1.5*atr(fetchOHLC(ticker,"60minute",60),200),0)))

def pandaEma(DF):
    df = DF.copy()
    return df

def getPositions():
    a = 0
    while a < 10:
        try:
            positions = kite.positions()["day"]
            positions = [item for item in positions if item["product"] == "MIS"]
            break
        except:
            logger.info("can't extract position data..retrying")
            a+=1
    return positions

def getOrders():
    a = 0
    while a < 10:
        try:
            orders = kite.orders()
            orders = [item for item in orders if item["tag"] == "renko_macd"]
            break
        except:
            logger.info("can't extract position data..retrying")
            a+=1
    return orders

def getRelavantOrders():
    a = 0
    while a < 10:
        try:
            orders = kite.orders()
            orders = [item for item in orders if "tags" in item and "renko_macd" in item["tags"] and "enter" in item["tags"]]
            break
        except:
            logger.info("can't extract position data..retrying")
            a+=1
    return orders

def placeMarketOrderSL(symbol,buy_sell,quantity,sl_price):    
    # Place an intraday market order on NSE
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_BUY
        t_type_sl=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_SELL
        t_type_sl=kite.TRANSACTION_TYPE_BUY
    else:
        t_type=None
        t_type_sl=None
    
    if (len(getRelavantOrders()) >= max_trades):
        logger.info("RMS119: More than {} positions already build, no entering the trade {}".format(max_trades, symbol))
        return "",""
    # you can use VARIETY_CO also
    response = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO, # NSE, BSE
                    transaction_type=t_type, # buy / sell
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET, # market price order - will get executed at market value
                    product=kite.PRODUCT_MIS, # intraday
                    tag=["renko_macd", "enter"],
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
    # for ORDER_TYPE_SLM we only provide trigger price, no price
    """limit_price = sl_price * 0.995 # 1% below than trigger price
    limit_price = round(round(limit_price / 0.05) * 0.05, 2) # 0.05 is tick size
    response2 = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SL,
                    trigger_price = sl_price,
                    price=limit_price,              # This is your limit price
                    product=kite.PRODUCT_MIS,
                    tag="renko_macd",
                    variety=kite.VARIETY_REGULAR)"""
    return response, None

def cancelOrder(order_id):
    # Modify order given order id
    logger.info("RMS150: Day end square off cancelling orders {}".format(order_id))
    kite.cancel_order(order_id=order_id, variety=kite.VARIETY_REGULAR) 

def squareOffOrderAndSL(symbol,buy_sell,quantity):
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_BUY
    else:
        t_type=None
    
    # first cancelling stop loss order as if get double executed will cause huge margin block
    sl_response = None
    orders = getOrders()
    for order in orders:
        if order["tradingsymbol"] == symbol and order['status'] == 'TRIGGER PENDING':
            # cancel order
            sl_response = kite.cancel_order(order_id=order["order_id"], variety=kite.VARIETY_REGULAR)  
            logger.info("RMS140: cancel stoploss order for {} response {} ".format(symbol, sl_response))
    # triggering exxit position
    response = kite.place_order(tradingsymbol=symbol,
                exchange=kite.EXCHANGE_NFO,
                transaction_type=t_type,
                quantity=quantity,
                order_type=kite.ORDER_TYPE_MARKET,
                product=kite.PRODUCT_MIS,
                tag="renko_macd",
                variety=kite.VARIETY_REGULAR)
    logger.info("RMS130: square off done for {} response {} ".format(symbol, response))    
    return response, sl_response

def squareOffEverything(fullExit = True):
    #fetching orders and position information   
    logger.info("RMS160: Squaring off everything ...")
    positions = getPositions()
 
    if not fullExit:
        positions = [item for item in positions if getTickerFromInsToken(int(item['instrument_token']))[0] in tickers]
    
    #closing all open position
    for trade in positions:
        if trade["quantity"] > 0:
            squareOffOrderAndSL(trade["tradingsymbol"], "BUY", trade["quantity"])
        if trade["quantity"] < 0:
            squareOffOrderAndSL(trade["tradingsymbol"], "SELL", abs(trade["quantity"]))

    
    #closing all pending orders
    orders = getOrders()
    if not fullExit:
        orders = [item for item in orders if getTickerFromInsToken(int(item['instrument_token']))[0] in tickers]

    ord_df = pd.DataFrame(orders)
    drop = []
    pending = ord_df[ord_df['status'].isin(["TRIGGER PENDING","OPEN"])]["order_id"].tolist()
    logger.info("pending orders {}".format(pending))
    attempt = 0
    while len(pending)>0 and attempt<5:
        pending = [j for j in pending if j not in drop]
        for order in pending:
            try:
                cancelOrder(order)
                drop.append(order)
            except:
                logger.info("unable to delete order id : {}".format(order))
                attempt+=1
    logger.info("RMS170: Its past 3:10 PM, Successfully square off everything .. ending ")
    pass

def getExistingPosition(symbol):
    # check if position exists before squareoff
    positions = getPositions()
    # if there are multiple trades of same symbol, output will be 0, 0, 10, 0
    qty = [item["quantity"] for item in positions if item["tradingsymbol"]==symbol]
    return sum(qty)


valid_order_status = ["OPEN", "TRIGGER PENDING", "OPEN PENDING"]

def getExistingOrder(symbol):
    # it is more probably used to get stop loss order, to edit it
    orders = getOrders()
    order = [item for item in orders if item["tradingsymbol"] == symbol and item["status"] in valid_order_status]
    if len(order) == 1:
        return order[0]
    else:
        logger.info("RMS180: More than 1 order found for {} order {}".format(symbol, order))
        return None

def isOrderOrPositionExists(symbol):
    # check if order is already in pending or position is already build before entering the trade
    positions = getPositions()
    orders = getOrders()
    order = [item for item in orders if item["tradingsymbol"] == symbol and item["status"] in valid_order_status]
    position = [item for item in positions if item["tradingsymbol"] == symbol and item["quantity"] != 0]
    if len(position) >= 1 or len(order) >= 1:
        logger.info("RMS190: Position/Order already exists for {}".format(symbol))
        return True
    return False
   
def renkoOperation(ticks):
    #print("renko operation tickers ticker ", len(ticks))
    # renko for now we do not sell, capp put we only buy 
    #print(ticks)
    for tick in ticks:
        brick_change = None
        ticker = None
        try:
            ticker, ins_type = getTickerFromInsToken(int(tick['instrument_token']))
            ticker_key = ticker + "_" + ins_type
            old_brick_number = renko_param[ticker_key]["brick"]
            if renko_param[ticker_key]["upper_limit"] == None:
                renko_param[ticker_key]["upper_limit"] = float(tick['last_price']) + renko_param[ticker_key]["brick_size"]
                renko_param[ticker_key]["lower_limit"] = float(tick['last_price']) - renko_param[ticker_key]["brick_size"]
            if float(tick['last_price']) > renko_param[ticker_key]["upper_limit"]:
                gap = (float(tick['last_price'] - renko_param[ticker_key]["upper_limit"]))//renko_param[ticker_key]["brick_size"]
                renko_param[ticker_key]["lower_limit"] = renko_param[ticker_key]["upper_limit"] + (gap*renko_param[ticker_key]["brick_size"]) - renko_param[ticker_key]["brick_size"]
                renko_param[ticker_key]["upper_limit"] = renko_param[ticker_key]["upper_limit"] + ((1+gap)*renko_param[ticker_key]["brick_size"])
                renko_param[ticker_key]["brick"] = max(1,renko_param[ticker_key]["brick"]+(1+gap))
                if old_brick_number <= 1 and renko_param[ticker_key]["brick"] == 2:
                    brick_change = "BUY"
            if float(tick['last_price']) < renko_param[ticker_key]["lower_limit"]:
                gap = (renko_param[ticker_key]["lower_limit"] - float(tick['last_price']))//renko_param[ticker_key]["brick_size"]
                renko_param[ticker_key]["upper_limit"] = renko_param[ticker_key]["lower_limit"] - (gap*renko_param[ticker_key]["brick_size"]) + renko_param[ticker_key]["brick_size"]
                renko_param[ticker_key]["lower_limit"] = renko_param[ticker_key]["lower_limit"] - ((1+gap)*renko_param[ticker_key]["brick_size"])
                renko_param[ticker_key]["brick"] = min(-1,renko_param[ticker_key]["brick"]-(1+gap))
                if old_brick_number > 0 and renko_param[ticker_key]["brick"] == -1:
                    brick_change = "BUY_SQ_OFF"
            if brick_change or old_brick_number != renko_param[ticker_key]["brick"]:
                logger.info("{}: brick number={}, old_brick_number={}, last price={}, brick_size={}, singnal={}"\
                      .format(ticker_key, renko_param[ticker_key]["brick"], old_brick_number, tick['last_price'], renko_param[ticker_key]["brick_size"], macd_xover[ticker]))
            # wait for x seconds before acting on renko direction change
            # we can do it by saving first encounter time
        except Exception as e:
            logger.error("exception occured in renko calculation for {} as {}".format(ticker, e))
            pass 
        try:
            # TODO : check RSI also https://youtu.be/cduGjKzPfbg
            # 2 period RSI crosses above 50 in 5 minute chart - momentum indicator - NO on 15 min
            # price above 50 ema - bullish - NO on 15 min chart
            # TODO: go with supertrend or ema 50 on 5 min chart, also try macd in 5 min chart
            if brick_change == "BUY":
                opt_name, option_in_consideration = getOptionFromInsToken(tick['instrument_token'])
                #generic_bull = entire_data_macd[ticker]["close"].iloc[-1] > entire_data_macd[ticker]["ema_50"].iloc[-1]
                if ins_type == 'CE' and macd_xover[ticker] == "bullish":
                    checkPositionAndExecute(ticker, option_in_consideration)
                    #print("$$ BUY triggered ", tick['instrument_token'])
                elif ins_type == 'PE' and macd_xover[ticker] == "bearish":
                    checkPositionAndExecute(ticker, option_in_consideration)
                    #print("$$ BUY triggered ", tick['instrument_token'])
            elif brick_change == "BUY_SQ_OFF":
                opt_name, option_in_consideration = getOptionFromInsToken(tick['instrument_token'])
                checkPositionAndQuareOff(ticker, option_in_consideration)
                #print("$$ SQ OFF triggered ", tick['instrument_token'])
                pass
        except Exception as e:
            logger.error("exception occured in order place for {} as {}".format(ticker, e))
            pass 

def getOptionFromInsToken(ins_token):
    for option in options_itm:
        if option["instrument_token"] == ins_token:
            return option["name"], option
        
def getOptionFromNameAndType(option_name, ins_type):
    for option in options_itm:
        if option["name"] == option_name and option["instrument_type"] == ins_type:
            return option

    
def checkPositionAndExecute(symbol, option_in_consideration):
    
    if now_in_timezone() > eleven_am and now_in_timezone() < one_thirty_pm:
        # if time is between 11 to 1:30 skip as markets are in sideways 
        logger.warning("Not taking trades between {} to {}".format(eleven_am, one_thirty_pm))
        return
    if now_in_timezone() > three_five_pm:
        logger.warning("Not taking trades after {}".format(three_five_pm))
        return
    if symbol in paper_trading_stocks:
        ltp = kite.quote("NFO:" + option_in_consideration["tradingsymbol"])["NFO:" + option_in_consideration["tradingsymbol"]]['last_price']
        logger.warning(f"..... executing PAPER trade for {symbol} with ltp {ltp} and symbol {option_in_consideration['tradingsymbol']}")
        return
    logger.info("checking position and execute", symbol, option_in_consideration)
    with lock:
        trade_symbol = option_in_consideration['tradingsymbol']
        if not isOrderOrPositionExists(trade_symbol):
            ltp = kite.quote("NFO:" + option_in_consideration["tradingsymbol"])["NFO:" + option_in_consideration["tradingsymbol"]]['last_price']
            sl_price = ltp - 2*renko_param[ticker + "_" + option_in_consideration["instrument_type"]]["brick_size"]
            lot_multiplier = 1
            if option_in_consideration['name'] in lot_multiplier_by_option_name:
                lot_multiplier = lot_multiplier_by_option_name[option_in_consideration['name']]
                cost = lot_multiplier * option_in_consideration['lot_size'] * ltp
                while (cost > max_investment_per_trade):
                    lot_multiplier = lot_multiplier - 1 
                    cost = lot_multiplier * option_in_consideration['lot_size'] * ltp
                    if lot_multiplier <= 0:
                        logger.info("Buy cancelled for trade_symbol {} bue to huge cost {}".format(trade_symbol, cost))
                        return
                    
            lot_size = lot_multiplier * option_in_consideration['lot_size']
            logger.info("$$$$ BUY triggered {} ltp {} sl {} lot_size {}".format(option_in_consideration['tradingsymbol'], ltp, sl_price, lot_size))
            placeMarketOrderSL(trade_symbol,'BUY',lot_size,sl_price)
            pass
    pass

def checkPositionAndQuareOff(symbol, option_in_consideration):
    #print("checkPositionAndQuareOff", symbol, option_in_consideration)
    with lock:
        trade_symbol = option_in_consideration["tradingsymbol"]
        ltp = kite.quote("NFO:" + trade_symbol)["NFO:" + trade_symbol]
        qty = getExistingPosition(trade_symbol)
        if qty != 0:
            logger.info("&&&& SQ OFF triggered {} ltp {} qty {}".format(trade_symbol, ltp['last_price'], qty))
        elif symbol in paper_trading_stocks:
            logger.info("..... SQ OFF PAPER trading triggered {} ltp {} qty {}".format(trade_symbol, ltp['last_price'], qty))
        if qty > 0:
            squareOffOrderAndSL(trade_symbol,'BUY',abs(qty))
        elif qty < 0:
            squareOffOrderAndSL(trade_symbol,'SELL',abs(qty))

def supertrend(DF,n,m):
    """function to calculate Supertrend given historical candle data
        n = n day ATR - usually 7 day ATR is used
        m = multiplier - usually 2 or 3 is used"""
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["B-U"]=((df['high']+df['low'])/2) + m*df['ATR'] 
    df["B-L"]=((df['high']+df['low'])/2) - m*df['ATR']
    df["U-B"]=df["B-U"]
    df["L-B"]=df["B-L"]
    ind = df.index
    for i in range(n,len(df)):
        if df['close'][i-1]<=df['U-B'][i-1]:
            df.loc[ind[i],'U-B']=min(df['B-U'][i],df['U-B'][i-1])
        else:
            df.loc[ind[i],'U-B']=df['B-U'][i]    
    for i in range(n,len(df)):
        if df['close'][i-1]>=df['L-B'][i-1]:
            df.loc[ind[i],'L-B']=max(df['B-L'][i],df['L-B'][i-1])
        else:
            df.loc[ind[i],'L-B']=df['B-L'][i]  
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['close'][test-1]<=df['U-B'][test-1] and df['close'][test]>df['U-B'][test]:
            df.loc[ind[test],'Strend']=df['L-B'][test]
            break
        if df['close'][test-1]>=df['L-B'][test-1] and df['close'][test]<df['L-B'][test]:
            df.loc[ind[test],'Strend']=df['U-B'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['U-B'][i-1] and df['close'][i]<=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
        elif  df['Strend'][i-1]==df['U-B'][i-1] and df['close'][i]>=df['U-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['close'][i]>=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['L-B'][i]
        elif df['Strend'][i-1]==df['L-B'][i-1] and df['close'][i]<=df['L-B'][i]:
            df.loc[ind[i],'Strend']=df['U-B'][i]
    return df['Strend']


def main(now_minute):
    
    if now_in_timezone() < macd_change_time:
        macd_candle_interval = "minute"
        run_after_interval = 1
    else:
        macd_candle_interval = "5minute"
        run_after_interval = 5
    
    
    # now_minute we get each minute, but need to run after 15 mins only
    whole_min = (now_minute // run_after_interval ) * run_after_interval 
    global renko_param, entire_data_macd
    if tickers[0] in entire_data_macd:
        if (entire_data_macd[tickers[0]].index[-1].minute == whole_min):
            return
    
    entire_data_macd = fetchOHLCExtendedAll(tickers,macd_candle_interval,4) # changed from period 4 to 1
    
    for ticker in tickers:
        logger.info(f"starting {macd_candle_interval} candle calculations for ... {ticker}")
        try:
            # beautify 15 min candles
            """index = entire_data_macd[ticker].index[-1]
            if (index.minute > whole_min):
                entire_data_macd[ticker].drop(entire_data_macd[ticker].index[-1], inplace=True)
            index = entire_data_macd[ticker].index[-1]"""
            
            #macd = MACD(entire_data_macd[ticker],12,26,9)
            # modified MACD setting for more and fast responsive
            macd = MACD(entire_data_macd[ticker],5,13,4)
            macd_xover_refresh(macd,ticker)
            
            # 50 and 20 ema calculate
            #entire_data_macd[ticker]["ema_20"]=entire_data_macd[ticker]["close"].ewm(span=20,min_periods=20).mean()
            #entire_data_macd[ticker]["ema_50"]=entire_data_macd[ticker]["close"].ewm(span=50,min_periods=50).mean()
            
            #generic_bull = entire_data_macd[ticker]["close"].iloc[-1] > entire_data_macd[ticker]["ema_50"].iloc[-1]
            
            # here we are filtering macd signals which are in generic bullish zone represented by value more than 50 ema
            # or we can also add 21 > 50 ema or 100 day SMA < 21 day EMA, for now added very simple check 
            # we only buy here, sell is done by renko only
            if macd_xover[ticker] == "bullish" and renko_param[ticker + "_CE"]["brick"] >=2:
                option_in_consideration = getOptionFromNameAndType(ticker_options_name[ticker], 'CE')
                logger.info("executing by MACD, by buying call")
                checkPositionAndExecute(ticker, option_in_consideration)
            if macd_xover[ticker] == "bearish" and renko_param[ticker + "_PE"]["brick"] >=2:
                option_in_consideration = getOptionFromNameAndType(ticker_options_name[ticker], 'PE')
                logger.info("executing by MACD sell, but buying put")
                checkPositionAndExecute(ticker, ticker_options_name[ticker])
            
        except Exception as e:
            logger.error("API error for ticker : {} as {}".format(ticker,e))
        

def mainSupertrend(now_minute):
    
    macd_candle_interval = "minute"
    run_after_interval = 1
    
    # now_minute we get each minute, but need to run after 15 mins only
    whole_min = (now_minute // run_after_interval ) * run_after_interval 
    global renko_param, entire_data_macd
    if tickers[0] in entire_data_macd:
        if (entire_data_macd[tickers[0]].index[-1].minute == whole_min):
            return
    
    entire_data_macd = fetchOHLCExtendedAll(tickers,macd_candle_interval,4) # changed from period 4 to 1
    
    for ticker in tickers:
        logger.info(f"starting {macd_candle_interval} candle calculations for ... {ticker}")
        try:
            # beautify 15 min candles
            """index = entire_data_macd[ticker].index[-1]
            if (index.minute > whole_min):
                entire_data_macd[ticker].drop(entire_data_macd[ticker].index[-1], inplace=True)
            index = entire_data_macd[ticker].index[-1]"""
            supertrend_reversal = None
            sup_series = supertrend(entire_data_macd[ticker],10,2)
            if sup_series.iloc[-1] > entire_data_macd[ticker]["close"][-1] and sup_series.iloc[-2] < entire_data_macd[ticker]["close"][-2]:
                supertrend_reversal = "red"
            elif sup_series.iloc[-1] < entire_data_macd[ticker]["close"][-1] and sup_series.iloc[-2] > entire_data_macd[ticker]["close"][-2]:
                supertrend_reversal = "green"
                
            if sup_series.iloc[-1] > entire_data_macd[ticker]["close"][-1]:
                supertrend_xover[ticker] = "bullish"
            elif sup_series.iloc[-1] < entire_data_macd[ticker]["close"][-1]:
                supertrend_xover[ticker] = "bearish"
            
            # 50 and 20 ema calculate
            #entire_data_macd[ticker]["ema_20"]=entire_data_macd[ticker]["close"].ewm(span=20,min_periods=20).mean()
            #entire_data_macd[ticker]["ema_50"]=entire_data_macd[ticker]["close"].ewm(span=50,min_periods=50).mean()
            
            #generic_bull = entire_data_macd[ticker]["close"].iloc[-1] > entire_data_macd[ticker]["ema_50"].iloc[-1]
            
            # here we are filtering macd signals which are in generic bullish zone represented by value more than 50 ema
            # or we can also add 21 > 50 ema or 100 day SMA < 21 day EMA, for now added very simple check 
            # we only buy here, sell is done by renko only
            if supertrend_reversal == "green" and renko_param[ticker + "_CE"]["brick"] >=2:
                option_in_consideration = getOptionFromNameAndType(ticker_options_name[ticker], 'CE')
                logger.info("Executing by Supertrend qreversal, by buying call")
                checkPositionAndExecute(ticker, option_in_consideration)
            if supertrend_reversal == "red" and renko_param[ticker + "_PE"]["brick"] >=2:
                option_in_consideration = getOptionFromNameAndType(ticker_options_name[ticker], 'PE')
                logger.info("Executing by Supertrend qreversal sell, but buying put")
                checkPositionAndExecute(ticker, ticker_options_name[ticker])
            
        except Exception as e:
            logger.error("API error for ticker : {} as {}".format(ticker,e))
    
######################################### Main execution ######################

DEFAULT_TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change this to your desired timezone
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)

options_instruments = kite.instruments(exchange="NFO")
today_date = now_in_timezone()
# we are not filtering todays expirty
options_expiring_near_future = [item for item in options_instruments if item["segment"] == "NFO-OPT" and item["expiry"] > today_date.date()]
#chosen_options_all = {}
nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)

#three_twenty_pm = today_date.replace(hour=15, minute=20, second=0, microsecond=0)
# exiting these all scalpings by 9:29 and working on macd in next
three_twenty_pm = today_date.replace(hour=9, minute=40, second=0, microsecond=0)
all_square_off = False
#three_five_pm = today_date.replace(hour=15, minute=5, second=0, microsecond=0)
three_five_pm = today_date.replace(hour=9, minute=30, second=0, microsecond=0)
eleven_am = today_date.replace(hour=11, minute=0, second=0, microsecond=0)
one_thirty_pm = today_date.replace(hour=13, minute=30, second=0, microsecond=0)
macd_change_time = today_date.replace(hour=15, minute=30, second=0, microsecond=0)


lock = threading.Lock()

locale.setlocale(locale.LC_ALL, '')
local_tz = pytz.timezone('Asia/Kolkata')
max_trades = 1
date_strftime_format = "%Y-%m-%d %H:%M:%S"
log_file_name = "options_scalping_tick_renko_" + str(today_date.day) + ".txt"
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt=date_strftime_format, 
                    handlers=[logging.FileHandler(log_file_name, mode="a"),logging.StreamHandler()])

logger = logging.getLogger("custom_logger")
    
#####################update ticker list######################################
macd_xover = {}
ticker_options_name = {}
renko_param = {}
supertrend_xover = {}

tickers = [ "ICICIBANK","HDFCBANK", "NIFTY 50", "NIFTY BANK", "RELIANCE", "INFY", "TCS", "SBIN", 
           "AXISBANK", "NIFTY FIN SERVICE"]
tickers = ["NIFTY BANK"]
paper_trading_stocks = ["RELIANCE"]


for ticker in tickers:
    macd_xover[ticker] = None
    supertrend_xover[ticker] = None
    ticker_options_name[ticker] = None

ticker_options_name = {"NIFTY 50":"NIFTY", "NIFTY BANK":"BANKNIFTY", "SBIN":"SBIN", "HDFCBANK":"HDFCBANK", "TCS":"TCS"}
# sbin 2, hdfc 8, tcs 10
lot_multiplier_by_option_name = {"NIFTY":1, "BANKNIFTY":1}
max_investment_per_trade = 50000

# nifty, bank nofty, reliance, tcs, axis currently are active
# chaging the brick size to different than current 10, 20, 4
renko_param["NIFTY 50_PE"] = {"brick_size" : 15, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["NIFTY 50_CE"] = {"brick_size" : 15, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["NIFTY BANK_PE"] = {"brick_size" : 30, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["NIFTY BANK_CE"] = {"brick_size" : 30, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["SBIN_PE"] = {"brick_size" : 2, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["SBIN_CE"] = {"brick_size" : 2, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["ICICIBANK_PE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["ICICIBANK_CE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["HDFCBANK_PE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["HDFCBANK_CE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["RELIANCE_PE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["RELIANCE_CE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["INFY_PE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["INFY_CE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["TCS_PE"] = {"brick_size" : 2.4, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["TCS_CE"] = {"brick_size" : 2.4, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["AXISBANK_PE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["AXISBANK_CE"] = {"brick_size" : 1, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["NIFTY FIN SERVICE_PE"] = {"brick_size" : 25, "upper_limit":None, "lower_limit":None, "brick":0}
renko_param["NIFTY FIN SERVICE_CE"] = {"brick_size" : 25, "upper_limit":None, "lower_limit":None, "brick":0}



#create KiteTicker object
kws = KiteTicker(key_secret[0],kite.access_token)

nine_sixteen_am = today_date.replace(hour=9, minute=15, second=2, microsecond=0)
logger.warning("Not taking trades before {}".format(nine_sixteen_am))
while now_in_timezone() < nine_sixteen_am:
    time.sleep(0.2)

#tokens = tokenLookup(instrument_df,tickers)
entire_data_hr = fetchOHLCExtendedAll(tickers, "60minute", period_days=150) 
entire_data_macd = {}

options_itm = tokenLookupOptions(tickers)
tokens = [item["instrument_token"] for item in options_itm ]
print("************* found toekns ", tokens)

#renko_param = {}
for ticker in tickers:
    renko_param[ticker+"_CE"] = {"brick_size":round(atr(fetchOHLCExtendedAll([ticker],"minute",4)[ticker],200),2),"upper_limit":None, "lower_limit":None,"brick":0}
    renko_param[ticker+"_PE"] = {"brick_size":round(atr(fetchOHLCExtendedAll([ticker],"minute",4)[ticker],200),2),"upper_limit":None, "lower_limit":None,"brick":0}
    
    
start_minute = dt.datetime.now().minute

def on_ticks(ws,ticks):
    global start_minute
    renkoOperation(ticks)
    now_minute = dt.datetime.now().minute
    if abs(now_minute - start_minute) >= 1:
        start_minute = now_minute
        main(now_minute)

def on_connect(ws,response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP,tokens)
    
def on_close(ws, code, reason):
    print("WebSocket closed:", code, reason)
    
kws.on_ticks=on_ticks
kws.on_connect=on_connect
kws.on_close = on_close
#kws.connect()

try:
    print ("*************** connection started")
    kws.connect(threaded=True)  # Non-blocking mode
    while True:
        time.sleep(1)
        #print("is tis inturrupting ???? ")
        if now_in_timezone() > three_twenty_pm:
            squareOffEverything(all_square_off)
            sys.exit()
        pass  # Keep main thread alive
except KeyboardInterrupt:
    print("Exiting...")
    kws.close()


    
