from datetime import date


def get_current_financial_date():
    today = date.today()
    financial_year_start = date(
        today.year, 4, 1
    )  # Assuming April 1st as the start of the financial year

    if today < financial_year_start:
        # If the current date is before the start of the financial year, use the previous year
        financial_year_start = date(today.year - 1, 4, 1)

    print(today, "today", financial_year_start, "financial_year_start")
    return today, financial_year_start


MONTHS = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
