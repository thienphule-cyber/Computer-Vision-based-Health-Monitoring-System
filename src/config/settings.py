import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

MQTT_RECONNECT_DELAY = 5

MQTT_TOPIC_SUBSCRIBE = "vitals/raw"
MQTT_TOPIC_PUBLISH = "vitals/result"

MQTT_CLIENT_ID_SUBSCRIBER = "analytics_subscriber"
MQTT_CLIENT_ID_PUBLISHER = "analytics_publisher"

STORAGE_TYPE = "sqlite"

# SQLite
DATABASE_PATH = os.path.join(BASE_DIR, "data", "processed", "health_data.db")
DATABASE_TABLE_NAME = "vitals"

# CSV
CSV_FILE_PATH = os.path.join(BASE_DIR, "data", "processed", "health_data.csv")

# Raw Data
RAW_DATA_LOG_PATH = os.path.join(BASE_DIR, "data", "raw", "raw_messages.log")

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "system.log")
LOG_LEVEL = "INFO"

# Heart Rate (BPM)
HEART_RATE_MIN_NORMAL = 60
HEART_RATE_MAX_NORMAL = 100
HEART_RATE_ELEVATED_THRESHOLD = 100
HEART_RATE_HIGH_THRESHOLD = 110
HEART_RATE_LOW_THRESHOLD = 60

RESPIRATORY_RATE_MIN_NORMAL = 12
RESPIRATORY_RATE_MAX_NORMAL = 20

VALID_RANGE = {
    "heartRate": (30, 220),
    "respiratoryRate": (5, 60),   # Optional field
    "confidence": (0, 100),
}

TREND_WINDOW_SIZE = 10
TREND_CONSECUTIVE_THRESHOLD = 5
EXPECTED_SAMPLE_INTERVAL = 2
DATA_TIMEOUT_MULTIPLIER = 5

HEALTH_SCORE_WEIGHTS = {
    "heart_rate": 0.8,
    "stability": 0.2,
}

RISK_LEVELS = ["Normal", "Elevated Heart Rate", "Abnormal Trend", "High Risk"]

RISK_SCORE_THRESHOLDS = {
    "Normal": 85,
    "Elevated Heart Rate": 70,
    "Abnormal Trend": 50,
    "High Risk": 0,
}

ALERT_CONSECUTIVE_TRIGGER = 3
ALERT_REPEAT_NOTIFICATION = False

REPORTS_OUTPUT_DIR = os.path.join(BASE_DIR, "reports_output")
REPORT_FORMAT = "pdf"

REPORT_INTERVAL = 86400

DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8501
DASHBOARD_REFRESH_INTERVAL = 2
DASHBOARD_HISTORY_POINTS = 50
