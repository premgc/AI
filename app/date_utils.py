from datetime import datetime, timedelta
import re


def parse_date_range(query: str):
    q = query.lower()

    today = datetime.today()

    # last 7 days
    if "last 7 days" in q:
        return today - timedelta(days=7), today

    # last 30 days
    if "last 30 days" in q:
        return today - timedelta(days=30), today

    # this month
    if "this month" in q:
        start = today.replace(day=1)
        return start, today

    # specific month (march, april...)
    months = {
        "january": 1, "february": 2, "march": 3,
        "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12
    }

    for month_name, month_num in months.items():
        if month_name in q:
            year = today.year
            start = datetime(year, month_num, 1)

            if month_num == 12:
                end = datetime(year, 12, 31)
            else:
                end = datetime(year, month_num + 1, 1) - timedelta(days=1)

            return start, end

    # between dates (simple)
    match = re.search(r"between (\d{1,2}) and (\d{1,2})", q)
    if match:
        d1, d2 = int(match.group(1)), int(match.group(2))
        start = today.replace(day=d1)
        end = today.replace(day=d2)
        return start, end

    return None, None