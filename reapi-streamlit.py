import streamlit as st
import pandas as pd
import requests
import json
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode, GridUpdateMode
import plotly.express as px
import pydeck as pdk
import re
# --- Constants ---
API_KEY_STORAGE_KEY = "real_estate_api_key"
USER_ID_STORAGE_KEY = "real_estate_user_id"
DEFAULT_USER_ID = "UniqueUserIdentifier"
PAGE_SIZE = 50  # Number of results per page

# --- Helper Functions ---
if 'results' not in st.session_state:
    st.session_state.results = None
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'search_filter' not in st.session_state:
    st.session_state.search_filter = {}
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = DEFAULT_USER_ID
if 'zip_codes_input' not in st.session_state:
    st.session_state.zip_codes_input = ''


def get_page_of_properties(filter_params, result_index=0, page_size=PAGE_SIZE):
@@ -66,8 +52,7 @@ def flatten_property_data(properties):
        for key, value in prop.items():
            if isinstance(value, dict):
                flattened_prop.update(
                    {f"{key}_{sub_key}": sub_value for sub_key,
                        sub_value in value.items()}
                    {f"{key}_{sub_key}": sub_value for sub_key, sub_value in value.items()}
                )
            else:
                flattened_prop[key] = value
@@ -82,50 +67,87 @@ def is_valid_zip_code(zip_code):

# --- Streamlit UI ---


def main():
    # --- Sidebar --- #
    st.sidebar.header("Search Parameters")

    # API Configuration
    # Initialize zip_codes_input in session state if it doesn't exist
    if 'zip_codes_input' not in st.session_state:
        st.session_state['zip_codes_input'] = '' 

    # Zip Code Input with Multiple Values and Validation
    zip_codes_input = st.sidebar.text_input(
        "ZIP Codes (comma-separated)", key="zip_code_input", value=st.session_state['zip_codes_input']
    )
    if st.sidebar.button("Add ZIP Code", key="add_zip_button"):
        zip_codes_input += ", "  # Add a comma and space for the next input

    # Update session state when input changes
    st.session_state['zip_codes_input'] = zip_codes_input


    # Initialize session state
    if API_KEY_STORAGE_KEY not in st.session_state:
        st.session_state[API_KEY_STORAGE_KEY] = ""
    if USER_ID_STORAGE_KEY not in st.session_state:
        st.session_state[USER_ID_STORAGE_KEY] = DEFAULT_USER_ID
    if "search_filter" not in st.session_state:
        st.session_state.search_filter = {}
    if "results" not in st.session_state:
        st.session_state.results = []
    if "total_pages" not in st.session_state:
        st.session_state.total_pages = 1
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # --- Sidebar ---
    st.sidebar.header("API Configuration")
    api_key = st.sidebar.text_input(
        "Enter your API key",
        type="password",
        value=st.session_state.api_key,
        value=st.session_state[API_KEY_STORAGE_KEY],
    )
    user_id = st.sidebar.text_input(
        "Enter your User ID", value=st.session_state.user_id
        "Enter your User ID", value=st.session_state[USER_ID_STORAGE_KEY]
    )
    if st.sidebar.button("Save Credentials"):
        st.session_state.api_key = api_key
        st.session_state.user_id = user_id
        st.session_state[API_KEY_STORAGE_KEY] = api_key
        st.session_state[USER_ID_STORAGE_KEY] = user_id
        st.success("API Key and User ID saved!")

    # Basic Search and API Options
    st.session_state.api_key = st.session_state.get(
        API_KEY_STORAGE_KEY, ""
    )  # Access the saved API Key
    st.session_state.user_id = st.session_state.get(
        USER_ID_STORAGE_KEY, DEFAULT_USER_ID
    )

    # --- Search Parameters ---
    st.sidebar.header("Search Parameters")


    # Basic Search and API Options
    address = st.sidebar.text_input("Address")
    city = st.sidebar.text_input("City")
    state = st.sidebar.text_input("State")

    # Zip Code Input with Multiple Values
    zip_codes_input = st.sidebar.text_input("ZIP Codes (comma-separated)", value=st.session_state.zip_codes_input)
    if zip_codes_input:
        zip_code_list = [z.strip() for z in zip_codes_input.split(",") if is_valid_zip_code(z.strip())]
        if zip_code_list:
            st.session_state.search_filter["zips"] = zip_code_list

    property_type = st.sidebar.selectbox("Property Type", ["", "Single Family", "Multi Family", "Condo", "Townhouse"])  # Example of fixed input

    # Zip Code Input with Multiple Values and Validation
    zip_codes_input = st.sidebar.text_input("ZIP Codes (comma-separated)")
    if st.sidebar.button("Add ZIP Code"):
        zip_codes_input += ", "  # Add a comma and space for the next input

    property_type = st.sidebar.text_input("Property Type")
    count = st.sidebar.radio("Count Only", ("", "True", "False"))
    ids_only = st.sidebar.radio("IDs Only", ("", "True", "False"))
    obfuscate = st.sidebar.radio("Obfuscate", ("", "True", "False"))
    summary = st.sidebar.radio("Summary", ("", "True", "False"))
    size = st.sidebar.number_input("Size", min_value=1, value=50, step=1, format="%.0f")
    result_index = st.sidebar.number_input("Result Index", min_value=0, value=0, step=1, format="%.0f")
    size = st.sidebar.number_input("Size", min_value=1, value=50)
    result_index = st.sidebar.number_input("Result Index", min_value=0, value=0)

    # Advanced Filtering
    # --- Advanced Filtering ---
    st.sidebar.header("Advanced Filters")

    # Property Characteristics
    with st.sidebar.expander("Property Characteristics"):
        absentee_owner = st.radio("Absentee Owner", ("", "True", "False"))
        adjustable_rate = st.radio("Adjustable Rate", ("", "True", "False"))
