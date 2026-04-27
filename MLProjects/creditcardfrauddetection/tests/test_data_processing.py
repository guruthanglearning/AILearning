"""
Tests for app/utils/data_processing.py (currently 0% coverage).
"""
import json
import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from app.utils.data_processing import (
    load_json_data,
    save_json_data,
    convert_to_dataframe,
    normalize_features,
    encode_categorical_features,
    filter_transactions_by_date,
    aggregate_transactions_by_customer,
)


# ── load_json_data ────────────────────────────────────────────────────────────

class TestLoadJsonData:
    def test_load_dict(self, tmp_path):
        data = {"key": "value", "number": 42}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        result = load_json_data(str(f))
        assert result == data

    def test_load_list(self, tmp_path):
        data = [{"a": 1}, {"b": 2}]
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        result = load_json_data(str(f))
        assert result == data

    def test_file_not_found_raises(self):
        with pytest.raises(Exception):
            load_json_data("/nonexistent/path/file.json")

    def test_invalid_json_raises(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{ not valid json }")
        with pytest.raises(Exception):
            load_json_data(str(f))


# ── save_json_data ────────────────────────────────────────────────────────────

class TestSaveJsonData:
    def test_save_dict(self, tmp_path):
        data = {"hello": "world"}
        f = tmp_path / "out.json"
        save_json_data(data, str(f))
        loaded = json.loads(f.read_text())
        assert loaded == data

    def test_save_list(self, tmp_path):
        data = [1, 2, 3]
        f = tmp_path / "out.json"
        save_json_data(data, str(f))
        loaded = json.loads(f.read_text())
        assert loaded == data

    def test_save_to_invalid_path_raises(self):
        with pytest.raises(Exception):
            save_json_data({"x": 1}, "/nonexistent/dir/file.json")

    def test_roundtrip(self, tmp_path):
        data = {"name": "test", "values": [1, 2, 3], "nested": {"a": True}}
        f = tmp_path / "rt.json"
        save_json_data(data, str(f))
        result = load_json_data(str(f))
        assert result == data


# ── convert_to_dataframe ──────────────────────────────────────────────────────

class TestConvertToDataframe:
    def test_basic_conversion(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        df = convert_to_dataframe(data)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["a", "b"]
        assert len(df) == 2

    def test_empty_list(self):
        df = convert_to_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_mixed_types(self):
        data = [{"name": "Alice", "amount": 100.0, "flag": True}]
        df = convert_to_dataframe(data)
        assert df["name"].iloc[0] == "Alice"
        assert df["amount"].iloc[0] == 100.0


# ── normalize_features ────────────────────────────────────────────────────────

class TestNormalizeFeatures:
    def test_numeric_columns_normalized(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
        result = normalize_features(df)
        # After normalization, mean should be ~0 and std ~1
        assert abs(result["a"].mean()) < 1e-10
        assert abs(result["b"].mean()) < 1e-10

    def test_non_numeric_columns_untouched(self):
        df = pd.DataFrame({"num": [1.0, 2.0, 3.0], "cat": ["x", "y", "z"]})
        result = normalize_features(df)
        assert list(result["cat"]) == ["x", "y", "z"]

    def test_single_value_column(self):
        # std=0 → NaN after normalization; ensure it doesn't raise
        df = pd.DataFrame({"a": [5.0, 5.0, 5.0]})
        result = normalize_features(df)
        assert isinstance(result, pd.DataFrame)

    def test_returns_dataframe(self):
        df = pd.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        result = normalize_features(df)
        assert isinstance(result, pd.DataFrame)


# ── encode_categorical_features ───────────────────────────────────────────────

class TestEncodeCategoricalFeatures:
    def test_basic_encoding(self):
        df = pd.DataFrame({"color": ["red", "blue", "red"], "value": [1, 2, 3]})
        result = encode_categorical_features(df, ["color"])
        assert "color" not in result.columns
        assert "value" in result.columns

    def test_nonexistent_columns_ignored(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = encode_categorical_features(df, ["nonexistent"])
        # Returns unchanged dataframe with a warning
        assert list(result.columns) == ["a", "b"]

    def test_empty_column_list(self):
        df = pd.DataFrame({"a": ["x", "y"], "b": [1, 2]})
        result = encode_categorical_features(df, [])
        assert list(result.columns) == ["a", "b"]

    def test_multiple_categorical_columns(self):
        df = pd.DataFrame({
            "color": ["red", "blue", "green"],
            "size": ["S", "M", "L"],
            "value": [1.0, 2.0, 3.0],
        })
        result = encode_categorical_features(df, ["color", "size"])
        assert "color" not in result.columns
        assert "size" not in result.columns
        assert "value" in result.columns


# ── filter_transactions_by_date ───────────────────────────────────────────────

class TestFilterTransactionsByDate:
    def _make_txns(self):
        return [
            {"timestamp": "2024-01-10T10:00:00Z", "amount": 100},
            {"timestamp": "2024-01-15T12:00:00Z", "amount": 200},
            {"timestamp": "2024-01-20T08:00:00Z", "amount": 300},
            {"timestamp": "2024-02-01T00:00:00Z", "amount": 400},
            {"no_timestamp": True, "amount": 50},  # missing timestamp
        ]

    def test_filters_within_range(self):
        txns = self._make_txns()
        result = filter_transactions_by_date(txns, "2024-01-12T00:00:00Z", "2024-01-18T23:59:59Z")
        assert len(result) == 1
        assert result[0]["amount"] == 200

    def test_inclusive_boundaries(self):
        txns = self._make_txns()
        result = filter_transactions_by_date(txns, "2024-01-10T10:00:00Z", "2024-01-10T10:00:00Z")
        assert len(result) == 1
        assert result[0]["amount"] == 100

    def test_no_results_for_empty_range(self):
        txns = self._make_txns()
        result = filter_transactions_by_date(txns, "2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z")
        assert result == []

    def test_skips_transactions_without_timestamp(self):
        txns = self._make_txns()
        result = filter_transactions_by_date(txns, "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z")
        # 4 have timestamps, 1 doesn't
        assert all("timestamp" in t for t in result)

    def test_all_transactions_in_wide_range(self):
        txns = [
            {"timestamp": "2024-01-10T10:00:00Z", "amount": 100},
            {"timestamp": "2024-06-15T12:00:00Z", "amount": 200},
        ]
        result = filter_transactions_by_date(txns, "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z")
        assert len(result) == 2

    def test_invalid_date_format_raises(self):
        txns = [{"timestamp": "2024-01-10T10:00:00Z", "amount": 100}]
        with pytest.raises(Exception):
            filter_transactions_by_date(txns, "not-a-date", "2024-12-31")


# ── aggregate_transactions_by_customer ────────────────────────────────────────

class TestAggregateTransactionsByCustomer:
    def _make_txns(self):
        return [
            {"customer_id": "cust_1", "amount": 100.0, "merchant_id": "m1"},
            {"customer_id": "cust_1", "amount": 200.0, "merchant_id": "m2"},
            {"customer_id": "cust_1", "amount": 150.0, "merchant_id": "m1"},
            {"customer_id": "cust_2", "amount": 500.0, "merchant_id": "m3"},
            {"no_customer": True, "amount": 999.0},  # missing customer_id
        ]

    def test_groups_by_customer(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert "cust_1" in result
        assert "cust_2" in result

    def test_transaction_count(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert result["cust_1"]["txn_count"] == 3
        assert result["cust_2"]["txn_count"] == 1

    def test_total_amount(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert result["cust_1"]["total_amount"] == pytest.approx(450.0)
        assert result["cust_2"]["total_amount"] == pytest.approx(500.0)

    def test_avg_amount(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert result["cust_1"]["avg_amount"] == pytest.approx(150.0)

    def test_max_min_amount(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert result["cust_1"]["max_amount"] == pytest.approx(200.0)
        assert result["cust_1"]["min_amount"] == pytest.approx(100.0)

    def test_unique_merchants(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert result["cust_1"]["unique_merchants"] == 2
        assert result["cust_2"]["unique_merchants"] == 1

    def test_skips_entries_without_customer_id(self):
        result = aggregate_transactions_by_customer(self._make_txns())
        assert "no_customer" not in result
        assert None not in result

    def test_empty_list(self):
        result = aggregate_transactions_by_customer([])
        assert result == {}

    def test_missing_amount_field(self):
        txns = [{"customer_id": "cust_x"}]
        result = aggregate_transactions_by_customer(txns)
        assert result["cust_x"]["total_amount"] == 0
        assert result["cust_x"]["avg_amount"] == 0
