import streamlit as st
import pandas as pd
import quantstats as qs
import pytz
import numpy as np
import time
import os
from IPython import get_ipython

# Replace with your published CSV link
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuyGRVZuafIk2s7moScIn5PAUcPYEyYIOOYJj54RXYUeugWmOP0iIToljSEMhHrg_Zp8Vab6YvBJDV/pub?output=csv"

# Load the data into a Pandas DataFrame
@st.cache_data
def load_data(csv_url):
    try:
        data = pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
    return data

# Data cleaning and preprocessing
def preprocess_data(data):
    # Delete rows with Portfolio Value, Absolute Gain, Nifty50, Day Change
    rows_to_delete = data[data['Date'].isin(['Portfolio Value', 'Absolute Gain', 'Nifty50', 'Day Change'])].index
    data.drop(rows_to_delete, inplace=True)

    # Delete the rows which does not have NAV value
    data = data.dropna(subset=['NAV'])

    # Convert the 'Date' column to datetime objects and set it as the index
    data['Date'] = pd.to_datetime(data['Date'], format='%d-%b-%y')
    # Sort the data by Date in ascending order
    data = data.sort_values(by='Date')
    # Make the index tz aware
    data['Date'] = data['Date'].apply(lambda x: x.replace(tzinfo=None))
    data.set_index('Date', inplace=True)

    # Convert the 'NAV' column to numeric values
    data['NAV'] = pd.to_numeric(data['NAV'])

    # Remove % in Nifty50 Change % Column
    data['Nifty50 Change %'] = data['Nifty50 Change %'].str.rstrip('%').astype('float')/100

    # Make a column of Nifty50 NAV
    data['Nifty50 NAV'] = data['Nifty50 Value'].cumprod()

    return data

# Calculate the daily returns
def calculate_returns(data):
    returns = data['NAV'].pct_change().dropna()
    nifty50 = data['Nifty50 Change %'].dropna()
    return returns, nifty50

# Verify if there are overlap in date range
def filter_data_by_date(returns, nifty50):
    start_date = max(returns.index[0], nifty50.index[0])
    end_date = min(returns.index[-1], nifty50.index[-1])

    # Convert start_date and end_date to Timestamp objects
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Filter the data to the overlapping date range
    returns = returns[start_date:end_date]
    nifty50 = nifty50[start_date:end_date]
    return returns, nifty50

# Display DataFrame
def display_dataframe(df, title):
    st.subheader(title)
    st.dataframe(df)

def main():
    st.title("Portfolio Performance Dashboard")
    data = load_data(csv_url)

    if data is not None:
        st.write("Raw Data")
        st.dataframe(data)
        data = preprocess_data(data)
        returns, nifty50 = calculate_returns(data)
        returns, nifty50 = filter_data_by_date(returns, nifty50)

        # Replace NaN and infinite values with 0
        returns = returns.replace([float('inf'), float('-inf')], 0).fillna(0)
        nifty50 = nifty50.replace([float('inf'), float('-inf')], 0).fillna(0)

        # Display Data
        display_dataframe(data, "Clean Data")
        display_dataframe(returns.to_frame(), "Returns")
        display_dataframe(nifty50.to_frame(), "Nifty50")
        
        st.subheader("Performance Report")

        if st.button('Generate Full Report'):
            report_html = qs.reports.html(returns, nifty50, title="Portfolio Performance vs Nifty50", output="portfolio_report.html")
            st.success(f"Portfolio Performance Report Generated.")
            with open("portfolio_report.html", "r") as f:
                report_content = f.read()
            st.components.v1.html(report_content, height=1000, scrolling=True)
            st.write("To see the saved report, check the left side panel of the file viewer and download the `portfolio_report.html` file to your computer.")
        
if __name__ == "__main__":
    main()