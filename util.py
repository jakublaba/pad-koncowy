from enum import Enum

import numpy as np
import pandas as pd


class Type(Enum):
    STRING = "str"
    DOUBLE = "float64"
    BOOL = "bool"


class TrafficColumn(Enum):
    BRIGADE_OG = "Brigade"
    BRIGADE = "Brygada"
    VEHICLE_NO_OG = "Vehicle No"
    VEHICLE_NO = "Numer pojazdu"
    DELAY_OG = "Delay"
    DELAY = "Opóźnienie"
    OUTSIDE_OG = "Outside"
    OUTSIDE = "Poza trasą"
    TIMESTAMP = "Timestamp"
    IS_HOLIDAY = "Święto"


class WeatherColumn(Enum):
    TEMPERATURE_OG = "temperatura"
    TEMPERATURE = "Temperatura"
    WIND_SPEED_OG = "predkosc_wiatru"
    WIND_SPEED = "Prędkość wiatru"
    HUMIDITY_OG = "wilgotnosc_wzgledna"
    HUMIDITY = "Wilgotność względna"
    RAINFALL_OG = "suma_opadu"
    RAINFALL = "Suma opadu"
    PRESSURE_OG = "cisnienie"
    PRESSURE = "Ciśnienie"
    TIMESTAMP = "timestamp"
    IS_HOLIDAY = "Święto"


class Metric(Enum):
    MEAN = "Średnia"
    MEDIAN = "Mediana"
    STD_DEV = "Odchylenie standardowe"
    Q1 = "25 centyl"
    Q3 = "75 centyl"
    COUNT = "Ilość"


def load_traffic_data() -> pd.DataFrame:
    traffic_df = pd.read_csv(
        "data/traffic/delays-merged.csv",
        dtype={
            TrafficColumn.VEHICLE_NO_OG.value: Type.STRING.value,
            TrafficColumn.BRIGADE_OG.value: Type.STRING.value,
            TrafficColumn.DELAY_OG.value: Type.DOUBLE.value,
            TrafficColumn.OUTSIDE_OG.value: Type.BOOL.value,
        },
        usecols=lambda col: col in [e.value for e in TrafficColumn if "OG" in e.name] + [TrafficColumn.TIMESTAMP.value]
    )
    traffic_df.rename(
        columns={
            TrafficColumn.VEHICLE_NO_OG.value: TrafficColumn.VEHICLE_NO.value,
            TrafficColumn.BRIGADE_OG.value: TrafficColumn.BRIGADE.value,
            TrafficColumn.DELAY_OG.value: TrafficColumn.DELAY.value,
            TrafficColumn.OUTSIDE_OG.value: TrafficColumn.OUTSIDE.value,
        },
        inplace=True
    )
    return traffic_df


def load_weather_data() -> pd.DataFrame:
    weather_df = pd.read_csv(
        "data/weather/weather-merged.csv",
        dtype={
            WeatherColumn.TEMPERATURE_OG.value: Type.DOUBLE.value,
            WeatherColumn.WIND_SPEED_OG.value: Type.DOUBLE.value,
            WeatherColumn.HUMIDITY_OG.value: Type.DOUBLE.value,
            WeatherColumn.RAINFALL_OG.value: Type.DOUBLE.value,
            WeatherColumn.PRESSURE_OG.value: Type.DOUBLE.value,
            WeatherColumn.TIMESTAMP.value: Type.STRING.value
        },
        usecols=lambda col: col not in ("id_stacji", "stacja", "kierunek_wiatru")
    )
    weather_df.rename(
        columns={
            WeatherColumn.TEMPERATURE_OG.value: WeatherColumn.TEMPERATURE.value,
            WeatherColumn.WIND_SPEED_OG.value: WeatherColumn.WIND_SPEED.value,
            WeatherColumn.HUMIDITY_OG.value: WeatherColumn.HUMIDITY.value,
            WeatherColumn.RAINFALL_OG.value: WeatherColumn.RAINFALL.value,
            WeatherColumn.PRESSURE_OG.value: WeatherColumn.PRESSURE.value,
        },
        inplace=True
    )
    return weather_df


def calculate_delay_stats(traffic: pd.DataFrame) -> pd.DataFrame:
    delay_stats_df = traffic.groupby(TrafficColumn.TIMESTAMP.value)[TrafficColumn.DELAY.value].agg(
        mean=np.mean,
        median=np.median,
        std_dev=np.std,
        q1=lambda x: np.quantile(x, 0.25),
        q3=lambda x: np.quantile(x, 0.75),
        count="count"
    ).reset_index()
    delay_stats_df.rename(
        columns={
            "mean": Metric.MEAN.value,
            "median": Metric.MEDIAN.value,
            "std_dev": Metric.STD_DEV.value,
            "q1": Metric.Q1.value,
            "q3": Metric.Q3.value,
            "count": Metric.COUNT.value
        },
        inplace=True
    )
    return delay_stats_df


def calculate_traffic_metrics(group: pd.DataFrame) -> pd.Series:
    return pd.Series({
        Metric.MEAN.value: group[TrafficColumn.DELAY.value].mean(),
        Metric.MEDIAN.value: group[TrafficColumn.DELAY.value].median(),
        Metric.STD_DEV.value: group[TrafficColumn.DELAY.value].std(),
        Metric.Q1.value: group[TrafficColumn.DELAY.value].quantile(0.25),
        Metric.Q3.value: group[TrafficColumn.DELAY.value].quantile(0.75),
        Metric.COUNT.value: group[TrafficColumn.DELAY.value].count(),
    })
