from enum import Enum

import pandas as pd
import plotly.express as px
import streamlit as st
from holidays.countries import Poland


class Types(Enum):
    STRING = "str"
    DOUBLE = "float64"


class TrafficColumn(Enum):
    BRIGADE = "Brygada"
    VEHICLE_NO = "Numer pojazdu"
    DELAY = "Opóźnienie"
    OUTSIDE = "Poza trasą"
    TIMESTAMP = "Timestamp"
    IS_HOLIDAY = "Święto"


class WeatherColumn(Enum):
    TEMPERATURE = "Temperatura"
    WIND_SPEED = "Prędkość wiatru"
    HUMIDITY = "Wilgotność względna"
    RAINFALL = "Suma opadu"
    PRESSURE = "Ciśnienie"
    TIMESTAMP = "timestamp"
    IS_HOLIDAY = "Święto"


class Metric(Enum):
    MEAN = "Średnia"
    MEDIAN = "Mediana"
    STD_DEV = "Odchylenie standardowe"
    Q1 = "1 kwantyl"
    Q3 = "3 kwantyl"
    COUNT = "Ilość"


traffic_df = pd.read_csv("data/traffic/delays-merged.csv")
traffic_df.rename(
    columns={
        "Brigade": TrafficColumn.BRIGADE.value,
        "Vehicle No": TrafficColumn.VEHICLE_NO.value,
        "Delay": TrafficColumn.DELAY.value,
        "Outside": TrafficColumn.OUTSIDE.value,
    },
    inplace=True
)

weather_df = pd.read_csv(
    "data/weather/weather-merged.csv",
    dtype={
        "temperatura": Types.DOUBLE.value,
        "predkosc_wiatru": Types.DOUBLE.value,
        "wilgotnosc_wzgledna": Types.DOUBLE.value,
        "suma_opadu": Types.DOUBLE.value,
        "cisnienie": Types.DOUBLE.value,
        "timestamp": Types.STRING.value
    },
    usecols=lambda col: col not in ("id_stacji", "stacja", "kierunek_wiatru")
)
weather_df.rename(
    columns={
        "temperatura": WeatherColumn.TEMPERATURE.value,
        "predkosc_wiatru": WeatherColumn.WIND_SPEED.value,
        "wilgotnosc_wzgledna": WeatherColumn.HUMIDITY.value,
        "suma_opadu": WeatherColumn.RAINFALL.value,
        "cisnienie": WeatherColumn.PRESSURE.value,
    },
    inplace=True
)

traffic_df[TrafficColumn.TIMESTAMP.value] = pd.to_datetime(traffic_df[TrafficColumn.TIMESTAMP.value])
weather_df[WeatherColumn.TIMESTAMP.value] = pd.to_datetime(weather_df[WeatherColumn.TIMESTAMP.value])

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


def calculate_traffic_metrics(group: pd.DataFrame) -> pd.Series:
    return pd.Series({
        Metric.MEAN.value: group[TrafficColumn.DELAY.value].mean(),
        Metric.MEDIAN.value: group[TrafficColumn.DELAY.value].median(),
        Metric.STD_DEV.value: group[TrafficColumn.DELAY.value].std(),
        Metric.Q1.value: group[TrafficColumn.DELAY.value].quantile(0.25),
        Metric.Q3.value: group[TrafficColumn.DELAY.value].quantile(0.75),
        Metric.COUNT.value: group[TrafficColumn.DELAY.value].count(),
    })


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
