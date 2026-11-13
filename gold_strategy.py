import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# gold futures, 2020 to now
ticker = "GC=F"

data = yf.download(
    ticker,
    start="2020-01-01",
    auto_adjust=True,
    progress=False
)

# yfinance gives multi-level columns, flattening
data.columns = data.columns.get_level_values(0)

print(data.head())

# moving average crossover - classic trend following setup
data['SMA_short'] = data['Close'].rolling(window=20).mean()
data['SMA_long'] = data['Close'].rolling(window=50).mean()

# tried without a trend filter first, strategy underperformed a lot
# adding a longer MA as a filter - only trade when price is above it
data['SMA_trend'] = data['Close'].rolling(
    window=100).mean()  # 200 was too slow, missed trends
data['trend_ok'] = np.where(data['Close'] > data['SMA_trend'], 1, 0)

data['signal'] = np.where(
    (data['SMA_short'] > data['SMA_long']) & (data['trend_ok'] == 1), 1, 0)

# shift by 1 so we're only using info we'd actually have (no lookahead bias)
data['position'] = data['signal'].shift(1)

data['market_return'] = data['Close'].pct_change()
data['strategy_return'] = data['market_return'] * data['position']

data['cum_market'] = (1 + data['market_return']).cumprod()
data['cum_strategy'] = (1 + data['strategy_return']).cumprod()

print(data[['cum_market', 'cum_strategy']].tail())

# sharpe ratio, annualized (252 trading days)
sharpe_strategy = (data['strategy_return'].mean() /
                   data['strategy_return'].std()) * np.sqrt(252)
sharpe_market = (data['market_return'].mean() /
                 data['market_return'].std()) * np.sqrt(252)

# max drawdown - worst drop from a peak
running_max = data['cum_strategy'].cummax()
drawdown = (data['cum_strategy'] - running_max) / running_max
max_dd = drawdown.min()

print(f"Strategy Sharpe: {sharpe_strategy:.2f}")
print(f"Buy & Hold Sharpe: {sharpe_market:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")

plt.figure(figsize=(12, 6))
plt.plot(data['cum_market'], label='Buy & Hold')
plt.plot(data['cum_strategy'], label='MA Crossover + Trend Filter')
plt.title(f'{ticker}: Strategy vs Buy & Hold')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.legend()
plt.savefig('strategy_vs_benchmark.png')
plt.show()
