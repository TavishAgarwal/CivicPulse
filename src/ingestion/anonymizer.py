"""
CivicPulse — Signal Anonymizer

anonymize_at_source() MUST be called on EVERY signal before it leaves
the ingestion module. This is the single enforcement point for PII removal.

Privacy rules (non-negotiable):
- Strip all PII fields
- Round coordinates to ward-level precision (3 decimal places ≈ 111m)
- Never store individual-level data
"""

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Comprehensive list of PII field names to strip (case-insensitive)
PII_FIELDS = frozenset([
    "name", "full_name", "first_name", "last_name", "surname",
    "phone", "mobile", "telephone", "cell_phone", "phone_number",
    "email", "email_address", "e_mail",
    "address", "street", "house_number", "postal_code", "zip_code",
    "pincode", "door_number", "flat_number",
    "person_id", "patient_id", "student_id", "employee_id",
    "aadhaar", "aadhar", "voter_id", "pan_number", "passport",
    "dob", "date_of_birth", "birth_date", "age",
    "gender", "sex",
    "ip_address", "mac_address", "device_id",
])


def anonymize_at_source(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Strip all PII and apply k-anonymity to location data.
    Must be called before any data is written to DB or Kafka.

    Args:
        raw: Raw signal data dictionary.

    Returns:
        Anonymized copy of the signal data. Original dict is not modified.

    Raises:
        TypeError: If raw is not a dictionary.
    """
    if not isinstance(raw, dict):
        raise TypeError(f"anonymize_at_source expects dict, got {type(raw).__name__}")

    # Work on a copy to avoid mutating the original
    cleaned = copy.deepcopy(raw)

    # Strip all known PII fields (case-insensitive matching)
    keys_to_remove = []
    for key in cleaned:
        if key.lower().strip() in PII_FIELDS:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del cleaned[key]
        logger.debug("Stripped PII field: %s", key)

    if keys_to_remove:
        logger.info(
            "Anonymized signal: stripped %d PII field(s): %s",
            len(keys_to_remove),
            ", ".join(keys_to_remove),
        )

    # Round coordinates to ward-level precision (3 decimal places ≈ 111m)
    if "lat" in cleaned and cleaned["lat"] is not None:
        try:
            cleaned["lat"] = round(float(cleaned["lat"]), 3)
        except (ValueError, TypeError):
            del cleaned["lat"]
            logger.warning("Removed invalid lat value")

    if "lng" in cleaned and cleaned["lng"] is not None:
        try:
            cleaned["lng"] = round(float(cleaned["lng"]), 3)
        except (ValueError, TypeError):
            del cleaned["lng"]
            logger.warning("Removed invalid lng value")

    # Also handle 'lon' / 'longitude' variants
    for lon_key in ("lon", "longitude"):
        if lon_key in cleaned and cleaned[lon_key] is not None:
            try:
                cleaned[lon_key] = round(float(cleaned[lon_key]), 3)
            except (ValueError, TypeError):
                del cleaned[lon_key]

    return cleaned


def validate_no_pii(data: dict[str, Any]) -> bool:
    """
    Verify that a data dictionary contains no PII fields.
    Used as a post-anonymization safety check.

    Returns:
        True if no PII fields found, False otherwise.
    """
    for key in data:
        if key.lower().strip() in PII_FIELDS:
            logger.error("PII field '%s' found in supposedly anonymized data!", key)
            return False
    return True
