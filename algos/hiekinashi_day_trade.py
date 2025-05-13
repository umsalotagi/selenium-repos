# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 00:15:50 2024

@author: usalotagi

1. check 15 min ichimoku price above cloud and line a is above line b
2. check 1 hour line a is above line b
3. large momentum candle OR 3 small momentum candle with add up to large
4. start of this candle should be opposite direction
4. exit hiekin ashi


for long term trade  --- do this first 
condition 1 with day data
condition 2 with weekly data
enter when prices are above cloud or crossover. 
add no stop loss
50% exit when prices are in cloud, all exit when prices cross low of cloud

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
        print("RMS109: No data found for ", ticker)
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
    logging.info("RMS110: Modiying order for {}, with {} with sl_price {}".format(symbol, order_id, price))

def getPositions():
    a = 0
    while a < 10:
        try:
            positions = kite.positions()["day"]
            positions = [item for item in positions if item["product"] == "MIS"]
            break
        except:
            print("can't extract position data..retrying")
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
            print("can't extract position data..retrying")
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
        logging.info("RMS119: More than 15 positions already build, no entering the trade {}".format(symbol))
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
    logging.info("RMS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
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
    logging.info("RMS130: square off done for {} response {} ".format(symbol, response))    
    orders = getOrders()
    for order in orders:
        if order["tradingsymbol"] == symbol and order['status'] == 'TRIGGER PENDING':
            # cancel order
            sl_response = kite.cancel_order(order_id=order["order_id"], variety=kite.VARIETY_REGULAR)  
            logging.info("RMS140: cancel stoploss order for {} response {} ".format(symbol, sl_response))
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
    
    if (len(getPositions()) >= max_trades):
        logging.info("RMS119: More than 15 positions already build, no entering the trade {}".format(symbol))
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
    logging.info("RMS120: Placed market {} order for {} with quantity {}".format(buy_sell, symbol, quantity))
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
    logging.info("RBS120: Placed market {} order for {} with quantity {} and sl_price {}".format(buy_sell, symbol, quantity, sl_price))
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
                product=kite.PRODUCT_MIS,
                tag="renko_macd",
                variety=kite.VARIETY_REGULAR)
    logging.info("RMS130: square off done for {} response {} ".format(symbol, response))
    # additional updated stoploss if we added one
    orders = getOrders()
    for order in orders:
        if order["tradingsymbol"] == symbol and order['status'] == 'TRIGGER PENDING':
            # cancel order
            sl_response = kite.cancel_order(order_id=order["order_id"], variety=kite.VARIETY_REGULAR)  
            logging.info("RBS140: cancel stoploss order for {} response {} ".format(symbol, sl_response))
            
    observe_position(symbol, "exit", buy_sell)
    return response

def observe_position(symbol, enter_exit, buy_sell):
    # observe options and future, get option chain and log its data, also get quote of it. log both
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
    logging.info("RMS150: Day end square off cancelling orders {}".format(order_id))
    kite.cancel_order(order_id=order_id, variety=kite.VARIETY_REGULAR)  
    
def squareOffEverything():
    #fetching orders and position information   
    logging.info("RMS160: Squaring off everything ...")
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
    print("pending orders ", pending)
    attempt = 0
    while len(pending)>0 and attempt<5:
        pending = [j for j in pending if j not in drop]
        for order in pending:
            try:
                cancelOrder(order)
                drop.append(order)
            except:
                print("unable to delete order id : ",order)
                attempt+=1
    logging.info("RMS170: Its past 3:10 PM, Successfully square off everything .. ending ")
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
        logging.info("RMS180: More than 1 order found for {} order {}".format(symbol, order))
        return None

def isOrderOrPositionExists(symbol):
    # check if order is already in pending or position is already build before entering the trade
    positions = getPositions()
    orders = getOrders()
    order = [item for item in orders if item["tradingsymbol"] == symbol and item["status"] in valid_order_status]
    position = [item for item in positions if item["tradingsymbol"] == symbol and item["quantity"] != 0]
    if len(position) >= 1 or len(order) >= 1:
        logging.info("RMS190: Position/Order already exists for {}".format(symbol))
        return True
    return False

def getQuantityForInvestment(lastTradedPrice):
    return abs(int(investment / lastTradedPrice))

DEFAULT_TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change this to your desired timezone

def now_in_timezone():
    """Returns the current time in the default timezone."""
    return dt.datetime.now(DEFAULT_TIMEZONE)



#==============================================================================
date_strftime_format = "%Y-%m-%d %H:%M:%S"
locale.setlocale(locale.LC_ALL, '')
local_tz = pytz.timezone('Asia/Kolkata')


investment = 10000
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
locale.setlocale(locale.LC_ALL, '')
date_strftime_format = "%Y-%m-%y %H:%M:%S"
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)


nine_15_am_today = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(9, 15)))
three_20_pm_today = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(15, 20)))
# TODO change quare off time to 3:15
my_squareoff_time = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(15, 5)))
do_not_enter_trade_after_this = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(14, 45)))

