# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 00:02:53 2025

@author: usalotagi
"""
import pandas_ta as ta
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
from stocktrends import Renko
from kiteconnect.exceptions import NetworkException
import sys


def ATR(df,n):
    "function to calculate True Range and Average True Range"
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df.drop(['H-L','H-PC','L-PC'],axis=1, inplace=True)


def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*24)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    # 24 being the number of candles per day, we are working on 15 min candles, so its 4*6 hr = 24
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*24)
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

invalid_token_tickers = []
def fetchOHLCExtendedAll(tickers, interval, period_days):
    entire_data = {}
    for ticker in tickers:
        instrument_token = None
        if ticker in ticker_token_map:
            instrument_token = ticker_token_map[ticker]
        try:
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today(), instrument_token)
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except NetworkException as e:
            print("Possible too many request error, retyring for ", ticker, e)
            time.sleep(0.2)
            from_date = dt.date.today() - dt.timedelta(period_days)
            entire_data[ticker] = fetchOHLC(ticker, interval, from_date, dt.date.today(), instrument_token)
            entire_data[ticker].dropna(inplace=True,how="all")
            
        except Exception as e:
            print("Possible invalid token for", ticker, e)
            invalid_token_tickers.append(ticker)
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

def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    df['Chikou_span'] = df["close"].shift(-shift_size)
    
def RS(DF_stock, DF_index, span=14, lookback=14):
    #df = DF_stock.copy()
    DF_stock['Index_Close'] = DF_index['close']
    # TODO : get index close of same date, time
    DF_stock['RS'] = DF_stock['close'] / DF_stock['Index_Close']
    DF_stock['RS_EMA'] = DF_stock['RS'].ewm(span=span, adjust=False).mean()
    DF_stock['RS_slope'] = DF_stock['RS_EMA'].diff()
    #df2 = df.drop(['Index_Close','RS'],axis=1)
    # Normalized RS: % outperformance over lookback period
    stock_return = DF_stock['close'] / DF_stock['close'].shift(lookback)
    index_return = DF_stock['Index_Close'] / DF_stock['Index_Close'].shift(lookback)
    DF_stock['Normalized_RS'] = (stock_return / index_return - 1) * 100
    #return df2
    
def MACD(df,a=12,b=26,c=9):
    """function to calculate MACD
       typical values a(fast moving average) = 12; 
                      b(slow moving average) =26; 
                      c(signal line ma window) =9"""
    #df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df["Signal_name"] = df.apply(lambda row: "bullish" if row["MACD"] > row["Signal"] else "bearish", axis=1)
    df["Histogram"] = df["MACD"] - df["Signal"]
    #df.dropna(inplace=True)
    #return df

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
    


def supertrendNEW(df, n=10, m=3):
    #df = df.copy()
    #df['ATR'] = atrNEW(df, n)
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
    
    #return df[['close', 'Strend', 'UpperBand', 'LowerBand']]
    return

###############################################################################
# check high tf histogram as more than certain amount, not jjust macd 
# and then current tf hiekienashi, with ha calculation where close = 0.5 open + high + low + 1.5 close
def fn_enter_condition(ticker, i, high_tf_idx):

    one = cp_ohlc_dict[ticker]["close"].iloc[i] > cp_ohlc_dict[ticker]["Senkou_span_A"].iloc[i]
    two = ohlc_dict_high_tf[ticker]["close"].iloc[high_tf_idx] > ohlc_dict_high_tf[ticker]["Senkou_span_A"].iloc[high_tf_idx]
    return one and two


def fn_exit_condition(ticker, i, high_tf_idx):
    
    one = cp_ohlc_dict[ticker]["close"].iloc[i] < cp_ohlc_dict[ticker]["Senkou_span_A"].iloc[i]
    two = ohlc_dict_high_tf[ticker]["close"].iloc[high_tf_idx] < ohlc_dict_high_tf[ticker]["Senkou_span_A"].iloc[high_tf_idx]
    return one or two


###############################################################################
nifty_100 = ['ABB','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ADANIPOWER','ATGL','AMBUJACEM','APOLLOHOSP','ASIANPAINT','DMART','AXISBANK','BAJAJ-AUTO','BAJFINANCE','BAJAJFINSV','BAJAJHLDNG','BANKBARODA','BERGEPAINT','BEL','BPCL','BHARTIARTL','BOSCHLTD','BRITANNIA','CANBK','CHOLAFIN','CIPLA','COALINDIA','COLPAL','DLF','DABUR','DIVISLAB','DRREDDY','EICHERMOT','GAIL','GODREJCP','GRASIM','HCLTECH','HDFCBANK','HDFCLIFE','HAVELLS','HEROMOTOCO','HINDALCO','HAL','HINDUNILVR','ICICIBANK','ICICIGI','ICICIPRULI','ITC','IOC','IRCTC','IRFC','INDUSINDBK','NAUKRI','INFY','INDIGO','JSWSTEEL','JINDALSTEL','JIOFIN','KOTAKBANK','LTIM','LT','LICI','M&M','MARICO','MARUTI','NTPC','NESTLEIND','ONGC','PIDILITIND','PFC','POWERGRID','PNB','RECLTD','RELIANCE','SBICARD','SBILIFE','SRF','MOTHERSON','SHREECEM','SHRIRAMFIN','SIEMENS','SBIN','SUNPHARMA','TVSMOTOR','TCS','TATACONSUM','TATAMOTORS','TATAPOWER','TATASTEEL','TECHM','TITAN','TORNTPHARM','TRENT','ULTRACEMCO','UNITDSPR','VBL','VEDL','WIPRO','ZYDUSLIFE']

tickers = ['ABB','ADANIENSOL','ADANIENT']
tickers = ['NIFTY_50_PE']

ticker_token_map = { "NIFTY_50_PE" : "17082626"}

strategy_tf = "15minute"
tf_fetch_days = 180
strtegy_high_tf = "day"
high_tf_fetch_days = 250

day_trade = False
trading_days = 252  # yearly
capital = 1_00_00_000  # 1 crore
slippage_rate = 0.0005  # example: 0.05%

trade_type = "Buy" # its Buy or Sell


###############################################################################


cwd = os.chdir("C:\\Users\\usalotagi\\Python\\webdriver")
locale.setlocale(locale.LC_ALL, '')
date_strftime_format = "%Y-%m-%y %H:%M:%S"
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

nse_instrument_dump = kite.instruments("NSE")
nse_instrument_df = pd.DataFrame(nse_instrument_dump)

ohlc_dict = fetchOHLCExtendedAll(tickers, strategy_tf, period_days=tf_fetch_days)
ohlc_dict_high_timeframe = fetchOHLCExtendedAll(tickers, strtegy_high_tf, period_days=high_tf_fetch_days)
index_DF = fetchOHLCExtendedAll(["NIFTY 50"], strategy_tf, period_days=tf_fetch_days)["NIFTY 50"]

for ticker in tickers:
    ohlc_dict[ticker]["ema_3"]=ohlc_dict[ticker]["close"].ewm(span=3,min_periods=3).mean()
    ohlc_dict[ticker]["ema_9"]=ohlc_dict[ticker]["close"].ewm(span=9,min_periods=9).mean()
    ohlc_dict[ticker]["ema_13"]=ohlc_dict[ticker]["close"].ewm(span=13,min_periods=13).mean()
    ohlc_dict[ticker]["ema_21"]=ohlc_dict[ticker]["close"].ewm(span=21,min_periods=21).mean()
    # ATR 14 was used in chatgpt
    ATR(ohlc_dict[ticker],20)
    # Pick stocks with rising RS → outperforming index.
    RS(ohlc_dict[ticker], index_DF,14,70)
    # ATR(14) / Close > 1.5%
    ohlc_dict[ticker]["ATR_to_price"] = ohlc_dict[ticker]["ATR"] / ohlc_dict[ticker]["close"]
    # Volume > 20-SMA of Volume
    ohlc_dict[ticker]["volume_sma"]=ohlc_dict[ticker]["volume"].rolling(window=20).mean()
    ichimoko(ohlc_dict[ticker])
    MACD(ohlc_dict[ticker],5,13,4)
    heikinashi(ohlc_dict[ticker]) # 5, 13, 26
    supertrendNEW(ohlc_dict[ticker])
    ohlc_dict[ticker].dropna(inplace=True)
    
    ichimoko(ohlc_dict_high_timeframe[ticker])
    MACD(ohlc_dict_high_timeframe[ticker],5,13,4)
    
    
   
###############################################################################

cp_ohlc_dict = copy.deepcopy(ohlc_dict)
ohlc_dict_high_tf = copy.deepcopy(ohlc_dict_high_timeframe)

tickers_signal = {}
tickers_trades = {}
tickers_entered = {}

for ticker in tickers:
    tickers_signal[ticker] = ""
    tickers_entered[ticker] = None
    tickers_trades[ticker] = []
    
for ticker in tickers:
    print("calculating returns for ",ticker)

    for i in range(0,len(ohlc_dict[ticker])-2):
        #print(f"tickers_signal  {tickers_signal[ticker]}")
        ts = cp_ohlc_dict[ticker].index[i]
        # Find the last closed high TF candle before or at this timestamp
        high_tf_idx = ohlc_dict_high_tf[ticker].index.get_indexer([ts], method="pad")[0] - 1
        
        if tickers_signal[ticker] == "":
            
            ENTER_CONDITION = fn_enter_condition(ticker, i, high_tf_idx)
            
            if ENTER_CONDITION:
                tickers_signal[ticker] = trade_type
                tickers_entered[ticker] = ohlc_dict[ticker].iloc[i+1]
                
        elif tickers_signal[ticker] == "Buy":
            
            EXIT_CONDITION = fn_exit_condition(ticker, i, high_tf_idx)
            
            day_trade_EOD = False
            index_adjuster = 0
            if day_trade and cp_ohlc_dict[ticker].iloc[i].name.minute == 15 and cp_ohlc_dict[ticker].iloc[i].name.hour == 15:
                print("got used index adjuster")
                day_trade_EOD = True
                index_adjuster = -1
                
            if EXIT_CONDITION or day_trade_EOD:
                tickers_signal[ticker] = ""
                trade_obj = {
                    "enter_index": tickers_entered[ticker].name,
                    "enter": tickers_entered[ticker]["open"],
                    "exit": ohlc_dict[ticker].iloc[i+1+index_adjuster]["open"],
                    "exit_index": ohlc_dict[ticker].iloc[i+1+index_adjuster].name,
                    "profit": ohlc_dict[ticker].iloc[i+1+index_adjuster]["open"] - tickers_entered[ticker]["open"]
                }
                tickers_trades[ticker].append(trade_obj)
                tickers_entered[ticker] = None
                
        elif tickers_signal[ticker] == "Sell":
            
            EXIT_CONDITION = fn_exit_condition(ticker, i, high_tf_idx)
            
            day_trade_EOD = False
            index_adjuster = 0
            if day_trade and cp_ohlc_dict[ticker].iloc[i].name.minute == 15 and cp_ohlc_dict[ticker].iloc[i].name.hour == 15:
                print("got used index adjuster")
                day_trade_EOD = True
                index_adjuster = -1
            
            if EXIT_CONDITION:
                tickers_signal[ticker] = ""
                trade_obj = {
                    "enter_index": tickers_entered[ticker].name,
                    "enter": tickers_entered[ticker]["open"],
                    "exit": ohlc_dict[ticker].iloc[i+1+index_adjuster]["open"],
                    "exit_index": ohlc_dict[ticker].iloc[i+1+index_adjuster].name,
                    "profit": tickers_entered[ticker]["open"] - ohlc_dict[ticker].iloc[i+1+index_adjuster]["open"]
                }
                tickers_trades[ticker].append(trade_obj)
                tickers_entered[ticker] = None
    

print("calculating stock wise metrices")

trades_df = {}
all_trades = []
all_trade_conclusion = {}

for ticker in tickers:
    # calculating sotck wise data
    if len(tickers_trades[ticker]) == 0:
        print("no trades took place for this ticker", ticker)
        continue
    trades_df[ticker] = pd.DataFrame(tickers_trades[ticker]) 
    all_trades.append(trades_df[ticker])
    trades_df[ticker]["slippage_cost"] = trades_df[ticker]["enter"] * slippage_rate + trades_df[ticker]["exit"] * slippage_rate
    trades_df[ticker]["net_profit"] = trades_df[ticker]["profit"] - trades_df[ticker]["slippage_cost"]
    
    trades_df[ticker]["return_pct"] = trades_df[ticker]["net_profit"] / capital
    mean_return = trades_df[ticker]["return_pct"].mean()
    std_return = trades_df[ticker]["return_pct"].std()
    sharpe_ratio = (mean_return / std_return) * np.sqrt(trading_days)
    
    trades_df[ticker]["cum_pnl"] = trades_df[ticker]["net_profit"].cumsum()
    trades_df[ticker]["cum_max"] = trades_df[ticker]["cum_pnl"].cummax()
    trades_df[ticker]["drawdown"] = trades_df[ticker]["cum_pnl"] - trades_df[ticker]["cum_max"]
    max_dd = trades_df[ticker]["drawdown"].min()  # Most negative value
    
    start_capital = capital
    end_capital = start_capital + trades_df[ticker]["net_profit"].sum()
    
    num_years = (len(trades_df[ticker]) / trading_days)
    cagr = (end_capital / start_capital) ** (1 / num_years) - 1
    
    win_rate = (trades_df[ticker]["net_profit"] > 0).mean()
    
    all_trade_conclusion[ticker] = {"cagr":cagr, "win_rate":win_rate, "max_dd":max_dd, "sharpe_ratio":sharpe_ratio, "total_trades":len(trades_df[ticker])}


print("calculating all metrices")
if len(all_trades) == 0:
    sys.exit("no trades in entire trade")
    
all_trades_df = pd.concat(all_trades, ignore_index=True).sort_values(by="enter_index")
# Slippage cost (enter + exit)
all_trades_df["slippage_cost"] = all_trades_df["enter"] * slippage_rate + all_trades_df["exit"] * slippage_rate

# Net profit after slippage
all_trades_df["net_profit"] = all_trades_df["profit"] - all_trades_df["slippage_cost"]

# Percentage return based on fixed capital
all_trades_df["return_pct"] = all_trades_df["net_profit"] / capital

    
# Cumulative PnL
# Cumulative PnL
all_trades_df["cum_pnl"] = all_trades_df["net_profit"].cumsum()

# Max Drawdown
all_trades_df["cum_max"] = all_trades_df["cum_pnl"].cummax()
all_trades_df["drawdown"] = all_trades_df["cum_pnl"] - all_trades_df["cum_max"]
max_dd = all_trades_df["drawdown"].min()

# CAGR
start_capital = capital
end_capital = start_capital + all_trades_df["net_profit"].sum()
num_years = len(all_trades_df) / trading_days
cagr = (end_capital / start_capital) ** (1 / num_years) - 1

# Sharpe Ratio
mean_return = all_trades_df["return_pct"].mean()
std_return = all_trades_df["return_pct"].std()
sharpe_ratio = (mean_return / std_return) * np.sqrt(trading_days)

# Win rate
win_rate = (all_trades_df["net_profit"] > 0).mean()

print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Max Drawdown: {max_dd:,.2f}")
print(f"CAGR: {cagr*100:.2f}%")
print(f"Win Rate: {win_rate*100:.2f}%, total trades: {len(all_trades_df)}")
print(f"Total Net Profit: {all_trades_df['net_profit'].sum():,.2f}")
