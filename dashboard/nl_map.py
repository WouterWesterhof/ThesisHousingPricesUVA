import streamlit as st
import geopandas as gpd
import plotly.express as px
import pydeck as pdk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go


px.set_mapbox_access_token("pk.eyJ1Ijoid3dlc3RlcmhvZiIsImEiOiJjbTc2aHJ2Ym0weWYxMmlxeWlpcTd1NHJ0In0.qD769Z26XQLQ1-3cwqHIuw")



@st.cache_data
def load_data():
    data = pd.read_csv('NL_map.csv')

    return data

@st.cache_data
def load_geojson():
    with open("polygons_neigborhoods_CBS.json", "r") as openfile:
        return json.load(openfile)



def style_slider():
    """Applies consistent gradient styling to the slider track and handle."""
    viridis_colors = ["#440154", "#31688E", "#35B779", "#FDE725"]  # Viridis color scheme
    slider_color_gradient = f"linear-gradient(90deg, {viridis_colors[0]}, {viridis_colors[1]}, {viridis_colors[2]}, {viridis_colors[3]})"


    st.markdown(
        f"""
        <style>
        div[data-baseweb="slider"] {{
            background: {slider_color_gradient};
            padding: 5px;
            border-radius: 5px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )




def slider(data, column, label_prefix="Select range for", key=None):
    """
    Create a slider with a unique key and filter the DataFrame.
    """
    min_val = float(data[column].min())
    max_val = float(data[column].max())

    # If the column has only one unique value, show a message and skip the slider
    if min_val == max_val:
        st.warning(
            f"Column '{column}' has a single value ({min_val}). "
            "Skipping slider."
        )
        return data  # Return unfiltered data in this case

    if key is None:
        key = f"{label_prefix}_{column}"
    selected_range = st.slider(
        f"{label_prefix} {column}:",
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val),
        key=key
    )
    return data[(data[column] >= selected_range[0]) & (data[column] <= selected_range[1])]


def display_map(selected_variables, price_map_var, additional_variable, data, json_poly_buurt):
    woz = selected_variables[0]
    precentage = selected_variables[1]

    # Filter by the price variable (woz) with a unique slider key.
    filtered_data = slider(data, price_map_var, label_prefix="Select range for", key=f"slider_{price_map_var}")
    
    # Filter by the additional variable with a different unique key.
    filtered_data = slider(filtered_data, additional_variable, label_prefix="Select range for", key=f"slider_{additional_variable}")


    filtered_data["log_price"] = np.log(filtered_data[price_map_var])

    fig = px.choropleth_map(filtered_data, 
                            geojson=json_poly_buurt, 
                            locations='gwb_code', # Same as buurtcode in JSON
                            color="log_price",
                            featureidkey="properties.buurtcode",  # Match JSON structure
                            color_continuous_scale="Blues",
                            range_color=[filtered_data["log_price"].min(), filtered_data["log_price"].max()],  # Keep scale fixed
                            zoom=7, 
                            center={"lat": 52.989, "lon": 5.621},  # Adjust for your region
                            opacity=0.6,
                            hover_data={"gwb_code": False,
                                        "regio": True,
                                        woz: True, 
                                        precentage: True,
                                        additional_variable: True}  # ✅ Show only relevant data
                            )
    

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig


def main():
    # Setup streamlit page to be wide by default
    st.set_page_config(layout='wide')
    st.header('Neighborhood Location Map')


    # Load Data Efficiently (Cached)
    data = load_data()
    json_poly_buurt = load_geojson()
    
    # Mapping of display names to actual column names
    variable_mapping = {
        "WOZ Value (2024)": "woz_2024", 
        "WOZ Value (2025)*": "woz_2025",
        "WOZ Value (2026)*": "woz_2026",        
    }

    # Select variable for color mapping
    selected_display_name = st.selectbox(
        "Choose a year to display:",
        list(variable_mapping.keys()),
        index=0,
        key="nl_map_year_select"
    )

    # Convert display name back to actual column name
    woz_year = variable_mapping[selected_display_name]

    # Map selected variable to extra columns
    selected_year_w_variables = {
        "woz_2024": ["woz_2024", "act_woz_incr"],
        "woz_2025": ["woz_2025", "pred_change_25"],
        "woz_2026": ["woz_2026", "pred_change_26"],
    }[woz_year]

    # Additional feature selection
    price_var = st.radio(
        "Select WOZ or price increase (%):",
        ("WOZ", "Price increase (%)")
    )    

    if price_var == "WOZ":
        price_map_var = selected_year_w_variables[0]
    else:
        price_map_var = selected_year_w_variables[1]


    # Additional feature selection
    additional_variable = st.radio(
        "Select additional variable to compare:",
        ("Average income per resident", "Energy consumption", "Population density")
    )    

    selected_additional_var = {
        "Average income per resident": "g_ink_pi",
        "Energy consumption": "g_ele",
        "Population density": "bev_dich",
    }[additional_variable]

    px_map = display_map(selected_year_w_variables, price_map_var, selected_additional_var, data, json_poly_buurt)

    st.plotly_chart(px_map, use_container_width=True)


main()





