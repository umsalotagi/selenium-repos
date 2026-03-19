# -*- coding: utf-8 -*-
"""
Created on Sat Mar 14 23:40:22 2026

@author: usalotagi

NOTE: all indicator add row to existing ohlc dataframe and does not copy or return new dataframe

to calculate all such idicators on HA or other ohlc data, create new dataframe for HA ohlc 
and pass that to these indicator and same indicator will calculate for HA ohlc
of couse you need to rename columns to standard open close low high for this to work
"""

import numpy as np
import pandas as pd



def ATR(df,n):
    "function to calculate True Range and Average True Range"
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df.drop(['H-L','H-PC','L-PC'],axis=1, inplace=True)
    

def ichimoko(df, fast=9, slow=26, span_b=52, shift_size=26):
    df['Tenkan_sen'] = (df["high"].rolling(window=fast).max() + df["low"].rolling(window=fast).min()) / 2
    df['Kijun_sen'] = (df["high"].rolling(window=slow).max() + df["low"].rolling(window=slow).min()) / 2
    df['Senkou_span_A'] = ((df['Tenkan_sen'] + df['Kijun_sen']) / 2).shift(shift_size)
    df['Senkou_span_B'] = (df["high"].rolling(window=span_b).max() + df["low"].rolling(window=span_b).min()) / 2
    df['Senkou_span_B'] = df['Senkou_span_B'].shift(shift_size)
    df['Chikou_span'] = df["close"].shift(-shift_size)
    
    
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
    
def RSI(df, n=14, ma_period=14):
    "function to calculate RSI"
    df["change"] = df["close"] - df["close"].shift(1)
    df["gain"] = np.where(df["change"]>=0, df["change"], 0)
    df["loss"] = np.where(df["change"]<0, -1*df["change"], 0)
    df["avgGain"] = df["gain"].ewm(alpha=1/n, min_periods=n).mean()
    df["avgLoss"] = df["loss"].ewm(alpha=1/n, min_periods=n).mean()
    df["rs"] = df["avgGain"]/df["avgLoss"]
    df["rsi"] = 100 - (100/ (1 + df["rs"]))
    df["rsi_ma"] = df["rsi"].ewm(span=ma_period, adjust=False).mean()
    df.drop(['change','gain','loss', 'avgGain', 'avgLoss'],axis=1, inplace=True)
    return
    
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
    
