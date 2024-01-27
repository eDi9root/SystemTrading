from datetime import datetime

def check_transaction_open():
    """
    Check whether the current is market time
    (09:00 ~ 15:20)
    :return:
    """
    now = datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return start_time <= now <= end_time


def check_transaction_closed():
    """
    Check whether the current is the end of the market
    :return:
    """
    now = datetime.now()
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return end_time < now


def check_adjacent_transaction_closed():
    """
    Check if the current time is near the end of the market
    (for the purchase time)
    :return:
    """
    now = datetime.now()
    base_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return base_time <= now < end_time