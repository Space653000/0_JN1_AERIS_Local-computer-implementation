"""Declared numerical resolution, separate from physical uncertainty bounds."""

DB_DECIMALS=12
CYCLE_DECIMALS=12
RATIO_DECIMALS=10
GEOMETRY_DECIMALS=12
# Avoid reporting precise intrinsic noise from ill-conditioned subtraction.
MIN_IDENTIFIABLE_VARIANCE_FRACTION=1e-8


def db_at_least(actual,limit):
    return round(actual,DB_DECIMALS)>=round(limit,DB_DECIMALS)


def db_at_most(actual,limit):
    return round(actual,DB_DECIMALS)<=round(limit,DB_DECIMALS)


def cycles_at_least(actual,limit):
    return round(actual,CYCLE_DECIMALS)>=round(limit,CYCLE_DECIMALS)


def ratio_at_least(actual,limit):
    return round(actual,RATIO_DECIMALS)>=round(limit,RATIO_DECIMALS)


def geometry_value(value):
    """Dimensionless representation only; never clip a physical interval."""
    return round(value,GEOMETRY_DECIMALS)
