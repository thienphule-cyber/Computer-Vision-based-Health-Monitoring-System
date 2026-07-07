import logging
from config import settings

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["heartRate"]
OPTIONAL_FIELDS = ["confidence", "respiratoryRate"]

class ValidationResult:
    def __init__(self, is_valid: bool, reason: str = "", record: dict = None):
        self.is_valid = is_valid
        self.reason = reason
        self.record = record

    def __repr__(self):
        return f"ValidationResult(is_valid={self.is_valid}, reason='{self.reason}')"
    
def validate_record(record: dict) -> ValidationResult:
        if not isinstance(record, dict):
            return _invalid(record, "Record is not a valid JSON object (dict).")
        
        missing_fields = [field for field in REQUIRED_FIELDS if field not in record]
        if missing_fields:
            return _invalid(record, f"Missing required fields: {missing_fields}")
        
        numeric_fields = [f for f in (REQUIRED_FIELDS + OPTIONAL_FIELDS) if f in record]
        for field in numeric_fields:
            value = record[field]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return _invalid(record, f"Field '{field}' must be numeric, got: {type(value).__name__}")
        
        for field, (min_val, max_val) in settings.VALID_RANGE.items():
            value = record.get(field)
            if value is None:
                continue
            if not (min_val <= value <= max_val):
                return _invalid(
                record,
                f"Field '{field}' out of valid range [{min_val}, {max_val}]: got {value}"
                )
        
        logger.debug(f"Record validate successfully: {record}")
        return ValidationResult(is_valid=True, reason="OK", record=record)
    
def _invalid(record, reason: str) -> ValidationResult:
        logger.warning(f"Invalid record rejected. Reason: {reason}. Record: {record}")
        return ValidationResult(is_valid=False, reason=reason, record=record)

if __name__ == "__main__":
        logging.basicConfig(level="DEBUG", format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        test_cases = [
        {"heartRate": 78},
        {"heartRate": 78, "respiratoryRate": 16},
        {},
        {"heartRate": "78"},
        {"heartRate": 500},
    ]

        for i, case in enumerate(test_cases, start=1):
            print(f"Test case {i}: {validate_record(case)}")

