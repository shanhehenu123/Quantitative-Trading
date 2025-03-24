import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import io
import csv

indices = {"^DJI": "Dow Jones Industrial Average", "^NDX": "Nasdaq 100"}
start_date = "2021-12-01"
end_date = "2024-12-01"

for index_symbol, index_name in indices.items():
    print(f"\nAnalyzing {index_name} ({index_symbol}):")

    # Excart Stock Code From Wiki
    try:
        if index_symbol == "^DJI":
            url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
            ticker_column_options = ['Symbol']
            table_index_options = [0]
        elif index_symbol == "^NDX":
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            ticker_column_options = ['Symbol']
            table_index_options = [3]
        else:
            print(f"Unsupported index: {index_symbol}")
            continue

        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for table_index in table_index_options:
            tables = soup.find_all('table', class_='wikitable')
            if len(tables) <= table_index:
                continue
            try:
                df = pd.read_html(io.StringIO(str(tables[table_index])))[0]
            except ValueError as e:
                print(f"Error parsing table {table_index}: {e}")
                continue
            for ticker_column in ticker_column_options:
                 if ticker_column in df.columns:
                    tickers = df[ticker_column].str.replace(".", "", regex=False).tolist()
                    print(f"Extracted tickers for {index_name}: {tickers}") # 打印股票代码
                    break
            else:
                 continue
            break
        else:
             print(f"Could not find ticker data in any expected format for {index_symbol} on {url}")
             continue

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        continue
    except Exception as e:
        print(f"General error during ticker retrieval: {e}")
        continue



# Get History Data
    try:
        index_data = yf.download(index_symbol, start=start_date, end=end_date)['Close']
        if index_data.empty:
            print(f"Could not retrieve data for {index_symbol}")
            continue

        correlations = {}
        for ticker in tickers:
            try:
                stock_data = yf.download(ticker, start=start_date, end=end_date)['Close']
                if stock_data.empty:
                    print(f"No data found for {ticker}")
                    continue

                combined = pd.concat([index_data, stock_data], axis=1, join='inner')
                combined.columns = ['Index', 'Stock']

                stock_returns = combined['Stock'].pct_change().dropna()
                index_returns = combined['Index'].pct_change().dropna()
                correlation = np.corrcoef(stock_returns, index_returns)[0, 1]
                correlations[ticker] = correlation
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
    except Exception as e:
        print(f"Error downloading data: {e}")
        continue

    # Calculate correlations and Filter to get > 0.7
    high_correlation_stocks = {k: v for k, v in correlations.items() if v > 0.7}
    print(f"Stocks with correlation > 0.7 to {index_name}:")
    filename = f"{index_name}_high_correlation.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Ticker", "Correlation"])
        if high_correlation_stocks:
            for ticker, correlation in high_correlation_stocks.items():
                print(f"- {ticker}: {correlation:.2f}")
                writer.writerow([ticker, correlation])
        else:
            print("No stocks found with correlation > 0.7.")