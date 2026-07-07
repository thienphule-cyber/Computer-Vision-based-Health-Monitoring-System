import logging

from config import settings

logger = logging.getLogger(__name__)


def compute_health_score(latest_record: dict, stats: dict) -> float:
    heart_rate_score = _score_heart_rate(latest_record.get("heartRate"))
    stability_score = _score_stability(stats)

    weights = settings.HEALTH_SCORE_WEIGHTS

    total_score = (
        heart_rate_score * weights["heart_rate"]
        + stability_score * weights["stability"]
    )

    total_score = round(max(0.0, min(100.0, total_score)), 1)

    logger.debug(f"Health score -> HR: {heart_rate_score}, Stability: {stability_score} => Total: {total_score}")

    return total_score


def _score_heart_rate(heart_rate) -> float:
    if heart_rate is None:
        return 100.0

    low, high = settings.HEART_RATE_MIN_NORMAL, settings.HEART_RATE_MAX_NORMAL

    if low <= heart_rate <= high:
        return 100.0

    deviation = abs(heart_rate - high) if heart_rate > high else abs(low - heart_rate)
    return max(0.0, 100.0 - deviation * 5)


def _score_stability(stats: dict) -> float:
    if not stats:
        return 100.0

    hr_std = stats.get("heartRate", {}).get("std", 0) if stats.get("heartRate") else 0
    penalty = min(100.0, hr_std * 5)
    return max(0.0, 100.0 - penalty)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    latest = {"heartRate": 78}
    stats = {"heartRate": {"std": 1.2}}
    print(compute_health_score(latest, stats))