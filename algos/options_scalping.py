# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 21:03:37 2025

@author: usalotagi
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May 27 15:18:28 2025

@author: usalotagi

create renko from 5 min chart and cross check with 5 min MACD, then inter exit, no other consition is needed

# also try stock with 10 min renko, but movement is not high enough
"""



from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import pytz
from kiteconnect.exceptions import NetworkException
import time
import logging
import locale
import threading
from stocktrends import Renko
import numpy as np
import requests
import math
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
import json
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

path_to_db = r"C:\Users\usalotagi\Python\Stock\hiekinashi\db_op.json"

db = TinyDB(path_to_db, storage=serialization)


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


def getQuoteOption(symbol):
    option_chosen_ltp = None
    count = 0;
    while (option_chosen_ltp is None and count < 5):
        try:
            option_chosen_ltp = kite.quote("NFO:" + symbol)["NFO:" + symbol]
            #print("option_chosen_ltp", option_chosen_ltp, symbol)
        except Exception as e:
            time.sleep(0.1)
            count = count + 1
            print("tried this many times", count, symbol, "with exception", e,)
            pass
    return option_chosen_ltp
        
"""        
def chooseOptionChainATM_ITM_4(tickers):
    global token_list
    token_list = []
    for symbol in tickers:
        ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]
        global filtered , sorted_data, option_chosen, latest_expiry_options
        option_name = symbol
        strike_tic_jump = None
        if ticker_options_name[symbol]["optionName"]:
            option_name = ticker_options_name[symbol]["optionName"]
            strike_tic_jump = ticker_options_name[symbol]["strike_tic_jump"]
            
        filtered = [item for item in options_expiring_near_future if item["name"]==option_name and item["instrument_type"]=="CE"]
        latest_expiry = min(item['expiry'] for item in filtered)
        
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] < ltp]
        option_chosen_CE_ATM = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
        token_list.append(option_chosen_CE_ATM)
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_CE_ATM["strike"] - 2*strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_CE_ATM["strike"] + strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_CE_ATM["strike"] + 4*strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_CE_ATM["strike"] + 8*strike_tic_jump)))
        
        filtered = [item for item in options_expiring_near_future if item["name"]==option_name and item["instrument_type"]=="PE"]
        latest_expiry = min(item['expiry'] for item in filtered)
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] > ltp]
        option_chosen_PE_ATM = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
        token_list.append(option_chosen_PE_ATM)
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_PE_ATM["strike"] - 2*strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_PE_ATM["strike"] + strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_PE_ATM["strike"] - 4*strike_tic_jump)))
        apendUpdate(token_list, (item for item in filtered if item['expiry'] == latest_expiry and item["strike"] == (option_chosen_PE_ATM["strike"] - 8*strike_tic_jump)))

    for option_chosen in token_list:
        option_chosen_ltp = getQuoteOption(option_chosen["tradingsymbol"])
        lot_size = option_chosen["lot_size"]
        last_price = option_chosen_ltp["last_price"]
        last_trade_time = option_chosen_ltp["last_trade_time"]
        instrument_type = option_chosen["instrument_type"]
        asking_price = option_chosen_ltp["depth"]["buy"][0]["price"]
        offer_price = option_chosen_ltp["depth"]["sell"][0]["price"]
        logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, option_chosen["strike"], option_chosen["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
        
    return token_list
"""


def apendUpdate(token_list, iterator):
    match = next(iterator, None)
    if match:
        token_list.append(match)
    
def getOptionNameFromSynbol(symbol):
    option_name = symbol
    if ticker_options_name[symbol]["optionName"]:
        option_name = ticker_options_name[symbol]["optionName"]
    return option_name

def chooseOptionChain(symbol, instrument_type, ltp, opType):
    global filtered , sorted_data, option_chosen, latest_expiry_options
    option_name = symbol
    if ticker_options_name[symbol]["optionName"]:
        option_name = ticker_options_name[symbol]["optionName"]
        
    filtered = [item for item in options_finalized if item["name"]==option_name and item["instrument_type"]==instrument_type]
    latest_expiry = min(item['expiry'] for item in filtered)
    
    option_chosen = None
    if opType == 'ATM' and instrument_type == 'CE':
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] < ltp]
        if len(latest_expiry_options) == 0:
            print("EERR latest_expiry_options length is zero, ltp is ", symbol, ltp, latest_expiry)
            return None
        option_chosen = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
    elif opType == 'ATM' and instrument_type == 'PE':
        latest_expiry_options = [item for item in filtered if item['expiry'] == latest_expiry and item["strike"] > ltp]
        if len(latest_expiry_options) == 0:
            print("EERR latest_expiry_options length is zero, ltp is ", symbol, ltp, latest_expiry)
            return None
        option_chosen = min(latest_expiry_options, key=lambda x: abs(x['strike'] - ltp))
        
    """
    option_chosen_ltp = kite.quote("NFO:" + option_chosen["tradingsymbol"])["NFO:" + option_chosen["tradingsymbol"]]
    lot_size = option_chosen["lot_size"]
    last_price = option_chosen_ltp["last_price"]
    last_quantity = option_chosen_ltp["last_quantity"]
    last_trade_time = option_chosen_ltp["last_trade_time"]
    asking_price = option_chosen_ltp["depth"]["buy"][0]["price"]
    offer_price = option_chosen_ltp["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, option_chosen["strike"], option_chosen["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    """
    
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


def checkPriceAboveLowOfCloud(df, a=9, b=26, c=52):
    ichimoko(df, fast=a, slow=b, span_b=c, shift_size=b)
    df = df.dropna(subset=["Senkou_span_A", "Senkou_span_B"])
    if df.empty:
        return False
    latest = df.iloc[-1]
    cloud_bottom = min(latest['Senkou_span_A'], latest['Senkou_span_B'])
    #logger.info(f"got information of ichimoku {latest['Senkou_span_A']} {latest['Senkou_span_B']} {latest['close'] } \n{latest}")
    return latest['close'] > cloud_bottom

        

def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

def getTickerFromInsToken(int_token):
    for option in options_finalized:
        if option.get("instrument_token") == int_token:
            for key, value in ticker_options_name.items():
                if value["optionName"] == option["name"]:
                    return key, option.get("instrument_type")
    return None, None  # Return None if not found  

def getParametersFromOptionName(optionName):
    for key, value in ticker_options_name.items():
        if value["optionName"] == optionName:
            return value
    return None

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

def fetchOHLCFromInstrument(instrument, interval, from_date, to_date):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
    if data.empty:
        logger.info("RMS109: No data found for ", ticker)
        return data
    data.set_index("date",inplace=True)
    return data

invalid_token_instruments = []
def fetchOHLCExtendedAllFromInstrument(instruments, interval, period_days):
    entire_data = {}
    for ins_token in instruments:
        try:
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ins_token] = fetchOHLCFromInstrument(ins_token, interval, from_date, dt.date.today())
            entire_data[ins_token].dropna(inplace=True,how="all")
            
        except NetworkException as e:
            print("Possible too many request error, retyring for ", ins_token, e)
            time.sleep(0.2)
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ins_token] = fetchOHLCFromInstrument(ins_token, interval, from_date, dt.date.today())
            entire_data[ins_token].dropna(inplace=True,how="all")
            
        except Exception as e:
            print("Possible invalid token for", ins_token, e)
            invalid_token_instruments.append(ins_token)
    return entire_data

def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR'].iloc[-1]

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
    df["Histogram"] = df["MACD"] - df["Signal"]
    df.dropna(inplace=True)
    return df

def is_histogram_expanding(series, n=3):
    """Returns True if histogram has expanded upward for last n bars."""
    if len(series) < n:
        return False
    return all(x < y for x, y in zip(series[-n:], series[-n+1:]))

def macd_xover_refresh(macd,ticker):
    global macd_xover
    if macd["MACD"].iloc[-1]>macd["Signal"].iloc[-1]:
        macd_xover[ticker]="bullish"
    elif macd["MACD"].iloc[-1]<macd["Signal"].iloc[-1]:
        macd_xover[ticker]="bearish"
        
def macd_xover_is_bullish(macd,ticker):
    if macd["MACD"].iloc[-1]>=macd["Signal"].iloc[-1]:
        return True
    elif macd["MACD"].iloc[-1]<macd["Signal"].iloc[-1]:
        return False
    
def macd_xover_is_near_crossover_bullish(macd,ticker):
    if macd["MACD"].iloc[-1]>macd["Signal"].iloc[-1]:
        # now currently its in bull, now check if it was bear in last n session
        wasBear = any(macd["MACD"].iloc[i] < macd["Signal"].iloc[i] for i in [-2, -3, -4])
        return wasBear
    return False
    
def macd_histogram_trend(macd,ticker):
    global macd_xover
    hist_current = macd["Histogram"].iloc[-1]
    hist_prev = macd["Histogram"].iloc[-2]

    if hist_current > hist_prev and hist_current > 0:
        macd_xover[ticker] = "bullish"
    elif hist_current < hist_prev and hist_current < 0:
        macd_xover[ticker] = "bearish"
    else:
        macd_xover[ticker] = "neutral"
        
def macd_histogram_trend_bull(macd):
    global macd_xover
    hist_current = macd["Histogram"].iloc[-1]
    hist_prev = macd["Histogram"].iloc[-2]

    if hist_current > hist_prev and hist_current > 0:
        return True
    return False
        
def atrNEW(df, n):
    df = df.copy()
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    return tr.rolling(n).mean()

def supertrendNEW(df, n=7, m=2):
    df = df.copy()
    df['ATR'] = atrNEW(df, n)
    hl2 = (df['high'] + df['low']) / 2
    df['UpperBand'] = hl2 + m * df['ATR']
    df['LowerBand'] = hl2 - m * df['ATR']
    df['Strend'] = np.nan
    trend = True  # True for bullish, False for bearish

    for i in range(n, len(df)):
        if trend:
            if df['close'].iloc[i] > df['LowerBand'].iloc[i-1]:
                df.loc[df.index[i], 'Strend'] = df['LowerBand'].iloc[i]
            else:
                trend = False
                df.loc[df.index[i], 'Strend'] = df['UpperBand'].iloc[i]
        else:
            if df['close'].iloc[i] < df['UpperBand'].iloc[i-1]:
                df.loc[df.index[i], 'Strend'] = df['UpperBand'].iloc[i]
            else:
                trend = True
                df.loc[df.index[i], 'Strend'] = df['LowerBand'].iloc[i]
    
    return df[['close', 'Strend', 'UpperBand', 'LowerBand']]


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
            orders = [item for item in orders if "tags" in item and strategy_tag in item["tags"]]
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
            orders = [item for item in orders if "tags" in item and strategy_tag in item["tags"] and "enter" in item["tags"]]
            break
        except:
            logger.info("can't extract position data..retrying")
            a+=1
    return orders

def placeMarketOrder(symbol,buy_sell,quantity):
    # Place an intraday market order on NSE
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_SELL
    else:
        t_type=None
    
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
                    tag=[strategy_tag, "enter"],
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
    return response


def placeLimitOrder(symbol,buy_sell,quantity,limit_price):    
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_SELL
    else:
        t_type=None
    
    # you can use VARIETY_CO also
    response = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO, # NSE, BSE
                    transaction_type=t_type, # buy / sell
                    quantity=quantity,
                    price=limit_price,
                    order_type=kite.ORDER_TYPE_LIMIT, # market price order - will get executed at market value
                    product=kite.PRODUCT_MIS, # intraday
                    tag=[strategy_tag],
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {} and limit_price {}".format(buy_sell, symbol, quantity, limit_price))
    return response


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
                    tag=[strategy_tag, "enter"],
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
    # for ORDER_TYPE_SLM we only provide trigger price, no price
    limit_price = sl_price * 0.995 # 1% below than trigger price
    limit_price = round(round(limit_price / 0.05) * 0.05, 2) # 0.05 is tick size
    response2 = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SL,
                    trigger_price = sl_price,
                    price=limit_price,              # This is your limit price
                    product=kite.PRODUCT_MIS,
                    tag=[strategy_tag],
                    variety=kite.VARIETY_REGULAR)
    return response, response2

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
                tag=[strategy_tag],
                variety=kite.VARIETY_REGULAR)
    logger.info("RMS130: square off done for {} response {} ".format(symbol, response))    
    return response, sl_response

def squareOffEverything():
    #fetching orders and position information   
    logger.info("RMS160: Squaring off everything ...")
    positions = getPositions()
    
    #closing all open position
    for trade in positions:
        if trade["quantity"] > 0:
            squareOffOrderAndSL(trade["tradingsymbol"], "BUY", trade["quantity"])
        if trade["quantity"] < 0:
            squareOffOrderAndSL(trade["tradingsymbol"], "SELL", abs(trade["quantity"]))

    
    #closing all pending orders
    orders = getOrders()
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
   

def getOptionFromInsToken(ins_token):
    for option in options_finalized:
        if option["instrument_token"] == ins_token:
            return option["name"], option

# option sell with reduced margin
def checkPositionAndExecuteSell(symbol, option_in_consideration):
    #trade_symbol = option_in_consideration['tradingsymbol']
    #ltp = kite.quote("NFO:" + trade_symbol)["NFO:" + trade_symbol]['last_price']
    # considering we are selling PE, we need to buy future PE to reduce margin
    if "margin_reducer_jump" in ticker_options_name[symbol]:
        margin_reducer_jump = ticker_options_name[symbol]["margin_reducer_jump"]
    else:
        strikes = sorted([ item["strike"] for item in options_finalized if item["expiry"]==option_in_consideration["expiry"] and item["instrument_type"]==option_in_consideration["instrument_type"]])
        min_gap_between_strikes = min(b - a for a, b in zip(strikes, strikes[1:]))
        margin_reducer_jump = 5 * min_gap_between_strikes
        
    margin_reducer_strike = option_in_consideration["strike"] - margin_reducer_jump
    
    margin_reducer_option = [ item for item in options_finalized if item["strike"]==margin_reducer_strike and item["expiry"]==option_in_consideration["expiry"] and item["instrument_type"]==option_in_consideration["instrument_type"]][0]
    if margin_reducer_option:
        margin_reducer_option_tr_list.append(margin_reducer_option['tradingsymbol'])
        margin_reducer_option_list.append(margin_reducer_option)
        placeMarketOrder(margin_reducer_option['tradingsymbol'],'BUY',option_in_consideration['lot_size'])
        placeMarketOrder(option_in_consideration['tradingsymbol'],'SELL',option_in_consideration['lot_size'])
    
    pass
    
def checkPositionAndExecute(symbol, option_in_consideration, isOptionSell = False):
    #print("checking position and execute", symbol, option_in_consideration)
    #if now_in_timezone() > trade_gap_start and now_in_timezone() < trade_gap_end:
    #    # if time is between 11 to 1:30 skip as markets are in sideways 
    #    logger.warn("Not taking trades between {} to {}".format(trade_gap_start, trade_gap_end))
    #    return
    if paper_trade:
        ltp = kite.quote("NFO:" + option_in_consideration["tradingsymbol"])["NFO:" + option_in_consideration["tradingsymbol"]]['last_price']
        logger.info("\n\n$$$$ BUY triggered {} ltp {}".format(option_in_consideration['tradingsymbol'], ltp))
        global paper_trade_qty
        paper_trade_qty = 1
        return
    if now_in_timezone() > not_enter_trade_after:
        logger.warn("Not taking trades after {}".format(not_enter_trade_after))
        return
    
    #with lock:
    trade_symbol = option_in_consideration['tradingsymbol']
    if not isOrderOrPositionExists(trade_symbol):
        if isOptionSell:
            checkPositionAndExecuteSell(symbol, option_in_consideration)
            return
        ltp = kite.quote("NFO:" + option_in_consideration["tradingsymbol"])["NFO:" + option_in_consideration["tradingsymbol"]]['last_price']
        sl_price = ltp - 2*renko_param[ticker + "_" + option_in_consideration["instrument_type"]]["brick_size"]
        lot_multiplier = 1
        opParamaters = getParametersFromOptionName(option_in_consideration['name'])
        if opParamaters:
            lot_multiplier = opParamaters["lot_multiplier"]
            cost = lot_multiplier * option_in_consideration['lot_size'] * ltp
            while (cost > max_investment_per_trade):
                lot_multiplier = lot_multiplier - 1 
                cost = lot_multiplier * option_in_consideration['lot_size'] * ltp
                if lot_multiplier <= 0:
                    logger.info("Buy cancelled for trade_symbol {} bue to huge cost {}".format(trade_symbol, cost))
                    return
                
        lot_size = lot_multiplier * option_in_consideration['lot_size']
        logger.info("$$$$ BUY triggered {} ltp {} sl {} lot_size {}".format(option_in_consideration['tradingsymbol'], ltp, sl_price, lot_size))
        placeMarketOrder(trade_symbol,'BUY',lot_size)
        db.insert({"symbol": trade_symbol, "type": "BUY", "quantity":lot_size, "ticker": symbol, "name": option_in_consideration['name'], "instrument_token": option_in_consideration["instrument_token"]} )
        pass
    pass

def checkPositionAndQuareOff(symbol, option_in_consideration, sq_off_per=1):
    print("**checkPositionAndQuareOff", symbol, option_in_consideration, sq_off_per)
    trade_symbol = option_in_consideration["tradingsymbol"]
    ltp = kite.quote("NFO:" + trade_symbol)["NFO:" + trade_symbol]
    qty = getExistingPosition(trade_symbol)
    if (sq_off_per != 1):
        if ( (qty / option_in_consideration["lot_size"]) % 2 == 0):
            final_qty = math.floor(abs(qty * sq_off_per))
        else:
            return
    else:
        final_qty = qty
    
    logger.info("&&&& SQ OFF triggered {} ltp {} qty {} and final_qty {}".format(trade_symbol, ltp['last_price'], qty, final_qty))
    if qty > 0:
        #squareOffOrderAndSL(trade_symbol,'BUY',abs(qty))
        squareOffOrderAndSL(trade_symbol,'BUY',final_qty)
        db.remove(StockHolding.symbol == trade_symbol)
        pass
    elif qty < 0:
        #squareOffOrderAndSL(trade_symbol,'SELL',abs(qty))
        squareOffOrderAndSL(trade_symbol,'SELL',final_qty)
        # close associated margin saver option
        margin_reducer_option = [ item for item in margin_reducer_option_list if item["expiry"]==option_in_consideration["expiry"] and item["instrument_type"]==option_in_consideration["instrument_type"]][0]
        checkPositionAndQuareOff(symbol, margin_reducer_option)
        pass
            
# Tenkan_sen, Kijun_sen, Senkou_span_A, Senkou_span_B, Chikou_span
# 
def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    
    df['Chikou_span'] = df["close"].shift(-shift_size)
    
def calculate_renko_brick_size(df, window=300):
    """
    Calculate Renko brick size using Caveman algorithm.
    
    Parameters:
        df (pd.DataFrame): Should contain 'high', 'low', and 'close' columns.
        window (int): Number of latest rows to consider (default = 300).
    
    Returns:
        float: Suggested brick size.
    """
    if len(df) < window:
        raise ValueError(f"Data must have at least {window} rows")
    
    df = df.tail(window).copy()
    
    # Calculate True Range for each candle
    df['prev_close'] = df['close'].shift(1)
    df['tr'] = df[['high', 'low']].max(axis=1) - df[['low', 'prev_close']].min(axis=1)
    
    # Calculate average true range
    atr = df['tr'].mean()
    
    # Round to a clean number (nearest 0.5 or 1 depending on value)
    if atr > 100:
        brick_size = round(atr / 10) * 10
    elif atr > 10:
        brick_size = round(atr)
    elif atr > 1:
        brick_size = round(atr * 2) / 2
    else:
        brick_size = round(atr, 2)
    
    return brick_size


def ema_crossover(df, fast=5, slow=20):
    df = df.copy()
    df['EMA_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['close'].ewm(span=slow, adjust=False).mean()

    df['prev_fast'] = df['EMA_fast'].shift(1)
    df['prev_slow'] = df['EMA_slow'].shift(1)

    # Create a column for crossover signal
    df['signal'] = None
    df.loc[(df['prev_fast'] < df['prev_slow']) & (df['EMA_fast'] > df['EMA_slow']), 'signal'] = 'bullish'
    df.loc[(df['prev_fast'] > df['prev_slow']) & (df['EMA_fast'] < df['EMA_slow']), 'signal'] = 'bearish'

    return df[['close', 'EMA_fast', 'EMA_slow', 'signal']]


def is_price_above_session_vwap(df: pd.DataFrame) -> bool:
    """
    Returns True if the latest close price is above the session VWAP.
    
    :param df: DataFrame with columns ['high', 'low', 'close', 'volume']
    :return: Boolean indicating if price is above VWAP
    """
    today = pd.Timestamp.now(tz=df.index.tz).normalize()
    df_today = df[df.index.normalize() == today]
    
    if df_today.empty:
        return True
    
    # Typical Price
    tp = (df_today['high'] + df_today['low'] + df_today['close']) / 3
    vwap = (tp * df_today['volume']).cumsum() / df_today['volume'].cumsum()
    # Store it in the DataFrame if needed
    #df_today['vwap'] = vwap
    # Compare last price to last VWAP
    #return df_today['close'].iloc[-1] > df_today['vwap'].iloc[-1]
    return df_today['close'].iloc[-1] > vwap.iloc[-1]


def calculate_adx(df, period=14):
    """
    Calculate ADX (Average Directional Index) for a given OHLC DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with 'High', 'Low', 'Close' columns.
        period (int): Period for ADX calculation (default is 14).

    Returns:
        pd.DataFrame: Original DataFrame with added columns:
                      'ADX', '+DI', '-DI', 'DX'
    """
    df = df.copy()

    # Calculate True Range (TR)
    df['prev_close'] = df['Close'].shift(1)
    df['high_low'] = df['High'] - df['Low']
    df['high_pc'] = abs(df['High'] - df['prev_close'])
    df['low_pc'] = abs(df['Low'] - df['prev_close'])
    df['TR'] = df[['high_low', 'high_pc', 'low_pc']].max(axis=1)

    # Calculate +DM and -DM
    df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']),
                         np.maximum(df['High'] - df['High'].shift(1), 0), 0)
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)),
                         np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)

    # Smooth the values
    tr_smooth = df['TR'].rolling(window=period).sum()
    plus_dm_smooth = df['+DM'].rolling(window=period).sum()
    minus_dm_smooth = df['-DM'].rolling(window=period).sum()

    # Calculate +DI and -DI
    df['+DI'] = 100 * (plus_dm_smooth / tr_smooth)
    df['-DI'] = 100 * (minus_dm_smooth / tr_smooth)

    # Calculate DX
    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])

    # Calculate ADX
    df['ADX'] = df['DX'].rolling(window=period).mean()

    # Clean up
    df.drop(columns=['prev_close', 'high_low', 'high_pc', 'low_pc'], inplace=True)

    return df


def heikinashi(df):
    df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    df['HA_Open'] = 0.0 
    for i in range(1, len(df)):
        df['HA_Open'].iat[i] = (df['HA_Open'].iat[i - 1] + df['HA_Close'].iat[i - 1]) / 2
    df['HA_Open'].iat[0] = df['open'].iat[0]
    df['HA_High'] = df[['HA_Open', 'HA_Close']].join(df['high']).max(axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close']].join(df['low']).min(axis=1)
    
    df['Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] == df['HA_Open'])
    df['Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] == df['HA_Open'])
    df['Doji_Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    df['Doji_Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    # medium to large body - to be calculated with percentage of close price
    df['large_body'] = np.abs(df['HA_Close'] - df['HA_Open']) > df['HA_Close'] * 0.001
    
    # size matter video from trading institute youtube 
    # check in 1 hour if we are in bull with respect to ichimoko cloud then enter with 15 min data 
    # stock whoes earning are nearing announced 
    
    # 3 green candle / or dojo and then 2/3 large body red -- then enter trade , also  confirmt with candles 
   

def remove_partial_candle_min(df, timeframe_minutes):
    if df.empty:
        return df
    # Get last candle timestamp
    last_index = df.index[-1]
    #logger.info(f" minutes {last_index.minute} and {(dt.datetime.now().minute // timeframe_minutes) * timeframe_minutes}")
    if last_index.minute >= (dt.datetime.now().minute // timeframe_minutes) * timeframe_minutes:
        #logger.info(" dropping .... mins")
        return df.drop(df.index[-1])
    return df


def renko_DF(DF, bricks_size):
    "function to convert ohlc data into renko bricks"
    df = DF.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:,[0,1,2,3,4,5]]
    df.columns = ["date","open","high","low","close","volume"]
    global renko_df
    renko_obj = Renko(df)
    #df2.brick_size = max(0.5,round(ATR(DF,120)["ATR"][-1],0)) #udemy
    renko_obj.brick_size = bricks_size
    
    #renko_df = df2.get_bricks()
    #renko_df = renko_obj.get_renko_df()
    renko_df = renko_obj.get_ohlc_data()
    renko_df["bar_num"] = np.where(renko_df["uptrend"]==True,1,np.where(renko_df["uptrend"]==False,-1,0))
    for i in range(1,len(renko_df["bar_num"])):
        if renko_df.loc[i, "bar_num"]>0 and renko_df.loc[i-1, "bar_num"]>0:
            renko_df.loc[i, "bar_num"]+=renko_df.loc[i-1, "bar_num"]
        elif renko_df.loc[i, "bar_num"]<0 and renko_df.loc[i-1, "bar_num"]<0:
            renko_df.loc[i, "bar_num"]+=renko_df.loc[i-1, "bar_num"]
    renko_df.drop_duplicates(subset="date",keep="last",inplace=True)
    return renko_df

def getOptionNameList(tickers):
    result = []
    for ticker in tickers:
        result.append(ticker_options_name[ticker]["optionName"])
        print(ticker_options_name[ticker]["optionName"])
    return result


def isHolidayToday():
    today = datetime.today()
    for event in holiday_List["FO"]:
        event_date_str = event.get("tradingDate", "")
        try:
            event_date = datetime.strptime(event_date_str, "%d-%b-%Y")
        except ValueError:
            continue
        
        if today.date() == event_date.date():
            return True
    return False
"""
def getOptionsStockList():
    op_st_list = []
    for op_stock in options_stock_data["data"]:
        op_st_list.append(op_stock.get("underlying", ""))
    return op_st_list"""

def getStocksWithEvent(purpose_filter, due_in_days):
    events = event_calendar
    today = datetime.today()
    cutoff_date = today + timedelta(days=due_in_days)
    matching_symbols = []
    for event in events:
        event_purpose = event.get("purpose", "").lower()
        event_date_str = event.get("date", "")
        try:
            event_date = datetime.strptime(event_date_str, "%d-%b-%Y")
        except ValueError:
            continue

        if (purpose_filter.lower() in event_purpose and
            today <= event_date <= cutoff_date):
            matching_symbols.append(event.get("symbol"))
            
    return matching_symbols

holiday_List = []
event_calendar = []
options_stock_data = []

def fetchNSEdata():
    
    global event_calendar, holiday_List, options_stock_data
    
    options = Options()
    #options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.nseindia.com")
        time.sleep(5)  # allow cookies to be set
        selenium_cookies = driver.get_cookies()
        cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua-platform":"Windows",
            "Connection": "keep-alive"
            
        }
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)
        
        url = "https://www.nseindia.com/api/event-calendar?"
        response = session.get(url)
        if response.status_code != 200:
            print("Error while getting calendar event")
        event_calendar = response.json()
        
        holiday_url = "https://www.nseindia.com/api/holiday-master?type=trading"
        holiday_response = session.get(holiday_url)
        if holiday_response.status_code != 200:
            print("Error while getting holiday_response")
        holiday_List = holiday_response.json()
        
        options_stock_url = "https://www.nseindia.com/api/liveEquity-derivatives?index=stock_opt"
        options_stock_url = "https://www.nseindia.com/api/master-quote"
        options_stock_response = session.get(options_stock_url)
        if options_stock_response.status_code != 200:
            print("Error while getting options_stock_response")
        options_stock_data = options_stock_response.json()
        
        """
        driver.get("https://www.nseindia.com/companies-listing/corporate-filings-event-calendar")
        time.sleep(2)
        table = driver.find_element(By.ID, "CFeventCalendarTable")
        rows = table.find_elements(By.TAG_NAME, "tr")
        headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
        events = []

        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) != len(headers):
                continue  # skip malformed rows

            row_data = {}
            for header, cell in zip(headers, cells):
                row_data[header] = cell.text.strip()

            events.append(row_data)
        print("size of events ", len(events))"""

    finally:
        driver.quit()
    
    return;
    
    
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


lock = threading.Lock()

locale.setlocale(locale.LC_ALL, '')
local_tz = pytz.timezone('Asia/Kolkata')
max_trades = 8
date_strftime_format = "%Y-%m-%d %H:%M:%S"
log_file_name = "options_scalping_candle_renko_" + str(today_date.day) + ".txt"
logger = logging.getLogger("custom_logger")
if not logger.hasHandlers():  # This prevents duplicate handlers
    logging.basicConfig(level=logging.INFO, 
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt=date_strftime_format, 
                        handlers=[logging.FileHandler(log_file_name, mode="a"),logging.StreamHandler()])


    
#####################update ticker list######################################
macd_xover = {}
ticker_options_name = {}


tickers = [ "ICICIBANK","HDFCBANK", "NIFTY 50", "NIFTY BANK", "RELIANCE", "INFY", "TCS", "SBIN", 
           "AXISBANK", "NIFTY FIN SERVICE"]
# , "NIFTY BANK", "RELIANCE", "TCS","AXISBANK"
tickers = ["NIFTY 50" ]
second_set_tickers = []
second_set_tickers_added = False

"""
fetchNSEdata()
if isHolidayToday():
    logging.info("Today is holiday")
    exit()
near_earning_stocks = getStocksWithEvent("Financial Results", 2)
#options_stock_list = getOptionsStockList()
options_stock_list = [item for item in near_earning_stocks if item in options_stock_data]
#tickers = list(set(options_stock_list + ticker))"""

for ticker in tickers:
    macd_xover[ticker] = None
    ticker_options_name[ticker] = None

max_investment_per_trade = 50000

ticker_options_name["NIFTY 50"] =   {"optionName":"NIFTY", "brick_size":5, "lot_multiplier":1, "strike_tic_jump":50, "margin_reducer_jump":500}
ticker_options_name["NIFTY BANK"] = {"optionName":"BANKNIFTY", "brick_size":5, "lot_multiplier":1, "strike_tic_jump":100, "margin_reducer_jump":1000}
ticker_options_name["SBIN"] =       {"optionName":"SBIN", "brick_size":1, "lot_multiplier":1, "strike_tic_jump":10, "margin_reducer_jump":100}
ticker_options_name["HDFCBANK"] =   {"optionName":"HDFCBANK", "brick_size":1, "lot_multiplier":1, "strike_tic_jump":20, "margin_reducer_jump":200}
ticker_options_name["RELIANCE"] =   {"optionName":"RELIANCE", "brick_size":1, "lot_multiplier":1, "strike_tic_jump":10, "margin_reducer_jump":100}
ticker_options_name["TCS"] =        {"optionName":"TCS", "brick_size":2.4, "lot_multiplier":1, "strike_tic_jump":20, "margin_reducer_jump":200}
ticker_options_name["AXISBANK"] =   {"optionName":"AXISBANK", "brick_size":1, "lot_multiplier":1, "strike_tic_jump":10, "margin_reducer_jump":100}

renko_param = {}

for ticker in tickers:
    renko_param[ticker + "_PE"] = {"brick_size":ticker_options_name[ticker]["brick_size"]  ,"upper_limit":None, "lower_limit":None,"brick":0}
    renko_param[ticker + "_CE"] = {"brick_size":ticker_options_name[ticker]["brick_size"]  ,"upper_limit":None, "lower_limit":None,"brick":0}
    
previous_close_data = {}
prev_close_ohlc = fetchOHLCExtendedAll(tickers, "day", 5);
for ticker in tickers:
    if prev_close_ohlc[ticker].iloc[-1].name.date() < dt.date.today():
        previous_close_data[ticker] = prev_close_ohlc[ticker].iloc[-1].close
    elif prev_close_ohlc[ticker].iloc[-2].name.date() < dt.date.today():
        previous_close_data[ticker] = prev_close_ohlc[ticker].iloc[-2].close
    
margin_reducer_option_list = []
margin_reducer_option_tr_list = []
optionNameList = getOptionNameList(tickers)
date_after_31_days = (today_date + dt.timedelta(days=31)).date()
options_finalized = [item for item in options_expiring_near_future if item["name"] in optionNameList and item["expiry"] < date_after_31_days]
entire_data_macd = {}
ohlc_renko ={}
strategy_tag = "options_1_min"
StockHolding = Query()

nine_sixteen_am = today_date.replace(hour=9, minute=15, second=45, microsecond=0)
if now_in_timezone() < nine_sixteen_am:
    logger.warning("Not taking trades before {}".format(nine_sixteen_am))
while now_in_timezone() < nine_sixteen_am:
    time.sleep(0.2)


option_interval = "minute"
option_high_tf = "3minute"
stock_interval = "3minute"
cycle_time = 1

option_interval = "3minute"
option_high_tf = "5minute"
stock_interval = "3minute"
cycle_time = 3

stock_fetch_period_days = 2
option_fetch_period_days = 2


start_minute = dt.datetime.now().minute


not_enter_trade_after = today_date.replace(hour=15, minute=5, second=0, microsecond=0)
trade_gap_start = today_date.replace(hour=11, minute=0, second=0, microsecond=0)
trade_gap_end = today_date.replace(hour=13, minute=30, second=0, microsecond=0)

trade_start_time = dt.datetime.combine(dt.date.today(), dt.time(9, 15)).timestamp()
three_20_pm_today = dt.datetime.combine(dt.date.today(), dt.time(15, 20)).timestamp()
second_set_addition_time = dt.datetime.combine(dt.date.today(), dt.time(9, 30)).timestamp()
my_squareoff_time = dt.datetime.combine(dt.date.today(), dt.time(15, 17)).timestamp()

    
paper_trade = False
paper_trade_qty = 0
STRATEGY_OPTION_SELL = False
strategy_and_brick_data = {}

while time.time() <= three_20_pm_today:
    try:
        # todo: wait for cycle sync 
        time_for_next_5_min_cycle = (60 * cycle_time) - dt.datetime.now().second
        logging.info("\n")
        logging.info("RBS500: sleeping for seconds {}".format(time_for_next_5_min_cycle))
        time.sleep(time_for_next_5_min_cycle)
        start_t = time.time()
        logging.info("RBS510: Now .. starting the loop")
        if time.time() < trade_start_time:
            logging.info("RBS520: not yet started trading time, wait for some more time {}".format(dt.datetime.now()))
            continue

        if (time.time() > my_squareoff_time):
            squareOffEverything()
            break
        
        if second_set_addition_time < time.time():
            if not second_set_tickers_added:
                tickers = tickers + second_set_tickers
                second_set_tickers_added = True
                
        ohlc_dict = fetchOHLCExtendedAll(tickers, stock_interval, stock_fetch_period_days)
        
        for ticker in tickers: 
            macd = MACD(ohlc_dict[ticker],8,21,5)   # was 8,21,5 here and giving good result, 5, 13, 4 was also used
            macd_xover_refresh(macd,ticker)
            #macd_histogram_trend(macd,ticker)
            
        
        positions = getPositions()
        #positions_opt = [item for item in positions if item["quantity"]!=0 and item["exchange"]=="NFO"]
        #positions_opt = [item for item in positions_opt if getTickerFromInsToken(item['instrument_token'])[0] in tickers]
        
        data_all = db.all()
        ordered_symbol = [item["instrument_token"] for item in data_all]
        positions_opt = [item for item in positions if item["quantity"]!=0 and item['instrument_token'] in ordered_symbol]
        
        dic_token_ticker = {}
        for position in positions_opt:
            name, opt = getOptionFromInsToken(position["instrument_token"])
            if opt["tradingsymbol"] not in margin_reducer_option_tr_list:
                if name in dic_token_ticker:
                    dic_token_ticker[name] = dic_token_ticker[name].add({"op_chain":opt, "buy_price":position["average_price"], "quantity":position["quantity"]})
                    pass
                else:    
                    dic_token_ticker[name] = [{"op_chain":opt, "buy_price":position["average_price"], "quantity":position["quantity"]}]
        
        
        for ticker in tickers:
            global df, here_ins_token
            # first check positions - act on them
            # get name from ticker 
            option_name = getOptionNameFromSynbol(ticker)
            if option_name in dic_token_ticker:
                options_list = dic_token_ticker[option_name]
                logger.info("found following active position {} for {}".format(options_list, ticker))
                for option_data_here in options_list:
                    options_buy_price = option_data_here["buy_price"]
                    option_here = option_data_here['op_chain']
                    here_ins_token = str(option_here["instrument_token"])
                    df = fetchOHLCExtendedAllFromInstrument([here_ins_token], option_interval, option_fetch_period_days)
                    
                    # beautifying the data by removing half data
                    """whole_min = dt.datetime.now().minute - 1
                    index = df[here_ins_token].index[-1]
                    if (index.minute > whole_min):
                        df[here_ins_token].drop(df[here_ins_token].index[-1], inplace=True)
                    index = df[here_ins_token].index[-1]"""
                    if (df[here_ins_token].index[-1].minute == dt.datetime.now().minute):
                        df[here_ins_token].drop(df[here_ins_token].index[-1], inplace=True)
                    
                    macd = MACD(df[here_ins_token],8,21,5) #8,21,5
                    options_macd_is_bull = macd_xover_is_bullish(macd,ticker)
                    options_macd_is_bear = (not options_macd_is_bull)
                    
                    heikinashi(df[here_ins_token])
                    ha_small_down_momentum = df[here_ins_token]['HA_Close'].iloc[-1] < df[here_ins_token]['HA_Open'].iloc[-1]
                    
                    #ren_brick_size = calculate_renko_brick_size(df[here_ins_token])
                    ren_brick_size = round(atr(df[here_ins_token], 14) * 1.5)
                    ren_brick_size_previous = strategy_and_brick_data[ticker + option_here["instrument_type"]]
                    renko = renko_DF(df[here_ins_token], ren_brick_size)
                    ohlc_renko[ticker] = renko
                    
                    op_ltp = kite.ltp([here_ins_token])[here_ins_token]["last_price"]
                    logger.info(f"Ticker {ticker} {option_here['tradingsymbol']}, options_macd_is_bear {options_macd_is_bear}")
                    logger.info(f"Renko data brick number {ohlc_renko[ticker]['bar_num'].iloc[-1]}, brick_size {ren_brick_size}, ren_brick_size_previous {ren_brick_size_previous}")
                    
                    if not STRATEGY_OPTION_SELL:
                        if ha_small_down_momentum:
                            checkPositionAndQuareOff(ticker, option_here)
                            strategy_and_brick_data[ticker + option_here["instrument_type"]] = None
                        #elif op_ltp > options_buy_price + (2*ren_brick_size):
                        #    logger.info(f"Target achieved for {ticker} {option_here['tradingsymbol']} ltp {op_ltp} and options_buy_price {options_buy_price}")
                        #    checkPositionAndQuareOff(ticker, option_here, 0.5)
                        #    strategy_and_brick_data[ticker + option_here["instrument_type"]] = None
                        
                    else:
                        if option_data_here["quantity"] > 0:
                            if options_macd_is_bear:
                                checkPositionAndQuareOff(ticker, option_here)
                                strategy_and_brick_data[ticker + option_here["instrument_type"]] = None
                            #elif op_ltp > options_buy_price + (2*ren_brick_size):
                            #    logger.info(f"** Target achieved for {ticker} {option_here['tradingsymbol']} ltp {op_ltp} and options_buy_price {options_buy_price}")
                            #    checkPositionAndQuareOff(ticker, option_here, 0.5)
                            #    strategy_and_brick_data[ticker + option_here["instrument_type"]] = None
                        else:
                            if options_macd_is_bull:
                                checkPositionAndQuareOff(ticker, option_here)
                                strategy_and_brick_data[ticker + option_here["instrument_type"]] = None
                        pass
                #since position already exists, no entering again
                continue
            
            
            ticker_ltp = kite.ltp("NSE:" + ticker)["NSE:" + ticker]["last_price"]
            option_in_consideration_CE = chooseOptionChain(ticker, "CE", ticker_ltp, "ATM")
            option_in_consideration_PE = chooseOptionChain(ticker, "PE", ticker_ltp, "ATM")
            token_atm_put_call = [option_in_consideration_PE["instrument_token"], option_in_consideration_CE["instrument_token"]]
            
            df = fetchOHLCExtendedAllFromInstrument(token_atm_put_call, option_interval, option_fetch_period_days)
            df_high_tf = fetchOHLCExtendedAllFromInstrument(token_atm_put_call, option_high_tf, option_fetch_period_days)
            
            for option_here in [option_in_consideration_CE,option_in_consideration_PE]:
                here_ins_token = option_here["instrument_token"]
                # beautifying the data by removing half data
                logger.info(f"Before beautify {df[here_ins_token].iloc[-1]} and name {option_here['tradingsymbol']}")
                """whole_min = dt.datetime.now().minute - 1
                index = 
                if (index.minute > whole_min):
                    df[here_ins_token].drop(df[here_ins_token].index[-1], inplace=True)
                #index = df[here_ins_token].index[-1]"""
                if (df[here_ins_token].index[-1].minute == dt.datetime.now().minute):
                    df[here_ins_token].drop(df[here_ins_token].index[-1], inplace=True)
                #df[here_ins_token] = remove_partial_candle_min(df[here_ins_token], cycle_time)
                logger.info(f"After beautify {df[here_ins_token].iloc[-1]} and name {option_here['tradingsymbol']}")
                
                # chatgpt: 1 min (6,13,5), 3 min (7,20,5), 5 min (8,21,5), 15 sec (3,9,3), day (12,26,9)
                macd = MACD(df[here_ins_token],8,21,5)
                options_macd_is_nr_co_bull = macd_xover_is_near_crossover_bullish(macd,ticker)
                options_macd_is_bull = macd_xover_is_bullish(macd, ticker)
                macd_slope_ok = calculate_macd_slope(macd, 3) > 0
                #macd_histogram_trend_bull = macd_histogram_trend_bull(macd)
                macd_above_zero = macd['MACD'].iloc[-1] > 0
                
                # NEW strategy  - hiekinashi macd 3 9 3 - 3 min timeframe and use 5 min for filtering 
                # OR hiekinashi green enter red exit - when underlying asset is in up macd 
                # use supertrend as filter 
                # OR USE HIGH TIMEFRAME OHLC MACD , then hiekienashi on 3 min
                # 3 min candle is better suited, because in 5 min, all gains tends to get roded in single candle
                # so when we see it in 3 min, it happens over 2 candles so is smooth 
                # 1 min - too many trades 
                # use supertrend - stop loss, ADX 25, macd 5,13,4, price above vwap
                heikinashi(df[here_ins_token])
                ha_small_momentum = df[here_ins_token]['HA_Close'].iloc[-1] > df[here_ins_token]['HA_Open'].iloc[-1]
                
                priceAboveMinOfCloud = checkPriceAboveLowOfCloud(df[here_ins_token], 5, 13, 26)
                
                # for higher timeframe 5,13,4 is good as it is fast and uqick
                macd = MACD(df_high_tf[here_ins_token],8,21,5) # chatgpt suggest 8,21,5 here
                options_high_tf_macd_is_bull = macd_xover_is_bullish(macd, ticker)
                # to check if macd is strong, 12, 26, 9 -- 2 is threshold, for 8,21,5 we will take 1.5
                histogram_above_threshold = macd["Histogram"].iloc[-1] > 0.5
                
                EMA_fast = df[here_ins_token]['close'].ewm(span=5, adjust=False).mean()
                EMA_slow = df[here_ins_token]['close'].ewm(span=20, adjust=False).mean()
                ema_bull = EMA_fast.iloc[-1] > EMA_slow.iloc[-1]
                
                # TODO: for stocks as well If ATR as a % of price is very low (e.g., ATR(14) / close < 1.5%), skip trading. - along with EMA and MACD
                # for options echimoku is good, because options prices does not stay consolidated, it goes down with time 
                #is_price_above_vwap = is_price_above_session_vwap(df[here_ins_token])
                
                #adx_is_good = calculate_adx(df[here_ins_token])['vwap'].iloc[-1] > 20
                
                avg_volume = df[here_ins_token]['volume'].iloc[-20:].mean()
                volume_confirmation = df[here_ins_token]['volume'].iloc[-1] > avg_volume * 1.5
                
                #ren_brick_size = calculate_renko_brick_size(df[here_ins_token])
                ren_brick_size = round(atr(df[here_ins_token], 14) * 1.5)
                renko = renko_DF(df[here_ins_token], ren_brick_size)
                ohlc_renko[ticker] = renko
                # if ohlc_renko[ticker]["bar_num"].iloc[-1]>=2
                
                op_ltp = kite.ltp([here_ins_token])[str(here_ins_token)]["last_price"]
                price_above_ema_20 = op_ltp > EMA_slow.iloc[-1] 
                #logger.info(f"Ticker {ticker} {option_here['tradingsymbol']}, brick {ohlc_renko[ticker]['bar_num'].iloc[-1]} and {ohlc_renko[ticker]['bar_num'].iloc[-2]}, macd {macd_xover[ticker]}, brick_size {ren_brick_size}, ticker_ltp {ticker_ltp}")
                #logger.info(f"Ticker {ticker} {option_here['tradingsymbol']}, ticker_ltp {ticker_ltp}, op_ltp {op_ltp}, ticker_trend {macd_xover[ticker]}, options_macd_nr_co {options_macd_is_nr_co_bull}, options_macd_is_bull {options_macd_is_bull}, options_high_tf_macd_is_bull {options_high_tf_macd_is_bull}, ema_bull {ema_bull}, is_price_above_vwap {is_price_above_vwap}, price_above_ema_20 {price_above_ema_20}, volume_confirmation {volume_confirmation}, macd_slope_ok {macd_slope_ok}")
                logger.info(f"Renko data brick number {ohlc_renko[ticker]['bar_num'].iloc[-1]}, brick_size {ren_brick_size}")
                logger.info(f"{option_here['tradingsymbol']}, op_ltp {op_ltp}, ticker_trend {macd_xover[ticker]}, options_macd_is_bull {options_macd_is_bull}, ha_small_momentum {ha_small_momentum}, macd_slope_ok {macd_slope_ok}, macd_above_zero {macd_above_zero}, priceAboveMinOfCloud {priceAboveMinOfCloud}")
                if paper_trade:
                    if not options_macd_is_bull:
                        logger.info(f"****SQUARE OFF Triggered {op_ltp} {option_here['tradingsymbol']}\n\n\n")
                        paper_trade_qty = 0
                        
                # other entry in consideration - macd_xover, options_high_tf_macd_is_bull, is_price_above_vwap, ha_small_momentum  
                # exit ha_small_momentum_end
                ENTER_CONDITION = (options_macd_is_nr_co_bull and 
                    options_high_tf_macd_is_bull and 
                    #is_price_above_vwap and
                    macd_slope_ok and
                    ha_small_momentum and 
                    ema_bull and 
                    #price_above_ema_20 and 
                    True)
                # 1 min - macd above 0, 393, macd bull, high tf bull ticker , HA, and slope, exit HA
                ENTER_CONDITION = ( options_macd_is_bull and ha_small_momentum and 
                                   macd_slope_ok and macd_above_zero and priceAboveMinOfCloud)
                
                # 3 min - macd bull, 393, high tf bull ticker , HA - no slope m no above 0
                # for 3 min 8,21,5 macd feels better as it gives confirmed trend instead of fluctuations.
                # if gap between macd and signal is more than 2 
                ENTER_CONDITION = ( options_macd_is_bull and ha_small_momentum 
                                   and priceAboveMinOfCloud and histogram_above_threshold)
                
                #ENTER_CONDITION_3_MIN = ( options_macd_is_bull and ha_small_momentum and priceAboveMinOfCloud)
                
                
                if not STRATEGY_OPTION_SELL:
                    if option_here["instrument_type"]=="CE":
                        if (macd_xover[ticker] == "bullish" and ENTER_CONDITION):
                            #logger.info("Starting execution")
                            checkPositionAndExecute(ticker, option_here)
                            strategy_and_brick_data[ticker + option_here["instrument_type"]] = ren_brick_size
                    elif option_here["instrument_type"]=="PE":
                        if (macd_xover[ticker] == "bearish" and ENTER_CONDITION):
                            #logger.info("Starting execution PE")
                            checkPositionAndExecute(ticker, option_here)
                            strategy_and_brick_data[ticker + option_here["instrument_type"]] = ren_brick_size
                        
                else:
                    # STRATEGY_OPTION_SELL, # sell put, and buy put ..
                    print("option sell")
                    if option_here["instrument_type"]=="PE":
                        if (
                            macd_xover[ticker] == "bearish" and 
                            options_macd_is_nr_co_bull and 
                            options_high_tf_macd_is_bull and 
                            #is_price_above_vwap and
                            #volume_confirmation and
                            ema_bull #and price_above_ema_20
                        ):
                            checkPositionAndExecute(ticker, option_here)
                            strategy_and_brick_data[ticker + option_here["instrument_type"]] = ren_brick_size
                        elif macd_xover[ticker] == "bullish" and (not options_macd_is_bull) and (not options_high_tf_macd_is_bull):
                            checkPositionAndExecute(ticker, option_here, isOptionSell=True)
                            strategy_and_brick_data[ticker + option_here["instrument_type"]] = ren_brick_size
                
            
        # loop for all tockers ended
        is_started = False
                    
                
                
                        
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
            
            
            
