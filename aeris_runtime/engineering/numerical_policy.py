"""Declared numerical resolution, separate from physical uncertainty bounds."""

DB_DECIMALS=12
# Avoid reporting precise intrinsic noise from ill-conditioned subtraction.
MIN_IDENTIFIABLE_VARIANCE_FRACTION=1e-8


def db_at_least(actual,limit):
    return round(actual,DB_DECIMALS)>=round(limit,DB_DECIMALS)


def db_at_most(actual,limit):
    return round(actual,DB_DECIMALS)<=round(limit,DB_DECIMALS)
