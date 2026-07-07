
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self):
        self._consecutive_counts = {
            "high_heart_rate": 0,
            "high_risk": 0,
        }
        self._last_alert_state = {
            "high_heart_rate": False,
            "high_risk": False,
        }

    def evaluate(self, latest_record: dict, risk_result: dict) -> list:
        triggered_alerts = []

        conditions = {
            "high_heart_rate": latest_record.get("heartRate") is not None
                        and latest_record["heartRate"] > settings.HEART_RATE_HIGH_THRESHOLD,
            "high_risk": risk_result.get("risk_level") == "High Risk",
        }

        for condition_name, is_triggered in conditions.items():
            if is_triggered:
                self._consecutive_counts[condition_name] += 1
            else:
                self._consecutive_counts[condition_name] = 0
                self._last_alert_state[condition_name] = False
                continue

            should_alert = self._consecutive_counts[condition_name] >= settings.ALERT_CONSECUTIVE_TRIGGER

            if should_alert:
                already_alerted = self._last_alert_state[condition_name]
                if already_alerted and not settings.ALERT_REPEAT_NOTIFICATION:
                    continue

                alert = self._build_alert(condition_name, latest_record, risk_result)
                triggered_alerts.append(alert)
                self._last_alert_state[condition_name] = True
                self._dispatch(alert)

        return triggered_alerts

    def _build_alert(self, condition_name: str, latest_record: dict, risk_result: dict) -> dict:
        messages = {
            "high_heart_rate": f"Heart rate critically high: {latest_record.get('heartRate')} BPM "
                        f"(threshold: {settings.HEART_RATE_HIGH_THRESHOLD} BPM)",
            "high_risk": f"Overall risk level is High Risk. Reasons: {risk_result.get('reasons')}",
        }

        return {
            "type": condition_name,
            "message": messages[condition_name],
            "consecutive_count": self._consecutive_counts[condition_name],
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "record": latest_record,
        }

    def _dispatch(self, alert: dict):
        logger.warning(f"[ALERT] {alert['type'].upper()}: {alert['message']}")