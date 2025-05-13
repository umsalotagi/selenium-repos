# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 00:15:50 2024

@author: usalotagi


for long term trade  --- do this first 
condition 1 with day data
condition 2 with weekly data
enter when prices are above cloud or crossover. 
add no stop loss
50% exit when prices are in cloud, all exit when prices cross low of cloud
problem : problem with aboe strategy is that, we dont know which one will rocket and which one will sleep
so better to ensure rocket and then enter trade

.... 
so first get monthly alpha stocks on daily data 
then check above consitions. 
where to store buyed stocks. database ? file based. how to login ? 

pip install tinydb_serialization
pip install tinydb
"""



import pandas as pd
import time
from kiteconnect import KiteConnect
from kiteconnect.exceptions import NetworkException
import os
import datetime as dt
import logging
import locale
import datetime
import numpy as np
import statsmodels.api as sm
from stocktrends import Renko
import configparser
import pytz
import sys
from io import StringIO
import requests
import copy
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
import json
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), 'TinyDate')


def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']

def instrumentLookup(symbol):
    try:
        return nse_instrument_df[nse_instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLCExtended(ticker, interval, period_days, inception_date=None):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    instrument = instrumentLookup(ticker)
    if inception_date:
        from_date = dt.datetime.strptime(inception_date, '%d-%m-%Y')
    else:
        from_date = dt.date.today() - dt.timedelta(period_days)
    to_date = dt.date.today()
    data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    while True:
        if from_date >= (dt.date.today() - dt.timedelta(100)):
            new_data = pd.DataFrame(kite.historical_data(instrument,from_date,dt.date.today(),interval))
            if data.empty:
                data = new_data
            else:
                data = pd.concat([data, new_data],ignore_index=True)
            break
        else:
            to_date = from_date + dt.timedelta(100)
            new_data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
            if data.empty:
                data = new_data
            else:
                data = pd.concat([data, new_data],ignore_index=True)
            from_date = to_date + dt.timedelta(1)
    data.set_index("date",inplace=True)
    return data

invalid_token_tickers = []
def fetchOHLCExtendedAll(tickers, interval, period_days):
    entire_data = {}
    for ticker in tickers:
        try:
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].fillna(method='ffill', inplace=True)
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except NetworkException as e:
            print("Possible too many request error, retyring for ", ticker, e)
            time.sleep(0.05)
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except Exception as e:
            print("Possible invalid token for", ticker, e)
            invalid_token_tickers.append(ticker)
    return entire_data

# possible infinite loop thats why not used anymore
def fecthOHLC2(entire_data, ticker, interval, period_days):
    try:
        from_date = dt.date.today() - dt.timedelta(period_days)
        entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today())
        entire_data[ticker].dropna(inplace=True,how="all")
        
    except NetworkException as e:
        print("Possible too many request error, retyring for ", e)
        time.sleep(0.05)
        fecthOHLC2(entire_data, ticker, interval, period_days)
        
    except Exception as e:
        print("possible invalid token for", ticker, e)
        invalid_token_tickers.append(ticker)
    

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

def trading_view_ema(ohlc, ema_period, column_name):
    # check definition from tradingview and code this line by line
    ohlc[column_name] = ohlc["close"].rolling(window=ema_period).mean()
    multiplier = 2 / (ema_period+1)
    firstRowDone = False
    ema_column = []
    prev = 0
    for index, row in ohlc.iterrows():
        if pd.isna(row[column_name]):
            #print("not good", row[column_name])
            ema_column.append(row[column_name])
        elif not firstRowDone:
            firstRowDone = True
            prev = row[column_name]
            ema_column.append(row[column_name])
            #print ("first ema is sma")
        else:
            new_ema = (row["close"] - prev)*multiplier + prev
            prev = new_ema
            ema_column.append(new_ema)
    ohlc[column_name] = ema_column
    
def modifySLOrder(symbol,order_id,price):    
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                    trigger_price=price,
                    order_type=kite.ORDER_TYPE_SLM,
                    variety=kite.VARIETY_REGULAR) 
    logger.info("RMS110: Modiying order for {}, with {} with sl_price {}".format(symbol, order_id, price))

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
    
    if (len(getPositions()) >= max_trades):
        logger.info("RMS119: More than 15 positions already build, no entering the trade {}".format(symbol))
        return "",""
    # you can use VARIETY_CO also
    response = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE, # NSE, BSE
                    transaction_type=t_type, # buy / sell
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET, # market price order - will get executed at market value
                    product=kite.PRODUCT_MIS, # intraday
                    tag="renko_macd",
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
    # for ORDER_TYPE_SLM we only provide trigger price, no price
    response2 = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SLM,
                    trigger_price = sl_price,
                    product=kite.PRODUCT_MIS,
                    tag="renko_macd",
                    variety=kite.VARIETY_REGULAR)
    return response, response2


def squareOffOrderAndSL(symbol,buy_sell,quantity):
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_BUY
    else:
        t_type=None
    response = kite.place_order(tradingsymbol=symbol,
                exchange=kite.EXCHANGE_NSE,
                transaction_type=t_type,
                quantity=quantity,
                order_type=kite.ORDER_TYPE_MARKET,
                product=kite.PRODUCT_MIS,
                tag="renko_macd",
                variety=kite.VARIETY_REGULAR)
    sl_response = None
    logger.info("RMS130: square off done for {} response {} ".format(symbol, response))    
    orders = getOrders()
    for order in orders:
        if order["tradingsymbol"] == symbol and order['status'] == 'TRIGGER PENDING':
            # cancel order
            sl_response = kite.cancel_order(order_id=order["order_id"], variety=kite.VARIETY_REGULAR)  
            logger.info("RMS140: cancel stoploss order for {} response {} ".format(symbol, sl_response))
    observe_position(symbol, "exit", buy_sell)
    return response, sl_response

def placeMarketOrder(symbol,buy_sell,quantity):    
    # Place an intraday market order on NSE
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_SELL
    else:
        t_type=None
    
    if test_mode:
        logger.info("RMS119: test_mode is active : Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
        return "",""
    # you can use VARIETY_CO also
    response = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE, # NSE, BSE
                    transaction_type=t_type, # buy / sell
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET, # market price order - will get executed at market value
                    product=kite.PRODUCT_CNC, # long - term
                    tag="long-swing",
                    variety=kite.VARIETY_REGULAR) # regular order
    logger.info("RMS120: Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
    observe_position(symbol, "enter", buy_sell)
    return response

def placeSLOrder(symbol,buy_sell,quantity,sl_price):  
    if buy_sell == "BUY":
        t_type_sl=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "SELL":
        t_type_sl=kite.TRANSACTION_TYPE_BUY
    else:
        t_type_sl=None
        
    
    # for ORDER_TYPE_SLM we only provide trigger price, no price
    response = kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SL,
                    trigger_price = sl_price,
                    price = sl_price,
                    product=kite.PRODUCT_MIS,
                    tag="resistance_breakout",
                    variety=kite.VARIETY_REGULAR)
    logger.info("RBS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
    return response
    

def squareOffOrder(symbol,buy_sell,quantity):
    if buy_sell == "BUY":
        t_type=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "SELL":
        t_type=kite.TRANSACTION_TYPE_BUY
    else:
        t_type=None
    response = kite.place_order(tradingsymbol=symbol,
                exchange=kite.EXCHANGE_NSE,
                transaction_type=t_type,
                quantity=quantity,
                order_type=kite.ORDER_TYPE_MARKET,
                product=kite.PRODUCT_CNC,
                tag="long-swing",
                variety=kite.VARIETY_REGULAR)
    logger.info("RMS130: square off done for {} response {} ".format(symbol, response))
    # additional updated stoploss if we added one
    orders = getOrders()
    for order in orders:
        if order["tradingsymbol"] == symbol and order['status'] == 'TRIGGER PENDING':
            # cancel order
            sl_response = kite.cancel_order(order_id=order["order_id"], variety=kite.VARIETY_REGULAR)  
            logger.info("RBS140: cancel stoploss order for {} response {} ".format(symbol, sl_response))
            
    observe_position(symbol, "exit", buy_sell)
    return response

def observe_position(symbol, enter_exit, buy_sell):
    # observe options and future, get option chain and log its data, also get quote of it. log both
    if symbol not in nifty_options_stocks:
        logger.info("symbol {} not present in options stock".format(symbol))
        return
    ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"] 
    put_call = "PE"
    if buy_sell == "BUY":
        put_call = "CE"
    if enter_exit == "enter":
        chooseOptionChain(symbol, put_call, ltp)
    else:
        chooseOptionChain2(symbol, put_call, ltp)
    pass

def cancelOrder(order_id):
    # Modify order given order id
    logger.info("RMS150: Day end square off cancelling orders {}".format(order_id))
    kite.cancel_order(order_id=order_id, variety=kite.VARIETY_REGULAR)  
    
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
    logger.info("pending orders ", pending)
    attempt = 0
    while len(pending)>0 and attempt<5:
        pending = [j for j in pending if j not in drop]
        for order in pending:
            try:
                cancelOrder(order)
                drop.append(order)
            except:
                logger.info("unable to delete order id : ",order)
                attempt+=1
    logger.info("RMS170: Its past 3:10 PM, Successfully square off everything .. ending ")
    pass

def getExistingPosition(symbol):
    # check if position exists before squareoff
    positions = getPositions()
    qty = [item["quantity"] for item in positions if item["tradingsymbol"]==symbol]
    return qty


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

def getQuantityForInvestment(lastTradedPrice):
    return abs(int(invetment_amount / lastTradedPrice))

def now_in_timezone():
    """Returns the current time in the default timezone."""
    return dt.datetime.now(DEFAULT_TIMEZONE)

DEFAULT_TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change this to your desired timezone
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)


# Tenkan_sen, Kijun_sen, Senkou_span_A, Senkou_span_B, Chikou_span
def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    
    df['Chikou_span'] = df["close"].shift(-shift_size)

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
   


def calculateAlpha(tickers, interval, description, start_date, alpha_until_day):
    
    global ohlc_dict, index_ohlc
    
    ohlc_dict = copy.deepcopy(entire_data)
    index_ohlc = copy.deepcopy(index_data)

    tickers = [item for item in tickers if item not in invalid_token_tickers]
    
    # data removal - keeping only 2 month
    st =  pd.Timestamp(year=2025, month=start_date[0], day=start_date[1], hour=0, minute=0).tz_localize('Asia/Kolkata')
    et =  pd.Timestamp(year=2025, month=alpha_until_day[0], day=alpha_until_day[1], hour=0, minute=0).tz_localize('Asia/Kolkata')
    
    if interval == "day":
        index_ohlc["return_week"] = (index_ohlc["close"] - index_ohlc["close"].shift(5)) / index_ohlc["close"].shift(5)
        index_ohlc["return_1mo"] = (index_ohlc["close"] - index_ohlc["close"].shift(22)) / index_ohlc["close"].shift(22)
        #index_ohlc["return_3mo"] = (index_ohlc["close"] - index_ohlc["close"].shift(66)) / index_ohlc["close"].shift(66)
        risk_free_rate = 0.0675 / 252
    else:
        index_ohlc["return_week"] = (index_ohlc["close"] - index_ohlc["close"].shift(30)) / index_ohlc["close"].shift(30)
        index_ohlc["return_1mo"] = (index_ohlc["close"] - index_ohlc["close"].shift(396)) / index_ohlc["close"].shift(396)
        risk_free_rate = (0.0675 / 252) / 6
    
    index_ohlc["return_daily"] = index_ohlc["close"].pct_change()
    index_ohlc["excess_return_daily"] = index_ohlc["return_daily"] - risk_free_rate
    index_ohlc.dropna(inplace=True)
    index_ohlc = index_ohlc[index_ohlc.index <= et]
    index_ohlc = index_ohlc[index_ohlc.index >= st]
    
    alpha = {}
    returns_1wk = {}
    returns_1mo = {}
    returns_3mo = {}
    
    
    for ticker in tickers:
        print("ticker### calculate alpha for stock", ticker)
        ohlc_dict[ticker]["return_daily"] =  ohlc_dict[ticker]["close"].pct_change()
        
        if interval == "day":
            ohlc_dict[ticker]["return_week"] = (ohlc_dict[ticker]["close"] - ohlc_dict[ticker]["close"].shift(5)) / ohlc_dict[ticker]["close"].shift(5)
            ohlc_dict[ticker]["return_1mo"] = (ohlc_dict[ticker]["close"] - ohlc_dict[ticker]["close"].shift(22)) / ohlc_dict[ticker]["close"].shift(22)
            ohlc_dict[ticker]["return_3mo"] = (ohlc_dict[ticker]["close"] - ohlc_dict[ticker]["close"].shift(66)) / ohlc_dict[ticker]["close"].shift(66)
        else:
            ohlc_dict[ticker]["return_week"] = (ohlc_dict[ticker]["close"] - ohlc_dict[ticker]["close"].shift(30)) / ohlc_dict[ticker]["close"].shift(30)
            ohlc_dict[ticker]["return_1mo"] = (ohlc_dict[ticker]["close"] - ohlc_dict[ticker]["close"].shift(396)) / ohlc_dict[ticker]["close"].shift(396)
            pass
            
        ohlc_dict[ticker]["excess_return_daily"] = ohlc_dict[ticker]["return_daily"] - risk_free_rate
        ohlc_dict[ticker].dropna(inplace=True)
        ohlc_dict[ticker] = ohlc_dict[ticker][ohlc_dict[ticker].index <= et]
        ohlc_dict[ticker] = ohlc_dict[ticker][ohlc_dict[ticker].index >= st]
        
        # check if data count is same in indexData and ohlc data for this stock
        if (len(index_ohlc) != len(ohlc_dict[ticker])):
            #KPI_df = pd.DataFrame([None,0,0,0],index=["Alpha","Week Return","1 month return","3 month return"])      
            del ohlc_dict[ticker]
            continue
        
        X = index_ohlc["excess_return_daily"]
        X = sm.add_constant(X)  # Add intercept term
        Y = ohlc_dict[ticker]["excess_return_daily"]
        model = sm.OLS(Y, X).fit()  # Ordinary Least Squares regression
        alpha[ticker]=model.params.iloc[0]
        
        if interval == "day":
            returns_1wk[ticker]=ohlc_dict[ticker]["return_week"].iloc[-1]
            returns_1mo[ticker]=ohlc_dict[ticker]["return_1mo"].iloc[-1]
            returns_3mo[ticker]=ohlc_dict[ticker]["return_3mo"].iloc[-1]
        else:
            returns_1wk[ticker]=ohlc_dict[ticker]["return_week"].iloc[-1]
            pass
        
    if interval == "day":
        KPI_df = pd.DataFrame([alpha,returns_1wk,returns_1mo,returns_3mo],index=["Alpha","Week Return","1 month return","3 month return"])      
    else:
        KPI_df = pd.DataFrame([alpha,returns_1wk],index=["Alpha","Week Return"])      
        
    return KPI_df
     


#======== options data for observation 
symbol_ltp = {}
def chooseOptionChain(symbol, instrument_type, ltp):

    filtered = [item for item in options_expiring_this_month if item["name"]==symbol and item["instrument_type"]==instrument_type]
    sorted_data = sorted(filtered, key=lambda x: x['strike'])
    lower_closest = None
    upper_closest = None
    for entry in sorted_data:
        strike = entry['strike']
        # Find the closest entry just below the input value
        if strike < ltp:
            lower_closest = entry
        # Find the closest entry just above the input value
        elif strike >= ltp and upper_closest is None:
            upper_closest = entry
            break


    quote_upper_closest = kite.quote("NFO:" + upper_closest["tradingsymbol"])["NFO:" + upper_closest["tradingsymbol"]]
    lot_size = upper_closest["lot_size"]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, ltp, upper_closest["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    
    quote_upper_closest = kite.quote("NFO:" + lower_closest["tradingsymbol"])["NFO:" + lower_closest["tradingsymbol"]]
    lot_size = upper_closest["lot_size"]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, ltp, lower_closest["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    
    chooseFuture(symbol, instrument_type)
    
    symbol_ltp[symbol] = upper_closest["tradingsymbol"] + ","+ lower_closest["tradingsymbol"]
    pass

def chooseFuture(symbol, buy_sell):
    future_data = [item for item in futures_expiring_this_month if item["name"]==symbol][0]
    real_ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]
    
    quote_fut = kite.quote("NFO:" + future_data["tradingsymbol"])["NFO:" + future_data["tradingsymbol"]]
    last_price = quote_fut["last_price"]
    last_quantity = quote_fut["last_quantity"]
    last_trade_time = quote_fut["last_trade_time"]
    asking_price = quote_fut["depth"]["buy"][0]["price"]
    offer_price = quote_fut["depth"]["sell"][0]["price"]
    logger.info("{}-{} FUTURE {} {}, lot {}, last_price {}, last_quantity {}, last_trade_time {}, asking_price {}, offer_price {}".format(symbol, real_ltp, buy_sell, future_data["tradingsymbol"], future_data["lot_size"], last_price, last_quantity, last_trade_time, asking_price, offer_price))
    pass

def chooseOptionChain2(symbol, instrument_type, ltp):
    
    if symbol in symbol_ltp:
        option_symbol = symbol_ltp[symbol].split(",")[0]
        option_symbol2 = symbol_ltp[symbol].split(",")[0]
    else:
        chooseOptionChain(symbol, instrument_type, ltp)
        return

    filtered = [item for item in options_expiring_this_month if item["name"]==symbol and item["instrument_type"]==instrument_type]
    sorted_data = sorted(filtered, key=lambda x: x['strike'])
    lower_closest = None
    upper_closest = None
    
    real_ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]

    quote_upper_closest = kite.quote("NFO:" + option_symbol)["NFO:" + option_symbol]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, real_ltp, option_symbol, last_price, last_trade_time, asking_price, offer_price))
    
    quote_upper_closest = kite.quote("NFO:" + option_symbol2)["NFO:" + option_symbol2]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logger.info("{}-{}, stock_ltp, {}, option_symbol, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, real_ltp, option_symbol2, last_price, last_trade_time, asking_price, offer_price))
    
    chooseFuture(symbol, instrument_type)
    pass

options_instruments = kite.instruments(exchange="NFO")
today_date = now_in_timezone()
current_year = today_date.year
if today_date.month<=25:
    current_month = today_date.month
else:
    current_month = today_date.month + 1
options_expiring_this_month = [item for item in options_instruments if item["segment"] == "NFO-OPT" and item["expiry"].year == current_year and  item["expiry"].month == current_month]
futures_expiring_this_month = [item for item in options_instruments if item["segment"] == "NFO-FUT" and item["expiry"].year == current_year and  item["expiry"].month == current_month]

#========= end options specific data


#==============================================================================

alpha_timeframe = "day"
trade_timeframe = "day"
higher_timeframe = "week"

date_strftime_format = "%Y-%m-%d %H:%M:%S"
locale.setlocale(locale.LC_ALL, '')
local_tz = pytz.timezone('Asia/Kolkata')

cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")

log_file_name = "hiekinashi_long_trade.txt"
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt=date_strftime_format, 
                    handlers=[logging.FileHandler(log_file_name, mode="a"),logging.StreamHandler()])


logger = logging.getLogger("custom_logger")
logger.setLevel(logging.INFO)  # Set minimum log level

# Create file handler
file_handler = logging.FileHandler(log_file_name, mode="a")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", date_strftime_format))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", date_strftime_format))

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Not eligible for sell off")
nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)

logger.info("Logging strting trade")

max_trades = 1
no_of_trades = 1
test_mode = False


nifty_options_stocks = ['M&M', 'ULTRACEMCO', 'HAL', 'TITAN', 'ADANIPORTS', 'COALINDIA', 'ASIANPAINT', 'POWERGRID', 'BAJAJ-AUTO', 'BAJAJFINSV', 'WIPRO', 'TRENT', 'IOC', 'NESTLEIND', 'SIEMENS', 'JSWSTEEL', 'BEL', 'DLF', 'SBILIFE', 'TATASTEEL', 'RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK', 'INFY', 'SBIN', 'HINDUNILVR', 'ITC', 'LT', 'HCLTECH', 'BAJFINANCE', 'SUNPHARMA', 'TATAMOTORS', 'ONGC', 'NTPC', 'MARUTI', 'AXISBANK', 'KOTAKBANK', 'ADANIENT', 'INDIGO', 'GRASIM', 'PFC', 'LTIM', 'VEDL', 'RECLTD', 'PIDILITIND', 'HDFCLIFE', 'ABB', 'TECHM', 'BPCL', 'AMBUJACEM', 'GAIL', 'GODREJCP', 'HINDALCO', 'BRITANNIA', 'DIVISLAB', 'TATAPOWER', 'CIPLA', 'EICHERMOT', 'TVSMOTOR', 'MOTHERSON', 'BANKBARODA', 'CHOLAFIN', 'PNB', 'SHRIRAMFIN', 'HAVELLS', 'TATACONSUM', 'TORNTPHARM', 'INDUSTOWER', 'DABUR', 'HEROMOTOCO', 'ZYDUSLIFE', 'DRREDDY', 'INDUSINDBK', 'ICICIGI', 'ICICIPRULI', 'UNITDSPR', 'CUMMINSIND', 'LUPIN', 'POLYCAB', 'IDEA', 'COLPAL', 'APOLLOHOSP', 'GMRINFRA', 'CANBK', 'OFSS', 'BHEL', 'JINDALSTEL', 'HDFCAMC', 'NAUKRI', 'BOSCHLTD', 'HINDPETRO', 'INDHOTEL', 'SHREECEM', 'AUROPHARMA', 'MARICO', 'PERSISTENT', 'GODREJPROP', 'MUTHOOTFIN', 'SRF', 'DIXON', 'IRCTC', 'BHARATFORG', 'ALKEM', 'ASHOKLEY', 'SBICARD', 'BERGEPAINT', 'PIIND', 'OBEROIRLTY', 'ABBOTINDIA', 'NMDC', 'LTTS', 'VOLTAS', 'CONCOR', 'MPHASIS', 'ABCAPITAL', 'MRF', 'BALKRISIND', 'IDFCFIRSTB', 'TATACOMM', 'PETRONET', 'SAIL', 'UBL', 'ASTRAL', 'AUBANK', 'COROMANDEL', 'GLENMARK', 'FEDERALBNK', 'PAGEIND', 'UPL', 'BIOCON', 'GUJGASLTD', 'ACC', 'JUBLFOOD', 'COFORGE', 'LTF', 'ESCORTS', 'EXIDEIND', 'DEEPAKNTR', 'M&MFIN', 'MFSL', 'IGL', 'LICHSGFIN', 'DALBHARAT', 'JKCEMENT', 'IPCALAB', 'SYNGENE', 'APOLLOTYRE', 'BANDHANBNK', 'NATIONALUM', 'SUNTV', 'ABFRL', 'HINDCOPPER', 'CROMPTON', 'LALPATHLAB', 'TATACHEM', 'MCX', 'LAURUSLABS', 'PEL', 'ATUL', 'AARTIIND', 'CHAMBLFERT', 'RAMCOCEM', 'BATAINDIA', 'IEX', 'INDIAMART', 'BSOFT', 'MGL', 'IDFC', 'MANAPPURAM', 'GRANULES', 'NAVINFLUOR', 'PVRINOX', 'RBLBANK', 'CUB', 'BALRAMCHIN', 'CANFINHOME', 'METROPOLIS', 'GNFC']
nifty_500 = ["360ONE","3MINDIA","ABB","ACC","AIAENG","APLAPOLLO","AUBANK","AARTIIND","AAVAS","ABBOTINDIA","ACE","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","AWL","ABCAPITAL","ABFRL","AEGISLOG","AETHER","AFFLE","AJANTPHARM","APLLTD","ALKEM","ALKYLAMINE","ALLCARGO","ALOKINDS","ARE&M","AMBER","AMBUJACEM","ANANDRATHI","ANGELONE","ANURAS","APARINDS","APOLLOHOSP","APOLLOTYRE","APTUS","ACI","ASAHIINDIA","ASHOKLEY","ASIANPAINT","ASTERDM","ASTRAZEN","ASTRAL","ATUL","AUROPHARMA","AVANTIFEED","DMART","AXISBANK","BEML","BLS","BSE","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALAMINES","BALKRISIND","BALRAMCHIN","BANDHANBNK","BANKBARODA","BANKINDIA","MAHABANK","BATAINDIA","BAYERCROP","BERGEPAINT","BDL","BEL","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIKAJI","BIOCON","BIRLACORPN","BSOFT","BLUEDART","BLUESTARCO","BBTC","BORORENEW","BOSCHLTD","BRIGADE","BRITANNIA","MAPMYINDIA","CCL","CESC","CGPOWER","CIEINDIA","CRISIL","CSBBANK","CAMPUS","CANFINHOME","CANBK","CAPLIPOINT","CGCL","CARBORUNIV","CASTROLIND","CEATLTD","CELLO","CENTRALBK","CDSL","CENTURYPLY","CENTURYTEX","CERA","CHALET","CHAMBLFERT","CHEMPLASTS","CHENNPETRO","CHOLAHLDNG","CHOLAFIN","CIPLA","CUB","CLEAN","COALINDIA","COCHINSHIP","COFORGE","COLPAL","CAMS","CONCORDBIO","CONCOR","COROMANDEL","CRAFTSMAN","CREDITACC","CROMPTON","CUMMINSIND","CYIENT","DCMSHRIRAM","DLF","DOMS","DABUR","DALBHARAT","DATAPATTNS","DEEPAKFERT","DEEPAKNTR","DELHIVERY","DEVYANI","DIVISLAB","DIXON","LALPATHLAB","DRREDDY","EIDPARRY","EIHOTEL","EPL","EASEMYTRIP","EICHERMOT","ELECON","ELGIEQUIP","EMAMILTD","ENDURANCE","ENGINERSIN","EQUITASBNK","ERIS","ESCORTS","EXIDEIND","FDC","NYKAA","FEDERALBNK","FACT","FINEORG","FINCABLES","FINPIPE","FSL","FIVESTAR","FORTIS","GAIL","GMMPFAUDLR","GMRINFRA","GRSE","GICRE","GILLETTE","GLAND","GLAXO","GLS","GLENMARK","MEDANTA","GPIL","GODFRYPHLP","GODREJCP","GODREJIND","GODREJPROP","GRANULES","GRAPHITE","GRASIM","GESHIP","GRINDWELL","GAEL","FLUOROCHEM","GUJGASLTD","GMDCLTD","GNFC","GPPL","GSFC","GSPL","HEG","HBLPOWER","HCLTECH","HDFCAMC","HDFCBANK","HDFCLIFE","HFCL","HAPPSTMNDS","HAPPYFORGE","HAVELLS","HEROMOTOCO","HSCL","HINDALCO","HAL","HINDCOPPER","HINDPETRO","HINDUNILVR","HINDZINC","POWERINDIA","HOMEFIRST","HONASA","HONAUT","HUDCO","ICICIBANK","ICICIGI","ICICIPRULI","ISEC","IDBI","IDFCFIRSTB","IDFC","IIFL","IRB","IRCON","ITC","ITI","INDIACEM","INDIAMART","INDIANB","IEX","INDHOTEL","IOC","IOB","IRCTC","IRFC","INDIGOPNTS","IGL","INDUSTOWER","INDUSINDBK","NAUKRI","INFY","INOXWIND","INTELLECT","INDIGO","IPCALAB","JBCHEPHARM","JKCEMENT","JBMA","JKLAKSHMI","JKPAPER","JMFINANCIL","JSWENERGY","JSWINFRA","JSWSTEEL","JAIBALAJI","J&KBANK","JINDALSAW","JSL","JINDALSTEL","JIOFIN","JUBLFOOD","JUBLINGREA","JUBLPHARMA","JWL","JUSTDIAL","JYOTHYLAB","KPRMILL","KEI","KNRCON","KPITTECH","KRBL","KSB","KAJARIACER","KPIL","KALYANKJIL","KANSAINER","KARURVYSYA","KAYNES","KEC","KFINTECH","KOTAKBANK","KIMS","LTF","LTTS","LICHSGFIN","LTIM","LT","LATENTVIEW","LAURUSLABS","LXCHEM","LEMONTREE","LICI","LINDEINDIA","LLOYDSME","LUPIN","MMTC","MRF","MTARTECH","LODHA","MGL","MAHSEAMLES","M&MFIN","M&M","MHRIL","MAHLIFE","MANAPPURAM","MRPL","MANKIND","MARICO","MARUTI","MASTEK","MFSL","MAXHEALTH","MAZDOCK","MEDPLUS","METROBRAND","METROPOLIS","MINDACORP","MSUMI","MOTILALOFS","MPHASIS","MCX","MUTHOOTFIN","NATCOPHARM","NBCC","NCC","NHPC","NLCINDIA","NMDC","NSLNISP","NTPC","NH","NATIONALUM","NAVINFLUOR","NESTLEIND","NETWORK18","NAM-INDIA","NUVAMA","NUVOCO","OBEROIRLTY","ONGC","OIL","OLECTRA","PAYTM","OFSS","POLICYBZR","PCBL","PIIND","PNBHOUSING","PNCINFRA","PVRINOX","PAGEIND","PATANJALI","PERSISTENT","PETRONET","PHOENIXLTD","PIDILITIND","PEL","PPLPHARMA","POLYMED","POLYCAB","POONAWALLA","PFC","POWERGRID","PRAJIND","PRESTIGE","PRINCEPIPE","PRSMJOHNSN","PGHH","PNB","QUESS","RRKABEL","RBLBANK","RECLTD","RHIM","RITES","RADICO","RVNL","RAILTEL","RAINBOW","RAJESHEXPO","RKFORGE","RCF","RATNAMANI","RTNINDIA","RAYMOND","REDINGTON","RELIANCE","RBA","ROUTE","SBFC","SBICARD","SBILIFE","SJVN","SKFINDIA","SRF","SAFARI","SAMMAANCAP","MOTHERSON","SANOFI","SAPPHIRE","SAREGAMA","SCHAEFFLER","SCHNEIDER","SHREECEM","RENUKA","SHRIRAMFIN","SHYAMMETL","SIEMENS","SIGNATURE","SOBHA","SOLARINDS","SONACOMS","SONATSOFTW","STARHEALTH","SBIN","SAIL","SWSOLAR","STLTECH","SUMICHEM","SPARC","SUNPHARMA","SUNTV","SUNDARMFIN","SUNDRMFAST","SUNTECK","SUPREMEIND","SUVENPHAR","SUZLON","SWANENERGY","SYNGENE","SYRMA","TV18BRDCST","TVSMOTOR","TVSSCS","TMB","TANLA","TATACHEM","TATACOMM","TCS","TATACONSUM","TATAELXSI","TATAINVEST","TATAMOTORS","TATAPOWER","TATASTEEL","TATATECH","TTML","TECHM","TEJASNET","NIACL","RAMCOCEM","THERMAX","TIMKEN","TITAGARH","TITAN","TORNTPHARM","TORNTPOWER","TRENT","TRIDENT","TRIVENI","TRITURBINE","TIINDIA","UCOBANK","UNOMINDA","UPL","UTIAMC","UJJIVANSFB","ULTRACEMCO","UNIONBANK","UBL","UNITDSPR","USHAMART","VGUARD","VIPIND","VAIBHAVGBL","VTL","VARROC","VBL","MANYAVAR","VEDL","VIJAYA","IDEA","VOLTAS","WELCORP","WELSPUNLIV","WESTLIFE","WHIRLPOOL","WIPRO","YESBANK","ZFCVINDIA","ZEEL","ZENSARTECH","ZOMATO","ZYDUSLIFE","ECLERX"]
nifty_microcap_250 = ["AGI","ASKAUTOLTD","AARTIDRUGS","AARTIPHARM","ADVENZYMES","AETHER","AHLUCONT","ALLCARGO","AMIORG","ANURAS","PARKHOTELS","ARVINDFASN","ARVIND","ASHOKA","ASTRAMICRO","AVALON","AZAD","BAJAJCON","BAJAJELEC","BAJAJHIND","BALMLAWRIE","BANCOINDIA","BEPL","BBL","BLUEJET","BOMDYEING","BOROLTD","BORORENEW","CMSINFO","CSBBANK","CARTRADE","CHOICEIN","CIGNITITEC","CONFIPET","CYIENTDLM","DCBBANK","DCMSHRIRAM","DCXINDIA","DATAMATICS","DELTACORP","DEN","DHANI","DHANUKA","DBL","DISHTV","DCAL","DODLA","DREAMFOLKS","DUMMYSTAR","DYNAMATECH","EPL","ESAFSFB","EDELWEISS","EMIL","ELECTCAST","ENTERO","EPIGRAL","EMBDL","ETHOSLTD","EVEREADY","FDC","FIEMIND","FCL","FORCEMOT","FUSION","GHCL","GMMPFAUDLR","GABRIEL","GANESHHOUC","GRWRHITECH","GATEWAY","GLS","GOCOLORS","GOKEX","GOPAL","GRAVITA","GREAVESCOT","GREENPANEL","GREENPLY","GUJALKALI","GULFOILLUB","HGINFRA","HAPPYFORGE","HARSHA","HATHWAY","HCG","HEIDELBERG","HEMIPROP","HERITGFOOD","HIKAL","HCC","HNDFDS","HINDOILEXP","HINDWAREAP","IFBIND","IIFLCAPS","ITDCEM","IDEAFORGE","IMAGICAA","INDIAGLYCO","IPL","INDIASHLTR","IMFA","INDIGOPNTS","ICIL","INFIBEAM","INGERRAND","INOXGREEN","IONEXCHANG","ISGEC","JKIL","JKPAPER","JTEKTINDIA","JTLIND","JAIBALAJI","JAICORPLTD","JISLJALEQS","JAMNAAUTO","JSFB","JINDWORLD","JCHAC","JUNIPER","JLHL","KRBL","KSL","KTKBANK","KSCL","KESORAMIND","KIRLPNU","KOLTEPATIL","LMW","LTFOODS","LANDMARK","LXCHEM","IXIGO","LLOYDSENGG","LUXIND","MOIL","MSTCLTD","MTARTECH","MHRIL","MAHLOG","MAITHANALL","MANINFRA","MARKSANS","MEDPLUS","MIDHANI","BECTORFOOD","MUTHOOTMF","NEOGEN","NESCO","NIITMTS","NOCIL","NRBBEARING","NFL","NAVA","NAZARA","NEULANDLAB","ODIGMA","OPTIEMUS","ORCHPHARMA","ORIENTCEM","ORIENTELEC","ORISSAMINE","PGEL","PTC","PAISALO","PARADEEP","PARAS","PATELENG","POLYPLEX","POWERMECH","PRICOLLTD","PRINCEPIPE","PGHL","PRUDENT","PURVA","RAIN","RALLIS","RAMKY","RATEGAIN","REDTAPE","RELINFRA","RELIGARE","RESPONIND","RBA","ROLEXRINGS","ROSSARI","SAFARI","KALAMANDIR","SAMHI","SANDUMA","SANGHIIND","SANGHVIMOV","SANSERA","SARDAEN","SENCO","SEQUENT","SHARDAMOTR","SHAREINDIA","SFL","SHILPAMED","SBCL","SHRIPISTON","SINDHUTRAD","SOUTHBANK","SPANDANA","STARCEMENT","SSWL","STLTECH","STAR","STYLAMIND","SUBROS","SUDARSCHEM","SULA","SUNFLAG","SUNTECK","SUPRAJIT","SPLPETRO","SUPRIYA","SURYAROSNI","SYMPHONY","TARC","TCIEXP","TDPOWERSYS","TEAMLEASE","TIIL","TEGA","TEXRAIL","TIRUMALCHM","THOMASCOOK","TI","TIMETECHNO","TIPSMUSIC","UTKARSHBNK","VMART","VSTIND","WABAG","VAIBHAVGBL","VEEDOL","VENKEYS","VENUSPIPES","VESUVIUS","VOLTAMP","WELENT","WSTCSTPAPR","WOCKPHARMA","WONDERLA","YATHARTH","ZENTEC","ZYDUSWELL","EMUDHRA"]

nifty_500_not_in_options = [item for item in nifty_500 if item not in nifty_options_stocks]

index_ticker = "NIFTY 50"
tickers = list(nifty_500_not_in_options + nifty_microcap_250)
#tickers = nifty_options_stocks

logger.info("starting download")
entire_data = fetchOHLCExtendedAll(tickers, alpha_timeframe, 150)# 230
index_data = fetchOHLCExtended(index_ticker, alpha_timeframe, 300)
logger.info("fininshed download")

path_to_db = r"C:\Users\usalotagi\Python\Stock\hiekinashi\db.json"

today = dt.datetime.today()
date_30_days_ago = today - dt.timedelta(days=30)

# internet suggest for daily alpha calculation - use 1 year of data, 6 month of data can also be used
KPI_df = calculateAlpha(tickers, alpha_timeframe, "3_month_daily_alpha", (date_30_days_ago.month, date_30_days_ago.day), (today.month, today.day))
#KPI_df = calculateAlpha(tickers, alpha_timeframe, "3_month_daily_alpha_options", (11, 30), (12, 30))

# daily alpha of 0.05% to 0.10% ==> 0.0005
# hourly alpha 0.01% to 0.05% per hour ==> 0.0001
zz1 = KPI_df.T.sort_values(by='Alpha', ascending=False)
# so alpha should be more than 0.002 and week return should be positive for now.
zz2 = zz1[zz1["Alpha"] > 0.002][zz1["Week Return"] > 0]
alpha_stocks_shortlisted = zz2.index.tolist()


tickers = alpha_stocks_shortlisted



logger.info("Debugging the details minute {} and ohlc_dict_hr_sell type".format(now_in_timezone().minute))
ohlc_dict = fetchOHLCExtendedAll(tickers, trade_timeframe, period_days=1000)
for key, value in ohlc_dict.items():
    ichimoko(value)

if higher_timeframe == "week":
    ohlc_dict_high_timeframe = copy.deepcopy(ohlc_dict)
    for key, value in ohlc_dict_high_timeframe.items():
        v1 = value.resample('W').agg({
            'open': 'first',      # First open price of the week
            'high': 'max',        # Max high price of the week
            'low': 'min',         # Min low price of the week
            'close': 'last',      # Last close price of the week
            'volume': 'sum'       # Sum of volume for the week
        })
        ichimoko(v1)
else:
    ohlc_dict_high_timeframe = fetchOHLCExtendedAll(tickers, higher_timeframe, period_days=1000)

db = TinyDB(path_to_db, storage=serialization)

data_all = db.all()
StockHolding = Query()

holdings_in_place = db.search(StockHolding.is_squared == False)
holdings = kite.holdings()


# Tenkan_sen, Kijun_sen, Senkou_span_A, Senkou_span_B, Chikou_span
for ticker in tickers:
    if no_of_trades > max_trades or len(holdings_in_place) > 30:
        logger.error("number of trades done is hiher than max_trades OR holdings_in_place is higher than 30")
        break
    weekly_line_bull = ohlc_dict_high_timeframe[ticker]["Tenkan_sen"].iloc[-1] > ohlc_dict_high_timeframe[ticker]["Kijun_sen"].iloc[-1]
    span_max = max(ohlc_dict[ticker]["Senkou_span_A"].iloc[-1], ohlc_dict[ticker]["Senkou_span_B"].iloc[-1])
    daily_above_cloud_1 = ohlc_dict[ticker]["close"].iloc[-1] > span_max
    daily_line_bull = ohlc_dict[ticker]["Tenkan_sen"].iloc[-1] > ohlc_dict[ticker]["Kijun_sen"].iloc[-1]
    # this is stoploss
    risk_amount = ohlc_dict[ticker]["Senkou_span_B"].iloc[-1] - ohlc_dict[ticker]["close"].iloc[-1]
    # alpha calculated here is risk adjusted return, so do we need to again calculate the volatiliy of stocks
    # and stock segment such as small cap etc. I think NO
    # just risk_amount here is the loss which will encur if stop loss is trigger, if that is big, investment made should be less
    risk_per = risk_amount / ohlc_dict[ticker]["close"].iloc[-1]
    invetment_amount = 12000
    if risk_per > 0.25:
        logger.warn ("high risk think do not enter")
        invetment_amount = 6000
    elif risk_per > 0.12:
        logger.warn("medium risk")
        invetment_amount = 8000
    else:
        logger.info("low risk")
        
    ltp = kite.ltp("NSE:" + ticker)["NSE:" + ticker]["last_price"] 
    qty = getQuantityForInvestment(ltp)
    if qty <= 0:
        logger.error("stock price is high " + ticker)
        continue
    
    # buy 
    if weekly_line_bull and daily_above_cloud_1 and daily_line_bull:
        logger.info("eligible symbol for investment {} of value {}".format(ticker, invetment_amount))
        # check if trade is already placed for this
        already_buyed = [item["symbol"] for item in data_all]
        if ticker not in already_buyed:
            # check if stock already present in holdings - no need, its fine to add more
            no_of_trades = no_of_trades + 1
            response = placeMarketOrder(ticker, "BUY", qty)
            db.insert({'symbol': ticker, 'is_squared': False, 'buy_date': dt.datetime.today(), 'qty': qty, "buy_price": ltp, "times": 1})
        else:
            logger.error("stock is already buyed by this method " + ticker)
        
        
# square off orders
data_all = db.all()
#db.truncate()
# to remove use db.remove(StockHolding.symbol == "INDEAFORGE") but we are using is_squared field instead

for data_1 in data_all:
    if not data_1["is_squared"]:
        symbol = data_1["symbol"]
        qty = data_1["qty"]
        ohlc_dict = fetchOHLCExtendedAll([symbol], trade_timeframe, period_days=1000)
        ichimoko(ohlc_dict[symbol])
        if higher_timeframe == "week":
            ohlc_dict_high_timeframe = copy.deepcopy(ohlc_dict)
            for key, value in ohlc_dict_high_timeframe.items():
                v1 = value.resample('W').agg({
                    'open': 'first',      # First open price of the week
                    'high': 'max',        # Max high price of the week
                    'low': 'min',         # Min low price of the week
                    'close': 'last',      # Last close price of the week
                    'volume': 'sum'       # Sum of volume for the week
                })
                ichimoko(v1)
        else:
            ohlc_dict_high_timeframe = fetchOHLCExtendedAll([symbol], higher_timeframe, period_days=1000)
            
        span_min = min(ohlc_dict[symbol]["Senkou_span_A"].iloc[-1], ohlc_dict[symbol]["Senkou_span_B"].iloc[-1])
        daily_below_cloud = ohlc_dict[symbol]["close"].iloc[-1] < span_min
        ltp = kite.ltp("NSE:" + symbol)["NSE:" + symbol]["last_price"]
        
        if daily_below_cloud and ltp < span_min:
            logger.info("eligible for sell off " + symbol)
            
            # check if holding have it, both symbol and quantity 
            #tradingsymbol, quantity, used_quantity, authorised_quantity
            ticker_holdings = [data for data in holdings if data["tradingsymbol"] == symbol]
            if ticker_holdings.__len__() != 0 and ticker_holdings[0]["quantity"] >= qty :
                # tocker exists in dmat account. we can sell it
                placeMarketOrder(symbol, "SELL", qty)
                # update the document 
                db.update({'is_squared': True}, StockHolding.symbol == symbol)
            else:
                logger.error("ERROR : stocks not present in holding " + symbol)
                
        else:
            logger.info("not eligible for sell off " + symbol)
        
        
        
            
            
            
            
        
