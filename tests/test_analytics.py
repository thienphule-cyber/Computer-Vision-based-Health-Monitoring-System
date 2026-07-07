import pytest

from analytics.statistics import compute_statistics
from analytics.trend_analysis import analyze_trend
from analytics.risk_assessment import assess_risk
from analytics.health_score import compute_health_score

class TestStatistics:
    def test_empty_records_returns_empty_dict(self):
        result = compute_statistics([])
        assert result == {}

    def test_single_record(self):
        records = [{"heartRate": 76, "spo2": 98, "temperature": 36.7}]
        result = compute_statistics(records)
        assert result["heartRate"]["mean"] == 76
        assert result["heartRate"]["std"] == 0.0
        assert result["heartRate"]["rate_of_change"] == 0.0

    def test_multiple_records_mean_min_max(self):
        records = [
            {"heartRate": 70, "spo2": 96, "temperature": 36.5},
            {"heartRate": 80, "spo2": 98, "temperature": 36.7},
            {"heartRate": 90, "spo2": 100, "temperature": 36.9},
        ]
        result = compute_statistics(records)
        assert result["heartRate"]["mean"] == 80.0
        assert result["heartRate"]["min"] == 70
        assert result["heartRate"]["max"] == 90

    def test_rate_of_change_increasing(self):
        records = [
            {"heartRate": 70, "spo2": 98, "temperature": 36.5},
            {"heartRate": 75, "spo2": 98, "temperature": 36.5},
            {"heartRate": 80, "spo2": 98, "temperature": 36.5},
        ]
        result = compute_statistics(records)
        assert result["heartRate"]["rate_of_change"] == 5.0

    def test_missing_metric_field_handled_gracefully(self):
        records = [{"heartRate": 76, "spo2": 98}]
        result = compute_statistics(records)
        assert result["temperature"] is None

class TestTrendAnalysis:
    def test_not_enough_records_returns_stable(self):
        records = [{"heartRate": 76, "spo2": 98, "temperature": 36.7}]
        result = analyze_trend(records)
        assert result["heartRate"]["direction"] == "stable"
        assert result["heartRate"]["consecutive_count"] == 0

    def test_detects_increasing_trend(self):
        records = [
            {"heartRate": 70, "spo2": 98, "temperature": 36.5},
            {"heartRate": 74, "spo2": 98, "temperature": 36.5},
            {"heartRate": 78, "spo2": 98, "temperature": 36.5},
            {"heartRate": 82, "spo2": 98, "temperature": 36.5},
        ]
        result = analyze_trend(records)
        assert result["heartRate"]["direction"] == "increasing"
        assert result["heartRate"]["consecutive_count"] == 3

    def test_detects_decreasing_trend(self):
        records = [
            {"heartRate": 76, "spo2": 98, "temperature": 36.5},
            {"heartRate": 76, "spo2": 96, "temperature": 36.5},
            {"heartRate": 76, "spo2": 94, "temperature": 36.5},
            {"heartRate": 76, "spo2": 92, "temperature": 36.5},
        ]
        result = analyze_trend(records)
        assert result["spo2"]["direction"] == "decreasing"

    def test_stable_when_within_noise_threshold(self):
        records = [
            {"heartRate": 76, "spo2": 98.0, "temperature": 36.70},
            {"heartRate": 76, "spo2": 98.1, "temperature": 36.72},
            {"heartRate": 76, "spo2": 98.0, "temperature": 36.71},
        ]
        result = analyze_trend(records)
        assert result["spo2"]["direction"] == "stable"

    def test_is_significant_flag(self):
        records = [
            {"heartRate": 70, "spo2": 98, "temperature": 36.5},
            {"heartRate": 74, "spo2": 98, "temperature": 36.5},
            {"heartRate": 78, "spo2": 98, "temperature": 36.5},
        ]
        result = analyze_trend(records)
        assert result["heartRate"]["is_significant"] is False

class TestRiskAssessment:
    def test_normal_values_return_normal_risk(self):
        latest = {"heartRate": 76, "spo2": 98, "temperature": 36.7, "status": "NORMAL"}
        trends = {}
        result = assess_risk(latest, trends)
        assert result["risk_level"] == "Normal"
        assert result["risk_points"] == 0

    def test_low_spo2_increases_risk(self):
        latest = {"heartRate": 76, "spo2": 85, "temperature": 36.7, "status": "LOW OXYGEN"}
        trends = {}
        result = assess_risk(latest, trends)
        assert result["risk_level"] in ("Low Risk", "Medium Risk", "High Risk")
        assert result["risk_points"] > 0

    def test_multiple_abnormal_values_high_risk(self):
        latest = {"heartRate": 115, "spo2": 88, "temperature": 38.5, "status": "CHECK REQUIRED"}
        trends = {}
        result = assess_risk(latest, trends)
        assert result["risk_level"] == "High Risk"

    def test_significant_negative_trend_adds_risk(self):
        latest = {"heartRate": 76, "spo2": 96, "temperature": 36.7, "status": "NORMAL"}
        trends = {
            "spo2": {"direction": "decreasing", "consecutive_count": 5, "is_significant": True}
        }
        result = assess_risk(latest, trends)
        assert result["risk_points"] > 0
        assert any("trending down" in reason for reason in result["reasons"])

    def test_reasons_list_not_empty_when_risk_detected(self):
        latest = {"heartRate": 76, "spo2": 85, "temperature": 36.7, "status": "LOW OXYGEN"}
        result = assess_risk(latest, {})
        assert len(result["reasons"]) > 0

class TestHealthScore:
    def test_perfect_vitals_score_close_to_100(self):
        latest = {"heartRate": 76, "spo2": 98, "temperature": 36.7, "status": "NORMAL"}
        stats = {
            "heartRate": {"std": 0.0},
            "spo2": {"std": 0.0},
        }
        score = compute_health_score(latest, stats)
        assert score == 100.0

    def test_low_spo2_reduces_score(self):
        latest = {"heartRate": 76, "spo2": 85, "temperature": 36.7, "status": "LOW OXYGEN"}
        stats = {}
        score = compute_health_score(latest, stats)
        assert score < 100.0

    def test_fever_reduces_score(self):
        latest = {"heartRate": 76, "spo2": 98, "temperature": 39.5, "status": "FEVER"}
        stats = {}
        score = compute_health_score(latest, stats)
        assert score < 100.0

    def test_score_never_below_zero(self):
        latest = {"heartRate": 220, "spo2": 50, "temperature": 45.0, "status": "CHECK REQUIRED"}
        stats = {}
        score = compute_health_score(latest, stats)
        assert score >= 0.0

    def test_score_never_above_100(self):
        latest = {"heartRate": 76, "spo2": 100, "temperature": 36.0, "status": "NORMAL"}
        stats = {"heartRate": {"std": 0.0}, "spo2": {"std": 0.0}}
        score = compute_health_score(latest, stats)
        assert score <= 100.0

    def test_high_instability_reduces_score(self):
        latest = {"heartRate": 76, "spo2": 98, "temperature": 36.7, "status": "NORMAL"}
        stable_stats = {"heartRate": {"std": 0.5}, "spo2": {"std": 0.2}}
        unstable_stats = {"heartRate": {"std": 15.0}, "spo2": {"std": 5.0}}

        stable_score = compute_health_score(latest, stable_stats)
        unstable_score = compute_health_score(latest, unstable_stats)

        assert stable_score > unstable_score
