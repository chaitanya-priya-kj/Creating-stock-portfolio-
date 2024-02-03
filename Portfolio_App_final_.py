# To run streamlit run Portfolio_App_.py
# Import necessary libraries
import streamlit as st
import sqlite3
import yfinance as yf
from datetime import datetime

# Database connection
conn = sqlite3.connect('chai.db')
c = conn.cursor()


#current_date = ''

# Create tables if not exists
c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                portfolio_name TEXT NOT NULL,
                creation_date DATE NOT NULL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS portfolio_stock (
                portfolio_id INTEGER,
                stock_id INTEGER,
                FOREIGN KEY (portfolio_id) REFERENCES portfolio(id),
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            )''')
# INSERT INTO price (stock_id, date, open, high, low, close, volume, dividends, Stock_Splits)

c.execute('''CREATE TABLE IF NOT EXISTS price (
                id INTEGER PRIMARY KEY,
                stock_id INTEGER,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                adj_close REAL, 
                FOREIGN KEY (stock_id) REFERENCES stocks(id)
            )''')

# Streamlit UI
def main():
    st.title('Stock Portfolio Management')

    menu = ['Create Portfolio', 'Add Stock', 'Remove Stock', 'Remove Portfolio', 'Display Portfolios']
    choice = st.sidebar.selectbox('Menu', menu)

    if choice == 'Create Portfolio':
        create_portfolio()
    elif choice == 'Add Stock':
        add_stock()
    elif choice == 'Remove Stock':
        remove_stock()
    elif choice == 'Remove Portfolio':
        remove_portfolio()
    elif choice == 'Display Portfolios':
        display_portfolios()

# Functions for each menu option
def create_portfolio():
    portfolio_name = st.text_input('Enter portfolio name:')
    if st.button('Create Portfolio'):
        c.execute("INSERT INTO portfolio (portfolio_name, creation_date) VALUES (?, DATE('now'))", (portfolio_name,))
        conn.commit()
        st.success(f'Portfolio "{portfolio_name}" created successfully.')

def add_stock():
    portfolio_id = st.selectbox('Select portfolio:', get_portfolio_names())
    stock_symbol = st.text_input('Enter stock symbol (e.g., AAPL):').upper()
    
    if st.button('Add Stock'):
        stock_id = get_or_create_stock_id(stock_symbol)
        if stock_id:
            if not is_stock_in_portfolio(portfolio_id[0], stock_id):
                c.execute("INSERT INTO portfolio_stock (portfolio_id, stock_id) VALUES (?, ?)", (portfolio_id[0], stock_id))
                conn.commit()
                fetch_and_populate_price(stock_id, stock_symbol)  # Fetch and populate price data
                st.success(f'Stock "{stock_symbol}" added to the portfolio.')
            else:
                st.warning(f'Stock "{stock_symbol}" is already in the portfolio.')
        else:
            st.error('Failed to add stock. Please try again.')

def remove_stock():
    portfolio = st.selectbox('Select portfolio:', get_portfolio_names())
    stocks = get_portfolio_stocks(portfolio[0])
    stock_to_remove = st.selectbox('Select stock to remove:', stocks)

    if st.button('Remove Stock'):
        stock_id = get_stock_id(stock_to_remove)
        if stock_id:
            c.execute("DELETE FROM portfolio_stock WHERE portfolio_id=? AND stock_id=?", (portfolio[0], stock_id))
            conn.commit()
            st.success(f'Stock "{stock_to_remove}" removed from the portfolio.')
        else:
            st.error('Failed to remove stock. Please try again.')

def remove_portfolio():
    portfolios = get_portfolio_names()
    portfolio_to_remove = st.selectbox('Select portfolio to remove:', portfolios)

    if st.button('Remove Portfolio'):
        portfolio_id = portfolio_to_remove[0]
        c.execute("DELETE FROM portfolio WHERE id=?", (portfolio_id,))
        conn.commit()
        st.success(f'Portfolio "{portfolio_to_remove[1]}" removed successfully.')

        # Remove portfolio's associated stocks
        c.execute("DELETE FROM portfolio_stock WHERE portfolio_id=?", (portfolio_id,))
        conn.commit()

def display_portfolios():
    portfolios = get_portfolio_names()
    x=1
    for portfolio_id, portfolio_name, creation_date in portfolios:
        st.write(f'* Portfolio Name: {portfolio_name}')
        x+=1
        stocks = get_portfolio_stocks(portfolio_id)
        stocks_str = ', '.join(stocks)
        st.write(f'$ Stocks: {stocks_str}')
        i=1
        for stock in stocks:
            st.write(i,stock)
            #info_stocks,column_names = get_info_stocks(stock,current_date)
            info_stocks,column_names = get_info_stocks(stock)
            data_with_header = [column_names] + info_stocks
            st.table(data_with_header)
            i+=1
        st.write("\n\n")
            # for info in info_stocks:
            #     st.table(info, header=column_names)

# def get_info_stocks(stock):
#     c.execute("SELECT price.* FROM price JOIN stocks ON price.stock_id = stocks.id WHERE stocks.symbol = ?", (stock,))
#     return c.fetchall()

def get_info_stocks(stock):
    c.execute("SELECT price.* FROM price JOIN stocks ON price.stock_id = stocks.id WHERE stocks.symbol = ? ORDER BY price.date DESC LIMIT 10", (stock,))
    # c.execute("SELECT price.* FROM price JOIN stocks ON price.stock_id = stocks.id WHERE stocks.symbol = ?", (stock,))
    #c.execute("SELECT price.* FROM price JOIN stocks ON price.stock_id = stocks.id WHERE stocks.symbol = ? AND price.date = ?", (stock, current_date))
    fetched_data = c.fetchall()
    column_names = [description[0] for description in c.description]
    return fetched_data, column_names

def get_portfolio_names():
    c.execute("SELECT id, portfolio_name, creation_date FROM portfolio")
    return c.fetchall()

def get_portfolio_stocks(portfolio_id):
    c.execute("SELECT s.symbol FROM stocks AS s INNER JOIN portfolio_stock AS ps ON s.id = ps.stock_id WHERE ps.portfolio_id=?", (portfolio_id,))
    return [stock[0] for stock in c.fetchall()]

def get_or_create_stock_id(symbol):
    c.execute("SELECT id FROM stocks WHERE symbol=?", (symbol,))
    stock = c.fetchone()
    if stock:
        return stock[0]
    else:
        try:
            stock_data = yf.Ticker(symbol)
            if stock_data:
                c.execute("INSERT INTO stocks (symbol) VALUES (?)", (symbol,))
                conn.commit()
                c.execute("SELECT id FROM stocks WHERE symbol=?", (symbol,))
                new_stock = c.fetchone()
                if new_stock:
                    return new_stock[0]
        except Exception as e:
            st.error(f"Failed to add stock: {e}")
            return None

def is_stock_in_portfolio(portfolio_id, stock_id):
    c.execute("SELECT COUNT(*) FROM portfolio_stock WHERE portfolio_id=? AND stock_id=?", (portfolio_id, stock_id))
    count = c.fetchone()[0]
    return count > 0

def fetch_and_populate_price(stock_id, symbol):
    # Fetch historical price data from Yahoo Finance
    try:

        stock_data = yf.download(symbol, period = '1y')
        for index, row in stock_data.iterrows():
            c.execute("""INSERT INTO price (stock_id, date, open, high, low, close, volume, adj_close)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (stock_id, index.date(), row['Open'], row['High'], row['Low'], row['Close'], row['Volume'], row['Adj Close']))
        conn.commit()
        st.success("Price data populated successfully.")
    except Exception as e:
        st.error(f"Failed to fetch price data: {e}")

def get_stock_id(symbol):
    c.execute("SELECT id FROM stocks WHERE symbol=?", (symbol,))
    stock = c.fetchone()
    if stock:
        return stock[0]
    else:
        return None

if __name__ == '__main__':
    main()
