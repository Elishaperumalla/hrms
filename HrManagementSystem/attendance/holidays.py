from datetime import timedelta


# Dates must be confirmed for each calendar year.
# Add only the public/festival holidays your company observes.
FIXED_HOLIDAYS = {
    (1, 1): "New Year",
    (1, 26): "Republic Day",
    (8, 15): "Independence Day",
    (10, 2): "Gandhi Jayanti",
    (12, 25): "Christmas",
}

VARIABLE_HOLIDAYS = {
    2026: {
        (1, 14): "Sankranthi",
        # Add confirmed dates for:
        # Holi, Vinayaka Chavithi, Dussehra and Diwali.
    },
    2027: {
        # Add confirmed dates for the variable festivals.
    },
}


def get_public_holidays(year):
    from datetime import date

    holidays = {}

    for (month, day), name in FIXED_HOLIDAYS.items():
        holidays[date(year, month, day)] = name

    for (month, day), name in VARIABLE_HOLIDAYS.get(
        year, {}
    ).items():
        try:
            holidays[date(year, month, day)] = name
        except ValueError:
            continue

    return holidays


def is_weekend(day):
    return day.weekday() >= 5


def is_public_holiday(day):
    return day in get_public_holidays(day.year)


def is_non_working_day(day):
    return is_weekend(day) or is_public_holiday(day)


def get_working_days(start_date, end_date):
    count = 0
    current = start_date

    while current <= end_date:
        if not is_non_working_day(current):
            count += 1

        current += timedelta(days=1)

    return count