import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

from util import load_traffic_data, load_weather_data, WeatherColumn, TrafficColumn, Metric, calculate_delay_stats

traffic_df = load_traffic_data()
traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df = load_weather_data()
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

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
    ],
)
selected_metric = st.selectbox(
    "Metryka",
    [
        Metric.MEAN.value,
        Metric.COUNT.value,
    ]
)
unique_values = merged_df[selected_category].dropna().unique()
unique_values.sort()
selected_value = st.selectbox(
    selected_category,
    unique_values,
)

filtered_df = merged_df[merged_df[selected_category] == selected_value]

delay_stats = calculate_delay_stats(traffic_df)
delay_stats = delay_stats[delay_stats[TrafficColumn.TIMESTAMP.value].isin(filtered_df[WeatherColumn.TIMESTAMP.value])]
merged_filtered_df = pd.merge(
    filtered_df,
    delay_stats[[TrafficColumn.TIMESTAMP.value, selected_metric]],
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="inner",
    validate="m:1"
)

X = merged_filtered_df[[
    WeatherColumn.TEMPERATURE.value,
    WeatherColumn.WIND_SPEED.value,
    WeatherColumn.HUMIDITY.value,
    WeatherColumn.RAINFALL.value,
    WeatherColumn.PRESSURE.value
]]
y = merged_filtered_df[selected_metric]

model = LinearRegression()
model.fit(X, y)

predictions = model.predict(X)
prediction_dates = merged_filtered_df[WeatherColumn.TIMESTAMP.value]

plot_df = pd.DataFrame({
    "Timestamp": prediction_dates,
    "Actual": y,
    "Predicted": predictions
})

trend_line = model.intercept_ + model.coef_[0] * X[WeatherColumn.TEMPERATURE.value].mean()

fig = px.line(
    plot_df,
    x="Timestamp",
    y=["Actual", "Predicted"],
    title=f"Delay Prediction for: {selected_category} {selected_value} (December)",
)
fig.update_layout(
    xaxis_title="Time",
    yaxis_title=f"{TrafficColumn.DELAY.value}: {selected_metric}",
)

fig.add_trace(
    go.Scatter(
        x=plot_df["Timestamp"],
        y=[trend_line] * len(plot_df),
        mode="lines",
        name="Trend",
        line=dict(color="red")
    )
)

st.plotly_chart(fig)
