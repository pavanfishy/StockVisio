import pandas as pd
import os

def read_all_csvs_in_folder(folder_path):
    """Read all CSV files in a given folder and return a list of DataFrames."""
    dfs = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def preprocess_zerodha(df):
    """Clean and standardize Zerodha trade book."""
    df = df.rename(columns={
        "symbol": "Symbol",
        "trade_type": "Type",
        "quantity": "Quantity",
        "price": "Price",
        "order_execution_time": "TradeTime",
        "segment": "Segment",
        "exchange": "Exchange"
    })
    df["TradeTime"] = pd.to_datetime(df["TradeTime"])
    df["Symbol"] = df["Symbol"].str.upper()
    df["Type"] = df["Type"].str.upper()
    df["Segment"] = df["Segment"].str.upper()
    df["Segment"] = df["Segment"].replace({"EQ": "EQUITY", "NSE_CASH": "EQUITY"})
    df["Broker"] = "Zerodha"
    return df[["TradeTime", "Symbol", "Type", "Segment", "Quantity", "Price", "Exchange", "Broker"]]

def preprocess_fyers(df):
    """Clean and standardize Fyers trade book."""
    df = df.rename(columns={
        "date": "Date",
        "time": "Time",
        "symbol": "Symbol",
        "type": "Type",
        "qty": "Quantity",
        "trade_price": "Price",
        "segment": "Segment"
    })
    df["TradeTime"] = pd.to_datetime(df["Date"] + " " + df["Time"], dayfirst=True)
    df["Symbol"] = df["Symbol"].str.upper()
    df["Type"] = df["Type"].str.upper()
    df["Segment"] = df["Segment"].str.upper()
    df["Exchange"] = df["Segment"].str.extract(r'(NSE|BSE)', expand=False)
    df["Segment"] = df["Segment"].replace({"EQ": "EQUITY", "NSE_CASH": "EQUITY", "BSE_CASH": "EQUITY"})
    df["Broker"] = "Fyers"
    return df[["TradeTime", "Symbol", "Type", "Segment", "Quantity", "Price", "Exchange", "Broker"]]

def preprocess_dhan(df):
    """Clean and standardize Dhan trade book."""
    df = df.rename(columns={
        "Date": "Date",
        "Time": "Time",
        "Name": "Symbol",
        "Buy/Sell": "Type",
        "Quantity/Lot": "Quantity",
        "Trade Price": "Price",
        "Segment": "Segment",
        "Exchange": "Exchange"
    })
    df["TradeTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    df["Symbol"] = df["Symbol"].str.upper()
    df["Type"] = df["Type"].str.upper()
    df["Segment"] = df["Segment"].str.upper()
    df["Segment"] = df["Segment"].replace({"EQ": "EQUITY", "NSE_CASH": "EQUITY"})
    df["Broker"] = "Dhan"
    return df[["TradeTime", "Symbol", "Type", "Segment", "Quantity", "Price", "Exchange", "Broker"]]

def preprocess_grow(df):
    """Clean and standardize Dhan trade book."""
    df = df.rename(columns={
        "Date": "Date",
        "Time": "Time",
        "Stock_Name": "Symbol",
        "B/S": "Type",
        "Lot": "Quantity",
        "Trade Price": "Price",
        "Segment": "Segment",
        "Exchange": "Exchange"
    })
    df["TradeTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    df["Symbol"] = df["Symbol"].str.upper()
    df["Type"] = df["Type"].str.upper()
    df["Segment"] = df["Segment"].str.upper()
    df["Segment"] = df["Segment"].replace({"EQ": "EQUITY", "NSE_CASH": "EQUITY"})
    df["Broker"] = "Grow"
    return df[["TradeTime", "Symbol", "Type", "Segment", "Quantity", "Price", "Exchange", "Broker"]]

def process_broker_trades(base_folder):
    """Main function to process all brokers."""
    brokers = {
        "zerodha": preprocess_zerodha,
        "fyers": preprocess_fyers,
        "dhan": preprocess_dhan,
        "grow": preprocess_grow
    }

    final_data = []

    for broker, preprocess_func in brokers.items():
        folder_path = os.path.join(base_folder, broker)
        if os.path.exists(folder_path):
            raw_df = read_all_csvs_in_folder(folder_path)
            if not raw_df.empty:
                clean_df = preprocess_func(raw_df)
                final_data.append(clean_df)

    return pd.concat(final_data, ignore_index=True) if final_data else pd.DataFrame()

