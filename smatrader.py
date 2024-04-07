#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from datetime import datetime, timezone
import time
import MetaTrader5 as mt5


# In[7]:


class Indicators:
    def __init__(self, symbols, timeframes, past_data, resample, timezone, sma_periods=(10, 20, 50, 100, 200)):
        self.symbols = symbols
        self.timeframes = timeframes
        self.past_data = past_data
        self.resample = resample
        self.timezone = timezone
        self.sma_periods = sma_periods
        self.raw_data = {}

        # Fetch and process data for all pairs and timeframes
        self.fetch_and_process_data()

    def fetch_and_process_data(self):
        for symbol in self.symbols:
            gmt_time = datetime.now(pytz.timezone('Etc/GMT'))
            gmt_now = gmt_time + timedelta(hours = self.timezone)
            # Fetch data for the current symbol and timeframe
            df = self.fetch_data(symbol, gmt_now)

            if df is not None:
                df_resampled = self.resample_data(df)
                self.raw_data[symbol] = df_resampled.dropna()

        # Perform strategy for all pairs and timeframes
        self.sma_strategy()

    def fetch_data(self, symbol, gmt_now):
        try:
        # This is where you fetch data for each symbol
            raw = pd.DataFrame(mt5.copy_rates_from(symbol, self.timeframes, gmt_now, self.past_data))
            raw['time'] = pd.to_datetime(raw['time'], unit='s', errors='coerce')
            raw.drop(columns=['tick_volume', 'real_volume', 'high', 'low'], inplace=True)
            raw.set_index('time', inplace=True)
            return raw
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
    def resample_data(self, df):
        return df.resample(self.resample).last()

    def sma_strategy(self):
        for key, df in self.raw_data.items():
            df = df.copy()
            df["SMA_7"] = df["close"].rolling(7).mean()
            df["SMA_28"] = df["close"].rolling(28).mean()
            df["SMA_100"] = df["close"].rolling(100).mean()
            df["SMA_200"] = df["close"].rolling(200).mean()

            condition_1 = (df["SMA_7"] > df["SMA_28"]) & (df["SMA_100"] > df["SMA_200"])
            condition_2 = (df["SMA_7"] < df["SMA_28"]) & (df["SMA_100"] < df["SMA_200"])

            df.loc[:, "position_sma"] = np.select([condition_1, condition_2], [1, -1], default=0)
            self.raw_data[key] = df

    def get_signal(self, symbol):
        df = self.raw_data.get(symbol, None)

        if df is not None:
            signal_value = df['position_sma'].iloc[-2]
            
            if signal_value == 1:
                return "buy"
            elif signal_value == -1:
                return "sell"
            else:
                return "neutral"
        else:
            return f"Data not available for {symbol}"

