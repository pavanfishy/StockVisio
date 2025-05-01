from preprocess import process_broker_trades

import pandas as pd

import pandas as pd

# Step 1: Manual buyback/off-market sales you want to reflect
# Format: Symbol, Type, Segment, Quantity, Price, Exchange, Broker, TradeTime
buyback_trades = pd.DataFrame([
    {
        "Symbol": "BAJAJ-AUTO",
        "Type": "SELL",
        "Segment": "EQUITY",
        "Quantity": 1,
        "Price": 10000.00,
        "Exchange": "BUYBACK",
        "Broker": "Zerodha",
        "TradeTime": pd.to_datetime("2024-03-20 10:00:00")
    },
    {
        "Symbol": "TCS",
        "Type": "SELL",
        "Segment": "EQUITY",
        "Quantity": 1,
        "Price": 4150.00,
        "Exchange": "BUYBACK",
        "Broker": "Fyers",
        "TradeTime": pd.to_datetime("2023-12-12 10:00:00")
    }
])


import pandas as pd

def compute_live_portfolio(df):
    df = df.sort_values("TradeTime").reset_index(drop=True)
    df["Type"] = df["Type"].str.upper()
    df["Segment"] = df["Segment"].str.upper()
    df["Exchange"] = df["Exchange"].str.upper()

    buybacks = df[df["Exchange"] == "BUYBACK"]
    normal_trades = df[df["Exchange"] != "BUYBACK"]

    adjusted_trades = []

    for symbol in buybacks["Symbol"].unique():
        for broker in buybacks[buybacks["Symbol"] == symbol]["Broker"].unique():
            bb_subset = buybacks[(buybacks["Symbol"] == symbol) & (buybacks["Broker"] == broker)]

                # To track which trade indexes were fully consumed by buyback
            fully_consumed_trade_ids = set()

            for _, bb_row in bb_subset.iterrows():
                qty_to_reduce = bb_row["Quantity"]
                bb_time = bb_row["TradeTime"]

                # Find buys before this buyback
                buys = normal_trades[
                    (normal_trades["Symbol"] == symbol) &
                    (normal_trades["Broker"] == broker) &
                    (normal_trades["Type"] == "BUY") &
                    (normal_trades["TradeTime"] < bb_time)
                ].copy()

                for i, row in buys.iterrows():
                    if qty_to_reduce <= 0:
                        break
                    reduce_qty = min(qty_to_reduce, row["Quantity"])

                    if row["Quantity"] > reduce_qty:
                        row_copy = row.copy()
                        row_copy["Quantity"] -= reduce_qty
                        adjusted_trades.append(row_copy)
                    else:
                        fully_consumed_trade_ids.add(i)

                    qty_to_reduce -= reduce_qty

            # Add all remaining trades that weren't fully consumed
            remaining_trades = normal_trades[
                (normal_trades["Symbol"] == symbol) &
                (normal_trades["Broker"] == broker)
            ]
            filtered_remaining = remaining_trades[~remaining_trades.index.isin(fully_consumed_trade_ids)]
            adjusted_trades.extend(filtered_remaining.to_dict("records"))

    # Trades from symbols with no buybacks
    all_symbols_with_buyback = set(zip(buybacks["Symbol"], buybacks["Broker"]))
    remaining_trades = normal_trades[~normal_trades.set_index(["Symbol", "Broker"]).index.isin(all_symbols_with_buyback)]
    adjusted_trades.extend(remaining_trades.to_dict("records"))

    adjusted_df = pd.DataFrame(adjusted_trades)
    if adjusted_df.empty:
        return pd.DataFrame(columns=["Symbol", "Broker", "NetQty", "AvgBuyPrice", "InvestedValue"])

    df_grouped = adjusted_df.groupby(["Symbol", "Broker", "Type"]).agg({
        "Quantity": "sum",
        "Price": lambda x: (x * adjusted_df.loc[x.index, "Quantity"]).sum()
    }).rename(columns={"Price": "TotalAmount"}).reset_index()

    pivot = df_grouped.pivot(index=["Symbol", "Broker"], columns="Type", values=["Quantity", "TotalAmount"]).fillna(0)
    pivot.columns = ['_'.join(col).lower() for col in pivot.columns]
    pivot = pivot.rename(columns={
        "quantity_buy": "BuyQty",
        "quantity_sell": "SellQty",
        "totalamount_buy": "BuyValue"
    })

    pivot["NetQty"] = pivot["BuyQty"] - pivot["SellQty"]
    pivot["AvgBuyPrice"] = pivot["BuyValue"] / pivot["BuyQty"]
    pivot["InvestedValue"] = pivot["NetQty"] * pivot["AvgBuyPrice"]
    live_holdings = pivot[pivot["NetQty"] > 0].reset_index()
    live_holdings = live_holdings[["Symbol", "Broker", "NetQty", "AvgBuyPrice", "InvestedValue"]]
    live_holdings = live_holdings.sort_values("InvestedValue", ascending=False).reset_index(drop=True)

    return live_holdings



# Example usage
if __name__ == "__main__":
    base_folder_path = r"C:\Users\lpava\OneDrive\Documents\Stock_Visio_2\trades"  # Replace with your actual folder path
    combined_df = process_broker_trades(base_folder_path)

    print(combined_df[['Broker', 'Exchange']].drop_duplicates())

    print(combined_df[combined_df['Exchange'] == 'BSE'])

    combined_df["Symbol"] = combined_df["Symbol"].replace("GOLDIETF-E", "GOLDIETF")

    combined_bb_df = pd.concat([combined_df, buyback_trades], ignore_index=True)

    print(combined_bb_df[combined_bb_df['Symbol'] == 'BAJAJ-AUTO'])

    combined_bb_df = combined_bb_df[combined_bb_df['Segment'] == 'EQUITY']
    live_portfolio = compute_live_portfolio(combined_bb_df)
    print(live_portfolio[live_portfolio['Symbol'] == 'GOLDIETF'])
    print(live_portfolio.head())

    # # Step 1: Filter Zerodha trades
    # zerodha_df = live_portfolio[live_portfolio['Broker'] == 'Fyers']

    # # Step 2: Sort by Symbol in ascending order (case-insensitive)
    # zerodha_sorted = zerodha_df.sort_values(by="Symbol", key=lambda x: x.str.lower()).reset_index(drop=True)

    # # Step 3: Print required columns
    # print(zerodha_sorted[["Symbol", "Broker", "NetQty", "InvestedValue"]])

    # summary = live_portfolio.groupby("Broker").agg(
    #     NumberOfStocks=("Symbol", "count"),
    #     TotalInvestedValue=("InvestedValue", "sum")
    # ).reset_index()

    # print(summary)

    