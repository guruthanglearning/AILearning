"""
Unit tests for feature engineering utilities.
Tests all functions in app/utils/feature_engineering.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.api.models import Transaction
from app.utils.feature_engineering import (
    engineer_features,
    get_velocity_features,
    is_sanctioned_country,
    calculate_country_risk,
    calculate_category_risk,
    detect_category_mismatch,
    calculate_geo_features,
    calculate_data_quality_risk,
    get_merchant_risk_score,
    calculate_behavioral_features,
    create_transaction_text,
    select_features_for_ml,
)


def make_transaction(**kwargs):
    """Helper to create a Transaction with defaults."""
    defaults = {
        "transaction_id": "tx_001",
        "card_id": "card_001",
        "merchant_id": "merch_001",
        "timestamp": "2025-05-07T10:23:45Z",
        "amount": 100.0,
        "merchant_category": "Grocery",
        "merchant_name": "Local Market",
        "merchant_country": "US",
        "customer_id": "cust_001",
        "is_online": False,
        "currency": "USD",
    }
    defaults.update(kwargs)
    return Transaction(**defaults)


# ── is_sanctioned_country ────────────────────────────────────────────────────

class TestIsSanctionedCountry:
    def test_sanctioned_countries(self):
        for code in ["RU", "BY", "KP", "IR", "SY", "CU", "VE"]:
            assert is_sanctioned_country(code) is True

    def test_non_sanctioned_countries(self):
        for code in ["US", "GB", "DE", "CA", "AU", "NG"]:
            assert is_sanctioned_country(code) is False

    def test_lowercase_input(self):
        assert is_sanctioned_country("ru") is True

    def test_empty_string(self):
        assert is_sanctioned_country("") is False

    def test_none_like_empty(self):
        assert is_sanctioned_country("") is False


# ── calculate_country_risk ───────────────────────────────────────────────────

class TestCalculateCountryRisk:
    def test_sanctioned_country_returns_max_risk(self):
        assert calculate_country_risk("RU") == 0.99

    def test_high_risk_country(self):
        risk = calculate_country_risk("NG")
        assert risk >= 0.8

    def test_medium_risk_country(self):
        risk = calculate_country_risk("TR")
        assert 0.4 <= risk <= 0.7

    def test_low_risk_country(self):
        risk = calculate_country_risk("US")
        assert risk <= 0.4

    def test_unknown_country_returns_default(self):
        risk = calculate_country_risk("ZZ")
        assert 0.0 <= risk <= 1.0


# ── calculate_category_risk ──────────────────────────────────────────────────

class TestCalculateCategoryRisk:
    def test_high_risk_category(self):
        assert calculate_category_risk("Electronics") >= 0.7
        assert calculate_category_risk("Cryptocurrency") >= 0.9

    def test_medium_risk_category(self):
        risk = calculate_category_risk("Online Retail")
        assert 0.4 <= risk <= 0.7

    def test_low_risk_category(self):
        risk = calculate_category_risk("Grocery")
        assert risk <= 0.4

    def test_unknown_category_default(self):
        risk = calculate_category_risk("Unknown Category XYZ")
        assert 0.0 <= risk <= 1.0

    def test_empty_category(self):
        risk = calculate_category_risk("")
        assert 0.0 <= risk <= 1.0


# ── detect_category_mismatch ─────────────────────────────────────────────────

class TestDetectCategoryMismatch:
    def test_no_mismatch(self):
        # Use a name that doesn't contain keywords from other categories
        score = detect_category_mismatch("TechGadget Inc", "Electronics")
        assert score == 0.0

    def test_mismatch_gas_station_electronics(self):
        score = detect_category_mismatch("Shell Gas Station", "Electronics")
        assert score > 0.0

    def test_empty_merchant_name(self):
        score = detect_category_mismatch("", "Electronics")
        assert score == 0.0

    def test_none_merchant_name(self):
        score = detect_category_mismatch(None, "Electronics")
        assert score == 0.0

    def test_no_keyword_match(self):
        score = detect_category_mismatch("Random Name", "Grocery")
        assert score == 0.0


# ── calculate_data_quality_risk ──────────────────────────────────────────────

class TestCalculateDataQualityRisk:
    def test_good_data_low_risk(self):
        txn = make_transaction(
            merchant_name="Normal Store",
            merchant_category="Grocery",
            is_online=False,
            latitude=40.7, longitude=-74.0
        )
        risk = calculate_data_quality_risk(txn)
        assert risk < 0.5

    def test_missing_merchant_name_high_risk(self):
        txn = make_transaction(merchant_name="")
        risk = calculate_data_quality_risk(txn)
        assert risk > 0.5

    def test_null_island_coordinates(self):
        txn = make_transaction(latitude=0.0, longitude=0.0)
        risk = calculate_data_quality_risk(txn)
        assert risk > 0.5

    def test_no_data_quality_issues(self):
        txn = make_transaction(
            merchant_name="Good Store",
            merchant_category="Grocery",
        )
        risk = calculate_data_quality_risk(txn)
        assert isinstance(risk, float)
        assert 0.0 <= risk <= 1.0


# ── get_merchant_risk_score ──────────────────────────────────────────────────

class TestGetMerchantRiskScore:
    def test_known_low_risk_merchant(self):
        score = get_merchant_risk_score("merch_24680", "SafeStore")
        assert score < 0.5

    def test_known_high_risk_merchant(self):
        score = get_merchant_risk_score("merch_13579", "BadStore")
        assert score >= 0.7

    def test_missing_merchant_name(self):
        score = get_merchant_risk_score("merch_unknown", "")
        assert score >= 0.5

    def test_unknown_merchant_id_default(self):
        score = get_merchant_risk_score("merch_99999999", "AnyStore")
        assert 0.0 <= score <= 1.0


# ── get_velocity_features ────────────────────────────────────────────────────

class TestGetVelocityFeatures:
    def test_returns_required_keys(self):
        features = get_velocity_features("cust_001", "card_001")
        required = ["txn_count_1h", "txn_count_24h", "txn_count_7d",
                    "avg_amount_7d", "amount_velocity_24h", "unique_merchants_24h"]
        for key in required:
            assert key in features

    def test_all_values_non_negative(self):
        features = get_velocity_features("cust_001", "card_001")
        for val in features.values():
            assert val >= 0


# ── calculate_behavioral_features ───────────────────────────────────────────

class TestCalculateBehavioralFeatures:
    def test_returns_required_keys(self):
        features = calculate_behavioral_features("cust_001")
        required = ["behavior_anomaly_score", "days_since_last_txn"]
        for key in required:
            assert key in features

    def test_anomaly_score_in_range(self):
        features = calculate_behavioral_features("cust_001")
        assert 0.0 <= features["behavior_anomaly_score"] <= 1.0


# ── calculate_geo_features ───────────────────────────────────────────────────

class TestCalculateGeoFeatures:
    def test_returns_geo_features(self):
        txn = make_transaction(
            merchant_country="US",
            latitude=40.7, longitude=-74.0
        )
        features = calculate_geo_features(txn)
        assert "location_risk_score" in features
        assert "country_risk_score" in features

    def test_high_risk_country_geo(self):
        txn = make_transaction(
            merchant_country="NG",
            latitude=9.0, longitude=8.6
        )
        features = calculate_geo_features(txn)
        assert features["country_risk_score"] >= 0.8


# ── engineer_features ────────────────────────────────────────────────────────

class TestEngineerFeatures:
    def test_basic_features_present(self):
        txn = make_transaction()
        features = engineer_features(txn)
        required = ["amount", "is_online", "hour_of_day", "day_of_week",
                    "merchant_risk_score", "behavior_anomaly_score",
                    "country_risk_score", "category_risk_score",
                    "is_sanctioned_country", "data_quality_risk_score"]
        for key in required:
            assert key in features, f"Missing feature: {key}"

    def test_sanctioned_country_flagged(self):
        txn = make_transaction(merchant_country="RU")
        features = engineer_features(txn)
        assert features["is_sanctioned_country"] is True
        assert features["country_risk_score"] == 0.99

    def test_non_sanctioned_country_not_flagged(self):
        txn = make_transaction(merchant_country="US")
        features = engineer_features(txn)
        assert features["is_sanctioned_country"] is False

    def test_with_geo_data(self):
        txn = make_transaction(latitude=40.7, longitude=-74.0)
        features = engineer_features(txn)
        assert "distance_from_home" in features

    def test_without_geo_data(self):
        txn = make_transaction()
        features = engineer_features(txn)
        assert "location_risk_score" in features

    def test_online_transaction(self):
        txn = make_transaction(is_online=True)
        features = engineer_features(txn)
        assert features["is_online"] == 1

    def test_offline_transaction(self):
        txn = make_transaction(is_online=False)
        features = engineer_features(txn)
        assert features["is_online"] == 0

    def test_hour_of_day_range(self):
        txn = make_transaction()
        features = engineer_features(txn)
        assert 0 <= features["hour_of_day"] <= 23

    def test_day_of_week_range(self):
        txn = make_transaction()
        features = engineer_features(txn)
        assert 0 <= features["day_of_week"] <= 6


# ── select_features_for_ml ───────────────────────────────────────────────────

class TestSelectFeaturesForML:
    def test_returns_ml_features(self):
        txn = make_transaction()
        features = engineer_features(txn)
        ml_features = select_features_for_ml(features)
        required = ["amount", "is_online", "hour_of_day", "day_of_week",
                    "merchant_risk_score", "behavior_anomaly_score"]
        for key in required:
            assert key in ml_features

    def test_with_geo_features_included(self):
        txn = make_transaction(latitude=40.7, longitude=-74.0)
        features = engineer_features(txn)
        ml_features = select_features_for_ml(features)
        assert "distance_from_home" in ml_features
        assert "location_risk_score" in ml_features

    def test_normalized_values(self):
        txn = make_transaction()
        features = engineer_features(txn)
        ml_features = select_features_for_ml(features)
        # hour_of_day should be normalized to 0-1
        assert 0.0 <= ml_features["hour_of_day"] <= 1.0


# ── create_transaction_text ──────────────────────────────────────────────────

class TestCreateTransactionText:
    def test_returns_string(self):
        txn = make_transaction()
        features = engineer_features(txn)
        text = create_transaction_text(txn, features)
        assert isinstance(text, str)

    def test_contains_transaction_id(self):
        txn = make_transaction(transaction_id="tx_unique_123")
        features = engineer_features(txn)
        text = create_transaction_text(txn, features)
        assert "tx_unique_123" in text

    def test_contains_amount(self):
        txn = make_transaction(amount=999.99)
        features = engineer_features(txn)
        text = create_transaction_text(txn, features)
        assert "999.99" in text

    def test_sanctioned_country_warning(self):
        txn = make_transaction(merchant_country="RU")
        features = engineer_features(txn)
        text = create_transaction_text(txn, features)
        assert "sanctioned" in text.lower() or "CRITICAL" in text

    def test_with_geo_data(self):
        txn = make_transaction(latitude=40.7, longitude=-74.0)
        features = engineer_features(txn)
        text = create_transaction_text(txn, features)
        assert "40.7" in text
