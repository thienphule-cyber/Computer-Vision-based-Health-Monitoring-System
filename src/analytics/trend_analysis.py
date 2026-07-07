import logging

from config import settings

logger = logging.getLogger(__name__)

METRICS = ["heartRate", "respiratoryRate"]

NOISE_THRESHOLD = {
    "heartRate": 1.0,
    "respiratoryRate": 0.5,
}


def analyze_trend(records: list) -> dict:
    if len(records) < 2:
        logger.debug("Not enough records to analyze trend (need >= 2).")
        return {metric: {"direction": "stable", "consecutive_count": 0} for metric in METRICS}

    result = {}
    for metric in METRICS:
        values = [r[metric] for r in records if r.get(metric) is not None]
        result[metric] = _analyze_single_metric_trend(metric, values)

    return result


def _analyze_single_metric_trend(metric: str, values: list) -> dict:
    if len(values) < 2:
        return {"direction": "stable", "consecutive_count": 0}

    threshold = NOISE_THRESHOLD.get(metric, 0.0)
    directions = []

    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        if diff > threshold:
            directions.append("increasing")
        elif diff < -threshold:
            directions.append("decreasing")
        else:
            directions.append("stable")

    last_direction = directions[-1]
    consecutive_count = 1
    for d in reversed(directions[:-1]):
        if d == last_direction:
            consecutive_count += 1
        else:
            break

    is_significant = (
        last_direction != "stable"
        and consecutive_count >= settings.TREND_CONSECUTIVE_THRESHOLD
    )

    if is_significant:
        logger.info(
            f"Significant trend detected for '{metric}': "
            f"{last_direction} for {consecutive_count} consecutive readings."
        )

    return {
        "direction": last_direction,
        "consecutive_count": consecutive_count,
        "is_significant": is_significant,
    }


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    sample = [{"heartRate": 70}, {"heartRate": 75}, {"heartRate": 80}, {"heartRate": 85}, {"heartRate": 90}, {"heartRate": 95}]
    print(analyze_trend(sample))