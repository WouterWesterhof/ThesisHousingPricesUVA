import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd 
import pandas as pd
import numpy as np
import json

px.set_mapbox_access_token("pk.eyJ1Ijoid3dlc3RlcmhvZiIsImEiOiJjbTc2aHJ2Ym0weWYxMmlxeWlpcTd1NHJ0In0.qD769Z26XQLQ1-3cwqHIuw")

@st.cache_data
def load_data():
    data_scatter = pd.read_csv('utrecht_map.csv')
    data_buurt = pd.read_csv('buurt_U_map.csv')

    return data_scatter, data_buurt

@st.cache_data
def load_geojson():
    with open("polygons_neigborhoods_Utrecht.json", "r") as openfile:
        return json.load(openfile)


def style_slider():
    """Applies consistent gradient styling to the slider track and handle."""
    color_scale = ["#fff5f0", "#fc9272", "#de2d26"]  # Light -> Medium -> Dark Blue (Blues in Plotly)
    slider_color_gradient = f"linear-gradient(90deg, {color_scale[0]}, {color_scale[1]}, {color_scale[2]})"


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


def woz_slider(location_data, woz_column):
    """Creates a slider to filter WOZ values and returns the selected range."""

    # Ensure WOZ values are numeric
    location_data[woz_column] = pd.to_numeric(location_data[woz_column], errors="coerce")

    min_val = float(location_data[woz_column].min())
    max_val = float(location_data[woz_column].max())

    # Create slider for WOZ value selection
    selected_range = st.slider(
        "Select WOZ value range:",
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val),
    )

    # Return filtered data
    return location_data[(location_data[woz_column] >= selected_range[0]) & 
                         (location_data[woz_column] <= selected_range[1])]



def display_map(scatter_data: pd.DataFrame, selected_variables, buurt_data, buurt_json):
    woz = selected_variables[0]
    m2 = selected_variables[1]
    precentage = selected_variables[2]


    # Apply slider and filter the data
    filtered_data = woz_slider(scatter_data, woz)


    # Create base figure
    fig = go.Figure()
    
    # Scatter Layer
    scatter_layer = go.Scattermapbox(
        lat=filtered_data["latitude"],
        lon=filtered_data["longitude"],
        mode="markers",
        marker=dict(
            size=4,
            color=filtered_data[woz],
            colorscale="Reds",
            opacity=0.6,
            showscale=False,
            colorbar=dict(title="WOZ Value (€)")
        ),
        customdata=scatter_data[["buurt", woz, m2, precentage]].values,
        hovertemplate =(
            "<b>Buurt: %{customdata[0]}<br>" +
            "<b>WOZ Value: %{customdata[1]}<br>" +
            "<b>WOZ/(m²): %{customdata[2]}<br>"
            "<b>Procentuele stijging WOZ: %{customdata[3]}<extra></extra>"
        ),
        name="Scatter Properties",   # Legend entry for scatter layer
        showlegend=True 
    )

     

    # Create a copy of the selected columns
    custom_data = buurt_data[["regio", woz, "g_ink_pi", "g_ele", "bev_dich"]].copy()
    custom_data[[woz, "g_ink_pi", "g_ele", "bev_dich"]] = custom_data[[woz, "g_ink_pi", "g_ele", "bev_dich"]].round(2)
    custom_data_array = custom_data.values

    # Choropleth Layer
    choropleth_layer = go.Choroplethmapbox(
        geojson=buurt_json,
        locations=buurt_data["gwb_code"],
        z=np.log1p(buurt_data[woz]),
        colorscale="Blues",
        colorbar=dict(title="WOZ value (Log-scaled)"),
        featureidkey="properties.buurtcode",
        marker_opacity=0.5,
        customdata=custom_data_array,  # Assign custom data here
        hovertemplate=(
            "Buurt name: %{customdata[0]}<br>" +
            "Average WOZ (x1000): %{customdata[1]}<br>" +
            "Average income: %{customdata[2]}<br>" +
            "Electricity consumption: %{customdata[3]}<br>" +
            "Population density: %{customdata[4]}<extra></extra>"
        ),
        name="Neighborhood Layer",   # Legend entry for choropleth layer
        showlegend=True  
    )

    # Add traces to your figure
    fig.add_trace(scatter_layer)
    fig.add_trace(choropleth_layer)

    center_lat = filtered_data["latitude"].mean()
    center_lon = filtered_data["longitude"].mean()

    # Layout Configuration
    fig.update_layout(
            legend=dict(
            title="Layers",
            orientation="h",  # Horizontal legend (or use "v" for vertical)
            x=0,
            y=1
        ),
        mapbox_style="carto-positron",
        mapbox_zoom=10,
        mapbox_center={"lat": center_lat, "lon": center_lon},  # Centered on Utrecht
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )


    return fig




def main():
   
    style_slider()
   
    # Load Data Efficiently (Cached)
    data_scatter, data_buurt = load_data()
    json_poly_buurt = load_geojson()
    

    # Mapping of display names to actual column names
    variable_mapping = {
        "WOZ Value (2023)": "woz_2023", 
        "WOZ Value (2024)*": "woz_2024",
        "WOZ Value (2025)**": "woz_2025",        
        "WOZ Value (2026)**": "woz_2026",
    }

    # Select variable for color mapping
    selected_display_name = st.selectbox(
        "Choose a year to display:",
        list(variable_mapping.keys()),
        index=0,
        key="utrecht_map_year"
    )

    # Convert display name back to actual column name
    selected_variable = variable_mapping[selected_display_name]

    # Give more then one variable to the years:
    # Map selected variable to extra columns
    selected_variables = {
        "woz_2023": ["woz_2023", "woz/m2_23", "act_woz_incr"],
        "woz_2024": ["woz_2024", "woz/m2_24", "pred_change_24"],
        "woz_2025": ["woz_2025", "woz/m2_25", "pred_change_25"],
        "woz_2026": ["woz_2026", "woz/m2_26", "pred_change_26"],
    }[selected_variable]

    
    px_map = display_map(data_scatter, selected_variables, data_buurt, json_poly_buurt)
    
    st.plotly_chart(px_map, use_container_width=True)




main()
