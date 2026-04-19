import math


MONTH_PRICE_RUB = 100
MONTH_DAYS = 30


def calculate_price(plan_type: str, days_count: int) -> int:
    if plan_type == "trial":
        return 0

    if plan_type == "month":
        return MONTH_PRICE_RUB

    raw_price = days_count * MONTH_PRICE_RUB / MONTH_DAYS
    return math.ceil(raw_price)