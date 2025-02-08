import streamlit as st
import pandas as pd
import quantstats as qs
import numpy as np

# Replace with your published CSV link
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuyGRVZuafIk2s7moScIn5PAUcPYEyYIOOYJj54RXYUeugWmOP0iIToljSEMhHrg_Zp8Vab6YvBJDV/pub?output=csv"

# Clear cache before fetching data to ensure fresh data on each run
st.cache_data.clear()

# Load the data into a Pandas DataFrame
@st.cache_data(ttl=0)  # Caching har baar bypass hoga
def load_data(csv_url):
    try:
        data = pd.read_csv(csv_url)
        return data
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Data cleaning and preprocessing
def preprocess_data(data):
    # Remove unwanted rows
    rows_to_delete = data[data['Date'].isin(['Portfolio Value', 'Absolute Gain', 'Nifty50', 'Day Change'])].index
    data.drop(rows_to_delete, inplace=True)

    # Remove rows without NAV
    data = data.dropna(subset=['NAV'])

    # Convert Date to datetime and remove timezone
    data['Date'] = pd.to_datetime(data['Date'], format='%d-%b-%y')
    data = data.sort_values(by='Date')
    data['Date'] = data['Date'].apply(lambda x: x.replace(tzinfo=None))  # Remove tz awareness
    data.set_index('Date', inplace=True)

    # Convert columns to numeric
    data['NAV'] = pd.to_numeric(data['NAV'])
    data['Nifty50 Change %'] = data['Nifty50 Change %'].str.rstrip('%').astype('float') / 100

    # Calculate Nifty50 NAV as a benchmark
    data['Nifty50 NAV'] = (1 + data['Nifty50 Change %']).cumprod()

    return data

# Calculate the daily returns
def calculate_returns(data):
    returns = data['NAV'].pct_change().dropna()
    nifty50 = data['Nifty50 Change %'].dropna()
    return returns, nifty50

# Filter data to ensure overlapping date ranges
def filter_data_by_date(returns, nifty50):
    start_date = max(returns.index[0], nifty50.index[0])
    end_date = min(returns.index[-1], nifty50.index[-1])

    returns = returns[start_date:end_date]
    nifty50 = nifty50[start_date:end_date]
    return returns, nifty50

# Main function for Streamlit app
def main():
    # Set page configuration to wide layout
    st.set_page_config(page_title="Portfolio Report", layout="wide")

    # Inject custom CSS for full-width iframe
    custom_css = """
    <style>
        .main iframe {
            width: 100% !important;
            height: calc(100vh - 2rem) !important;
            border: none !important;
        }
        .main > div {
            padding: 0 !important;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Load and preprocess data
    data = load_data(csv_url)
    if data is not None:
        processed_data = preprocess_data(data)
        returns, nifty50 = calculate_returns(processed_data)

        # Filter for overlapping dates
        returns, nifty50 = filter_data_by_date(returns, nifty50)

        # Handle NaN and Inf values
        returns = returns.replace([np.inf, -np.inf], 0).fillna(0)
        nifty50 = nifty50.replace([np.inf, -np.inf], 0).fillna(0)

        # Generate QuantStats report
        try:
            qs.reports.html(returns, nifty50, output="report.html")
            with open("report.html", "r") as f:
                report_html = f.read()

            # Embed the QuantStats report in full width
            st.components.v1.html(report_html, scrolling=True)
        except Exception as e:
            st.error(f"Error displaying QuantStats report: {e}")

if __name__ == "__main__":
    main()
