from pathlib import Path
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker


fake = Faker()

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "sample"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VALID_STATUSES = ["INITIATED", "VALIDATED", "APPROVED", "REJECTED", "FAILED"]
CONTENT_CATEGORIES = ["Sports", "News", "Entertainment", "Movies", "Kids", "Music"]
LANGUAGES = ["Hindi", "English", "Tamil", "Telugu", "Marathi", "Bengali"]
REGIONS = ["North", "South", "East", "West", "Central"]
DEVICE_TYPES = ["SET_TOP_BOX", "SMART_TV", "MOBILE", "WEB"]


def generate_vendors(count: int = 100) -> pd.DataFrame:
    vendors = []

    for i in range(1, count + 1):
        vendors.append(
            {
                "vendor_id": f"V{i:04d}",
                "vendor_name": fake.company(),
                "vendor_type": random.choice(["CONTENT_PARTNER", "DEVICE_VENDOR", "DISTRIBUTION_PARTNER"]),
                "is_active": random.choice(["Y", "Y", "Y", "N"]),
                "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
            }
        )

    return pd.DataFrame(vendors)


def generate_devices(vendors_df: pd.DataFrame, count: int = 1000) -> pd.DataFrame:
    vendor_ids = vendors_df["vendor_id"].tolist()
    devices = []

    for i in range(1, count + 1):
        devices.append(
            {
                "device_id": f"D{i:06d}",
                "vendor_id": random.choice(vendor_ids),
                "device_type": random.choice(DEVICE_TYPES),
                "whitelisted": random.choice(["Y", "Y", "Y", "N"]),
                "region": random.choice(REGIONS),
                "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
            }
        )

    return pd.DataFrame(devices)


def generate_content_metadata(vendors_df: pd.DataFrame, count: int = 2000) -> pd.DataFrame:
    vendor_ids = vendors_df["vendor_id"].tolist()
    content_records = []

    for i in range(1, count + 1):
        content_records.append(
            {
                "content_id": f"C{i:06d}",
                "vendor_id": random.choice(vendor_ids),
                "title": fake.sentence(nb_words=4).replace(".", ""),
                "language": random.choice(LANGUAGES + [None]),
                "category": random.choice(CONTENT_CATEGORIES),
                "duration_sec": random.randint(60, 10800),
                "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
            }
        )

    return pd.DataFrame(content_records)


def generate_workflow_events(
    vendors_df: pd.DataFrame,
    devices_df: pd.DataFrame,
    content_df: pd.DataFrame,
    count: int = 10000,
) -> pd.DataFrame:
    vendor_ids = vendors_df["vendor_id"].tolist()
    device_ids = devices_df["device_id"].tolist()
    content_ids = content_df["content_id"].tolist()

    events = []
    start_time = datetime.now() - timedelta(days=30)

    for i in range(1, count + 1):
        event_time = start_time + timedelta(minutes=random.randint(1, 43200))

        events.append(
            {
                "event_id": f"E{i:08d}",
                "workflow_id": f"WF{random.randint(1, 3000):07d}",
                "vendor_id": random.choice(vendor_ids),
                "device_id": random.choice(device_ids),
                "content_id": random.choice(content_ids),
                "status": random.choice(VALID_STATUSES + ["UNKNOWN"]),
                "event_time": event_time,
                "source_system": random.choice(["VENDOR_PORTAL", "BROADCASTING_APP", "DEVICE_SERVICE"]),
            }
        )

    return pd.DataFrame(events)


def save_dataframe(df: pd.DataFrame, filename: str) -> None:
    output_path = OUTPUT_DIR / filename
    df.to_csv(output_path, index=False)
    print(f"Created {output_path} with {len(df)} rows")


def main() -> None:
    print("Generating synthetic broadcasting pipeline data...")

    vendors_df = generate_vendors(count=100)
    devices_df = generate_devices(vendors_df, count=1000)
    content_df = generate_content_metadata(vendors_df, count=2000)
    workflow_df = generate_workflow_events(vendors_df, devices_df, content_df, count=10000)

    save_dataframe(vendors_df, "vendors.csv")
    save_dataframe(devices_df, "devices.csv")
    save_dataframe(content_df, "content_metadata.csv")
    save_dataframe(workflow_df, "workflow_events.csv")

    print("Synthetic data generation completed.")


if __name__ == "__main__":
    main()