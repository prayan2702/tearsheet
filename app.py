import streamlit as st
import pandas as pd
import quantstats as qs
import numpy as np

# Replace with your published CSV link
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuyGRVZuafIk2s7moScIn5PAUcPYEyYIOOYJj54RXYUeugWmOP0iIToljSEMhHrg_Zp8Vab6YvBJDV/pub?output=csv"

# Load the data into a Pandas DataFrame
@st.cache_data
def load_data(csv_url):
    try:
        data = pd.read_csv(csv_url)
        return data
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Data cleaning and preprocessing
def preprocess_data(data):
    rows_to_delete = data[data['Date'].isin(['Portfolio Value', 'Absolute Gain', 'Nifty50', 'Day Change'])].index
    data.drop(rows_to_delete, inplace=True)
    data = data.dropna(subset=['NAV'])

    data['Date'] = pd.to_datetime(data['Date'], format='%d-%b-%y')
    data = data.sort_values(by='Date')
    data['Date'] = data['Date'].apply(lambda x: x.replace(tzinfo=None))  # Remove timezone
    data.set_index('Date', inplace=True)

    data['NAV'] = pd.to_numeric(data['NAV'])
    data['Nifty50 Change %'] = data['Nifty50 Change %'].str.rstrip('%').astype('float') / 100

    # Calculate cumulative Nifty50 NAV (benchmark)
    data['Nifty50 NAV'] = (1 + data['Nifty50 Change %']).cumprod()

    return data

# Calculate the daily returns
def calculate_returns(data):
    returns = data['NAV'].pct_change().dropna()
    nifty50 = data['Nifty50 Change %'].dropna()
    return returns, nifty50

# Filter returns to overlapping date ranges
def filter_data_by_date(returns, nifty50):
    start_date = max(returns.index[0], nifty50.index[0])
    end_date = min(returns.index[-1], nifty50.index[-1])

    returns = returns[start_date:end_date]
    nifty50 = nifty50[start_date:end_date]
    return returns, nifty50

def main():
    st.set_page_config(page_title="Portfolio Report", layout="wide")
    st.title("Portfolio Performance Dashboard")

    data = load_data(csv_url)

    if data is not None:
        st.write("Raw Data")
        st.dataframe(data)

        # Preprocess and clean data
        data = preprocess_data(data)
        returns, nifty50 = calculate_returns(data)
        returns, nifty50 = filter_data_by_date(returns, nifty50)

        # Handle NaN and infinite values
        returns = returns.replace([np.inf, -np.inf], 0).fillna(0)
        nifty50 = nifty50.replace([np.inf, -np.inf], 0).fillna(0)

        st.write("Processed Data")
        st.dataframe(data)
        
        st.write("Returns")
        st.dataframe(returns)

        st.write("Nifty50 (Benchmark) Returns")
        st.dataframe(nifty50)

        # Generate QuantStats report
        if st.button("Generate Full Report"):
            try:
                report_html = qs.reports.html(returns, nifty50, title="Portfolio Performance vs Nifty50", output=None)
                st.components.v1.html(report_html, height=1000, scrolling=True)
            except Exception as e:
                st.error(f"Error generating report: {e}")

if __name__ == "__main__":
    main()
