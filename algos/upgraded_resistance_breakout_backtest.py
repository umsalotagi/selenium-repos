# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 18:07:31 2024

https://www.youtube.com/watch?v=ZudTPpJCbbA


@author: usalotagi
"""


import numpy as np
import pandas as pd
import copy
import time
import datetime as dt
import os
import locale
from kiteconnect import KiteConnect
import statsmodels.api as sm
import csv
import ast


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

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*78)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*78)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_dd(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd


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

def fetchOHLCExtendedAll(tickers, interval, period_days):
    entire_data = {}
    for ticker in tickers:
        try:
            entire_data[ticker] = fetchOHLCExtended(ticker, interval, period_days)
            entire_data[ticker].dropna(inplace=True,how="all")
        except:
            print("possible invalida token for stock ", ticker)
    return entire_data

def fetchOHLC(ticker, interval, from_date, to_date, instrument_token=None):
    """extracts historical data and outputs in the form of dataframe
       inception date string format - dd-mm-yyyy"""
    if instrument_token:
        instrument = instrument_token
    else:
        instrument = instrumentLookup(ticker)
    #print("fetchOHLC", ticker, instrument, interval, from_date, to_date)
    data = pd.DataFrame(kite.historical_data(instrument,from_date,to_date,interval))
    if data.empty:
        print("No data found for ", ticker)
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




################################Backtesting####################################


def run_strategy(interval, atr_multi, tickers, tickers_strategy_definition, start_day_list, end_day_list, enter_strategy_list, exit_strategy_list):
    
    global entire_data, entire_data_hr, ohlc_dict_hr, ohlc_dict
    
    print("started downloading data", interval)
    entire_data = fetchOHLCExtendedAll(tickers, interval, data_period_days) #75 # 120 #30
    print("started downloading 60 min data")
    entire_data_hr = fetchOHLCExtendedAll(tickers, "60minute", period_days=hourly_data_period_days) #500 #45
    
    ohlc_dict_hr = copy.deepcopy(entire_data_hr)
    # calculating ATR and rolling max price for each stock and consolidating this info by stock in a separate dataframe
    ohlc_dict = copy.deepcopy(entire_data)
    
    for ticker in tickers:
        print ("for ", ticker)
        ohlc_dict_hr[ticker]["ema_9_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=9,min_periods=9).mean()
        ohlc_dict_hr[ticker]["ema_13_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=13,min_periods=13).mean()
        ohlc_dict_hr[ticker]["ema_21_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=21,min_periods=21).mean()
        ohlc_dict_hr[ticker]["ema_55_new"]=ohlc_dict_hr[ticker]["close"].ewm(span=55,min_periods=55).mean()
        
        trading_view_ema(ohlc_dict_hr[ticker], 9, "ema_9")
        trading_view_ema(ohlc_dict_hr[ticker], 13, "ema_13")
        trading_view_ema(ohlc_dict_hr[ticker], 55, "ema_55")
        
        ohlc_dict_hr[ticker].dropna(inplace=True)
    

    tickers_signal = {}
    tickers_ret = {}
    for ticker in tickers:
        print("calculating ATR and rolling max price for ",ticker)
        ohlc_dict[ticker]["ATR"] = ATR(ohlc_dict[ticker],20)
        ohlc_dict[ticker]["roll_max_cp"] = ohlc_dict[ticker]["high"].rolling(20).max()
        ohlc_dict[ticker]["roll_min_cp"] = ohlc_dict[ticker]["low"].rolling(20).min()
        ohlc_dict[ticker]["roll_max_vol"] = ohlc_dict[ticker]["volume"].rolling(20).max()
        ohlc_dict[ticker]["roll_vol_mean"] = ohlc_dict[ticker]["volume"].rolling(20).mean()
        
        ohlc_dict[ticker]["roll_5_max_high"] = ohlc_dict[ticker]["high"].rolling(5).max()
        ohlc_dict[ticker]["roll_5_min_low"] = ohlc_dict[ticker]["low"].rolling(5).min()
        ohlc_dict[ticker]["ATR_5"] = ATR(ohlc_dict[ticker],5)
        
        trading_view_ema(ohlc_dict[ticker], 9, "ema_9")
        trading_view_ema(ohlc_dict[ticker], 13, "ema_13")
        trading_view_ema(ohlc_dict[ticker], 21, "ema_21")
        trading_view_ema(ohlc_dict[ticker], 55, "ema_55")
    
        ohlc_dict[ticker]['body'] = abs(ohlc_dict[ticker]['close'] - ohlc_dict[ticker]['open'])
        ohlc_dict[ticker]['range'] = ohlc_dict[ticker]['high'] - ohlc_dict[ticker]['low']
        ohlc_dict[ticker]['upper_wick'] = ohlc_dict[ticker]['high'] - ohlc_dict[ticker][['open', 'close']].max(axis=1)
        ohlc_dict[ticker]['lower_wick'] = ohlc_dict[ticker][['open', 'close']].min(axis=1) - ohlc_dict[ticker]['low']
        
        # Define thresholds
        body_ratio_threshold = 0.7  # Body should be at least 70% of the total range
        wick_to_body_threshold = 0.2  # Wick should be less than 20% of the body
        
        # Calculate the conditions
        ohlc_dict[ticker]['is_momentum_candle'] = ((ohlc_dict[ticker]['body'] / ohlc_dict[ticker]['range'] >= body_ratio_threshold) &
                                    (ohlc_dict[ticker]['upper_wick'] / ohlc_dict[ticker]['body'] <= wick_to_body_threshold) &
                                    (ohlc_dict[ticker]['lower_wick'] / ohlc_dict[ticker]['body'] <= wick_to_body_threshold))
    
        ohlc_dict[ticker].dropna(inplace=True)
        tickers_signal[ticker] = ""
        tickers_ret[ticker] = [0]
        
    # run in loops
    for i in range(len(enter_strategy_list)):
        global start_day, end_day, enter_strategy, exit_strategy
        start_date = start_day_list[i]
        end_date = end_day_list[i]
        enter_strategy = enter_strategy_list[i]
        exit_strategy = exit_strategy_list[i]
        run_other_parts_of_strategy(ohlc_dict, atr_multi, interval, tickers, tickers_strategy_definition, start_date[0], start_date[1], end_date[0], end_date[1], enter_strategy, exit_strategy)
    pass
    

def run_other_parts_of_strategy(ohlc_renko_global, atr_multi, interval, tickers, tickers_strategy_definition, start_month, start_day, end_month, end_day, enter_strategy, exit_strategy):
    
    # here this will not be global 
    ohlc_renko = copy.deepcopy(ohlc_renko_global)
    print("starting strategy inputs ", ohlc_renko_global, atr_multi, interval, tickers, tickers_strategy_definition, start_month, start_day, end_month, end_day, enter_strategy, exit_strategy)
    start_month=9
    start_day=30
    end_month=10
    end_day=19
    st =  pd.Timestamp(year=2024, month=start_month, day=start_day, hour=0, minute=0).tz_localize('Asia/Kolkata')
    et =  pd.Timestamp(year=2024, month=end_month, day=end_day, hour=0, minute=0).tz_localize('Asia/Kolkata')
    for ticker in tickers:
        ohlc_renko[ticker] = ohlc_renko[ticker][ohlc_renko[ticker].index <= et]
        ohlc_renko[ticker] = ohlc_renko[ticker][ohlc_renko[ticker].index >= st]
        
        
    tickers_signal = {}
    tickers_ret = {}
    for ticker in tickers:
        tickers_signal[ticker] = ""
        tickers_ret[ticker] = [0]
        
    final_output = []
    final_output_2 = {}
    global output_all, sell_output_all
    output_all =  None
    sell_output_all = None
    
    
    # identifying signals and calculating daily return (stop loss factored in)
    for ticker in tickers:
        
        buy_enter_time = []
        buy_enter_price = []
        buy_exit_time = []
        buy_exit_price = []
        buy_stop_loss = []
        buy_target = []
        buy_symbol = []
        sell_symbol = []
        sell_enter_time = []
        sell_enter_price = []
        sell_exit_time = []
        sell_exit_price = []
        sell_stop_loss = []
        sell_target = []
        
        print("calculating returns for ",ticker)
        for i in range(1,len(ohlc_dict[ticker])):
            index = ohlc_dict[ticker].index[i]
            #print(ticker, i, index)
            if tickers_signal[ticker] == "":
                
                if (index.hour == 15 and index.minute >= 15):
                    continue
                if (index.hour == 9 and index.minute <= 25):
                    # not to enter in this area as initial is crusial and pullback can be there
                    continue
                if (index.hour == 9 and index.minute <= 25):
                    m = max(ohlc_dict[ticker]["open"].iloc[i-1], ohlc_dict[ticker]["close"].iloc[i-1])
                    n = min(ohlc_dict[ticker]["open"].iloc[i-1], ohlc_dict[ticker]["close"].iloc[i-1])
                    if (m < ohlc_dict[ticker]["close"].iloc[i] and m < ohlc_dict[ticker]["open"].iloc[i]):
                        continue
                    if (n > ohlc_dict[ticker]["close"].iloc[i] and n > ohlc_dict[ticker]["open"].iloc[i]):
                        continue
    
                
                if ohlc_dict[ticker]["high"].iloc[i]>= (ohlc_dict[ticker]["roll_max_cp"].iloc[i]  ) and \
                   (ohlc_dict[ticker]["volume"].iloc[i]>1.5*ohlc_dict[ticker]["roll_max_vol"].iloc[i-1] ):
                    # cchecks 
                    # 1 we should be closer to 55 day ema (before breakout and after brakout should be near)
                    #ema_21_in_range = ohlc_dict[ticker]["roll_5_max_high"].iloc[i-1] > ohlc_dict[ticker]["ema_21"].iloc[i-1] and ohlc_dict[ticker]["ema_21"].iloc[i-1] < ohlc_dict[ticker]["roll_5_min_low"].iloc[i-1]
                    #ema_55_in_range = (ohlc_dict[ticker]["roll_5_max_high"].iloc[i-1]+ohlc_dict[ticker]["ATR_5"].iloc[i-1]) > ohlc_dict[ticker]["ema_55"].iloc[i-1] and ohlc_dict[ticker]["ema_55"].iloc[i-1] < (ohlc_dict[ticker]["roll_5_min_low"].iloc[i-1]-ohlc_dict[ticker]["ATR_5"].iloc[i-1])
                    # check bollinger band instead, 
                    ema_21_in_range, ema_55_in_range = True, True
                    
                    # 2 breakout candle should be momentum candle (large body small wig)
                    is_momentum_candle = ohlc_dict[ticker]['is_momentum_candle'].iloc[i]
                    
                    # to check relative large body 
                    greater_relative_body = ohlc_dict[ticker]['body'].iloc[i] > 1.5*ohlc_dict[ticker]['body'].iloc[i-1]
                    # is_momentum_candle and greater_relative_body
                    
                    # or 3 small green candles 
                    green1 = ohlc_dict[ticker]["open"].iloc[i] < ohlc_dict[ticker]["close"].iloc[i]
                    green2 = ohlc_dict[ticker]["open"].iloc[i-1] < ohlc_dict[ticker]["close"].iloc[i-1]
                    green3 = ohlc_dict[ticker]["open"].iloc[i-2] < ohlc_dict[ticker]["close"].iloc[i-2]
                    # is_momentum_candle and green1 and green2 and green3
                    
                    # 3 larger part of candle should fall outside, if small part of candle, next wait for next
                    body = abs(ohlc_dict[ticker]['close'].iloc[i] - ohlc_dict[ticker]['open'].iloc[i] + 0.001) # added in case open and close both are zero, then to safe it from division
                    outside_body = ohlc_dict[ticker]['close'].iloc[i] - ohlc_dict[ticker]["roll_max_cp"].iloc[i-1] 
                    outside_body_per = outside_body/body > 0.55  # IF NOT WAIT FOR NEXT CANDLE
                    # you can check this with hiekien ashi candle 
                    
                    # 4 check pullback with fibonacci series 
                    
                    # 5 my addition 
                    # 6 volume dry out check - my addition -- but its needs to be entered early 
                    buy_1 = ohlc_dict_hr[ticker][ohlc_dict_hr[ticker].index <= index].iloc[-1]
                    is_houly_bull = buy_1["ema_9_new"]>buy_1["ema_55_new"] and buy_1["ema_9_new"]>buy_1["ema_13_new"]
                    is_houly_bull = True
                    
                    print("time", index, "ema_21_in_range", ema_21_in_range, "ema_55_in_range", ema_55_in_range, "is_momentum_candle", is_momentum_candle, "greater_relative_body", greater_relative_body)
                    print("time", index, "green1", green1, "green2", green2,"green3", green3,  "outside_body_per", outside_body_per, "is_houly_bull", is_houly_bull)
                        
                    if ema_21_in_range and ema_55_in_range and outside_body_per and is_houly_bull:
                        if is_momentum_candle and greater_relative_body:
                            #print("BUY adding for ", ticker, index, i)
                            tickers_signal[ticker] = "Buy"
                            buy_enter_time.append(index)
                            buy_enter_price.append(ohlc_dict[ticker]["close"].iloc[i])
                            buy_symbol.append(ticker)
                        elif is_momentum_candle and green1 and green2 and green3:
                            #print("BUY adding for ", ticker, index, i)
                            tickers_signal[ticker] = "Buy"
                            buy_enter_time.append(index)
                            buy_enter_price.append(ohlc_dict[ticker]["close"].iloc[i])
                            buy_symbol.append(ticker)
                    
                elif ohlc_dict[ticker]["low"].iloc[i]<= (ohlc_dict[ticker]["roll_min_cp"].iloc[i] ) and \
                   (ohlc_dict[ticker]["volume"].iloc[i]>1.5*ohlc_dict[ticker]["roll_max_vol"].iloc[i-1]):
                    # 1 we should be closer to 55 day ema (before breakout and after brakout should be near)
                    #ema_21_in_range = ohlc_dict[ticker]["roll_5_max_high"].iloc[i-1] > ohlc_dict[ticker]["ema_21"].iloc[i-1] and ohlc_dict[ticker]["ema_21"].iloc[i-1] < ohlc_dict[ticker]["roll_5_min_low"].iloc[i-1]
                    #ema_55_in_range = (ohlc_dict[ticker]["roll_5_max_high"].iloc[i-1]+ohlc_dict[ticker]["ATR_5"].iloc[i-1]) > ohlc_dict[ticker]["ema_55"].iloc[i-1] and ohlc_dict[ticker]["ema_55"].iloc[i-1] < (ohlc_dict[ticker]["roll_5_min_low"].iloc[i-1]-ohlc_dict[ticker]["ATR_5"].iloc[i-1])
                    ema_21_in_range, ema_55_in_range = True, True
                    
                    # 2 breakout candle should be momentum candle (large body small wig)
                    is_momentum_candle = ohlc_dict[ticker]['is_momentum_candle'].iloc[i]
                    
                    # to check relative large body 
                    greater_relative_body = ohlc_dict[ticker]['body'].iloc[i] > 1.5*ohlc_dict[ticker]['body'].iloc[i-1]
                    # is_momentum_candle and greater_relative_body
                    
                    # 3 larger part of candle should fall outside, if small part of candle, next wait for next
                    body = abs(ohlc_dict[ticker]['close'].iloc[i] - ohlc_dict[ticker]['open'].iloc[i] + 0.001)
                    outside_body = ohlc_dict[ticker]["roll_min_cp"].iloc[i-1] - ohlc_dict[ticker]['close'].iloc[i]
                    outside_body_per = outside_body/body > 0.55  # IF NOT WAIT FOR NEXT CANDLE LIKE BELOW
                    
                    # or 3 small green candles -- to be considered in NEXT
                    red1 = ohlc_dict[ticker]["open"].iloc[i] > ohlc_dict[ticker]["close"].iloc[i]
                    red2 = ohlc_dict[ticker]["open"].iloc[i-1] > ohlc_dict[ticker]["close"].iloc[i-1]
                    red3 = ohlc_dict[ticker]["open"].iloc[i-2] > ohlc_dict[ticker]["close"].iloc[i-2]
                    # green1 and green2 and green3
                    
                    # 4 check pullback with fibonacci series 
                    
                    # 5 my addition 
                    # 6 volume dry out check - my addition -- but its needs to be entered early 
                    sell_1 = ohlc_dict_hr[ticker][ohlc_dict_hr[ticker].index <= index].iloc[-1]
                    is_houly_bear = sell_1["ema_9_new"]<sell_1["ema_55_new"] and sell_1["ema_9_new"]<sell_1["ema_13_new"]
                    is_houly_bear = True
                    
                    print("time", index, "SELL ema_21_in_range", ema_21_in_range, "ema_55_in_range", ema_55_in_range, "is_momentum_candle", is_momentum_candle, "greater_relative_body", greater_relative_body)
                    print("time", index, "SELL red1", red1, "red2", red2,"red3", red3,  "outside_body_per", outside_body_per, "is_houly_bear", is_houly_bear)
                        
                    if ema_21_in_range and ema_55_in_range and outside_body_per and is_houly_bear:
                        if is_momentum_candle and greater_relative_body:
                            #print("BUY adding for ", ticker, index, i)
                            tickers_signal[ticker] = "Sell"
                            sell_enter_time.append(index)
                            sell_enter_price.append(ohlc_dict[ticker]["close"].iloc[i])
                            sell_symbol.append(ticker)
                            #sell_stop_loss.append()
                            #sell_target.append()
                        """elif is_momentum_candle and red1 and red2 and red3:
                            #print("BUY adding for ", ticker, index, i)
                            tickers_signal[ticker] = "Sell"
                            sell_enter_time.append(index)
                            sell_enter_price.append(ohlc_dict[ticker]["close"].iloc[i])
                            sell_symbol.append(ticker)"""
                pass
            elif tickers_signal[ticker] == "Buy":
                # stop loss check and exit check todo
                if ohlc_dict[ticker]["low"].iloc[i]< (ohlc_dict[ticker]["close"].iloc[i-1] - atr_multi*ohlc_dict[ticker]["ATR"].iloc[i-1]):
                    tickers_signal[ticker] = ""
                    buy_exit_price.append(ohlc_dict[ticker]["close"].iloc[i-1] - atr_multi*ohlc_dict[ticker]["ATR"].iloc[i-1])
                    buy_exit_time.append(index)
                elif (index.hour == 15 and index.minute == 5):
                    # trading end time
                    tickers_signal[ticker] = ""
                    buy_exit_price.append(ohlc_dict[ticker]["close"].iloc[i])
                    buy_exit_time.append(index)
                pass
            elif tickers_signal[ticker] == "Sell":
                #print("trying sell", index)
                if ohlc_dict[ticker]["high"].iloc[i]> (ohlc_dict[ticker]["close"].iloc[i-1] + atr_multi*ohlc_dict[ticker]["ATR"].iloc[i-1]):
                    tickers_signal[ticker] = ""
                    sell_exit_price.append(ohlc_dict[ticker]["close"].iloc[i-1] + atr_multi*ohlc_dict[ticker]["ATR"].iloc[i-1])
                    sell_exit_time.append(index)
                elif (index.hour == 15 and index.minute == 5):
                    # trading end time
                    tickers_signal[ticker] = ""
                    sell_exit_price.append(ohlc_dict[ticker]["close"].iloc[i])
                    sell_exit_time.append(index)
                pass
            pass
            
        if len(buy_enter_time) != len(buy_exit_time):
            print("SOMETHING WRONG", buy_enter_time, "exit", buy_exit_time)
            buy_enter_time.pop()
            buy_enter_price.pop()
            buy_symbol.pop()
        if len(sell_enter_time) != len(sell_exit_time):
            print("SOMETHING WRONG SELL", sell_enter_time, "sell_exit", sell_exit_time)
            sell_enter_time.pop()
            sell_enter_price.pop()
            sell_symbol.pop()
            
        output = pd.DataFrame(data = {"time": buy_enter_time, "buy_enter_price": buy_enter_price, "buy_exit_price" : buy_exit_price, "buy_exit_time": buy_exit_time})
        output["profit"] = output["buy_exit_price"] - output["buy_enter_price"]
        output["ret"] = output["profit"]/output["buy_enter_price"]
        output["holding_time"] = output["buy_exit_time"] - output["time"]
        
        sell_output = pd.DataFrame(data = {"time": sell_enter_time, "sell_symbol": sell_symbol, "sell_enter_price": sell_enter_price, "sell_exit_price" : sell_exit_price, "sell_exit_time": sell_exit_time})
        sell_output["profit"] = sell_output["sell_enter_price"] - sell_output["sell_exit_price"]
        sell_output["ret"] = sell_output["profit"]/sell_output["sell_enter_price"]
        sell_output["holding_time"] = sell_output["sell_exit_time"] - sell_output["time"]
        
        if len(output) == 0:
            #print(len(output), " length of output..")
            output_summary = {"symbol": ticker, "interval": interval, "mean_ret": 0, 
                              "strike": 0, "avg_holding_period" : 0, "no_of_trades": len(output)}
        else:
            #output["ret"].mean()
            #print("now again ")
            #output["holding_time"].mean()
            # assuming its weekly return, calculating all max_dd, cagr and sharpe metrices
            output_summary = {"symbol": ticker, "interval": interval, "mean_ret": output["ret"].mean(), 
                        "strike": (output["profit"] > 0).sum() / len(output),
                        "avg_holding_period" : output["holding_time"].mean(),"no_of_trades": len(output)}
            
        if len(sell_output) == 0:
            #print(len(output), " length of output..")
            output_summary_sell = {"symbol": ticker, "interval": interval, "mean_ret": 0, 
                              "strike": 0, "avg_holding_period" : 0, "no_of_trades": len(sell_output)}
        else:
            # assuming its weekly return, calculating all max_dd, cagr and sharpe metrices
            output_summary_sell = {"symbol": ticker, "interval": interval, "mean_ret": sell_output["ret"].mean(), 
                        "strike": (sell_output["profit"] > 0).sum() / len(sell_output),
                        "avg_holding_period" : sell_output["holding_time"].mean(),"no_of_trades": len(sell_output)}
            
        final_output_2[ticker + "BUY"] = output_summary
        final_output_2[ticker + "SELL"] = output_summary_sell
        final_output.append(output_summary)
        final_output.append(output_summary_sell)
        
        
        
        if len(output) > 0:
            if output_all is not None:
                output_all = pd.concat([output_all, output], ignore_index=True)
            else:
                output_all = output
        if len(sell_output) > 0:
            print("ouuuuu", sell_output)
            if sell_output_all is not None:
                sell_output_all = pd.concat([sell_output_all, sell_output], ignore_index=True) 
            else:
                sell_output_all = sell_output
    
    if type(output_all) == pd.DataFrame:
        cagr_buy = (output_all["buy_exit_price"].sum() / output_all["buy_enter_price"].sum()) ** (252/5) - 1
        no_of_trades_buy = len(output_all)
        avg_return = round(output_all["ret"].sum()/no_of_trades_buy, 5)
        sum_return = round(output_all["ret"].sum(), 5)
        strike_buy = round( (output_all["profit"] > 0).sum() / no_of_trades_buy , 2)
        str_output_buy_pretext = "BUY interval {} brick_size {}, tickers_strategy_definition {}, enter {}, exit {}, start_time {}, end_time {}, tickers {}".format(interval, atr_multi, tickers_strategy_definition, enter_strategy, exit_strategy, start_day, end_day, "no_storing_here")
        str_output_buy = "BUY cagr {} avg_return {} simple_return_buy {} strike {} trades {} cagr_per_trade {} profit_per_trade {}".format(cagr_buy, avg_return, sum_return, strike_buy, no_of_trades_buy, cagr_buy/no_of_trades_buy, sum_return/no_of_trades_buy)
        serious_output.append(str_output_buy_pretext)
        serious_output.append(str_output_buy)
        print(str_output_buy_pretext)
        print(str_output_buy)
    
    if type(sell_output_all) == pd.DataFrame:
        cagr_sell = (sell_output_all["sell_enter_price"].sum() / sell_output_all["sell_exit_price"].sum()) ** (252/5) - 1
        no_of_trades_sell = len(sell_output_all)
        avg_return = round( sell_output_all["ret"].sum()/no_of_trades_sell , 5)
        sum_return = round( sell_output_all["ret"].sum() , 5)
        strike_sell = round( (sell_output_all["profit"] > 0).sum() / no_of_trades_sell , 2)
        str_output_sell_pretext = "SELL interval {} brick_size {}, tickers_strategy_definition {}, enter {}, exit {}, start_time {}, end_time {}, tickers {}".format(interval, atr_multi, tickers_strategy_definition, enter_strategy, exit_strategy, start_day, end_day, "no_storing_here")
        str_output_sell = "SELL cagr {} avg_return {} simple_return_buy {} strike {} trades {} cagr_per_trade {} profit_per_trade {}".format(cagr_sell, avg_return, sum_return, strike_sell, no_of_trades_sell, cagr_sell/no_of_trades_sell, sum_return/no_of_trades_sell)
        serious_output.append(str_output_sell_pretext)
        serious_output.append(str_output_sell)
        print(str_output_sell_pretext)
        print(str_output_sell)
        pass
    pass

# ============================================================================


investment = 10000
cwd = os.chdir("C:\\Users\\usalotagi\\Python\\Stock\\breakout\\logs")
locale.setlocale(locale.LC_ALL, '')
date_strftime_format = "%Y-%m-%y %H:%M:%S"
access_token = open("C:\\Users\\usalotagi\\Python\\webdriver\\access_token.txt",'r').read()
key_secret = open("C:\\Users\\usalotagi\\Python\\webdriver\\api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

nifty_200_stocks = ['ABB','ACC','APLAPOLLO','AUBANK','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ADANIPOWER','ATGL','ABCAPITAL','ABFRL','ALKEM','AMBUJACEM','APOLLOHOSP','APOLLOTYRE','ASHOKLEY','ASIANPAINT','ASTRAL','AUROPHARMA','DMART','AXISBANK','BSE','BAJAJ-AUTO','BAJFINANCE','BAJAJFINSV','BAJAJHLDNG','BALKRISIND','BANDHANBNK','BANKBARODA','BANKINDIA','MAHABANK','BERGEPAINT','BDL','BEL','BHARATFORG','BHEL','BPCL','BHARTIARTL','BIOCON','BOSCHLTD','BRITANNIA','CGPOWER','CANBK','CHOLAFIN','CIPLA','COALINDIA','COFORGE','COLPAL','CONCOR','CUMMINSIND','DLF','DABUR','DALBHARAT','DEEPAKNTR','DELHIVERY','DIVISLAB','DIXON','LALPATHLAB','DRREDDY','EICHERMOT','ESCORTS','NYKAA','FEDERALBNK','FACT','FORTIS','GAIL','GMRINFRA','GLAND','GODREJCP','GODREJPROP','GRASIM','GUJGASLTD','HCLTECH','HDFCAMC','HDFCBANK','HDFCLIFE','HAVELLS','HEROMOTOCO','HINDALCO','HAL','HINDPETRO','HINDUNILVR','ICICIBANK','ICICIGI','ICICIPRULI','IDBI','IDFCFIRSTB','ITC','INDIANB','INDHOTEL','IOC','IRCTC','IRFC','IGL','INDUSTOWER','INDUSINDBK','NAUKRI','INFY','INDIGO','IPCALAB','JSWENERGY','JSWINFRA','JSWSTEEL','JINDALSTEL','JIOFIN','JUBLFOOD','KPITTECH','KALYANKJIL','KOTAKBANK','LTF','LTTS','LICHSGFIN','LTIM','LT','LAURUSLABS','LICI','LUPIN','MRF','LODHA','M&MFIN','M&M','MANKIND','MARICO','MARUTI','MFSL','MAXHEALTH','MAZDOCK','MPHASIS','NHPC','NMDC','NTPC','NESTLEIND','OBEROIRLTY','ONGC','OIL','PAYTM','OFSS','POLICYBZR','PIIND','PAGEIND','PATANJALI','PERSISTENT','PETRONET','PIDILITIND','PEL','POLYCAB','POONAWALLA','PFC','POWERGRID','PRESTIGE','PNB','RECLTD','RVNL','RELIANCE','SBICARD','SBILIFE','SJVN','SRF','MOTHERSON','SHREECEM','SHRIRAMFIN','SIEMENS','SONACOMS','SBIN','SAIL','SUNPHARMA','SUNTV','SUPREMEIND','SUZLON','SYNGENE','TVSMOTOR','TATACHEM','TATACOMM','TCS','TATACONSUM','TATAELXSI','TATAMOTORS','TATAPOWER','TATASTEEL','TATATECH','TECHM','TITAN','TORNTPHARM','TORNTPOWER','TRENT','TIINDIA','UPL','ULTRACEMCO','UNIONBANK','UNITDSPR','VBL','VEDL','IDEA','VOLTAS','WIPRO','YESBANK','ZEEL','ZOMATO','ZYDUSLIFE']
nifty_options_stocks = ['M&M', 'ULTRACEMCO', 'HAL', 'TITAN', 'ADANIPORTS', 'COALINDIA', 'ASIANPAINT', 'POWERGRID', 'BAJAJ-AUTO', 'BAJAJFINSV', 'WIPRO', 'TRENT', 'IOC', 'NESTLEIND', 'SIEMENS', 'JSWSTEEL', 'BEL', 'DLF', 'SBILIFE', 'TATASTEEL', 'RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK', 'INFY', 'SBIN', 'HINDUNILVR', 'ITC', 'LT', 'HCLTECH', 'BAJFINANCE', 'SUNPHARMA', 'TATAMOTORS', 'ONGC', 'NTPC', 'MARUTI', 'AXISBANK', 'KOTAKBANK', 'ADANIENT', 'INDIGO', 'GRASIM', 'PFC', 'LTIM', 'VEDL', 'RECLTD', 'PIDILITIND', 'HDFCLIFE', 'ABB', 'TECHM', 'BPCL', 'AMBUJACEM', 'GAIL', 'GODREJCP', 'HINDALCO', 'BRITANNIA', 'DIVISLAB', 'TATAPOWER', 'CIPLA', 'EICHERMOT', 'TVSMOTOR', 'MOTHERSON', 'BANKBARODA', 'CHOLAFIN', 'PNB', 'SHRIRAMFIN', 'HAVELLS', 'TATACONSUM', 'TORNTPHARM', 'INDUSTOWER', 'DABUR', 'HEROMOTOCO', 'ZYDUSLIFE', 'DRREDDY', 'INDUSINDBK', 'ICICIGI', 'ICICIPRULI', 'UNITDSPR', 'CUMMINSIND', 'LUPIN', 'POLYCAB', 'IDEA', 'COLPAL', 'APOLLOHOSP', 'GMRINFRA', 'CANBK', 'OFSS', 'BHEL', 'JINDALSTEL', 'HDFCAMC', 'NAUKRI', 'BOSCHLTD', 'HINDPETRO', 'INDHOTEL', 'SHREECEM', 'AUROPHARMA', 'MARICO', 'PERSISTENT', 'GODREJPROP', 'MUTHOOTFIN', 'SRF', 'DIXON', 'IRCTC', 'BHARATFORG', 'ALKEM', 'ASHOKLEY', 'SBICARD', 'BERGEPAINT', 'PIIND', 'OBEROIRLTY', 'ABBOTINDIA', 'NMDC', 'LTTS', 'VOLTAS', 'CONCOR', 'MPHASIS', 'ABCAPITAL', 'MRF', 'BALKRISIND', 'IDFCFIRSTB', 'TATACOMM', 'PETRONET', 'SAIL', 'UBL', 'ASTRAL', 'AUBANK', 'COROMANDEL', 'GLENMARK', 'FEDERALBNK', 'PAGEIND', 'UPL', 'BIOCON', 'GUJGASLTD', 'ACC', 'JUBLFOOD', 'COFORGE', 'LTF', 'ESCORTS', 'EXIDEIND', 'DEEPAKNTR', 'M&MFIN', 'MFSL', 'IGL', 'LICHSGFIN', 'DALBHARAT', 'JKCEMENT', 'IPCALAB', 'SYNGENE', 'APOLLOTYRE', 'BANDHANBNK', 'NATIONALUM', 'SUNTV', 'ABFRL', 'HINDCOPPER', 'CROMPTON', 'LALPATHLAB', 'TATACHEM', 'MCX', 'LAURUSLABS', 'PEL', 'ATUL', 'AARTIIND', 'CHAMBLFERT', 'RAMCOCEM', 'BATAINDIA', 'IEX', 'INDIAMART', 'BSOFT', 'MGL', 'IDFC', 'MANAPPURAM', 'GRANULES', 'NAVINFLUOR', 'PVRINOX', 'RBLBANK', 'CUB', 'BALRAMCHIN', 'CANFINHOME', 'METROPOLIS', 'GNFC']
nifty_100 = ['ABB','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ADANIPOWER','ATGL','AMBUJACEM','APOLLOHOSP','ASIANPAINT','DMART','AXISBANK','BAJAJ-AUTO','BAJFINANCE','BAJAJFINSV','BAJAJHLDNG','BANKBARODA','BERGEPAINT','BEL','BPCL','BHARTIARTL','BOSCHLTD','BRITANNIA','CANBK','CHOLAFIN','CIPLA','COALINDIA','COLPAL','DLF','DABUR','DIVISLAB','DRREDDY','EICHERMOT','GAIL','GODREJCP','GRASIM','HCLTECH','HDFCBANK','HDFCLIFE','HAVELLS','HEROMOTOCO','HINDALCO','HAL','HINDUNILVR','ICICIBANK','ICICIGI','ICICIPRULI','ITC','IOC','IRCTC','IRFC','INDUSINDBK','NAUKRI','INFY','INDIGO','JSWSTEEL','JINDALSTEL','JIOFIN','KOTAKBANK','LTIM','LT','LICI','M&M','MARICO','MARUTI','NTPC','NESTLEIND','ONGC','PIDILITIND','PFC','POWERGRID','PNB','RECLTD','RELIANCE','SBICARD','SBILIFE','SRF','MOTHERSON','SHREECEM','SHRIRAMFIN','SIEMENS','SBIN','SUNPHARMA','TVSMOTOR','TCS','TATACONSUM','TATAMOTORS','TATAPOWER','TATASTEEL','TECHM','TITAN','TORNTPHARM','TRENT','ULTRACEMCO','UNITDSPR','VBL','VEDL','WIPRO','ZOMATO','ZYDUSLIFE']
nifty_50 = ["ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BPCL","BHARTIARTL","BRITANNIA","CIPLA","COALINDIA","DIVISLAB","DRREDDY","EICHERMOT","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","ITC","INDUSINDBK","INFY","JSWSTEEL","KOTAKBANK","LTIM","LT","M&M","MARUTI","NTPC","NESTLEIND","ONGC","POWERGRID","RELIANCE","SBILIFE","SHRIRAMFIN","SBIN","SUNPHARMA","TCS","TATACONSUM","TATAMOTORS","TATASTEEL","TECHM","TITAN","ULTRACEMCO","WIPRO"]
nifty_alpha_50_june = ["ABB","ADANIPOWER","ARE&M","APARINDS","AUROPHARMA","BSE","BAJAJ-AUTO","BDL","BEL","BHEL","CDSL","CENTURYTEX","COLPAL","CUMMINSIND","DIXON","GLENMARK","HAL","HINDCOPPER","HINDPETRO","POWERINDIA","HUDCO","IRFC","INDUSTOWER","INOXWIND","JSL","KEI","KALYANKJIL","LUPIN","LODHA","MCX","NBCC","NHPC","OIL","OFSS","POLICYBZR","PHOENIXLTD","PFC","PRESTIGE","RECLTD","RVNL","SJVN","SOLARINDS","SUZLON","TVSMOTOR","TORNTPOWER","TRENT","VBL","ZOMATO","ZYDUSLIFE"]
nifty_my_alpha_500 = ['CONCORDBIO','BSE','GODFRYPHLP','INOXWIND','PCBL','KFINTECH','CHOLAHLDNG','BBTC','HSCL','PAYTM','CDSL','KALYANKJIL','SUVENPHAR','MCX','FSL','SUZLON','JUBLPHARMA','POLICYBZR','QUESS','ZOMATO','INDIACEM','KAYNES','JUBLINGREA','SHYAMMETL','HFCL','GODREJIND','JMFINANCIL','TRENT','CAPLIPOINT','PERSISTENT','BALRAMCHIN','BAJAJHLDNG','NUVAMA','SHRIRAMFIN','RVNL','BIKAJI','PRSMJOHNSN','NAUKRI','CAMPUS','CRAFTSMAN','MPHASIS','IEX','MGL','DIXON','MAXHEALTH','JINDALSAW','CAMS']

merged_list = list(set(nifty_200_stocks + nifty_options_stocks))

# 2 month alpha with more than 0.003 value


nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)



# ==========================================================================

start_day_list = [(9,31),  (9,31),  (9,31)]
end_day_list = [(10,19),  (10,12), (10,5)]
enter_stategy_list = ["", "",  ""]
exit_strategy_list = ["", "", ""]


start_day_list = [(9,31)]
end_day_list = [(10,19)]
enter_stategy_list = [""]
exit_strategy_list = [""]


serious_output = []
options_daily_3_month_negative_alpha_0005 = ['KOTAKBANK','COALINDIA','GAIL','DALBHARAT','NATIONALUM','OBEROIRLTY','PETRONET','RECLTD','INDUSTOWER','GRASIM','APOLLOTYRE','POLYCAB','LT','HINDCOPPER','INDUSINDBK','JSWSTEEL','ZYDUSLIFE','GUJGASLTD','HINDALCO','AXISBANK','ESCORTS','WIPRO','CHAMBLFERT','ULTRACEMCO','SRF','BANDHANBNK','CUB','BATAINDIA','ASHOKLEY','LTF','GODREJPROP','JINDALSTEL','CUMMINSIND','TATAMOTORS','GNFC','SHREECEM','SIEMENS','ACC','ADANIENT','ABB','TATACHEM','ABCAPITAL','AMBUJACEM','ADANIPORTS','GMRINFRA','NAVINFLUOR','IRCTC','BALKRISIND','BEL','MANAPPURAM','CANFINHOME','SBIN','BHEL','TATASTEEL','CANBK','IDFCFIRSTB','NMDC','BANKBARODA','SAIL','BHARATFORG','CONCOR','PNB','ASTRAL','EXIDEIND','HAL','BSOFT','AARTIIND','LICHSGFIN','RBLBANK','IDEA']
hourly_data_period_days = 55
data_period_days = 41

#tickers = 
many_tickers = [options_daily_3_month_negative_alpha_0005]
many_tickers_names = ["options_daily_3_month_negative_alpha_0005"]

for i in range(0, len(many_tickers)):
    tickers = many_tickers[i]
    ticker_name = many_tickers_names[i]
    
    serious_output = []
    run_strategy("10minute", 1.5, tickers, ticker_name + "_resistance_breakout", start_day_list, end_day_list, enter_stategy_list, exit_strategy_list)
    with open(ticker_name + "_resistance_breakout" + ".txt", "w") as file:
        for line in serious_output:
            file.write(line + "\n")
    
    
