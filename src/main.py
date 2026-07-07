import logging
import signal
import sys
import threading
import time
from datetime import datetime

from config import settings
from utils.logger import setup_logging

from mqtt.mqtt_listener import MQTTListener
from mqtt.mqtt_publisher import MQTTPublisher
from validation.validator import validate_record
from storage.database import init_db
from storage.storage import save_record, update_record_analytics, get_latest_records
from analytics.statistics import compute_statistics
from analytics.trend_analysis import analyze_trend
from analytics.risk_assessment import assess_risk
from analytics.health_score import compute_health_score
from alerts.alert_manager import AlertManager
from reports.report_generator import generate_report


setup_logging()
logger = logging.getLogger(__name__)

alert_manager = AlertManager()
mqtt_publisher = MQTTPublisher()
_shutdown_event = threading.Event()


def process_record(record: dict) -> None:
    result = validate_record(record)
    if not result.is_valid:
        logger.warning(f"Record rejected by validator: {result.reason}")
        return

    valid_record = result.record
    valid_record["received_at"] = valid_record.get(
        "received_at", datetime.now().isoformat(timespec="seconds")
    )

    try:
        record_id = save_record(valid_record)
    except Exception as e:
        logger.error(f"Failed to save record, skipping analytics for this record: {e}")
        return

    try:
        history = get_latest_records()
        stats = compute_statistics(history)
        trends = analyze_trend(history)
        risk_result = assess_risk(valid_record, trends)
        health_score = compute_health_score(valid_record, stats)
    except Exception as e:
        logger.error(f"Analytics computation failed for record_id={record_id}: {e}")
        return

    try:
        update_record_analytics(
            record_id, health_score, risk_result["risk_level"], risk_result["status"]
        )
    except Exception as e:
        logger.error(f"Failed to update analytics for record_id={record_id}: {e}")

    logger.info(
        f"Processed record_id={record_id} | HR={valid_record.get('heartRate')} | "
        f"Confidence={valid_record.get('confidence')} | "
        f"HealthScore={health_score} RiskLevel={risk_result['risk_level']} Status={risk_result['status']}"
    )

    # Publish result to Arduino and any other subscriber
    try:
        mqtt_publisher.publish_result(
            heart_rate=valid_record.get("heartRate"),
            status=risk_result["status"],
            confidence=valid_record.get("confidence"),
        )
    except Exception as e:
        logger.error(f"Failed to publish result to Arduino: {e}")

    try:
        enriched_record = dict(valid_record)
        enriched_record["health_score"] = health_score
        enriched_record["risk_level"] = risk_result["risk_level"]
        alert_manager.evaluate(enriched_record, risk_result)
    except Exception as e:
        logger.error(f"Alert evaluation failed for record_id={record_id}: {e}")


def report_scheduler():
    logger.info(f"Report scheduler started. Interval: {settings.REPORT_INTERVAL}s")
    while not _shutdown_event.is_set():
        for _ in range(settings.REPORT_INTERVAL):
            if _shutdown_event.is_set():
                return
            time.sleep(1)
        try:
            path = generate_report()
            logger.info(f"Scheduled report generated: {path}")
        except Exception as e:
            logger.error(f"Scheduled report generation failed: {e}")


def handle_shutdown(signum, frame):
    logger.info("Shutdown signal received. Stopping system...")
    _shutdown_event.set()
    sys.exit(0)


def main():
    logger.info("=" * 60)
    logger.info("Starting Biomedical Analytics Layer")
    logger.info(f"Started at: {datetime.now().isoformat(timespec='seconds')}")
    logger.info("=" * 60)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    init_db()
    mqtt_publisher.connect()

    report_thread = threading.Thread(target=report_scheduler, daemon=True)
    report_thread.start()

    listener = MQTTListener(on_data_callback=process_record)

    try:
        listener.start()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Stopping MQTT listener and publisher...")
        listener.stop()
        mqtt_publisher.stop()
        _shutdown_event.set()
        logger.info("System stopped cleanly.")


if __name__ == "__main__":
    main()