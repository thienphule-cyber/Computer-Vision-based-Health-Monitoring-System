import logging
import statistics as pystat

logger = logging.getLogger(__name__)

METRICS = ["heartRate", "respiratoryRate"]


def compute_statistics(records: list) -> dict:
    if not records:
        logger.warning("compute_statistics called with empty records list.")
        return {}

    result = {}
    for metric in METRICS:
        values = [r[metric] for r in records if r.get(metric) is not None]

        if not values:
            result[metric] = None
            continue

        result[metric] = {
            "mean": round(pystat.fmean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "std": round(pystat.pstdev(values), 2) if len(values) > 1 else 0.0,
            "variance": round(pystat.pvariance(values), 2) if len(values) > 1 else 0.0,
            "rate_of_change": _compute_rate_of_change(values),
        }

    return result


def _compute_rate_of_change(values: list) -> float:
    if len(values) < 2:
        return 0.0
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    return round(pystat.fmean(diffs), 2)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    sample = [{"heartRate": 74}, {"heartRate": 78}, {"heartRate": 82}]
    print(compute_statistics(sample))