def heikinashi_analysis(df):
    df['Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] == df['HA_Open'])
    df['Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] == df['HA_Open'])
    df['Doji_Bearish'] = (df['HA_Close'] < df['HA_Open']) & (df['HA_High'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    df['Doji_Bullish'] = (df['HA_Close'] > df['HA_Open']) & (df['HA_Low'] != df['HA_Open']) & np.abs(df['HA_Close'] - df['HA_Open']) < ((df['HA_High'] - df['HA_Low']) * 0.1)
    # medium to large body - to be calculated with percentage of close price
    df['large_body'] = np.abs(df['HA_Close'] - df['HA_Open']) > df['HA_Close'] * 0.001
    

def __atrCalc(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']

def supertrend(DF, n=10, m=3, name="Strend"):
    df = DF.copy()
    df['ATR1'] = __atrCalc(df, n)
    hl2 = (df['high'] + df['low']) / 2
    df['UpperBand'] = hl2 + m * df['ATR1']
    df['LowerBand'] = hl2 - m * df['ATR1']
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
    DF[name] = df['Strend']
    return

    
def donchian_channel(df, period=20, shift=0):
    """
    Calculates Donchian Channel with shift.
    df must contain 'high' and 'low' columns.
    """
    df["donchian_upper"] = df["high"].rolling(window=period).max().shift(shift)
    df["donchian_lower"] = df["low"].rolling(window=period).min().shift(shift)
    df["donchian_middle"] = (df["donchian_upper"] + df["donchian_lower"]) / 2
    return


def calculate_cpr(df):
    """
    Calculate CPR, Supports, and Resistances.
    Requires columns: ['high', 'low', 'close'].
    Assumes df is daily data.
    """
    # Pivot Point
    df["cpr_pivot"] = (df["high"] + df["low"] + df["close"]) / 3

    # CPR
    df["cpr_bottom"] = (df["high"] + df["low"]) / 2
    df["cpr_top"] = 2 * df["cpr_pivot"] - df["cpr_bottom"]

    # Support & Resistance
    df["cpr_r1"] = 2 * df["cpr_pivot"] - df["low"]
    df["cpr_s1"] = 2 * df["cpr_pivot"] - df["high"]

    df["cpr_r2"] = df["cpr_pivot"] + (df["high"] - df["low"])
    df["cpr_s2"] = df["cpr_pivot"] - (df["high"] - df["low"])

    df["cpr_r3"] = df["high"] + 2 * (df["cpr_pivot"] - df["low"])
    df["cpr_s3"] = df["low"] - 2 * (df["high"] - df["cpr_pivot"])
    
    # CPR width and % of pivot
    df["cpr_width"] = abs(df["cpr_top"] - df["cpr_bottom"])
    df["cpr_width_pct"] = (df["cpr_width"] / df["cpr_pivot"]) * 100
    df["cpr_atr_ratio"] = df["cpr_width"] / df["ATR"]

    # Tagging thresholds (index-style)
    def tag(row):
        if row["cpr_width_pct"] < 0.15 and row["cpr_atr_ratio"] < 0.45:
            return "Narrow"
        elif row["cpr_width_pct"] > 0.25 or row["cpr_atr_ratio"] > 0.70:
            return "Wide"
        else:
            return "Normal"

    df["cpr_tag"] = df.apply(tag, axis=1)

    return df




def add_last_week_cpr_levels(df: pd.DataFrame) -> pd.DataFrame:

    #df.index = pd.to_datetime(df.index)

    # Get last completed trading week (Mon–Fri)
    tz = df.index.tz 
    today = pd.Timestamp.now(tz=tz).normalize()
    last_friday = today - pd.offsets.Week(weekday=4)
    last_monday = last_friday - pd.offsets.BDay(4)

    week_df = df.loc[last_monday:last_friday]

    high = week_df["high"].max()
    low = week_df["low"].min()
    close = week_df["close"].iloc[-1]

    pivot = (high + low + close) / 3
    bc = (high + low) / 2
    tc = 2 * pivot - bc

    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    df["week_cpr_pivot"] = pivot
    df["week_cpr_bottom"] = bc
    df["week_cpr_top"] = tc
    df["week_cpr_r1"] = r1
    df["week_cpr_r2"] = r2
    df["week_cpr_r3"] = r3
    df["week_cpr_s1"] = s1
    df["week_cpr_s2"] = s2
    df["week_cpr_s3"] = s3
    
    df["week_cpr_width"] = abs(df["week_cpr_top"] - df["week_cpr_bottom"])
    df["week_cpr_width_pct"] = (df["week_cpr_width"] / df["week_cpr_pivot"]) * 100
    df["week_cpr_atr_ratio"] = df["week_cpr_width"] / week_df["ATR"]
    
    # Weekly tagging (optimized thresholds)
    def tag_weekly(row):
        if row["week_cpr_width_pct"] < 0.15 :#and row["week_cpr_atr_ratio"] < 0.35:
            return "Narrow"
        elif row["week_cpr_width_pct"] > 0.40:# or row["week_cpr_atr_ratio"] > 0.80:
            return "Wide"
        else:
            return "Normal"
    
    df["weekly_cpr_tag"] = df.apply(tag_weekly, axis=1)

    return df


def wilder_rma(series, period):
    rma = series.copy()
    rma[:] = np.nan

    # first value = SMA
    rma.iloc[period - 1] = series.iloc[:period].mean()

    # Wilder smoothing
    for i in range(period, len(series)):
        rma.iloc[i] = (
            (rma.iloc[i - 1] * (period - 1) + series.iloc[i]) / period
        )

    return rma


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
    #df = df.copy()

    # Calculate True Range (TR)
    df['prev_close'] = df['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_pc'] = abs(df['high'] - df['prev_close'])
    df['low_pc'] = abs(df['low'] - df['prev_close'])
    df['TR'] = df[['high_low', 'high_pc', 'low_pc']].max(axis=1)

    # Calculate +DM and -DM
    df['+DM'] = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                         np.maximum(df['high'] - df['high'].shift(1), 0), 0)
    df['-DM'] = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                         np.maximum(df['low'].shift(1) - df['low'], 0), 0)

    # Smooth the values
    """tr_smooth = df['TR'].rolling(window=period).sum()
    plus_dm_smooth = df['+DM'].rolling(window=period).sum()
    minus_dm_smooth = df['-DM'].rolling(window=period).sum()"""
    tr_smooth = wilder_rma(df['TR'], period)
    plus_dm_smooth = wilder_rma(df['+DM'], period)
    minus_dm_smooth = wilder_rma(df['-DM'], period)

    # Calculate +DI and -DI
    df['+DI'] = 100 * (plus_dm_smooth / tr_smooth)
    df['-DI'] = 100 * (minus_dm_smooth / tr_smooth)

    # Calculate DX
    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])

    # Calculate ADX
    #df['ADX'] = df['DX'].rolling(window=period).mean()
    df['ADX'] = wilder_rma(df['DX'], period)

    # Clean up
    df.drop(columns=['prev_close', 'high_low', 'high_pc', 'low_pc', 'TR', '+DM', '-DM'], inplace=True)

    return df



def kaufman_efficiency_ratio(df: pd.DataFrame, period: int = 10):
    """
    Calculate Kaufman Efficiency Ratio (KER)
    """
    price = df['close']
    # Direction (net movement)
    direction = abs(price - price.shift(period))
    # Volatility (sum of absolute movements)
    volatility = abs(price.diff()).rolling(period).sum()
    df['KER'] = direction / volatility

    
def add_session_vwap(df: pd.DataFrame) -> pd.DataFrame:
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    # Cumulative VWAP
    cum_pv = (typical_price * df['volume']).groupby(df.index.date).cumsum()
    cum_vol = df['volume'].groupby(df.index.date).cumsum()
    df['vwap'] = cum_pv / cum_vol
    return df

def add_absolute_vwap(df: pd.DataFrame) -> pd.DataFrame:
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_pv = (typical_price * df['volume']).cumsum()
    cum_vol = df['volume'].cumsum()
    df['vwap'] = cum_pv / cum_vol
    return df
    
NIFTY_100_stocks = ['ABB','ADANIENSOL','ADANIENT','ADANIGREEN','ADANIPORTS','ADANIPOWER','ATGL','AMBUJACEM','APOLLOHOSP','ASIANPAINT','DMART','AXISBANK','BAJAJ-AUTO','BAJFINANCE','BAJAJFINSV','BAJAJHLDNG','BANKBARODA','BERGEPAINT','BEL','BPCL','BHARTIARTL','BOSCHLTD','BRITANNIA','CANBK','CHOLAFIN','CIPLA','COALINDIA','COLPAL','DLF','DABUR','DIVISLAB','DRREDDY','EICHERMOT','GAIL','GODREJCP','GRASIM','HCLTECH','HDFCBANK','HDFCLIFE','HAVELLS','HEROMOTOCO','HINDALCO','HAL','HINDUNILVR','ICICIBANK','ICICIGI','ICICIPRULI','ITC','IOC','IRCTC','IRFC','INDUSINDBK','NAUKRI','INFY','INDIGO','JSWSTEEL','JINDALSTEL','JIOFIN','KOTAKBANK','LTIM','LT','LICI','M&M','MARICO','MARUTI','NTPC','NESTLEIND','ONGC','PIDILITIND','PFC','POWERGRID','PNB','RECLTD','RELIANCE','SBICARD','SBILIFE','SRF','MOTHERSON','SHREECEM','SHRIRAMFIN','SIEMENS','SBIN','SUNPHARMA','TVSMOTOR','TCS','TATACONSUM','TATAMOTORS','TATAPOWER','TATASTEEL','TECHM','TITAN','TORNTPHARM','TRENT','ULTRACEMCO','UNITDSPR','VBL','VEDL','WIPRO','ZYDUSLIFE']
INDEXES = ["NIFTY 50", "NIFTY BANK", "NIFTY FIN SERVICE"]
INDEXES_OP_NAME = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
