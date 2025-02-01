import os
from datetime import datetime, timedelta
from typing import List

import pandas as pd


def _file_paths(base_dir: str, start_date: datetime, end_date: datetime) -> List[str]:
    paths = []
    current_date = start_date
    while current_date <= end_date:
        paths.append(f"{base_dir}/{current_date.strftime('%Y/%m/%d/delays-%H.csv')}")
        current_date += timedelta(hours=1)
    return list(filter(os.path.exists, paths))


def _normalize_brigade(brigade: str) -> str:
    return str(int(float(brigade))) if brigade.isdigit() or brigade.replace(".0", "").isdigit() else brigade


def _normalize_delay(delay: str) -> int:
    return -int(delay.split()[0]) if "przed czasem" in delay else int(delay.split()[0])


def _normalize_outside(outside) -> bool:
    return pd.notna(outside)


def merge_traffic():
    paths = _file_paths(
        "../data/traffic",
        datetime(2024, 12, 8, 0, 0),
        datetime(2025, 1, 2, 23)
    )

    df = pd.read_csv(paths[0])
    for path in paths[1:]:
        df = pd.concat([df, pd.read_csv(path)])
    df.drop_duplicates(inplace=True)

    df["Brigade"] = df["Brigade"].astype(str).apply(_normalize_brigade)
    df["Delay"] = df["Delay"].apply(_normalize_delay)
    df["Outside"] = df["Outside"].apply(_normalize_outside)

    df.to_csv("data/traffic/delays-merged.csv", index=False)
