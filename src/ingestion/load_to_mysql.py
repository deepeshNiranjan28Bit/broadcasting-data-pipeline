from pathlib import Path

import pandas as pd
import mysql.connector


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "sample"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "app_user",
    "password": "app_password",
    "database": "broadcasting_db",
}


def get_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def truncate_tables() -> None:
    tables = [
        "workflow_events",
        "content_metadata",
        "devices",
        "vendors",
        "validation_errors",
        "reconciliation_summary",
    ]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table};")
        print(f"Truncated table: {table}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    conn.commit()
    cursor.close()
    conn.close()


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.where(pd.notnull(df), None)


def load_vendors() -> None:
    df = pd.read_csv(DATA_DIR / "vendors.csv")
    df = clean_dataframe(df)

    query = """
        INSERT INTO vendors
        (vendor_id, vendor_name, vendor_type, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """

    records = df[
        ["vendor_id", "vendor_name", "vendor_type", "is_active", "created_at"]
    ].values.tolist()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, records)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Loaded {len(records)} rows into vendors")


def load_devices() -> None:
    df = pd.read_csv(DATA_DIR / "devices.csv")
    df = clean_dataframe(df)

    query = """
        INSERT INTO devices
        (device_id, vendor_id, device_type, whitelisted, region, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    records = df[
        ["device_id", "vendor_id", "device_type", "whitelisted", "region", "created_at"]
    ].values.tolist()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, records)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Loaded {len(records)} rows into devices")


def load_content_metadata() -> None:
    df = pd.read_csv(DATA_DIR / "content_metadata.csv")
    df = clean_dataframe(df)

    query = """
        INSERT INTO content_metadata
        (content_id, vendor_id, title, language, category, duration_sec, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    records = df[
        [
            "content_id",
            "vendor_id",
            "title",
            "language",
            "category",
            "duration_sec",
            "created_at",
        ]
    ].values.tolist()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, records)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Loaded {len(records)} rows into content_metadata")


def load_workflow_events() -> None:
    df = pd.read_csv(DATA_DIR / "workflow_events.csv")
    df = clean_dataframe(df)

    query = """
        INSERT INTO workflow_events
        (event_id, workflow_id, vendor_id, device_id, content_id, status, event_time, source_system)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    records = df[
        [
            "event_id",
            "workflow_id",
            "vendor_id",
            "device_id",
            "content_id",
            "status",
            "event_time",
            "source_system",
        ]
    ].values.tolist()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, records)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Loaded {len(records)} rows into workflow_events")


def main() -> None:
    print("Starting MySQL data load...")

    truncate_tables()

    load_vendors()
    load_devices()
    load_content_metadata()
    load_workflow_events()

    print("MySQL data load completed.")


if __name__ == "__main__":
    main()