@@ -158,7 +180,9 @@ def main():
        patio = st.radio("Patio", ("", "True", "False"))
        pool = st.radio("Pool", ("", "True", "False"))
        pre_foreclosure = st.radio("Pre-Foreclosure", ("", "True", "False"))
        prior_owner_individual = st.radio("Prior Owner Individual", ("", "True", "False"))
        prior_owner_individual = st.radio(
            "Prior Owner Individual", ("", "True", "False")
        )
        private_lender = st.radio("Private Lender", ("", "True", "False"))
        quit_claim = st.radio("Quit Claim", ("", "True", "False"))
        reo = st.radio("REO", ("", "True", "False"))
@@ -167,13 +191,22 @@ def main():
        trust_owned = st.radio("Trust Owned", ("", "True", "False"))
        vacant = st.radio("Vacant", ("", "True", "False"))

    # Additional Search Fields
    with st.sidebar.expander("Additional Search Fields"):
        house = st.sidebar.text_input("House Number")
        street = st.sidebar.text_input("Street Name")
        county = st.sidebar.text_input("County")
        latitude = st.sidebar.number_input("Latitude", format="%.5f")
        longitude = st.sidebar.number_input("Longitude", format="%.5f")
        radius = st.sidebar.slider("Radius (miles)", min_value=0.1, max_value=10.0, value=5.0, step=0.1, format="%.1f")
        latitude = st.sidebar.number_input("Latitude")
        longitude = st.sidebar.number_input("Longitude")

        # Radius Input with Slider (0.1-10 miles)
        radius = st.sidebar.number_input(
            "Radius (miles)", min_value=0.1, max_value=10.0, value=5.0, step=0.1
        )
        radius = st.sidebar.slider(
            "Radius (miles)", min_value=0.1, max_value=10.0, value=radius, step=0.1
        )

        property_use_code = st.sidebar.text_input("Property Use Code")
        census_block = st.sidebar.text_input("Census Block")
        census_block_group = st.sidebar.text_input("Census Block Group")
