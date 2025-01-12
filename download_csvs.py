from utils import download_all_csvs

CONTAINERS = "gtfs", "traffic", "weather"


if __name__ == '__main__':
    for container in CONTAINERS:
        download_all_csvs(container, f"data/{container}")
