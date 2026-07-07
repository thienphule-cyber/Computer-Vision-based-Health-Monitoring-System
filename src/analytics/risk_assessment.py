import logging

from config import settings

logger = logging.getLogger(__name__)


def assess_risk(latest_record: dict, trends: dict) -> dict:
    reasons = []
    risk_points = 0

    heart_rate = latest_record.get("heartRate")
    respiratory_rate = latest_record.get("respiratoryRate")

    # --------------------------------------------------------
    # 1. Instantaneous value checks
    # --------------------------------------------------------
    if heart_rate is not None:
        if heart_rate > settings.HEART_RATE_HIGH_THRESHOLD:
            risk_points += 4
            reasons.append(f"Heart rate critically high: {heart_rate} BPM")
        elif heart_rate > settings.HEART_RATE_ELEVATED_THRESHOLD:
            risk_points += 2
            reasons.append(f"Heart rate elevated: {heart_rate} BPM")
        elif heart_rate < settings.HEART_RATE_LOW_THRESHOLD:
            risk_points += 2
            reasons.append(f"Heart rate low: {heart_rate} BPM")

    if respiratory_rate is not None:
        if not (settings.RESPIRATORY_RATE_MIN_NORMAL <= respiratory_rate <= settings.RESPIRATORY_RATE_MAX_NORMAL):
            risk_points += 1
            reasons.append(f"Respiratory rate outside normal range: {respiratory_rate}")

    # --------------------------------------------------------
    # 2. Trend-based checks (erratic/unstable trend -> High Risk)
    # --------------------------------------------------------
    is_erratic_trend = False

    if trends:
        hr_trend = trends.get("heartRate", {})

        if hr_trend.get("direction") == "increasing" and hr_trend.get("is_significant"):
            risk_points += 3
            reasons.append(
                f"Heart rate trending up for {hr_trend.get('consecutive_count')} consecutive readings"
            )
            is_erratic_trend = True
        elif hr_trend.get("direction") == "decreasing" and hr_trend.get("is_significant"):
            risk_points += 2
            reasons.append(
                f"Heart rate trending down for {hr_trend.get('consecutive_count')} consecutive readings"
            )
            is_erratic_trend = True

    # --------------------------------------------------------
    # 3. Map points -> risk_level + status
    # --------------------------------------------------------
    risk_level, status = _map_to_risk_level(heart_rate, risk_points, is_erratic_trend)

    if risk_level != "Normal":
        logger.info(f"Risk assessed as '{risk_level}' (points={risk_points}). Reasons: {reasons}")

    return {
        "risk_level": risk_level,
        "status": status,
        "risk_points": risk_points,
        "reasons": reasons,
    }


def _map_to_risk_level(heart_rate, points: int, is_erratic_trend: bool) -> tuple:
    """
    Returns (risk_level, status).
    status matches the Arduino-facing schema: NORMAL / ELEVATED / LOW / HIGH_RISK
    """
    if points == 0:
        return "Normal", "NORMAL"

    # Erratic trend or accumulated risk points too high -> High Risk
    if is_erratic_trend or points >= 5:
        return "High Risk", "HIGH_RISK"

    if heart_rate is not None and heart_rate < settings.HEART_RATE_LOW_THRESHOLD:
        return "Low Heart Rate", "LOW"

    if heart_rate is not None and heart_rate > settings.HEART_RATE_ELEVATED_THRESHOLD:
        return "Elevated Heart Rate", "ELEVATED"

    return "Normal", "NORMAL"


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")

    latest = {"heartRate": 118}
    trends = {"heartRate": {"direction": "increasing", "consecutive_count": 5, "is_significant": True}}
    print("High risk case:", assess_risk(latest, trends))

    latest_low = {"heartRate": 52}
    print("Low heart rate case:", assess_risk(latest_low, {}))

    latest_elevated = {"heartRate": 112}
    print("Elevated case:", assess_risk(latest_elevated, {}))

    latest_normal = {"heartRate": 82}
    print("Normal case:", assess_risk(latest_normal, {}))