@@ -187,228 +220,509 @@ def main():
        notice_type = st.sidebar.text_input("Notice Type")
        parcel_account_number = st.sidebar.text_input("Parcel Account Number")
        search_range = st.sidebar.text_input("Search Range")
        sewage = st.sidebar.selectbox("Sewage", ["", "Municipal", "Yes", "Septic", "None", "Storm"])  # Example of fixed input
        sewage = st.sidebar.text_input("Sewage")
        water_source = st.sidebar.text_input("Water Source")
        estimated_equity = st.sidebar.number_input("Estimated Equity", step=0.5, format="%.1f")
        equity_operator = st.sidebar.selectbox("Equity Operator", ["", "lt", "lte", "gt", "gte"])
        equity_percent = st.sidebar.slider("Equity Percent", min_value=0, max_value=100, value=50, step=5, format="%.0f")
        equity_percent_operator = st.sidebar.selectbox("Equity Percent Operator", ["", "lt", "lte", "gt", "gte"])
        estimated_equity = st.sidebar.number_input("Estimated Equity")
        equity_operator = st.sidebar.selectbox(
            "Equity Operator", ["", "lt", "lte", "gt", "gte"]
        )

        # Equity Percent Input with Slider (0-100)
        equity_percent = st.sidebar.number_input(
            "Equity Percent", min_value=0, max_value=100, value=50
        )
        equity_percent = st.sidebar.slider(
            "Equity Percent", min_value=0, max_value=100, value=equity_percent
        )

        equity_percent_operator = st.sidebar.selectbox(
            "Equity Percent Operator", ["", "lt", "lte", "gt", "gte"]
        )
        last_sale_date = st.sidebar.date_input("Last Sale Date")
        last_sale_date_operator = st.sidebar.selectbox("Last Sale Date Operator", ["", "lt", "lte", "gt", "gte"])
        median_income = st.sidebar.number_input("Median Income", step=500, format="%.0f")
        median_income_operator = st.sidebar.selectbox("Median Income Operator", ["", "lt", "lte", "gt", "gte"])
        years_owned = st.sidebar.number_input("Years Owned", step=0.5, format="%.1f")
        years_owned_operator = st.sidebar.selectbox("Years Owned Operator", ["", "lt", "lte", "gt", "gte"])

        last_sale_date_operator = st.sidebar.selectbox(
            "Last Sale Date Operator", ["", "lt", "lte", "gt", "gte"]
        )
        median_income = st.sidebar.number_input("Median Income")
        median_income_operator = st.sidebar.selectbox(
            "Median Income Operator", ["", "lt", "lte", "gt", "gte"]
        )
        years_owned = st.sidebar.number_input("Years Owned")
        years_owned_operator = st.sidebar.selectbox(
            "Years Owned Operator", ["", "lt", "lte", "gt", "gte"]
        )
        # ... (Add other text/number input fields as needed) ...

    # Numeric Range Filters
    with st.sidebar.expander("Numeric Range Filters"):
        assessed_improvement_value_min = st.sidebar.number_input("Assessed Improvement Value (Min)", step=500, format="%.0f")
        assessed_improvement_value_max = st.sidebar.number_input("Assessed Improvement Value (Max)", step=500, format="%.0f")
        assessed_land_value_min = st.sidebar.number_input("Assessed Land Value (Min)", step=500, format="%.0f")
        assessed_land_value_max = st.sidebar.number_input("Assessed Land Value (Max)", step=500, format="%.0f")
        assessed_value_min = st.sidebar.number_input("Assessed Value (Min)", step=500, format="%.0f")
        assessed_value_max = st.sidebar.number_input("Assessed Value (Max)", step=500, format="%.0f")
        baths_min = st.sidebar.number_input("Baths (Min)", step=0.5, format="%.1f")
        baths_max = st.sidebar.number_input("Baths (Max)", step=0.5, format="%.1f")
        beds_min = st.sidebar.number_input("Beds (Min)", step=0.5, format="%.1f")
        beds_max = st.sidebar.number_input("Beds (Max)", step=0.5, format="%.1f")
        building_size_min = st.sidebar.number_input("Building Size (Min)", step=500, format="%.0f")
        building_size_max = st.sidebar.number_input("Building Size (Max)", step=500, format="%.0f")
        deck_area_min = st.sidebar.number_input("Deck Area (Min)", step=500, format="%.0f")
        deck_area_max = st.sidebar.number_input("Deck Area (Max)", step=500, format="%.0f")
        estimated_equity_min = st.sidebar.number_input("Estimated Equity (Min)", step=500, format="%.0f")
        estimated_equity_max = st.sidebar.number_input("Estimated Equity (Max)", step=500, format="%.0f")
        last_sale_price_min = st.sidebar.number_input("Last Sale Price (Min)", step=500, format="%.0f")
        last_sale_price_max = st.sidebar.number_input("Last Sale Price (Max)", step=500, format="%.0f")
        lot_size_min = st.sidebar.number_input("Lot Size (Min)", step=500, format="%.0f")
        lot_size_max = st.sidebar.number_input("Lot Size (Max)", step=500, format="%.0f")
        ltv_min = st.sidebar.slider("LTV (Min)", min_value=0, max_value=100, value=0, step=1, format="%.0f")
        ltv_max = st.sidebar.slider("LTV (Max)", min_value=0, max_value=100, value=100, step=1, format="%.0f")
        median_income_min = st.sidebar.number_input("Median Income (Min)", step=500, format="%.0f")
        median_income_max = st.sidebar.number_input("Median Income (Max)", step=500, format="%.0f")
        mortgage_min = st.sidebar.number_input("Mortgage (Min)", step=500, format="%.0f")
        mortgage_max = st.sidebar.number_input("Mortgage (Max)", step=500, format="%.0f")
        rooms_min = st.sidebar.number_input("Rooms (Min)", step=0.5, format="%.1f")
        rooms_max = st.sidebar.number_input("Rooms (Max)", step=0.5, format="%.1f")
        pool_area_min = st.sidebar.number_input("Pool Area (Min)", step=500, format="%.0f")
        pool_area_max = st.sidebar.number_input("Pool Area (Max)", step=500, format="%.0f")
        portfolio_equity_min = st.sidebar.number_input("Portfolio Equity (Min)", step=500, format="%.0f")
        portfolio_equity_max = st.sidebar.number_input("Portfolio Equity (Max)", step=500, format="%.0f")
        portfolio_mortgage_balance_min = st.sidebar.number_input("Portfolio Mortgage Balance (Min)", step=500, format="%.0f")
        portfolio_mortgage_balance_max = st.sidebar.number_input("Portfolio Mortgage Balance (Max)", step=500, format="%.0f")
        portfolio_purchased_last12_min = st.sidebar.number_input("Portfolio Purchased Last 12 Months (Min)", step=500, format="%.0f")
        portfolio_purchased_last12_max = st.sidebar.number_input("Portfolio Purchased Last 12 Months (Max)", step=500, format="%.0f")
        portfolio_purchased_last6_min = st.sidebar.number_input("Portfolio Purchased Last 6 Months (Min)", step=500, format="%.0f")
        portfolio_purchased_last6_max = st.sidebar.number_input("Portfolio Purchased Last 6 Months (Max)", step=500, format="%.0f")
        portfolio_value_min = st.sidebar.number_input("Portfolio Value (Min)", step=500, format="%.0f")
        portfolio_value_max = st.sidebar.number_input("Portfolio Value (Max)", step=500, format="%.0f")
        prior_owner_months_owned_min = st.sidebar.number_input("Prior Owner Months Owned (Min)", step=0.5, format="%.1f")
        prior_owner_months_owned_max = st.sidebar.number_input("Prior Owner Months Owned (Max)", step=0.5, format="%.1f")
        properties_owned_min = st.sidebar.number_input("Properties Owned (Min)", step=0.5, format="%.1f")
        properties_owned_max = st.sidebar.number_input("Properties Owned (Max)", step=0.5, format="%.1f")
        stories_min = st.sidebar.number_input("Stories (Min)", step=0.5, format="%.1f")
        stories_max = st.sidebar.number_input("Stories (Max)", step=0.5, format="%.1f")
        tax_delinquent_year_min = st.sidebar.number_input("Tax Delinquent Year (Min)", step=1, format="%.0f")
        tax_delinquent_year_max = st.sidebar.number_input("Tax Delinquent Year (Max)", step=1, format="%.0f")
        units_min = st.sidebar.number_input("Units (Min)", step=0.5, format="%.1f")
        units_max = st.sidebar.number_input("Units (Max)", step=0.5, format="%.1f")
        value_min = st.sidebar.number_input("Value (Min)", step=500, format="%.0f")
        value_max = st.sidebar.number_input("Value (Max)", step=500, format="%.0f")
        year_min = st.sidebar.number_input("Year (Min)", step=1, format="%.0f")
        year_max = st.sidebar.number_input("Year (Max)", step=1, format="%.0f")
        year_built_min = st.sidebar.number_input("Year Built (Min)", step=1, format="%.0f")
        year_built_max = st.sidebar.number_input("Year Built (Max)", step=1, format="%.0f")
        years_owned_min = st.sidebar.number_input("Years Owned (Min)", step=0.5, format="%.1f")
        years_owned_max = st.sidebar.number_input("Years Owned (Max)", step=0.5, format="%.1f")

        assessed_improvement_value_min = st.sidebar.number_input(
            "Assessed Improvement Value (Min)"
        )
        if assessed_improvement_value_min != 0:  # Check for non-default value
            st.session_state.params[
                "assessed_improvement_value_min"
            ] = assessed_improvement_value_min
        assessed_improvement_value_max = st.sidebar.number_input(
            "Assessed Improvement Value (Max)"
        )
        if assessed_improvement_value_max != 0:
            st.session_state.params[
                "assessed_improvement_value_max"
            ] = assessed_improvement_value_max

        assessed_land_value_min = st.sidebar.number_input("Assessed Land Value (Min)")
        if assessed_land_value_min != 0:
            st.session_state.params["assessed_land_value_min"] = assessed_land_value_min
        assessed_land_value_max = st.sidebar.number_input("Assessed Land Value (Max)")
        if assessed_land_value_max != 0:
            st.session_state.params["assessed_land_value_max"] = assessed_land_value_max

        assessed_value_min = st.sidebar.number_input("Assessed Value (Min)")
        if assessed_value_min != 0:
            st.session_state.params["assessed_value_min"] = assessed_value_min
        assessed_value_max = st.sidebar.number_input("Assessed Value (Max)")
        if assessed_value_max != 0:
            st.session_state.params["assessed_value_max"] = assessed_value_max

        baths_min = st.sidebar.number_input("Baths (Min)")
        if baths_min != 0:
            st.session_state.params["baths_min"] = baths_min
        baths_max = st.sidebar.number_input("Baths (Max)")
        if baths_max != 0:
            st.session_state.params["baths_max"] = baths_max

        beds_min = st.sidebar.number_input("Beds (Min)")
        if beds_min != 0:
            st.session_state.params["beds_min"] = beds_min
        beds_max = st.sidebar.number_input("Beds (Max)")
        if beds_max != 0:
            st.session_state.params["beds_max"] = beds_max

        building_size_min = st.sidebar.number_input("Building Size (Min)")
        if building_size_min != 0:
            st.session_state.params["building_size_min"] = building_size_min
        building_size_max = st.sidebar.number_input("Building Size (Max)")
        if building_size_max != 0:
            st.session_state.params["building_size_max"] = building_size_max

        deck_area_min = st.sidebar.number_input("Deck Area (Min)")
        if deck_area_min != 0:
            st.session_state.params["deck_area_min"] = deck_area_min
        deck_area_max = st.sidebar.number_input("Deck Area (Max)")
        if deck_area_max != 0:
            st.session_state.params["deck_area_max"] = deck_area_max

        estimated_equity_min = st.sidebar.number_input("Estimated Equity (Min)")
        if estimated_equity_min != 0:
            st.session_state.params["estimated_equity_min"] = estimated_equity_min
        estimated_equity_max = st.sidebar.number_input("Estimated Equity (Max)")
        if estimated_equity_max != 0:
            st.session_state.params["estimated_equity_max"] = estimated_equity_max

        last_sale_price_min = st.sidebar.number_input("Last Sale Price (Min)")
        if last_sale_price_min != 0:
            st.session_state.params["last_sale_price_min"] = last_sale_price_min
        last_sale_price_max = st.sidebar.number_input("Last Sale Price (Max)")
        if last_sale_price_max != 0:
            st.session_state.params["last_sale_price_max"] = last_sale_price_max

        lot_size_min = st.sidebar.number_input("Lot Size (Min)")
        if lot_size_min != 0:
            st.session_state.params["lot_size_min"] = lot_size_min
        lot_size_max = st.sidebar.number_input("Lot Size (Max)")
        if lot_size_max != 0:
            st.session_state.params["lot_size_max"] = lot_size_max

        # LTV Input with Sliders (0-100)
        ltv_min = st.sidebar.number_input(
            "LTV (Min)", min_value=0, max_value=100, value=0
        )
        ltv_min = st.sidebar.slider(
            "LTV (Min)", min_value=0, max_value=100, value=ltv_min
        )
        ltv_max = st.sidebar.number_input(
            "LTV (Max)", min_value=0, max_value=100, value=100
        )
        ltv_max = st.sidebar.slider(
            "LTV (Max)", min_value=0, max_value=100, value=ltv_max
        )

        median_income_min = st.sidebar.number_input("Median Income (Min)")
        if median_income_min != 0:
            st.session_state.params["median_income_min"] = median_income_min
        median_income_max = st.sidebar.number_input("Median Income (Max)")
        if median_income_max != 0:
            st.session_state.params["median_income_max"] = median_income_max

        mortgage_min = st.sidebar.number_input("Mortgage (Min)")
        if mortgage_min != 0:
            st.session_state.params["mortgage_min"] = mortgage_min
        mortgage_max = st.sidebar.number_input("Mortgage (Max)")
        if mortgage_max != 0:
            st.session_state.params["mortgage_max"] = mortgage_max

        rooms_min = st.sidebar.number_input("Rooms (Min)")
        if rooms_min != 0:
            st.session_state.params["rooms_min"] = rooms_min
        rooms_max = st.sidebar.number_input("Rooms (Max)")
        if rooms_max != 0:
            st.session_state.params["rooms_max"] = rooms_max

        pool_area_min = st.sidebar.number_input("Pool Area (Min)")
        if pool_area_min != 0:
            st.session_state.params["pool_area_min"] = pool_area_min
        pool_area_max = st.sidebar.number_input("Pool Area (Max)")
        if pool_area_max != 0:
            st.session_state.params["pool_area_max"] = pool_area_max

        portfolio_equity_min = st.sidebar.number_input("Portfolio Equity (Min)")
        if portfolio_equity_min != 0:
            st.session_state.params["portfolio_equity_min"] = portfolio_equity_min
        portfolio_equity_max = st.sidebar.number_input("Portfolio Equity (Max)")
        if portfolio_equity_max != 0:
            st.session_state.params["portfolio_equity_max"] = portfolio_equity_max

        portfolio_mortgage_balance_min = st.sidebar.number_input(
            "Portfolio Mortgage Balance (Min)"
        )
        if portfolio_mortgage_balance_min != 0:
            st.session_state.params[
                "portfolio_mortgage_balance_min"
            ] = portfolio_mortgage_balance_min
        portfolio_mortgage_balance_max = st.sidebar.number_input(
            "Portfolio Mortgage Balance (Max)"
        )
        if portfolio_mortgage_balance_max != 0:
            st.session_state.params[
                "portfolio_mortgage_balance_max"
            ] = portfolio_mortgage_balance_max

        portfolio_purchased_last12_min = st.sidebar.number_input(
            "Portfolio Purchased Last 12 Months (Min)"
        )
        if portfolio_purchased_last12_min != 0:
            st.session_state.params[
                "portfolio_purchased_last12_min"
            ] = portfolio_purchased_last12_min
        portfolio_purchased_last12_max = st.sidebar.number_input(
            "Portfolio Purchased Last 12 Months (Max)"
        )
        if portfolio_purchased_last12_max != 0:
            st.session_state.params[
                "portfolio_purchased_last12_max"
            ] = portfolio_purchased_last12_max

        portfolio_purchased_last6_min = st.sidebar.number_input(
            "Portfolio Purchased Last 6 Months (Min)"
        )
        if portfolio_purchased_last6_min != 0:
            st.session_state.params[
                "portfolio_purchased_last6_min"
            ] = portfolio_purchased_last6_min
        portfolio_purchased_last6_max = st.sidebar.number_input(
            "Portfolio Purchased Last 6 Months (Max)"
        )
        if portfolio_purchased_last6_max != 0:
            st.session_state.params[
                "portfolio_purchased_last6_max"
            ] = portfolio_purchased_last6_max

        portfolio_value_min = st.sidebar.number_input("Portfolio Value (Min)")
        if portfolio_value_min != 0:
            st.session_state.params["portfolio_value_min"] = portfolio_value_min
        portfolio_value_max = st.sidebar.number_input("Portfolio Value (Max)")
        if portfolio_value_max != 0:
            st.session_state.params["portfolio_value_max"] = portfolio_value_max

        prior_owner_months_owned_min = st.sidebar.number_input(
            "Prior Owner Months Owned (Min)"
        )
        if prior_owner_months_owned_min != 0:
            st.session_state.params[
                "prior_owner_months_owned_min"
            ] = prior_owner_months_owned_min
        prior_owner_months_owned_max = st.sidebar.number_input(
            "Prior Owner Months Owned (Max)"
        )
        if prior_owner_months_owned_max != 0:
            st.session_state.params[
                "prior_owner_months_owned_max"
            ] = prior_owner_months_owned_max

        properties_owned_min = st.sidebar.number_input("Properties Owned (Min)")
        if properties_owned_min != 0:
            st.session_state.params["properties_owned_min"] = properties_owned_min
        properties_owned_max = st.sidebar.number_input("Properties Owned (Max)")
        if properties_owned_max != 0:
            st.session_state.params["properties_owned_max"] = properties_owned_max

        stories_min = st.sidebar.number_input("Stories (Min)")
        if stories_min != 0:
            st.session_state.params["stories_min"] = stories_min
        stories_max = st.sidebar.number_input("Stories (Max)")
        if stories_max != 0:
            st.session_state.params["stories_max"] = stories_max

        tax_delinquent_year_min = st.sidebar.number_input("Tax Delinquent Year (Min)")
        if tax_delinquent_year_min != 0:
            st.session_state.params["tax_delinquent_year_min"] = tax_delinquent_year_min
        tax_delinquent_year_max = st.sidebar.number_input("Tax Delinquent Year (Max)")
        if tax_delinquent_year_max != 0:
            st.session_state.params["tax_delinquent_year_max"] = tax_delinquent_year_max

        units_min = st.sidebar.number_input("Units (Min)")
        if units_min != 0:
            st.session_state.params["units_min"] = units_min
        units_max = st.sidebar.number_input("Units (Max)")
        if units_max != 0:
            st.session_state.params["units_max"] = units_max

        value_min = st.sidebar.number_input("Value (Min)")
        if value_min != 0:
            st.session_state.params["value_min"] = value_min
        value_max = st.sidebar.number_input("Value (Max)")
        if value_max != 0:
            st.session_state.params["value_max"] = value_max

        year_min = st.sidebar.number_input("Year (Min)")
        if year_min != 0:
            st.session_state.params["year_min"] = year_min
        year_max = st.sidebar.number_input("Year (Max)")
        if year_max != 0:
            st.session_state.params["year_max"] = year_max

        year_built_min = st.sidebar.number_input("Year Built (Min)")
        if year_built_min != 0:
            st.session_state.params["year_built_min"] = year_built_min
        year_built_max = st.sidebar.number_input("Year Built (Max)")
        if year_built_max != 0:
            st.session_state.params["year_built_max"] = year_built_max

        years_owned_min = st.sidebar.number_input("Years Owned (Min)")
        if years_owned_min != 0:
            st.session_state.params["years_owned_min"] = years_owned_min
        years_owned_max = st.sidebar.number_input("Years Owned (Max)")
        if years_owned_max != 0:
            st.session_state.params["years_owned_max"] = years_owned_max

    # Date Range Filters
    with st.sidebar.expander("Date Range Filters"):
        auction_date_min = st.sidebar.date_input("Auction Date (Min)")
        if auction_date_min:  # Check if a date has been selected
            st.session_state.params[
                "auction_date_min"
            ] = auction_date_min.strftime("%Y-%m-%d")
        auction_date_max = st.sidebar.date_input("Auction Date (Max)")
        if auction_date_max:
            st.session_state.params[
                "auction_date_max"
            ] = auction_date_max.strftime("%Y-%m-%d")

        foreclosure_date_min = st.sidebar.date_input("Foreclosure Date (Min)")
        if foreclosure_date_min:
            st.session_state.params[
                "foreclosure_date_min"
            ] = foreclosure_date_min.strftime("%Y-%m-%d")
        foreclosure_date_max = st.sidebar.date_input("Foreclosure Date (Max)")
        if foreclosure_date_max:
            st.session_state.params[
                "foreclosure_date_max"
            ] = foreclosure_date_max.strftime("%Y-%m-%d")

        last_sale_date_min = st.sidebar.date_input("Last Sale Date (Min)")
        if last_sale_date_min:
            st.session_state.params[
                "last_sale_date_min"
            ] = last_sale_date_min.strftime("%Y-%m-%d")
        last_sale_date_max = st.sidebar.date_input("Last Sale Date (Max)")
        if last_sale_date_max:
            st.session_state.params[
                "last_sale_date_max"
            ] = last_sale_date_max.strftime("%Y-%m-%d")

        pre_foreclosure_date_min = st.sidebar.date_input("Pre-Foreclosure Date (Min)")
        if pre_foreclosure_date_min:
            st.session_state.params[
                "pre_foreclosure_date_min"
            ] = pre_foreclosure_date_min.strftime("%Y-%m-%d")
        pre_foreclosure_date_max = st.sidebar.date_input("Pre-Foreclosure Date (Max)")
        if pre_foreclosure_date_max:
            st.session_state.params[
                "pre_foreclosure_date_max"
            ] = pre_foreclosure_date_max.strftime("%Y-%m-%d")

        last_update_date_min = st.sidebar.date_input("Last Update Date (Min)")
        if last_update_date_min:
            st.session_state.params[
                "last_update_date_min"
            ] = last_update_date_min.strftime("%Y-%m-%d")
        last_update_date_max = st.sidebar.date_input("Last Update Date (Max)")
        if last_update_date_max:
            st.session_state.params[
                "last_update_date_max"
            ] = last_update_date_max.strftime("%Y-%m-%d")

    # MLS Filters
    with st.sidebar.expander("MLS Filters"):
        mls_days_on_market_min = st.sidebar.number_input("MLS Days on Market (Min)", step=1, format="%.0f")
        mls_days_on_market_max = st.sidebar.number_input("MLS Days on Market (Max)", step=1, format="%.0f")
        mls_listing_price_min = st.sidebar.number_input("MLS Listing Price (Min)", step=500, format="%.0f")
        mls_listing_price_max = st.sidebar.number_input("MLS Listing Price (Max)", step=500, format="%.0f")
        mls_listing_price = st.sidebar.number_input("MLS Listing Price", step=500, format="%.0f")
        mls_listing_price_operator = st.sidebar.selectbox("MLS Listing Price Operator", ["", "lt", "lte", "gt", "gte"])

    # Main Content
    st.title("Real Estate Property Search")

    if st.sidebar.button("Search"):
        # Access params from session state
        params = st.session_state.search_filter

        # Add parameters to `params` based on user input
        if count != "":
            params["count"] = count == "True"  # Convert string to boolean
        if ids_only != "":
            params["ids_only"] = ids_only == "True"
        if obfuscate != "":
            params["obfuscate"] = obfuscate == "True"
        if summary != "":
            params["summary"] = summary == "True"
        params["size"] = size
        params["resultIndex"] = result_index

        if address:
            params["address"] = address
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if property_type:
            params["property_type"] = property_type
        # ... (Add other parameters to params based on user input) ...

        st.session_state.search_filter = params.copy()  # Store filter for later use

        # Fetch initial page of results
        data = get_page_of_properties(params)
        if data:
            st.session_state.results = flatten_property_data(data.get("data", []))
            st.session_state.total_pages = (
                data.get("resultCount", 0) // PAGE_SIZE
                + (data.get("resultCount", 0) % PAGE_SIZE > 0)
        mls_days_on_market_min = st.sidebar.number_input("MLS Days on Market (Min)")
        if mls_days_on_market_min != 0:
            st.session_state.params["mls_days_on_market_min"] = mls_days_on_market_min
        mls_days_on_market_max = st.sidebar.number_input("MLS Days on Market (Max)")
        if mls_days_on_market_max != 0:
            st.session_state.params["mls_days_on_market_max"] = mls_days_on_market_max
        mls_listing_price_min = st.sidebar.number_input("MLS Listing Price (Min)")
        if mls_listing_price_min != 0:
            st.session_state.params["mls_listing_price_min"] = mls_listing_price_min
        mls_listing_price_max = st.sidebar.number_input("MLS Listing Price (Max)")
        if mls_listing_price_max != 0:
            st.session_state.params["mls_listing_price_max"] = mls_listing_price_max
        mls_listing_price = st.sidebar.number_input("MLS Listing Price")
        if mls_listing_price != 0:
            st.session_state.params["mls_listing_price"] = mls_listing_price
        mls_listing_price_operator = st.sidebar.selectbox(
            "MLS Listing Price Operator", ["", "lt", "lte", "gt", "gte"]
        )
        if mls_listing_price_operator != "":
            st.session_state.params["mls_listing_price_operator"] = mls_listing_price_operator

        # ... (Add other MLS-related input fields) ...


# --- Main Content ---
st.title("Real Estate Property Search")

if st.sidebar.button("Search"):
    # Access params from session state
    params = st.session_state.params

    # Add parameters to `params` based on user input
    if count != "":
        params["count"] = count == "True"  # Convert string to boolean
    if ids_only != "":
        params["ids_only"] = ids_only == "True"
    if obfuscate != "":
        params["obfuscate"] = obfuscate == "True"
    if summary != "":
        params["summary"] = summary == "True"
    params["size"] = size
    params["resultIndex"] = result_index

    if address:
        params["address"] = address
    if city:
        params["city"] = city
    if state:
        params["state"] = state
    if property_type:
        params["property_type"] = property_type
    # ... (Add other parameters to params based on user input) ...

    st.session_state.search_filter = params.copy()  # Store filter for later use

    # Fetch initial page of results
    data = get_page_of_properties(params)
    if data:
        st.session_state.results = flatten_property_data(data.get("data", []))
        st.session_state.total_pages = (
            data.get("resultCount", 0) // PAGE_SIZE
            + (data.get("resultCount", 0) % PAGE_SIZE > 0)
        )


    # Fetch and display current page of results
    data = get_page_of_properties(
        st.session_state.search_filter,
        (st.session_state.current_page - 1) * PAGE_SIZE,
    )
    if data:
        current_page_results = flatten_property_data(data.get("data", []))

        # --- Data Display Options ---
        display_option = st.selectbox(
            "Choose how to display the data:",
            ("Table", "Map", "Charts"),
        )

        if display_option == "Table":
            # --- AgGrid Table ---
            gb = GridOptionsBuilder.from_dataframe(
                pd.DataFrame(current_page_results))
            gb.configure_pagination(
                paginationAutoPageSize=True, paginationPageSize=10
            )
            gb.configure_side_bar()
            gb.configure_selection(
                selection_mode="single",
                use_checkbox=True,
                groupSelectsChildren="Group checkbox select children",
            )
            st.session_state.total_results = data.get("resultCount", 0)
        else:
            st.session_state.results = []

    # Display Results
    if st.session_state.results:
        st.header("Search Results")

        # Display total results and paging controls
        total_results = st.session_state.total_results
        st.write(f"Total Results: {total_results}")
        if st.session_state.total_pages > 1:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.session_state.current_page > 1:
                    if st.button("Previous Page"):
                        st.session_state.current_page -= 1
            with col2:
                st.write(f"Page {st.session_state.current_page} of {st.session_state.total_pages}")
            with col3:
                if st.session_state.current_page < st.session_state.total_pages:
                    if st.button("Next Page"):
                        st.session_state.current_page += 1

            # Fetch and display current page of results
            result_index = (st.session_state.current_page - 1) * PAGE_SIZE
            data = get_page_of_properties(st.session_state.search_filter, result_index)
            if data:
                current_page_results = flatten_property_data(data.get("data", []))
                st.session_state.results = current_page_results

        # Display results in a responsive table with filtering options using AgGrid
        df = pd.DataFrame(st.session_state.results)
        if not df.empty:
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=True)  # Responsive Pagination
            gb.configure_side_bar()  # Enable the sidebar with filters
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)  # Enable Pivoting but not by default
            gb.configure_auto_height(True)  # Auto-size rows based on content
            grid_options = gb.build()

            AgGrid(
                df,
                gridOptions=grid_options,
                data_return_mode=DataReturnMode.AS_INPUT,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=False,  # Allow columns to expand to screen size
                theme='alpine',  # Updated to "alpine" theme
            gridOptions = gb.build()

            grid_response = AgGrid(
                pd.DataFrame(current_page_results),
                gridOptions=gridOptions,
                data_return_mode="AS_INPUT",
                update_mode="MODEL_CHANGED",
                fit_columns_on_grid_load=False,
                theme="dark",  # Enable dark mode
                enable_enterprise_modules=True,
                height=350,
                width="100%",
                reload_data=True,
            )
            data = grid_response["data"]
            selected = grid_response["selected_rows"]
            if selected:
                st.write("Selected Row:")
                st.dataframe(selected)

        elif display_option == "Map":
            # --- Map Display ---
            # Filter out properties without latitude/longitude
            map_data = [
                prop
                for prop in current_page_results
                if prop.get("latitude") and prop.get("longitude")
            ]
            if map_data:
                view_state = pdk.ViewState(
                    latitude=map_data[0]["latitude"],
                    longitude=map_data[0]["longitude"],
                    zoom=12,
                    pitch=50,
                )
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_data,
                    get_position=["longitude", "latitude"],
                    get_radius=100,
                    get_color=[255, 0, 0],
                    pickable=True,
                )
                st.pydeck_chart(
                    pdk.Deck(layers=[layer], initial_view_state=view_state))
            else:
                st.warning(
                    "No properties with latitude and longitude to display on the map."
                )

        elif display_option == "Charts":
            # --- Chart Display ---
            chart_type = st.selectbox(
                "Choose a chart type:", ("Scatter Plot",
                                        "Bar Chart", "Histogram")
            )
        else:
            st.write("No data available to display in table format.")

        # Display four relevant charts automatically
        st.subheader("Automatic Data Visualizations")

        if not df.empty:
            # Example chart 1: Distribution of property types
            if "property_type" in df.columns:
                fig1 = px.histogram(df, x="property_type", title="Distribution of Property Types")
                fig1.update_layout(autosize=True)  # Ensure chart expands to full width
                st.plotly_chart(fig1, use_container_width=True)

            # Example chart 2: Distribution of property values
            if "estimated_value" in df.columns:
                fig2 = px.histogram(df, x="estimated_value", title="Distribution of Property Values")
                fig2.update_layout(autosize=True)
                st.plotly_chart(fig2, use_container_width=True)

            # Example chart 3: Scatter plot of property values by size
            if "building_size_max" in df.columns and "estimated_value" in df.columns:
                fig3 = px.scatter(df, x="building_size_max", y="estimated_value", title="Property Value vs. Building Size")
                fig3.update_layout(autosize=True)
                st.plotly_chart(fig3, use_container_width=True)

            # Example chart 4: Pie chart of properties by foreclosure status
            if "foreclosure" in df.columns:
                foreclosure_counts = df["foreclosure"].value_counts().reset_index()
                foreclosure_counts.columns = ["Foreclosure Status", "Count"]
                fig4 = px.pie(foreclosure_counts, names="Foreclosure Status", values="Count", title="Foreclosure Status Distribution")
                fig4.update_layout(autosize=True)
                st.plotly_chart(fig4, use_container_width=True)

    # If no search has been performed yet
    elif st.session_state.api_key and st.session_state.user_id:
        st.info("Enter search criteria in the sidebar and click 'Search'.")

    else:
        st.warning("Please configure your API key and User ID in the sidebar.")


if __name__ == "__main__":
    main()
            if chart_type == "Scatter Plot":
                x_axis = st.selectbox(
                    "X-axis", list(current_page_results[0].keys()))
                y_axis = st.selectbox(
                    "Y-axis", list(current_page_results[0].keys()))
                fig = px.scatter(
                    current_page_results, x=x_axis, y=y_axis, title="Scatter Plot"
                )
                st.plotly_chart(fig)
            # ... (Add options for other chart types: Bar Chart, Histogram, etc.) ...

elif st.session_state.api_key and st.session_state.user_id:
    st.info("Enter search criteria in the sidebar and click 'Search'.")
else:
    st.warning("Please configure your API key and User ID in the side