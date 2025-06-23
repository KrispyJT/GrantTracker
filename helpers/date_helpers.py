# helpers/date_helpers.py

from datetime import datetime
from dateutil.relativedelta import relativedelta

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
