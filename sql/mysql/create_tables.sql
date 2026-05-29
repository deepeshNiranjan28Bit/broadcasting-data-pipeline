CREATE DATABASE IF NOT EXISTS broadcasting_db;

USE broadcasting_db;

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id VARCHAR(20) PRIMARY KEY,
    vendor_name VARCHAR(255),
    vendor_type VARCHAR(100),
    is_active CHAR(1),
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(20) PRIMARY KEY,
    vendor_id VARCHAR(20),
    device_type VARCHAR(100),
    whitelisted CHAR(1),
    region VARCHAR(100),
    created_at DATETIME,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS content_metadata (
    content_id VARCHAR(20) PRIMARY KEY,
    vendor_id VARCHAR(20),
    title VARCHAR(500),
    language VARCHAR(100),
    category VARCHAR(100),
    duration_sec INT,
    created_at DATETIME,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS workflow_events (
    event_id VARCHAR(30) PRIMARY KEY,
    workflow_id VARCHAR(30),
    vendor_id VARCHAR(20),
    device_id VARCHAR(20),
    content_id VARCHAR(20),
    status VARCHAR(50),
    event_time DATETIME,
    source_system VARCHAR(100),
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (content_id) REFERENCES content_metadata(content_id)
);

CREATE TABLE IF NOT EXISTS validation_errors (
    error_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100),
    record_id VARCHAR(100),
    error_type VARCHAR(100),
    error_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reconciliation_summary (
    reconciliation_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100),
    source_count INT,
    target_count INT,
    mismatch_count INT,
    status VARCHAR(50),
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);