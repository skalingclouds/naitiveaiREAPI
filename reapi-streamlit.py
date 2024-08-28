import streamlit as st
import pandas as pd
import requests
import json
from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode, GridUpdateMode
import plotly.express as px
import streamlit as st
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
if 'total_results_count' not in st.session_state:
    st.session_state.total_results_count = 0
if 'result_index' not in st.session_state:
    st.session_state.result_index = 0
if 'search_filter' not in st.session_state:
    st.session_state.search_filter = {}
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = DEFAULT_USER_ID
if 'zip_codes_input' not in st.session_state:
    st.session_state.zip_codes_input = ''

def get_properties(filter_params, page_size=PAGE_SIZE, result_index=0):
    """Retrieves properties with pagination."""
    url = "https://api.realestateapi.com/v2/PropertySearch"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-user-id": st.session_state.user_id,
        "x-api-key": st.session_state.api_key,
    }
    payload = {
        "count": False,
        "size": page_size,
        "resultIndex": result_index,
        **filter_params,
    }

    print("Filter Params:", filter_params)
    print("Result Index:", result_index)

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        print("API Response:", response.json())

        return response.json()
    except requests.RequestException as e:
        st.error(f"API call failed: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            st.error(f"Response content: {e.response.text}")
        return None

def fetch_all_properties(filter_params, page_size=50):
    """Fetches all properties across all pages."""
    print("Fetching all properties with params:", filter_params)
    result_index = 0
    total_results = []
    while True:
        data = get_properties(filter_params, page_size=page_size, result_index=result_index)
        if data is None or 'data' not in data:
            break

        # Append results from the current page to the total results
        total_results.extend(data.get('data', []))

        # Update result_index to fetch the next page
        result_index += len(data.get('data', []))

        # Check if we have retrieved all results
        if result_index >= data.get('resultCount', 0):
            break

    st.session_state.total_results_count = len(total_results)
    return total_results

def flatten_property_data(properties):
    """Flattens the nested JSON structure of the property data."""
    display_data = []
    for prop in properties:
        flattened_prop = {}
        for key, value in prop.items():
            if isinstance(value, dict):
                flattened_prop.update(
                    {f"{key}_{sub_key}": sub_value for sub_key,
                        sub_value in value.items()}
                )
            else:
                flattened_prop[key] = value
        display_data.append(flattened_prop)
    return display_data

def is_valid_zip_code(zip_code):
    """Checks if a zip code is valid (5 digits or 5+4 format)."""
    return re.match(r"^\d{5}(-\d{4})?$", zip_code) is not None

# --- Streamlit UI ---
def main():
    # Set page config to wide mode
    st.set_page_config(layout="wide")

    # --- Sidebar --- #
    st.sidebar.header("Search Parameters")
    
    # Move the Search button to the top
    search_clicked = st.sidebar.button("Search")

    # API Configuration
    st.sidebar.header("API Configuration")
    api_key = st.sidebar.text_input(
        "Enter your API key",
        type="password",
        value=st.session_state.api_key,
    )
    user_id = st.sidebar.text_input(
        "Enter your User ID", value=st.session_state.user_id
    )
    if st.sidebar.button("Save Credentials"):
        st.session_state.api_key = api_key
        st.session_state.user_id = user_id
        st.success("API Key and User ID saved!")

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
    count = st.sidebar.radio("Count Only", ("", "True", "False"))
    ids_only = st.sidebar.radio("IDs Only", ("", "True", "False"))
    obfuscate = st.sidebar.radio("Obfuscate", ("", "True", "False"))
    summary = st.sidebar.radio("Summary", ("", "True", "False"))
    size = st.sidebar.number_input("Size", min_value=1, value=50, step=1, format="%d")
    result_index = st.sidebar.number_input("Result Index", min_value=0, value=0, step=1, format="%d")

    # Advanced Filtering
    st.sidebar.header("Advanced Filters")

    with st.sidebar.expander("Property Characteristics"):
        absentee_owner = st.radio("Absentee Owner", ("", "True", "False"))
        adjustable_rate = st.radio("Adjustable Rate", ("", "True", "False"))
        assumable = st.radio("Assumable", ("", "True", "False"))
        attic = st.radio("Attic", ("", "True", "False"))
        auction = st.radio("Auction", ("", "True", "False"))
        basement = st.radio("Basement", ("", "True", "False"))
        breezeway = st.radio("Breezeway", ("", "True", "False"))
        carport = st.radio("Carport", ("", "True", "False"))
        cash_buyer = st.radio("Cash Buyer", ("", "True", "False"))
        corporate_owned = st.radio("Corporate Owned", ("", "True", "False"))
        death = st.radio("Death", ("", "True", "False"))
        deck = st.radio("Deck", ("", "True", "False"))
        equity = st.radio("Equity", ("", "True", "False"))
        feature_balcony = st.radio("Feature Balcony", ("", "True", "False"))
        fire_sprinklers = st.radio("Fire Sprinklers", ("", "True", "False"))
        flood_zone = st.radio("Flood Zone", ("", "True", "False"))
        foreclosure = st.radio("Foreclosure", ("", "True", "False"))
        free_clear = st.radio("Free Clear", ("", "True", "False"))
        garage = st.radio("Garage", ("", "True", "False"))
        high_equity = st.radio("High Equity", ("", "True", "False"))
        inherited = st.radio("Inherited", ("", "True", "False"))
        in_state_owner = st.radio("In-State Owner", ("", "True", "False"))
        investor_buyer = st.radio("Investor Buyer", ("", "True", "False"))
        judgment = st.radio("Judgment", ("", "True", "False"))
        mfh_2to4 = st.radio("MFH 2 to 4", ("", "True", "False"))
        mfh_5plus = st.radio("MFH 5+", ("", "True", "False"))
        negative_equity = st.radio("Negative Equity", ("", "True", "False"))
        out_of_state_owner = st.radio("Out-of-State Owner", ("", "True", "False"))
        patio = st.radio("Patio", ("", "True", "False"))
        pool = st.radio("Pool", ("", "True", "False"))
        pre_foreclosure = st.radio("Pre-Foreclosure", ("", "True", "False"))
        prior_owner_individual = st.radio("Prior Owner Individual", ("", "True", "False"))
        private_lender = st.radio("Private Lender", ("", "True", "False"))
        quit_claim = st.radio("Quit Claim", ("", "True", "False"))
        reo = st.radio("REO", ("", "True", "False"))
        rv_parking = st.radio("RV Parking", ("", "True", "False"))
        tax_lien = st.radio("Tax Lien", ("", "True", "False"))
        trust_owned = st.radio("Trust Owned", ("", "True", "False"))
        vacant = st.radio("Vacant", ("", "True", "False"))

    with st.sidebar.expander("Additional Search Fields"):
        house = st.sidebar.text_input("House Number")
        street = st.sidebar.text_input("Street Name")
        county = st.sidebar.text_input("County")
        latitude = st.sidebar.number_input("Latitude", format="%.5f")
        longitude = st.sidebar.number_input("Longitude", format="%.5f")
        radius = st.sidebar.slider("Radius (miles)", min_value=0.1, max_value=10.0, value=5.0, step=0.1, format="%.1f")
        property_use_code = st.sidebar.text_input("Property Use Code")
        census_block = st.sidebar.text_input("Census Block")
        census_block_group = st.sidebar.text_input("Census Block Group")
        census_tract = st.sidebar.text_input("Census Tract")
        construction = st.sidebar.text_input("Construction")
        document_type_code = st.sidebar.text_input("Document Type Code")
        flood_zone_type = st.sidebar.text_input("Flood Zone Type")
        loan_type_code_first = st.sidebar.text_input("Loan Type Code (First)")
        loan_type_code_second = st.sidebar.text_input("Loan Type Code (Second)")
        loan_type_code_third = st.sidebar.text_input("Loan Type Code (Third)")
        notice_type = st.sidebar.text_input("Notice Type")
        parcel_account_number = st.sidebar.text_input("Parcel Account Number")
        search_range = st.sidebar.text_input("Search Range")
        sewage = st.sidebar.selectbox("Sewage", ["", "Municipal", "Yes", "Septic", "None", "Storm"])  # Example of fixed input
        water_source = st.sidebar.text_input("Water Source")
        estimated_equity = st.sidebar.number_input("Estimated Equity", step=0.5, format="%.1f")
        equity_operator = st.sidebar.selectbox("Equity Operator", ["", "lt", "lte", "gt", "gte"])
        equity_percent = st.sidebar.slider("Equity Percent", min_value=0, max_value=100, value=50, step=5, format="%d")
        equity_percent_operator = st.sidebar.selectbox("Equity Percent Operator", ["", "lt", "lte", "gt", "gte"])
        last_sale_date = st.sidebar.date_input("Last Sale Date")
        last_sale_date_operator = st.sidebar.selectbox("Last Sale Date Operator", ["", "lt", "lte", "gt", "gte"])
        median_income = st.sidebar.number_input("Median Income", step=500, format="%d")
        median_income_operator = st.sidebar.selectbox("Median Income Operator", ["", "lt", "lte", "gt", "gte"])
        years_owned = st.sidebar.number_input("Years Owned", step=0.5, format="%.1f")
        years_owned_operator = st.sidebar.selectbox("Years Owned Operator", ["", "lt", "lte", "gt", "gte"])

    with st.sidebar.expander("Numeric Range Filters"):
        assessed_improvement_value_min = st.sidebar.number_input("Assessed Improvement Value (Min)", step=500, format="%d")
        assessed_improvement_value_max = st.sidebar.number_input("Assessed Improvement Value (Max)", step=500, format="%d")
        assessed_land_value_min = st.sidebar.number_input("Assessed Land Value (Min)", step=500, format="%d")
        assessed_land_value_max = st.sidebar.number_input("Assessed Land Value (Max)", step=500, format="%d")
        assessed_value_min = st.sidebar.number_input("Assessed Value (Min)", step=500, format="%d")
        assessed_value_max = st.sidebar.number_input("Assessed Value (Max)", step=500, format="%d")
        baths_min = st.sidebar.number_input("Baths (Min)", step=0.5, format="%.1f")
        baths_max = st.sidebar.number_input("Baths (Max)", step=0.5, format="%.1f")
        beds_min = st.sidebar.number_input("Beds (Min)", step=0.5, format="%.1f")
        beds_max = st.sidebar.number_input("Beds (Max)", step=0.5, format="%.1f")
        building_size_min = st.sidebar.number_input("Building Size (Min)", step=500, format="%d")
        building_size_max = st.sidebar.number_input("Building Size (Max)", step=500, format="%d")
        deck_area_min = st.sidebar.number_input("Deck Area (Min)", step=500, format="%d")
        deck_area_max = st.sidebar.number_input("Deck Area (Max)", step=500, format="%d")
        estimated_equity_min = st.sidebar.number_input("Estimated Equity (Min)", step=500, format="%d")
        estimated_equity_max = st.sidebar.number_input("Estimated Equity (Max)", step=500, format="%d")
        last_sale_price_min = st.sidebar.number_input("Last Sale Price (Min)", step=500, format="%d")
        last_sale_price_max = st.sidebar.number_input("Last Sale Price (Max)", step=500, format="%d")
        lot_size_min = st.sidebar.number_input("Lot Size (Min)", step=500, format="%d")
        lot_size_max = st.sidebar.number_input("Lot Size (Max)", step=500, format="%d")
        ltv_min = st.sidebar.slider("LTV (Min)", min_value=0, max_value=100, value=0, step=1, format="%d")
        ltv_max = st.sidebar.slider("LTV (Max)", min_value=0, max_value=100, value=100, step=1, format="%d")
        median_income_min = st.sidebar.number_input("Median Income (Min)", step=500, format="%d")
        median_income_max = st.sidebar.number_input("Median Income (Max)", step=500, format="%d")
        mortgage_min = st.sidebar.number_input("Mortgage (Min)", step=500, format="%d")
        mortgage_max = st.sidebar.number_input("Mortgage (Max)", step=500, format="%d")
        rooms_min = st.sidebar.number_input("Rooms (Min)", step=0.5, format="%.1f")
        rooms_max = st.sidebar.number_input("Rooms (Max)", step=0.5, format="%.1f")
        pool_area_min = st.sidebar.number_input("Pool Area (Min)", step=500, format="%d")
        pool_area_max = st.sidebar.number_input("Pool Area (Max)", step=500, format="%d")
        portfolio_equity_min = st.sidebar.number_input("Portfolio Equity (Min)", step=500, format="%d")
        portfolio_equity_max = st.sidebar.number_input("Portfolio Equity (Max)", step=500, format="%d")
        portfolio_mortgage_balance_min = st.sidebar.number_input("Portfolio Mortgage Balance (Min)", step=500, format="%d")
        portfolio_mortgage_balance_max = st.sidebar.number_input("Portfolio Mortgage Balance (Max)", step=500, format="%d")
        portfolio_purchased_last12_min = st.sidebar.number_input("Portfolio Purchased Last 12 Months (Min)", step=500, format="%d")
        portfolio_purchased_last12_max = st.sidebar.number_input("Portfolio Purchased Last 12 Months (Max)", step=500, format="%d")
        portfolio_purchased_last6_min = st.sidebar.number_input("Portfolio Purchased Last 6 Months (Min)", step=500, format="%d")
        portfolio_purchased_last6_max = st.sidebar.number_input("Portfolio Purchased Last 6 Months (Max)", step=500, format="%d")
        portfolio_value_min = st.sidebar.number_input("Portfolio Value (Min)", step=500, format="%d")
        portfolio_value_max = st.sidebar.number_input("Portfolio Value (Max)", step=500, format="%d")
        prior_owner_months_owned_min = st.sidebar.number_input("Prior Owner Months Owned (Min)", step=0.5, format="%.1f")
        prior_owner_months_owned_max = st.sidebar.number_input("Prior Owner Months Owned (Max)", step=0.5, format="%.1f")
        properties_owned_min = st.sidebar.number_input("Properties Owned (Min)", step=0.5, format="%.1f")
        properties_owned_max = st.sidebar.number_input("Properties Owned (Max)", step=0.5, format="%.1f")
        stories_min = st.sidebar.number_input("Stories (Min)", step=0.5, format="%.1f")
        stories_max = st.sidebar.number_input("Stories (Max)", step=0.5, format="%.1f")
        tax_delinquent_year_min = st.sidebar.number_input("Tax Delinquent Year (Min)", step=1, format="%d")
        tax_delinquent_year_max = st.sidebar.number_input("Tax Delinquent Year (Max)", step=1, format="%d")
        units_min = st.sidebar.number_input("Units (Min)", step=0.5, format="%.1f")
        units_max = st.sidebar.number_input("Units (Max)", step=0.5, format="%.1f")
        value_min = st.sidebar.number_input("Value (Min)", step=500, format="%d")
        value_max = st.sidebar.number_input("Value (Max)", step=500, format="%d")
        year_min = st.sidebar.number_input("Year (Min)", step=1, format="%d")
        year_max = st.sidebar.number_input("Year (Max)", step=1, format="%d")
        year_built_min = st.sidebar.number_input("Year Built (Min)", step=1, format="%d")
        year_built_max = st.sidebar.number_input("Year Built (Max)", step=1, format="%d")
        years_owned_min = st.sidebar.number_input("Years Owned (Min)", step=0.5, format="%.1f")
        years_owned_max = st.sidebar.number_input("Years Owned (Max)", step=0.5, format="%.1f")

    with st.sidebar.expander("Date Range Filters"):
        auction_date_min = st.sidebar.date_input("Auction Date (Min)")
        auction_date_max = st.sidebar.date_input("Auction Date (Max)")
        foreclosure_date_min = st.sidebar.date_input("Foreclosure Date (Min)")
        foreclosure_date_max = st.sidebar.date_input("Foreclosure Date (Max)")
        last_sale_date_min = st.sidebar.date_input("Last Sale Date (Min)")
        last_sale_date_max = st.sidebar.date_input("Last Sale Date (Max)")
        pre_foreclosure_date_min = st.sidebar.date_input("Pre-Foreclosure Date (Min)")
        pre_foreclosure_date_max = st.sidebar.date_input("Pre-Foreclosure Date (Max)")
        last_update_date_min = st.sidebar.date_input("Last Update Date (Min)")
        last_update_date_max = st.sidebar.date_input("Last Update Date (Max)")

    with st.sidebar.expander("MLS Filters"):
        mls_days_on_market_min = st.sidebar.number_input("MLS Days on Market (Min)", step=1, format="%d")
        mls_days_on_market_max = st.sidebar.number_input("MLS Days on Market (Max)", step=1, format="%d")
        mls_listing_price_min = st.sidebar.number_input("MLS Listing Price (Min)", step=500, format="%d")
        mls_listing_price_max = st.sidebar.number_input("MLS Listing Price (Max)", step=500, format="%d")
        mls_listing_price = st.sidebar.number_input("MLS Listing Price", step=500, format="%d")
        mls_listing_price_operator = st.sidebar.selectbox("MLS Listing Price Operator", ["", "lt", "lte", "gt", "gte"])

    # Main Content
    st.title("Real Estate Property Search")

    if search_clicked:
        # Access params from session state
        params = st.session_state.search_filter

        # Add parameters to `params` based on user input
        if count != "":
            params["count"] = count == "True"
        if ids_only != "":
            params["ids_only"] = ids_only == "True"
        if obfuscate != "":
            params["obfuscate"] = obfuscate == "True"
        if summary != "":
            params["summary"] = summary == "True"
        if size:
            params["size"] = size
        if result_index:
            params["resultIndex"] = result_index

        # Add all other parameters similarly based on user input
        if address:
            params["address"] = address
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if property_type:
            params["propertyType"] = property_type
        
        # FETCH THE DATA HERE!
        results = fetch_all_properties(params)
        if results:
            st.session_state.results = flatten_property_data(results)

            # Display results in a responsive table with filtering options using AgGrid
            df = pd.DataFrame(st.session_state.results)
            
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
            gridOptions = gb.build()

            grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                data_return_mode='AS_INPUT',
                update_mode='MODEL_CHANGED',
                fit_columns_on_grid_load=False,
                theme='streamlit',
                enable_enterprise_modules=True,
                height=400, 
                width='100%',
                reload_data=True
            )

            selected = grid_response['selected_rows']
            selected_df = pd.DataFrame(selected)

            if not selected_df.empty:
                st.write("Selected Rows:")
                st.dataframe(selected_df)

            # Create charts
            st.header("Data Visualization")

            # Chart 1: Distribution of Property Types
            st.subheader("Distribution of Property Types")
            property_type_counts = df['propertyType'].value_counts()
            fig_property_types = px.pie(values=property_type_counts.values, names=property_type_counts.index, title="Property Types")
            st.plotly_chart(fig_property_types)

            # Chart 2: Average Price by City
            st.subheader("Average Price by City")
            avg_price_by_city = df.groupby('city')['value'].mean().sort_values(ascending=False).head(10)
            fig_avg_price = px.bar(x=avg_price_by_city.index, y=avg_price_by_city.values, title="Top 10 Cities by Average Property Value")
            fig_avg_price.update_layout(xaxis_title="City", yaxis_title="Average Property Value")
            st.plotly_chart(fig_avg_price)

            # Chart 3: Scatter plot of Property Value vs. Building Size
            st.subheader("Property Value vs. Building Size")
            fig_scatter = px.scatter(df, x='buildingSize', y='value', color='propertyType',
                                     hover_data=['address_address', 'city', 'state'],
                                     title="Property Value vs. Building Size")
            fig_scatter.update_layout(xaxis_title="Building Size (sq ft)", yaxis_title="Property Value ($)")
            st.plotly_chart(fig_scatter)

            # Chart 4: Distribution of Years Built
            st.subheader("Distribution of Years Built")
            fig_years_built = px.histogram(df, x='yearBuilt', nbins=50, title="Distribution of Years Built")
            fig_years_built.update_layout(xaxis_title="Year Built", yaxis_title="Count")
            st.plotly_chart(fig_years_built)

            # Chart 5: Foreclosure Status
            st.subheader("Foreclosure Status")
            foreclosure_counts = df['foreclosure'].value_counts()
            fig_foreclosure = px.pie(values=foreclosure_counts.values, names=foreclosure_counts.index, title="Foreclosure Status")
            st.plotly_chart(fig_foreclosure)

            # Chart 6: Pre-Foreclosure Status
            st.subheader("Pre-Foreclosure Status")
            pre_foreclosure_counts = df['preForeclosure'].value_counts()
            fig_pre_foreclosure = px.pie(values=pre_foreclosure_counts.values, names=pre_foreclosure_counts.index, title="Pre-Foreclosure Status")
            st.plotly_chart(fig_pre_foreclosure)

            # Map view of properties
            st.subheader("Property Locations")
            map_data = df[['latitude', 'longitude', 'address_address', 'value']].dropna()
            st.pydeck_chart(pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v9',
                initial_view_state=pdk.ViewState(
                    latitude=map_data['latitude'].mean(),
                    longitude=map_data['longitude'].mean(),
                    zoom=11,
                    pitch=50,
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=map_data,
                        get_position='[longitude, latitude]',
                        get_color='[200, 30, 0, 160]',
                        get_radius='value',
                        radius_scale=0.05,
                    ),
                ],
            ))

if __name__ == "__main__":
    main()
