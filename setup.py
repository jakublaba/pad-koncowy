from csv_download import download_all_csvs
from merge_traffic import merge_traffic
from merge_weather import merge_weather

CONTAINERS = "gtfs", "traffic", "weather"

if __name__ == '__main__':
    for container in CONTAINERS:
        download_all_csvs(container, f"data/{container}")

    merge_traffic()
    merge_weather()
