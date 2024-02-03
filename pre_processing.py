import pandas as pd

data = pd.read_csv("price_data.csv")
print(data.head())
# Handle Missing Values:

#ffill will propagate last valid observation forward.
data.fillna(method='ffill', inplace = True)


# Converting timestamp
if data['date'].dtype == 'datetime64[ns]':
    print("\nThe 'date' attribute is already in datetime format.")
else:
    print("The 'date' attribute is not in datetime format.")
    data['date'] = pd.to_datetime(data['date'])
    print("Conversion complete ")


# Identifying stochastic oscillator and daily returns as relavant metrics that will be usefull in predicting the stock prices in future assignmnets
    
def calculate_stochastic_oscillator(data, period=14, smooth=3):
    #Computeing rolling minimum and maximum of closing prices
    data['min_low'] = data['low'].rolling(window=period).min()
    data['max_high'] = data['high'].rolling(window=period).max()
    
    #Computing %K line and %D line
    data['%K'] = (data['close'] - data['min_low']) / (data['max_high'] - data['min_low']) * 100
    data['%D'] = data['%K'].rolling(window=smooth).mean()
    
    return data[['date', 'stock_id', '%K', '%D']].dropna()

def calculate_daily_returns(data):
    data['daily_return'] = data['adj_close'].pct_change()
    return data[['date', 'stock_id', 'daily_return']].dropna()

daily_returns_data = calculate_daily_returns(data)
print("\nDataframe with daily returns")
print(daily_returns_data.head())
stochastic_data = calculate_stochastic_oscillator(data)
print("\nDataframe with calculated stochastic oscillator which is a metric used for stock price preditiction")
print(stochastic_data.head())



