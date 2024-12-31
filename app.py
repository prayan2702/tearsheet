import streamlit as st
import pandas as pd
import quantstats as qs
import pytz
import numpy as np
import time
import os
from IPython import get_ipython
import matplotlib.pyplot as plt

# Replace with your published CSV link
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuyGRVZuafIk2s7moScIn5PAUcPYEyYIOOYJj54RXYUeugWmOP0iIToljSEMhHrg_Zp8Vab6YvBJDV/pub?output=csv"

# Load the data into a Pandas DataFrame
@st.cache_data
def load_data(csv_url):
    print("Loading data...")  # Print when the function is called
    try:
        data = pd.read_csv(csv_url)
        print("Data loaded successfully.") # Print when data is loaded
    except Exception as e:
        st.error(f"An error occurred: {e}")
        print(f"Error during data loading: {e}") # Print if an error occurs
        return None
    return data

# Data cleaning and preprocessing
def preprocess_data(data):
    print("Preprocessing data...")
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
    data['Nifty50 NAV'] = (1 + data['Nifty50 Change %']).cumprod()
    print("Data preprocessed successfully.")
    return data

# Calculate the daily returns
def calculate_returns(data):
    print("Calculating returns...")
    returns = data['NAV'].pct_change().dropna()
    nifty50 = data['Nifty50 Change %'].dropna()
    print("Returns calculated successfully.")
    return returns, nifty50

# Verify if there are overlap in date range
def filter_data_by_date(returns, nifty50):
    print("Filtering data by date...")
    start_date = max(returns.index.min(), nifty50.index.min())
    end_date = min(returns.index.max(), nifty50.index.max())

    returns = returns[start_date:end_date]
    nifty50 = nifty50[start_date:end_date]
    print("Data filtered by date.")
    return returns, nifty50, start_date, end_date
# Main function for Streamlit app
def main():
    st.title("Portfolio Performance Analysis")
    print("App title set.")

    # Load data
    data = load_data(csv_url)

    if data is not None:
        print("Data not null, proceeding...")
        # Preprocess data
        processed_data = preprocess_data(data.copy())

        # Calculate returns
        returns, nifty50 = calculate_returns(processed_data)

        # Verify if there are overlap in date range and filter it
        returns, nifty50, start_date, end_date = filter_data_by_date(returns, nifty50)

        # Display QuantStats report
        st.subheader("QuantStats Report")
        try:
            # CSS to adjust the width of the iframe and remove padding
            adjust_width_css = """
                <style>
                    section.main > div:has(~ footer ) {
                        padding-bottom: 0px;
                    }
                    iframe {
                        width: 100% !important;
                        border: none !important;
                    }
                </style>
            """
            st.markdown(adjust_width_css, unsafe_allow_html=True)
            fig = qs.reports.html(returns, nifty50, output="report.html")
            with open("report.html", "r") as f:
                report_html = f.read()
            st.components.v1.html(report_html, height=1600, scrolling=True)
        except Exception as e:
            st.error(f"Error displaying QuantStats report: {e}")

        st.write("This is the end") #Add a text to check if it is displayed.

if __name__ == "__main__":
    main()
