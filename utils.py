from datetime import date


def is_valid_age(bday: date):
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))

    if age < 16 or age > 40:
        return False

    return True
