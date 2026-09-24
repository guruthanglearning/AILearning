#!/usr/bin/env python3
"""
Generate a larger synthetic labeled transaction dataset for training the
demo XGBoost fraud model (scripts/manage_models.py --action train).

data/sample/synthetic_transactions.csv only has 30 rows - nowhere near
enough for XGBoost to learn anything. This generates a few thousand rows
instead, sampling fraud vs. legitimate transactions from two different
feature distributions so the resulting model has genuine, if modest,
predictive signal. It's still synthetic/toy data for a learning-sandbox
project, not real fraud data - the sampling rule below is hand-written,
not derived from actual fraud cases.

The feature choices here are deliberately aimed at what
app/utils/feature_engineering.py's select_features_for_ml() actually
passes to the model: amount, is_online, hour_of_day/day_of_week,
merchant_risk_score (driven by merchant_id/merchant_name), and
location_risk_score (driven by merchant_country, only when lat/long are
present). Most of the other engineered features (txn_count_*,
avg_amount_7d, behavior_anomaly_score, etc.) are hardcoded mock constants
in feature_engineering.py regardless of input, so varying them here
wouldn't teach the model anything.
"""

import argparse
import random
from datetime import datetime, timedelta

import pandas as pd

# Mirrors app/models/ml_model.py's small hardcoded merchant risk table, so
# merchant_risk_score has real variance across rows instead of always
# landing on the 0.5 "unknown merchant" default.
LOW_RISK_MERCHANTS = [("merch_24680", "TechWorld Store"), ("merch_98765", "Corner Grocery")]
HIGH_RISK_MERCHANTS = [("merch_13579", "QuickCash Kiosk")]
DEFAULT_MERCHANTS = [
    (f"merch_{i:05d}", name)
    for i, name in enumerate(
        [
            "Downtown Cafe", "City Electronics", "Family Pharmacy", "Metro Grocery",
            "Sunset Diner", "Harbor Clothing", "Central Utilities", "Bright Gas Station",
        ],
        start=1,
    )
]

MERCHANT_CATEGORIES = [
    "Grocery", "Gas Station", "Restaurant", "Pharmacy", "Utilities",
    "Clothing", "Entertainment", "Electronics", "Digital Goods",
    "Jewelry", "Luxury Goods",
]

# Spans app/utils/feature_engineering.py's calculate_country_risk tiers.
# Sanctioned countries (RU, BY, KP, IR, SY, CU, VE) are deliberately
# excluded - those short-circuit in FraudDetectionService.detect_fraud()
# before the ML model ever runs, so they wouldn't teach the classifier
# anything relevant to its actual job.
LOW_RISK_COUNTRIES = ["US", "CA", "GB", "DE", "FR", "AU"]
MEDIUM_RISK_COUNTRIES = ["TR", "ZA", "TH", "MY"]
HIGH_RISK_COUNTRIES = ["NG", "PK", "CN", "IN", "BR", "MX", "RO", "UA"]

CURRENCIES = ["USD", "EUR", "GBP"]


def _pick_merchant(rng, fraud_leaning):
    """Occasionally pick a merchant from the low/high-risk pools MLModel's
    hardcoded lookup recognizes, so merchant_risk_score carries signal."""
    if fraud_leaning and rng.random() < 0.35:
        return rng.choice(HIGH_RISK_MERCHANTS)
    if not fraud_leaning and rng.random() < 0.35:
        return rng.choice(LOW_RISK_MERCHANTS)
    return rng.choice(LOW_RISK_MERCHANTS + HIGH_RISK_MERCHANTS + DEFAULT_MERCHANTS)


def generate(n_rows: int, fraud_rate: float, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    base_time = datetime(2025, 1, 1)
    rows = []

    for i in range(n_rows):
        is_fraud = rng.random() < fraud_rate

        merchant_id, merchant_name = _pick_merchant(rng, is_fraud)
        # Missing/placeholder merchant name also drives merchant_risk_score
        # up (see get_merchant_risk_score) - let some fraud-leaning rows
        # exercise that path too, instead of only the hardcoded IDs.
        if is_fraud and rng.random() < 0.2:
            merchant_name = rng.choice(["", "Unknown", "N/A"])

        is_online = rng.random() < (0.85 if is_fraud else 0.5)

        if is_fraud:
            amount = round(rng.uniform(300, 4000), 2)
            hour = rng.choice([1, 2, 3, 4] * 3 + list(range(24)))
        else:
            amount = round(rng.uniform(5, 400), 2)
            hour = rng.choice(list(range(7, 23)) * 3 + list(range(24)))

        day_offset = rng.randint(0, 269)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        timestamp = (base_time + timedelta(days=day_offset)).replace(
            hour=hour, minute=minute, second=second
        )

        has_geo = rng.random() < 0.6
        if has_geo:
            country = rng.choice(
                HIGH_RISK_COUNTRIES
                if is_fraud and rng.random() < 0.5
                else LOW_RISK_COUNTRIES + MEDIUM_RISK_COUNTRIES
            )
            latitude = round(rng.uniform(-60, 60), 4)
            longitude = round(rng.uniform(-179, 179), 4)
        else:
            country = rng.choice(LOW_RISK_COUNTRIES + MEDIUM_RISK_COUNTRIES + HIGH_RISK_COUNTRIES)
            latitude = None
            longitude = None

        rows.append(
            {
                "transaction_id": f"tx_{i:05d}",
                "card_id": f"card_{rng.randint(1, 800):05d}",
                "merchant_id": merchant_id,
                "merchant_name": merchant_name,
                "timestamp": timestamp.isoformat(),
                "amount": amount,
                "merchant_category": rng.choice(MERCHANT_CATEGORIES),
                "merchant_country": country,
                "customer_id": f"cust_{rng.randint(1, 500):05d}",
                "is_online": is_online,
                "currency": rng.choice(CURRENCIES),
                "latitude": latitude,
                "longitude": longitude,
                "is_fraud": is_fraud,
            }
        )

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic labeled transactions for training")
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--fraud-rate", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="data/sample/synthetic_transactions_large.csv")
    args = parser.parse_args()

    df = generate(args.rows, args.fraud_rate, args.seed)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df)} rows ({int(df['is_fraud'].sum())} fraud, {df['is_fraud'].mean():.1%}) to {args.output}")


if __name__ == "__main__":
    main()
