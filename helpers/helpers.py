# helpers/helpers.py

from datetime import datetime
from dateutil.relativedelta import relativedelta



# ---- Date Utils

def generate_month_range(start_date, end_date):
    """
    Returns a list of 'YYYY-MM' strings between two dates, inclusive.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    months = []
    current = start_date
    while current <= end_date:
        months.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)
    return months



def validate_date_range(start_date, end_date):
    if isinstance(start_date, str): start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str): end_date = datetime.strptime(end_date, "%Y-%m-%d")
    if end_date < start_date:
        raise ValueError("End date must be after start date.")

# Financial Utilities

def distribute_amount_evenly(allocated_amount: float, months: list[str]) -> dict[str, float]:
    """Evenly distribute the allocated amount across the months without exceeding it."""
    monthly_base = round(allocated_amount / len(months), 2)
    distribution = {month: monthly_base for month in months}

    # Calculate how much was actually distributed
    total_distributed = round(monthly_base * len(months), 2)
    remainder = round(allocated_amount - total_distributed, 2)

    # Add the remainder to the final month to match total
    if remainder != 0:
        last_month = months[-1]
        distribution[last_month] = round(distribution[last_month] + remainder, 2)

    return distribution

# ----- String Utilities -----
def normalize_string(value, title_case=True):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip()
    return value.title() if title_case else value