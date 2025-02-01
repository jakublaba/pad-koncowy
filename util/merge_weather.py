import glob
import os

import pandas as pd


def merge_weather():
    path = "data/weather/"

    all_files = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)

    df_from_each_file = [pd.read_csv(f) for f in all_files]

    weather = pd.concat(df_from_each_file, ignore_index=True) if df_from_each_file else pd.DataFrame()

    weather["data_pomiaru"] = pd.to_datetime(weather["data_pomiaru"])
    weather["godzina_pomiaru"] = weather["godzina_pomiaru"].astype(str).str.zfill(2) + ":00:00"
    weather.dropna(subset=["data_pomiaru", "godzina_pomiaru"], inplace=True)
    weather["timestamp"] = pd.to_datetime(weather["data_pomiaru"].astype(str) + " " + weather["godzina_pomiaru"])

    weather.drop(columns=["data_pomiaru", "godzina_pomiaru"], inplace=True)

    weather["temperatura"] = pd.to_numeric(weather["temperatura"], errors="coerce")
    weather["predkosc_wiatru"] = pd.to_numeric(weather["predkosc_wiatru"], errors="coerce")
    weather["wilgotnosc_wzgledna"] = pd.to_numeric(weather["wilgotnosc_wzgledna"], errors="coerce")
    weather["suma_opadu"] = pd.to_numeric(weather["suma_opadu"], errors="coerce")
    weather["cisnienie"] = pd.to_numeric(weather["cisnienie"], errors="coerce")

    weather.drop_duplicates(inplace=True)
    weather.to_csv("data/weather/weather-merged.csv", index=False)
