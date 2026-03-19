# -*- coding: utf-8 -*-
"""
Created on Sat Mar 14 16:58:17 2026

@author: usalotagi
"""

import pandas as pd
import time
from kiteconnect import KiteConnect, KiteTicker
import os
import datetime as dt
import logging
import locale
import datetime
import pytz
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
import json
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

from kiteApi import ZerodhaBroker, TradeSetup
import indicators 

def now_in_timezone():
    """Returns the current time in the default timezone."""
    return dt.datetime.now(DEFAULT_TIMEZONE)


DEFAULT_TIMEZONE = pytz.timezone('Asia/Kolkata')  # Change this to your desired timezone
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)
kws = KiteTicker(key_secret[0], access_token)

options_instruments = kite.instruments(exchange="NFO")
today_date = now_in_timezone()
current_year = today_date.year
if today_date.month<=25:
    current_month = today_date.month
else:
    current_month = today_date.month + 1
options_expiring_this_month = [item for item in options_instruments if item["segment"] == "NFO-OPT" and item["expiry"].year == current_year and  item["expiry"].month == current_month]
futures_expiring_this_month = [item for item in options_instruments if item["segment"] == "NFO-FUT" and item["expiry"].year == current_year and  item["expiry"].month == current_month]


date_strftime_format = "%Y-%m-%d %H:%M:%S"
locale.setlocale(locale.LC_ALL, '')
local_tz = pytz.timezone('Asia/Kolkata')

cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")

log_file_name = "5_min_trade.txt"
tradeSetup = TradeSetup()
logger = tradeSetup.logger_setup(log_file_name, date_strftime_format)


logger.info("Not eligible for sell off")
nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)

logger.info("Logging strting trade")

max_trades = 2000
no_of_trades = 0
test_mode = True

zerodhaBroker = ZerodhaBroker(kite, nse_instrument_df, logger, "cpr")


def on_order_update(ws, data):
    all_trades = zerodhaBroker.my_orders
    
    logger.info("detected order update {}".format(data))
    if data["status"] == "COMPLETE":
        # target triggered, cancel stop loss order
        cpr_trade = [item for item in all_trades if item.target_order and item.target_order['order_id'] == data["order_id"]]
        if cpr_trade:
            zerodhaBroker.cancelOrder(cpr_trade.sl_order["order_id"])
            return
        # stop loss triggered, cancel target order
        cpr_trade = [item for item in all_trades if item.sl_order and item.sl_order['order_id'] == data["order_id"]]
        if cpr_trade:
            zerodhaBroker.cancelOrder(cpr_trade.target_order["order_id"])
            return
        #main order executed, place target and stoploss order
        cpr_trade = [item for item in all_trades if item.enter_order and item.enter_order['order_id'] == data["order_id"]]
        if cpr_trade:
            quantity = cpr_trade.enter_order['quantity']
            transaction_type = cpr_trade.enter_order['transaction_type']
            tradingsymbol = cpr_trade.enter_order['tradingsymbol']
            exit_t_type = "SELL" if transaction_type == "BUY" else "BUY"
            if cpr_trade.target_price:
                zerodhaBroker.placeLimitOrder(tradingsymbol, exit_t_type, quantity, cpr_trade.target_price, data["order_id"])
            if cpr_trade.sl_price:
                zerodhaBroker.placeStopLossOrder(tradingsymbol, exit_t_type, quantity, cpr_trade.sl_price, data["order_id"])
            return
        
kws.on_order_update = on_order_update
kws.connect(threaded=True)

        

nine_15_am_today = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(9, 15)))
three_20_pm_today = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(15, 20)))
my_squareoff_time = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(15, 5)))
do_not_enter_trade_after_this = DEFAULT_TIMEZONE.localize(dt.datetime.combine(now_in_timezone().today(), dt.time(14, 45)))
ohlc_dict_hr = None
investment = 10000

#---- cpr strategy variables ----
cpr_tickers = indicators.NIFTY_100_stocks + indicators.INDEXES
cpr_option_tickers = indicators.INDEXES

