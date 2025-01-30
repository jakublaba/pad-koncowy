import pandas as pd
import plotly.express as px
import streamlit as st
from holidays.countries import Poland

from util import TrafficColumn, WeatherColumn, load_traffic_data, load_weather_data, Metric, calculate_delay_stats, \
    calculate_traffic_metrics

traffic_df = load_traffic_data()
weather_df = load_weather_data()

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])
merged_df = pd.merge(
    weather_df, traffic_df,
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="left",
    validate="1:m"
)
delay_stats_df = calculate_delay_stats(traffic_df)
correlation_df = pd.merge(
    weather_df, delay_stats_df,
    left_on=WeatherColumn.TIMESTAMP.value,
    right_on=TrafficColumn.TIMESTAMP.value,
    how="left",
    validate="1:m"
)
correlation_matrix = correlation_df.corr()
correlation_fig = px.imshow(
    correlation_matrix,
    text_auto=True,
    aspect="auto",
    title="Macierz korelacji"
)
st.plotly_chart(correlation_fig)

start_date = min(
    traffic_df[TrafficColumn.TIMESTAMP.value].min(),
    weather_df[WeatherColumn.TIMESTAMP.value].min()
)
end_date = max(
    traffic_df[TrafficColumn.TIMESTAMP.value].max(),
    weather_df[WeatherColumn.TIMESTAMP.value].max()
)

pl_holidays = [
    date for date in
    Poland(years=range(start_date.year, end_date.year + 1))
    if start_date <= pd.Timestamp(date) <= end_date
]

traffic_df[TrafficColumn.IS_HOLIDAY.value] = traffic_df[TrafficColumn.TIMESTAMP.value].dt.date.isin(pl_holidays)
weather_df[WeatherColumn.IS_HOLIDAY.value] = weather_df[WeatherColumn.TIMESTAMP.value].dt.date.isin(pl_holidays)

weather_holiday_analysis = {
    Metric.MEAN.value: weather_df.groupby(WeatherColumn.IS_HOLIDAY.value).mean().reset_index(),
    Metric.MEDIAN.value: weather_df.groupby(WeatherColumn.IS_HOLIDAY.value).median().reset_index(),
    Metric.STD_DEV.value: weather_df.groupby(WeatherColumn.IS_HOLIDAY.value).std().reset_index(),
    Metric.Q1.value: weather_df.groupby(WeatherColumn.IS_HOLIDAY.value).quantile(0.25).reset_index(),
    Metric.Q3.value: weather_df.groupby(WeatherColumn.IS_HOLIDAY.value).quantile(0.75).reset_index(),
}

selected_weather_metric = st.selectbox(
    "Metryka",
    [e.value for e in Metric if e != Metric.COUNT]
)
selected_weather_param = st.selectbox(
    "Parametr pogody",
    [
        WeatherColumn.TEMPERATURE.value,
        WeatherColumn.WIND_SPEED.value,
        WeatherColumn.HUMIDITY.value,
        WeatherColumn.RAINFALL.value,
        WeatherColumn.PRESSURE.value,
    ]
)

avg_weather_params_fig = px.bar(
    weather_holiday_analysis[selected_weather_metric][[
        WeatherColumn.IS_HOLIDAY.value,
        selected_weather_param
    ]],
    x=WeatherColumn.IS_HOLIDAY.value,
    y=selected_weather_param,
    title=f"{selected_weather_metric} dla parametru: {selected_weather_param}",
)

st.plotly_chart(avg_weather_params_fig)

traffic_groups = [
    TrafficColumn.VEHICLE_NO.value,
    TrafficColumn.BRIGADE.value,
    TrafficColumn.OUTSIDE.value,
    TrafficColumn.IS_HOLIDAY.value
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
