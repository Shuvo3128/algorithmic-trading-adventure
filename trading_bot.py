import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


class TradingBot:
    def __init__(self, symbol, start_date, end_date, budget=5000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget

        self.data = None
        self.position = False
        self.buy_price = 0.0
        self.shares = 0
        self.total_profit = 0.0

        # Trade history for graph
        self.buy_points = []
        self.sell_points = []

    def fetch_data(self):
        print(f"Downloading data for {self.symbol}...")
        df = yf.download(self.symbol, start=self.start_date, end=self.end_date)

        # FIX: flatten MultiIndex columns (important for yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        self.data = df

    def clean_data(self):
        self.data = self.data[~self.data.index.duplicated()]
        self.data = self.data.ffill()

    def add_moving_averages(self):
        self.data["MA50"] = self.data["Close"].rolling(50).mean()
        self.data["MA200"] = self.data["Close"].rolling(200).mean()

    def buy(self, price, date):
        self.shares = int(self.budget // price)
        if self.shares == 0:
            return

        self.buy_price = float(price)
        self.position = True
        self.buy_points.append((date, price))

        print(f"BUY  | {date.date()} | Price: {price:.2f} | Shares: {self.shares}")

    def sell(self, price, date):
        price = float(price)
        trade_profit = (price - self.buy_price) * self.shares
        self.total_profit += trade_profit
        self.position = False

        self.sell_points.append((date, price))

        print(
            f"SELL | {date.date()} | Price: {price:.2f} "
            f"| Trade P/L: {trade_profit:.2f}"
        )

        self.shares = 0
        self.buy_price = 0.0

    def trade(self):
        for i in range(1, len(self.data)):
            prev = self.data.iloc[i - 1]
            curr = self.data.iloc[i]
            date = self.data.index[i]

            ma50_prev = float(prev["MA50"])
            ma200_prev = float(prev["MA200"])
            ma50_curr = float(curr["MA50"])
            ma200_curr = float(curr["MA200"])
            close_price = float(curr["Close"])

            # Skip rows where MA is NaN
            if pd.isna(ma50_prev) or pd.isna(ma200_prev):
                continue

            # Golden Cross → BUY
            if (
                not self.position
                and ma50_prev < ma200_prev
                and ma50_curr > ma200_curr
            ):
                self.buy(close_price, date)

            # Death Cross → SELL
            elif (
                self.position
                and ma50_prev > ma200_prev
                and ma50_curr < ma200_curr
            ):
                self.sell(close_price, date)

        # Force sell on last day
        if self.position:
            last_price = float(self.data.iloc[-1]["Close"])
            last_date = self.data.index[-1]
            self.sell(last_price, last_date)

    def plot_results(self):
        plt.figure(figsize=(14, 7))

        plt.plot(self.data.index, self.data["Close"], label="Close Price", alpha=0.8)
        plt.plot(self.data.index, self.data["MA50"], label="MA 50", linestyle="--")
        plt.plot(self.data.index, self.data["MA200"], label="MA 200", linestyle="--")

        if self.buy_points:
            buy_dates, buy_prices = zip(*self.buy_points)
            plt.scatter(buy_dates, buy_prices, marker="^", s=120, label="BUY", zorder=5)

        if self.sell_points:
            sell_dates, sell_prices = zip(*self.sell_points)
            plt.scatter(sell_dates, sell_prices, marker="v", s=120, label="SELL", zorder=5)

        plt.title(
            f"{self.symbol} Golden Cross Strategy\nFinal Profit/Loss: {self.total_profit:.2f}"
        )
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def run(self):
        self.fetch_data()
        self.clean_data()
        self.add_moving_averages()
        self.trade()

        print("\n==============================")
        if self.total_profit >= 0:
            print(f"FINAL RESULT: PROFIT 💰")
        else:
            print(f"FINAL RESULT: LOSS 📉")
        print(f"Final Profit / Loss: {self.total_profit:.2f}")
        print("==============================\n")

        self.plot_results()


if __name__ == "__main__":
    bot = TradingBot("AAPL", "2018-01-01", "2023-12-31")
    bot.run()
