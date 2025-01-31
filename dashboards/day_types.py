import pandas as pd
import plotly.express as px
import streamlit as st
from holidays.countries import Poland

from util import load_traffic_data, load_weather_data, TrafficColumn, WeatherColumn, calculate_delay_stats, DayType, \
    Metric

traffic_df = load_traffic_data()
weather_df = load_weather_data()

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value]).dt.floor("h")
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

# ============================== CORRELATION MATRIX ==============================
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
# ================================================================================

# ============================== DELAY STATS =====================================
start_date = min(
    traffic_df[TrafficColumn.TIMESTAMP.value].min(),
    weather_df[WeatherColumn.TIMESTAMP.value].min()
)
end_date = max(
    traffic_df[TrafficColumn.TIMESTAMP.value].max(),
    weather_df[WeatherColumn.TIMESTAMP.value].max()
)

pl_holidays = [
    pd.Timestamp(date) for date in
    Poland(years=range(start_date.year, end_date.year + 1))
]


def get_day_type(date):
    date = pd.Timestamp(date)
    if date in pl_holidays:
        return DayType.HOLIDAY.value
    elif date.weekday() >= 5:
        return DayType.WEEKEND.value
    else:
        return DayType.WEEKDAY.value


traffic_df[TrafficColumn.DAY_TYPE.value] = traffic_df[TrafficColumn.TIMESTAMP.value].dt.date.apply(get_day_type)
weather_df[WeatherColumn.DAY_TYPE.value] = weather_df[WeatherColumn.TIMESTAMP.value].dt.date.apply(get_day_type)

weather_holiday_analysis = {
    Metric.MEAN.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).mean().reset_index(),
    Metric.MEDIAN.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).median().reset_index(),
    Metric.STD_DEV.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).std().reset_index(),
    Metric.Q1.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).quantile(0.25).reset_index(),
    Metric.Q3.value: weather_df.groupby(WeatherColumn.DAY_TYPE.value).quantile(0.75).reset_index(),
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
        WeatherColumn.DAY_TYPE.value,
        selected_weather_param
    ]],
    x=WeatherColumn.DAY_TYPE.value,
    y=selected_weather_param,
    title=f"{selected_weather_metric} dla parametru: {selected_weather_param}",
)

st.plotly_chart(avg_weather_params_fig)
# ================================================================================

# ============================== GLOBAL DELAY STATS ==============================
delay_stats = {
    Metric.MEAN.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].mean().reset_index(),
    Metric.MEDIAN.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[
        TrafficColumn.DELAY.value].median().reset_index(),
    Metric.STD_DEV.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[
        TrafficColumn.DELAY.value].std().reset_index(),
    Metric.Q1.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].quantile(
        0.25).reset_index(),
    Metric.Q3.value: traffic_df.groupby(TrafficColumn.DAY_TYPE.value)[TrafficColumn.DELAY.value].quantile(
        0.75).reset_index(),
}

selected_delay_stat = st.selectbox(
    "Metryka",
    [e.value for e in Metric]
)

delay_stats_fig = px.bar(
    delay_stats[selected_delay_stat],
    x=TrafficColumn.DAY_TYPE.value,
    y=TrafficColumn.DELAY.value,
    title=f"{selected_delay_stat} opóźnień dla różnych typów dni",
    labels={TrafficColumn.DAY_TYPE.value: "Typ dnia", TrafficColumn.DELAY.value: "Opóźnienie (minuty)"}
)

st.plotly_chart(delay_stats_fig)
# ================================================================================
