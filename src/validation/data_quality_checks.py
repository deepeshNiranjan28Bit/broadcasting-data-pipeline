from pathlib import Path

import mysql.connector
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config" / "validation_rules.yaml"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "app_user",
    "password": "app_password",
    "database": "broadcasting_db",
}


def get_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def read_table(table_name: str) -> pd.DataFrame:
    conn = get_connection()
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def clear_old_validation_errors() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE validation_errors;")
    conn.commit()
    cursor.close()
    conn.close()
    print("Old validation errors cleared.")


def insert_validation_error(
    table_name: str,
    record_id: str,
    error_type: str,
    error_description: str,
) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO validation_errors
        (table_name, record_id, error_type, error_description)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            table_name,
            str(record_id),
            error_type,
            error_description,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()


def check_nulls(
    df: pd.DataFrame,
    table_name: str,
    key_column: str,
    columns: list[str],
) -> int:
    error_count = 0

    for column in columns:
        null_records = df[df[column].isnull()]

        for _, row in null_records.iterrows():
            insert_validation_error(
                table_name=table_name,
                record_id=row[key_column],
                error_type="NULL_CHECK_FAILED",
                error_description=f"{column} is null",
            )
            error_count += 1

    return error_count


def check_duplicates(
    df: pd.DataFrame,
    table_name: str,
    key_column: str,
) -> int:
    duplicate_records = df[df.duplicated(subset=[key_column], keep=False)]
    error_count = 0

    for _, row in duplicate_records.iterrows():
        insert_validation_error(
            table_name=table_name,
            record_id=row[key_column],
            error_type="DUPLICATE_CHECK_FAILED",
            error_description=f"Duplicate {key_column} found",
        )
        error_count += 1

    return error_count


def check_invalid_workflow_status(
    workflow_df: pd.DataFrame,
    valid_statuses: list[str],
) -> int:
    invalid_records = workflow_df[~workflow_df["status"].isin(valid_statuses)]
    error_count = 0

    for _, row in invalid_records.iterrows():
        insert_validation_error(
            table_name="workflow_events",
            record_id=row["event_id"],
            error_type="INVALID_STATUS",
            error_description=f"Invalid workflow status: {row['status']}",
        )
        error_count += 1

    return error_count


def check_inactive_vendor_usage(
    workflow_df: pd.DataFrame,
    vendors_df: pd.DataFrame,
) -> int:
    merged_df = workflow_df.merge(
        vendors_df[["vendor_id", "is_active"]],
        on="vendor_id",
        how="left",
    )

    invalid_records = merged_df[merged_df["is_active"] != "Y"]
    error_count = 0

    for _, row in invalid_records.iterrows():
        insert_validation_error(
            table_name="workflow_events",
            record_id=row["event_id"],
            error_type="INACTIVE_VENDOR_USED",
            error_description=f"Workflow used inactive vendor: {row['vendor_id']}",
        )
        error_count += 1

    return error_count


def check_non_whitelisted_device(
    workflow_df: pd.DataFrame,
    devices_df: pd.DataFrame,
) -> int:
    merged_df = workflow_df.merge(
        devices_df[["device_id", "whitelisted"]],
        on="device_id",
        how="left",
    )

    invalid_records = merged_df[merged_df["whitelisted"] != "Y"]
    error_count = 0

    for _, row in invalid_records.iterrows():
        insert_validation_error(
            table_name="workflow_events",
            record_id=row["event_id"],
            error_type="NON_WHITELISTED_DEVICE",
            error_description=f"Workflow used non-whitelisted device: {row['device_id']}",
        )
        error_count += 1

    return error_count


def check_missing_content_language(content_df: pd.DataFrame) -> int:
    invalid_records = content_df[content_df["language"].isnull()]
    error_count = 0

    for _, row in invalid_records.iterrows():
        insert_validation_error(
            table_name="content_metadata",
            record_id=row["content_id"],
            error_type="MISSING_CONTENT_LANGUAGE",
            error_description="Content language is missing",
        )
        error_count += 1

    return error_count


def run_validation() -> None:
    config = load_config()

    print("Starting data quality validation...")

    clear_old_validation_errors()

    vendors_df = read_table("vendors")
    devices_df = read_table("devices")
    content_df = read_table("content_metadata")
    workflow_df = read_table("workflow_events")

    total_errors = 0

    total_errors += check_nulls(
        vendors_df,
        "vendors",
        "vendor_id",
        ["vendor_id", "vendor_name", "vendor_type", "is_active"],
    )

    total_errors += check_nulls(
        devices_df,
        "devices",
        "device_id",
        ["device_id", "vendor_id", "device_type", "whitelisted", "region"],
    )

    total_errors += check_nulls(
        content_df,
        "content_metadata",
        "content_id",
        ["content_id", "vendor_id", "title", "language", "category"],
    )

    total_errors += check_nulls(
        workflow_df,
        "workflow_events",
        "event_id",
        ["event_id", "workflow_id", "vendor_id", "device_id", "content_id", "status"],
    )

    total_errors += check_duplicates(vendors_df, "vendors", "vendor_id")
    total_errors += check_duplicates(devices_df, "devices", "device_id")
    total_errors += check_duplicates(content_df, "content_metadata", "content_id")
    total_errors += check_duplicates(workflow_df, "workflow_events", "event_id")

    total_errors += check_invalid_workflow_status(
        workflow_df,
        config["valid_workflow_statuses"],
    )

    total_errors += check_inactive_vendor_usage(workflow_df, vendors_df)
    total_errors += check_non_whitelisted_device(workflow_df, devices_df)
    total_errors += check_missing_content_language(content_df)

    print(f"Validation completed. Total errors found: {total_errors}")


if __name__ == "__main__":
    run_validation()