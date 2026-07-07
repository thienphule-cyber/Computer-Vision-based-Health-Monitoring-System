import pytest
from validation.validator import validate_record, ValidationResult

class TestValidRecords:
    def test_valid_normal_record(self):
        record = {"spo2": 98, "heartRate": 76, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is True
        assert result.reason == "OK"

    def test_valid_record_with_float_values(self):
        record = {"spo2": 97.5, "heartRate": 76.0, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is True

    def test_valid_record_boundary_values(self):
        record = {"spo2": 100, "heartRate": 220, "temperature": 45.0, "status": "CHECK REQUIRED"}
        result = validate_record(record)
        assert result.is_valid is True

    def test_unrecognized_status_still_accepted(self):
        record = {"spo2": 98, "heartRate": 76, "temperature": 36.7, "status": "SOMETHING_NEW"}
        result = validate_record(record)
        assert result.is_valid is True

class TestInvalidRecords:
    def test_not_a_dict(self):
        result = validate_record("not a dict")
        assert result.is_valid is False
        assert "not a valid JSON object" in result.reason

    def test_missing_single_field(self):
        record = {"spo2": 98, "heartRate": 76, "temperature": 36.7}
        result = validate_record(record)
        assert result.is_valid is False
        assert "status" in result.reason

    def test_missing_multiple_fields(self):
        record = {"spo2": 98}
        result = validate_record(record)
        assert result.is_valid is False
        assert "Missing required fields" in result.reason

    def test_wrong_type_string_instead_of_number(self):
        record = {"spo2": "98", "heartRate": 76, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is False
        assert "spo2" in result.reason

    def test_boolean_rejected_as_numeric(self):
        record = {"spo2": True, "heartRate": 76, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is False

    def test_status_wrong_type(self):
        record = {"spo2": 98, "heartRate": 76, "temperature": 36.7, "status": 123}
        result = validate_record(record)
        assert result.is_valid is False
        assert "status" in result.reason

    @pytest.mark.parametrize("spo2_value", [-10, 0, 49, 101, 150])
    def test_spo2_out_of_range(self, spo2_value):
        record = {"spo2": spo2_value, "heartRate": 76, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is False
        assert "spo2" in result.reason

    @pytest.mark.parametrize("heart_rate_value", [0, 29, 221, 500])
    def test_heart_rate_out_of_range(self, heart_rate_value):
        record = {"spo2": 98, "heartRate": heart_rate_value, "temperature": 36.7, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is False
        assert "heartRate" in result.reason

    @pytest.mark.parametrize("temperature_value", [10.0, 29.9, 45.1, 100.0])
    def test_temperature_out_of_range(self, temperature_value):
        record = {"spo2": 98, "heartRate": 76, "temperature": temperature_value, "status": "NORMAL"}
        result = validate_record(record)
        assert result.is_valid is False
        assert "temperature" in result.reason

class TestValidationResultObject:
    def test_result_has_expected_attributes(self):
        result = ValidationResult(is_valid=True, reason="OK", record={"a": 1})
        assert result.is_valid is True
        assert result.reason == "OK"
        assert result.record == {"a": 1}

    def test_result_repr(self):
        result = ValidationResult(is_valid=False, reason="test error")
        assert "is_valid=False" in repr(result)
        assert "test error" in repr(result)
