import pandas as pd
import plotly.express as px
import streamlit as st

from util import TrafficColumn, WeatherColumn, Metric, calculate_traffic_metrics, load_traffic_data, load_weather_data

traffic_df = load_traffic_data()
weather_df = load_weather_data()

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

# ============================== TRAFFIC CATEGORIES ==============================
traffic_groups = [
    TrafficColumn.VEHICLE_NO.value,
    TrafficColumn.BRIGADE.value,
    TrafficColumn.OUTSIDE.value,
    TrafficColumn.DAY_TYPE.value
]

selected_traffic_group = st.selectbox("Kategoria", traffic_groups)
selected_traffic_metric = st.selectbox("Metryka", [e.value for e in Metric])

traffic_metrics_df = (traffic_df
                      .groupby(selected_traffic_group)[[TrafficColumn.DELAY.value]]
                      .apply(calculate_traffic_metrics)
                      .reset_index())

fig = px.bar(
    traffic_metrics_df,
    x=selected_traffic_group,
    y=selected_traffic_metric,
    title=f"{selected_traffic_metric.replace('_', ' ').title()} w kategorii: {selected_traffic_group}",
)
fig.update_layout(
    xaxis_type="category",
    yaxis_title="Opóźnienie (min)"
)
st.plotly_chart(fig)
# ===============================================================================
