from pathlib import Path

import mysql.connector
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "sample"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "app_user",
    "password": "app_password",
    "database": "broadcasting_db",
}


TABLE_FILE_MAPPING = {
    "vendors": "vendors.csv",
    "devices": "devices.csv",
    "content_metadata": "content_metadata.csv",
    "workflow_events": "workflow_events.csv",
}


def get_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def get_source_count(file_name: str) -> int:
    file_path = DATA_DIR / file_name
    df = pd.read_csv(file_path)
    return len(df)


def get_target_count(table_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return int(result)


def clear_old_reconciliation() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE reconciliation_summary;")

    conn.commit()
    cursor.close()
    conn.close()


def insert_reconciliation_result(
    table_name: str,
    source_count: int,
    target_count: int,
) -> None:
    mismatch_count = abs(source_count - target_count)
    status = "MATCHED" if mismatch_count == 0 else "MISMATCHED"

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO reconciliation_summary
        (table_name, source_count, target_count, mismatch_count, status)
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            table_name,
            source_count,
            target_count,
            mismatch_count,
            status,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()


def run_reconciliation() -> None:
    print("Starting reconciliation checks...")

    clear_old_reconciliation()

    for table_name, file_name in TABLE_FILE_MAPPING.items():
        source_count = get_source_count(file_name)
        target_count = get_target_count(table_name)

        insert_reconciliation_result(
            table_name=table_name,
            source_count=source_count,
            target_count=target_count,
        )

        status = "MATCHED" if source_count == target_count else "MISMATCHED"

        print(
            f"{table_name}: source={source_count}, "
            f"target={target_count}, status={status}"
        )

    print("Reconciliation completed.")


if __name__ == "__main__":
    run_reconciliation()