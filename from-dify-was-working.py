import streamlit as st
import pandas as pd
import requests
import json
from st_aggrid import GridOptionsBuilder, AgGrid
from st_aggrid.shared import GridUpdateMode, DataReturnMode

# Function to retrieve a single page of results
def get_page_of_properties(filter_params, result_index=0, page_size=10):
    url = "https://api.realestateapi.com/v2/PropertySearch"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-user-id": st.session_state.user_id,
        "x-api-key": st.session_state.api_key
    }
    payload = {
        "count": False,
        "size": page_size,
        "resultIndex": result_index,
        **filter_params
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()    
        return data
    except requests.RequestException as e:
        st.error(f"API call failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response content: {e.response.text}")
        return None

# Set page config
st.set_page_config(page_title="Real Estate Property Search", layout="wide")

# Initialize session state variables
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'user_id' not in st.session_state:
    st.session_state.user_id = 'UniqueUserIdentifier'
if 'search_filter' not in st.session_state:
    st.session_state.search_filter = {}
if 'results' not in st.session_state:
    st.session_state.results = []
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 1
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# Streamlit UI
st.title("Real Estate Property Search")

# API Key and User ID input
st.sidebar.header("API Configuration")
api_key = st.sidebar.text_input("Enter your API key", type="password", value=st.session_state.api_key)
user_id = st.sidebar.text_input("Enter your User ID", value=st.session_state.user_id)
if st.sidebar.button("Save API Key"):
    st.session_state.api_key = api_key
    st.session_state.user_id = user_id
    st.success("API Key and User ID saved!")

# Set API key and User ID from session state
if api_key:
    st.session_state.api_key = api_key
if user_id:
    st.session_state.user_id = user_id

# Search parameters
st.sidebar.header("Search Parameters")

# Collecting search criteria
address = st.sidebar.text_input("Address")
city = st.sidebar.text_input("City")
state = st.sidebar.text_input("State")
zip_code = st.sidebar.text_input("ZIP")
property_type = st.sidebar.selectbox("Property Type", ["", "residential", "commercial"])
beds_min = st.sidebar.number_input("Min Bedrooms", min_value=0, step=1)
beds_max = st.sidebar.number_input("Max Bedrooms", min_value=0, step=1)

# Search button logic
if st.sidebar.button("Search Properties"):
    params = {}
    if address: params["address"] = address
    if city: params["city"] = city
    if state: params["state"] = state
    if zip_code: params["zip"] = zip_code
    if property_type: params["property_type"] = property_type
    if beds_min != 0: params["beds_min"] = beds_min
    if beds_max != 0: params["beds_max"] = beds_max

    # Store the search parameters in session state
    st.session_state.search_filter = params

    # Fetch the first page of results
    st.session_state.results = get_page_of_properties(params, result_index=0)
    if st.session_state.results and 'resultCount' in st.session_state.results:
        total_results = st.session_state.results['resultCount']
        records_per_page = len(st.session_state.results.get('data', []))
        st.session_state.total_pages = (total_results + records_per_page - 1) // records_per_page
        st.session_state.current_page = 1
        st.write(f"Total Results Found: {total_results}")

# Display results
if st.session_state.results:
    properties = st.session_state.results.get('data', [])
    
    display_data = []

    # Extracting and formatting all data
    for prop in properties:
        flattened_prop = {}
        for key, value in prop.items():
            if isinstance(value, dict):
                flattened_prop.update({f"{key}_{sub_key}": sub_value for sub_key, sub_value in value.items()})
            else:
                flattened_prop[key] = value

        display_data.append(flattened_prop)
        
    df = pd.DataFrame(display_data)
    
    # Check specifically if DataFrame is empty
    if not df.empty:
        # Using Ag-Grid to display data
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
        gb.configure_side_bar()  # Enable sidebar for pivot and other options.
        gb.configure_default_column(
            resizable=True,
            auto_size_mode="max",
            wrap_text=True,
            filterable=True,
            pivotable=True,
            enableRowGroup=True,
            enableValue=True
        )

        # Enable filtering for each column and allow them to be used in pivots and groups
        for col in df.columns:
            gb.configure_column(col, filter=True)

        gridOptions = gb.build()

        AgGrid(
            df,
            gridOptions=gridOptions,
            height=600,  # Increase height, as pivot tables can take up more space
            fit_columns_on_grid_load=False,  # Disable automatic column fit, allowing horizontal scroll
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            enable_enterprise_modules=True,  # Ensure enterprise features are enabled
        )

# Debug: Display constructed API call
st.header("Constructed API Call Debugging Info")
if 'search_filter' in st.session_state:
    payload = {
        "count": False,
        "size": 10,
        "resultIndex": (st.session_state.current_page - 1) * 10,
        **st.session_state.search_filter
    }
    formatted_payload = json.dumps(payload, indent=4)
    st.code(f"""
    import requests

    url = "https://api.realestateapi.com/v2/PropertySearch"
    headers = {{
        "accept": "application/json",
        "content-type": "application/json",
        "x-user-id": "{st.session_state.user_id}",
        "x-api-key": "{st.session_state.api_key}"
    }}
    payload = {formatted_payload}

    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    """)