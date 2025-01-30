import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression

from holiday_analysis import delay_stats_df
from util import load_traffic_data, load_weather_data, WeatherColumn, TrafficColumn, Metric

traffic_df = load_traffic_data()
weather_df = load_weather_data()

merged_df = pd.merge(
    weather_df, traffic_df,
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="left",
    validate="1:m"
)

selected_category = st.selectbox(
    "Kategoria",
    [
        TrafficColumn.VEHICLE_NO.value,
        TrafficColumn.BRIGADE.value
    ]
)
selected_metric = st.selectbox(
    "Metryka",
    [e.value for e in Metric]
)
unique_values = merged_df[selected_category].unique()
selected_value = st.selectbox(
    selected_category,
    unique_values
)

filtered_df = merged_df[merged_df[selected_category] == selected_value]

if filtered_df.empty:
    st.write(f"No data available for {selected_category} {selected_value}")
else:
    X = filtered_df[[
        WeatherColumn.TEMPERATURE.value,
        WeatherColumn.WIND_SPEED.value,
        WeatherColumn.HUMIDITY.value,
        WeatherColumn.RAINFALL.value,
        WeatherColumn.PRESSURE.value
    ]]
    y = delay_stats_df[selected_metric]

    model = LinearRegression()
    model.fit(X, y)
    predictions = model.predict(X)

    fig = px.line(
        x=filtered_df[WeatherColumn.TIMESTAMP.value],
        y=predictions,
        title=f"Prognoza opóźnień dla {selected_category} {selected_value}",
        labels={WeatherColumn.TIMESTAMP.value: "Czas", "y": "Opóźnienie"}
    )
    st.plotly_chart(fig)