logging.info("Logging strting trade")
print("Print, starting trade.")



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
    logging.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, ltp, upper_closest["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    
    quote_upper_closest = kite.quote("NFO:" + lower_closest["tradingsymbol"])["NFO:" + lower_closest["tradingsymbol"]]
    lot_size = upper_closest["lot_size"]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logging.info("{}-{}, stock_ltp, {}, option_symbol, {}, lot_size, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, ltp, lower_closest["tradingsymbol"], lot_size, last_price, last_trade_time, asking_price, offer_price))
    
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
    logging.info("{}-{} FUTURE {} {}, lot {}, last_price {}, last_quantity {}, last_trade_time {}, asking_price {}, offer_price {}".format(symbol, real_ltp, buy_sell, future_data["tradingsymbol"], future_data["lot_size"], last_price, last_quantity, last_trade_time, asking_price, offer_price))
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
    logging.info("{}-{}, stock_ltp, {}, option_symbol, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, real_ltp, option_symbol, last_price, last_trade_time, asking_price, offer_price))
    
    quote_upper_closest = kite.quote("NFO:" + option_symbol2)["NFO:" + option_symbol2]
    last_price = quote_upper_closest["last_price"]
    last_quantity = quote_upper_closest["last_quantity"]
    last_trade_time = quote_upper_closest["last_trade_time"]
    asking_price = quote_upper_closest["depth"]["buy"][0]["price"]
    offer_price = quote_upper_closest["depth"]["sell"][0]["price"]
    logging.info("{}-{}, stock_ltp, {}, option_symbol, {}, last_price, {}, last_trade_time, {}, asking_price, {}, offer_price, {}".format(instrument_type, symbol, real_ltp, option_symbol2, last_price, last_trade_time, asking_price, offer_price))
    
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


max_trades = 2
tradeInLoop = True


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
   
   
#==============================================================================

options_daily_3_month_negative_alpha_001 = ['NAVINFLUOR','INDUSTOWER','BEL','MGL','TATACONSUM','APOLLOTYRE','BHARATFORG','SBIN','INDUSINDBK','LTF','IDFCFIRSTB','AXISBANK','CANBK','GMRINFRA','RECLTD','HAL','GODREJCP','TATAMOTORS','EXIDEIND','SAIL','NESTLEIND','GUJGASLTD','DABUR','PFC','IRCTC','PNB','ONGC','SHREECEM','ZYDUSLIFE','RELIANCE','RBLBANK','ACC','IGL','BHEL','CONCOR','AMBUJACEM','ASTRAL','BSOFT','LICHSGFIN','AARTIIND','MANAPPURAM','IDEA']


while now_in_timezone() <= three_20_pm_today:
    try:
        
        min_in_loop = now_in_timezone().minute
        if min_in_loop%5 == min_in_loop%10:
            time_for_next_10_min_cycle = (60 * (5 - now_in_timezone().minute % 5)) - now_in_timezone().second + 3
        else:
            time_for_next_10_min_cycle = (60 * (10 - now_in_timezone().minute % 5)) - now_in_timezone().second + 3
        
        logging.info("RMS500: sleeping for seconds {}".format(time_for_next_10_min_cycle))
        logging.info("\n")
        time.sleep(time_for_next_10_min_cycle)
        start_t = time.time()
        logging.info("RMS510: Now .. starting the loop")
        if now_in_timezone() < nine_15_am_today:
            logging.info("RMS520: not yet started trading time, wait for some more time {}".format(now_in_timezone()))
            continue
        can_enter_trade = do_not_enter_trade_after_this > now_in_timezone()
        if (now_in_timezone() > my_squareoff_time):
            squareOffEverything()
            break
        minute_in_loop = now_in_timezone().minute
        
        # ================================= 10 minute trades ===================
        tickers = options_daily_3_month_negative_alpha_001
        
        fetch_hr_data = (now_in_timezone().minute >= 15 and now_in_timezone().minute <= 17) or (not ohlc_dict_hr_sell)
        if fetch_hr_data:
            logging.info("RMS580_1HR: Downloading new hour data for sell")
            logging.info("Debugging the details minute {} and ohlc_dict_hr_sell type {}".format(now_in_timezone().minute, type(ohlc_dict_hr_sell)))
            ohlc_dict_hr_sell = fetchOHLCExtendedAll(tickers, "60minute", period_days=20)
            for ticker in tickers:
                #logging.info("RMS590_1HR: for ticker hour sell data {} index {}".format(ticker, ohlc_dict_hr_sell[ticker].index[-1]))
                
                index = ohlc_dict_hr_sell[ticker].index[-1]
                time_index = index - pd.Timedelta(minutes=50)
                if (index > time_index):
                    ohlc_dict_hr_sell[ticker].drop(ohlc_dict_hr_sell[ticker].index[-1], inplace=True)
                index = ohlc_dict_hr_sell[ticker].index[-1]
                #logging.info("RMS590_1HR: SELL for ticker {} index {}".format(ticker, index))
                
                ohlc_dict_hr_sell[ticker]["ema_9"]=ohlc_dict_hr_sell[ticker]["close"].ewm(span=9,min_periods=9).mean()
                ohlc_dict_hr_sell[ticker]["ema_13"]=ohlc_dict_hr_sell[ticker]["close"].ewm(span=13,min_periods=13).mean()
                ohlc_dict_hr_sell[ticker]["ema_55"]=ohlc_dict_hr_sell[ticker]["close"].ewm(span=55,min_periods=55).mean()
                #ohlc_dict_hr_sell[ticker].dropna(inplace=True)
                #ohlc_dict_hr_sell[ticker].index = ohlc_dict_hr[ticker].index.tz_localize(None)
                pass
                
        logging.info("RMS590: Downloading 10 min data for sell")
        # 120 ATR brick size is used, 36 in one day, 10 days --- 360 may be needed to identify trend by renko
        ohlc_dict = fetchOHLCExtendedAll(tickers, sell_interval, 14)
        
        positions = getPositions()
        # first work on exit positions to fast exit stocks 
        for position in positions:
            qty = position["quantity"]
            if qty != 0:
                tradingsymbol = position["tradingsymbol"]
                ticker = tradingsymbol # for stocks, ticker will be same as tradingsymbol
                
                