tickers = indicators.NIFTY_100_stocks +  indicators.INDEXES

ohlc_dict_day = zerodhaBroker.fetchOHLCExtendedAll(tickers, "day", period_days=30)
for ticker in tickers:
    ohlc_dict_day[ticker]["ATR"] = indicators.ATR(ohlc_dict_day[ticker],14)
    indicators.calculate_cpr(ohlc_dict_day[ticker])
    indicators.add_last_week_cpr_levels(ohlc_dict_day[ticker])
    index = ohlc_dict_day[ticker].index[-1]
    if (index.day == now_in_timezone().day):
        ohlc_dict_day[ticker].drop(ohlc_dict_day[ticker].index[-1], inplace=True)
    
    

while now_in_timezone() <= three_20_pm_today:
#while True:
    try:
        
        time_for_next_5_min_cycle = (60 * (5 - now_in_timezone().minute % 5)) - now_in_timezone().second + 3
        logging.info("RBS500: sleeping for seconds {}".format(time_for_next_5_min_cycle))
        logging.info("\n")
        # Observer implementation here for zerodhaBroker.addObserverOrder
        zerodhaBroker.observerTradeCheck(time_for_next_5_min_cycle)
        start_t = time.time()
        logging.info("RMS510: Now .. starting the loop")
        if now_in_timezone() < nine_15_am_today:
            logging.info("RMS520: not yet started trading time, wait for some more time {}".format(now_in_timezone()))
            continue
        can_enter_trade = do_not_enter_trade_after_this > now_in_timezone()
        
        if (now_in_timezone() > my_squareoff_time):
            zerodhaBroker.squareOffEverything()
            break
        minute_in_loop = now_in_timezone().minute
        
        # ================================= 5 minute trades ===================
        
        fetch_hr_data = (now_in_timezone().minute >= 15 and now_in_timezone().minute <= 17) or (not ohlc_dict_hr)
        if fetch_hr_data:
            logging.info("RMS580_1HR: Downloading new hour data for buy")
            #logging.info("Debugging the details minute {} and  type {}".format(now_in_timezone().minute, type(ohlc_dict_hr_sell)))
            ohlc_dict_hr = zerodhaBroker.fetchOHLCExtendedAll(tickers, "60minute", period_days=20)
            for ticker in tickers:
                #logging.info("RMS590_1HR: for ticker hour sell data {} index {}".format(ticker, ohlc_dict_hr_sell[ticker].index[-1]))
                
                index = ohlc_dict_hr[ticker].index[-1]
                time_index = index - pd.Timedelta(minutes=50)
                if (index > time_index):
                    ohlc_dict_hr[ticker].drop(ohlc_dict_hr[ticker].index[-1], inplace=True)
                index = ohlc_dict_hr[ticker].index[-1]
                #logging.info("RMS590_1HR: SELL for ticker {} index {}".format(ticker, index))
                
                pass
                
        logging.info("RMS590: Downloading 10 min data for sell")
        # 120 ATR brick size is used, 36 in one day, 10 days --- 360 may be needed to identify trend by renko
        ohlc_dict = zerodhaBroker.fetchOHLCExtendedAll(tickers, "5minute", 14)
        
        # calculate indicators here
        for ticker in tickers:
            #ohlc_dict[ticker]["ATR"] = indicators.ATR(ohlc_dict[ticker],14)
            indicators.donchian_channel(ohlc_dict[ticker], 5, 0)
        
            
        for ticker in tickers:
            
            index = ohlc_dict[ticker].index[-1]
            if (index.minute == minute_in_loop):
                # this is bringing latest data, we only need 5 min data
                ohlc_dict[ticker].drop(ohlc_dict[ticker].index[-1], inplace=True)
            index = ohlc_dict[ticker].index[-1]
            
            # cpr trade
            order_exists = any(obj.ticker == ticker for obj in zerodhaBroker.my_orders)
            logger.info("order_exists {} and {} ".format( order_exists, ticker))
            if not order_exists:
                # if there is no trade for given symbol, only then proceed to execute trade
                maxxx = ohlc_dict_day[ticker]["cpr_top"].iloc[-1]
                #maxxx = max(ohlc_dict_day[ticker]["cpr_r1"].iloc[-1], ohlc_dict_day[ticker]["high"].iloc[-1])
                stop_loss = ohlc_dict_day[ticker]["cpr_bottom"].iloc[-1] - 1
                target = ohlc_dict_day[ticker]["cpr_r1"].iloc[-1]
                buy_at = ohlc_dict[ticker]["high"].iloc[-1]
                should_enter_buy = ( True and
                    ohlc_dict[ticker]["high"].iloc[-1] > ohlc_dict[ticker]["donchian_upper"].iloc[-2] and
                    # following condition is future, we place limit order for this
                    #ohlc_dict[ticker]["high"].iloc[-1] < ohlc_dict[ticker]["high"].iloc[i+1] and 
                    ohlc_dict_day[ticker]['cpr_tag'].iloc[-1]  == "Narrow" and
                    # followin conditions confirm that prices coming from down
                    ohlc_dict[ticker]["open"].iloc[-4] > ohlc_dict_day[ticker]["cpr_top"].iloc[-1] and
                    ohlc_dict[ticker]["close"].iloc[-4] > ohlc_dict_day[ticker]["cpr_top"].iloc[-1] and
                    # following condition confirms crossover
                    ohlc_dict[ticker]["low"].iloc[-2] < maxxx and
                    ohlc_dict[ticker]["close"].iloc[-1] > maxxx)
                
                minnn = ohlc_dict_day[ticker]["cpr_bottom"].iloc[-1]
                stop_loss = ohlc_dict_day[ticker]["cpr_top"].iloc[-1] + 1
                target = ohlc_dict_day[ticker]["cpr_s1"].iloc[-1]
                sell_at = ohlc_dict[ticker]["low"].iloc[-1]
                should_enter_sell =  ( True and
                    ohlc_dict[ticker]["low"].iloc[-1] < ohlc_dict[ticker]["donchian_lower"].iloc[-2] and
                    # following condition is future, we place limit order for this
                    #ohlc_dict[ticker]["low"].iloc[-1] > ohlc_dict[ticker]["low"].iloc[i+1] and 
                    ohlc_dict_day[ticker]['cpr_tag'].iloc[-1]  == "Narrow" and
                    # followin conditions confirm that prices coming down from up
                    ohlc_dict[ticker]["open"].iloc[-4] < ohlc_dict_day[ticker]["cpr_bottom"].iloc[-1] and
                    ohlc_dict[ticker]["close"].iloc[-4] < ohlc_dict_day[ticker]["cpr_bottom"].iloc[-1] and
                    # following condition confirms crossover
                    ohlc_dict[ticker]["high"].iloc[-2] > minnn and
                    ohlc_dict[ticker]["close"].iloc[-1] < minnn)
                
                if (should_enter_buy):
                    if ticker in cpr_option_tickers:
                        # place option trade, option trade need to triggered when prices cross previous high
                        # so here we need to add observer and that observer will place main order, sl and target also
                        # observer should run each 20 seconds
                        zerodhaBroker.addObserverOrder(ticker, sell_at, "PUT")
                        pass
                    else:
                        # place stock trade
                        quantity = abs(int(investment / buy_at))
                        if quantity == 0 :
                            continue;
                        my_new_order = zerodhaBroker.placeLimitOrder("NSE:"+ticker, "BUY", quantity, buy_at)
                        my_new_order.target_price = target
                        my_new_order.sl_price = stop_loss
                        
                if (should_enter_sell):
                    if ticker in cpr_option_tickers:
                        # place option trade
                        zerodhaBroker.addObserverOrder(ticker, buy_at, "CALL")
                        pass
                    else:
                        # place stock trade
                        quantity = abs(int(investment / sell_at))
                        if quantity == 0 :
                            continue;
                        my_new_order = zerodhaBroker.placeLimitOrder("NSE:"+ticker, "SELL", quantity, sell_at)
                        my_new_order.target_price = target
                        my_new_order.sl_price = stop_loss
                
            
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
                

