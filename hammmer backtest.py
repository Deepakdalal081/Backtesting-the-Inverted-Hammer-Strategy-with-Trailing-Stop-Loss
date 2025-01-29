"""
Created on Tue Jan 28 20:59:04 2025

@author: Deepak Dalal
"""

import numpy as np
import pandas as pd
import datetime as dt 
import yfinance as yf
import matplotlib.pyplot as plt
import os

# Define the date range for stock data
end_date = dt.date.today()
start_date = end_date - dt.timedelta(days=50)

# stock symbol for testing
stocks = ["TCS.NS"]
trades = []
detailed_trades = []  # For storing all the information (entry ,exit and trailing stoploss)

for stock in stocks:
    data = yf.download(stock, start=start_date, end=end_date, interval="30m")
    
    # Store original index for reference
    data['time'] = data.index
    
    # Shift price data
    High = data["High"].shift(1)
    Low = data["Low"].shift(1)
    Close = data["Close"].shift(1)
    Open = data["Open"].shift(1)
    
    # Pattern identification
    data["inverted_pattern"] = (Close < Open) & (2*(Open - Low) < (High - Open) )
    
    entry_price = None # To store the entry price of a trade when an entry signal is triggered
    is_tracking = False # No trade has been entered that why false 
    in_position = False # False? because as there is no trade active 
    total_profit_loss = 0  # Trading starts with no profits or losses.
    

    for i in range(len(data)):
        
        #Storing the time for values
        current_time = data.index[i]
        
        # Entry condition
        if data["inverted_pattern"].iloc[i] and not in_position:
            if i + 1 < len(data):
                
                #inverted hammer formed and entry on the next candle open price
                entry_price = data["Open"].iloc[i+1]
                
                #initial stop-loss at the high of the candle before entry
                stop_loss = data["High"].iloc[i-1] if i > 0 else data["High"].iloc[i]
                
                
                target_price = entry_price * 0.99  # 1% target
                
                #Storing the details in structured format with key-value pairs
                detailed_trades.append({
                    "time": current_time,
                    "action": "Entry",
                    "price": entry_price,
                    "stop_loss": stop_loss,
                    "target": target_price,
                    "current_close": data["Close"].iloc[i]
                })
                
                is_tracking = True
                in_position = True
        
        # Position tracking
        elif entry_price is not None and is_tracking:
            
            # Update stop-loss to the high of the previous candle
            if i > 0:
                new_stop_loss = data["High"].iloc[i-1]
                
                # Updating the new stop-loss is lower than the current one
                if new_stop_loss < stop_loss:
                    stop_loss = new_stop_loss
            
            detailed_trades.append({
                "time": current_time,
                "action": "Tracking",
                "entry_price": entry_price,
                "current_price": data["Close"].iloc[i],
                "stop_loss": stop_loss,
                "target": target_price,
                "high": data["High"].iloc[i],
                "low": data["Low"].iloc[i]
            })
            
            # Check for target hit
            if data["Low"].iloc[i] <= target_price:
                #calculating the profit 
                profit = entry_price - target_price
                total_profit_loss += profit
                
                detailed_trades.append({
                    "time": current_time,
                    "action": "Exit",
                    "type": "Target Hit",
                    "entry_price": entry_price,
                    "exit_price": target_price,
                    "profit": profit
                })
                
                
                # Reset position tracking
                entry_price = None
                is_tracking = False
                in_position = False
                
            # Check for stop-loss hit
            elif data["High"].iloc[i] >= stop_loss:
                
                #calculating the loss
                loss = entry_price - stop_loss
                total_profit_loss += loss
                
                #Storing all the values in the detailed_trades 
                detailed_trades.append({
                    "time": current_time,
                    "action": "Exit",
                    "type": "Stop Loss Hit",
                    "entry_price": entry_price,
                    "exit_price": stop_loss,
                    "profit": loss
                })
                                
                # Reset position tracking
                entry_price = None
                is_tracking = False
                in_position = False


# Create detailed trade DataFrame
detailed_df = pd.DataFrame(detailed_trades)
print("\nDetailed Trade Progression:")

#Storing all the values entry price, exit price, traling stoploss, profit and loss 
print(detailed_df.to_string()) 

print("\nTrade Summary:")

#Only the exit price rows where all the entry, exit and profit/Loss (Avoiding the tracking part rows) 
summary_df = detailed_df[detailed_df['action'] == 'Exit']


if not summary_df.empty:  # if summaray_df have some trades than finding there result in the below columns 
    print(f"\nTotal Profit/Loss: {total_profit_loss:.2f}")
    print(f"Number of Trades: {len(summary_df)}")
    print(f"Win Rate: {(summary_df['profit'] > 0).mean()*100:.2f}%")
    print(f"Average Profit per Trade: {summary_df['profit'].mean():.2f}")
else:
    print("\nNo trades were executed during this period.")
