from input_algorithms.errors import BadSpecValue

from dateutil.relativedelta import relativedelta
from datetime import datetime
import enum

class Sizes(enum.Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

valid_sizes = [s.value for s in Sizes]

def common_size(min_size, max_size):
    if min_size not in valid_sizes or max_size not in valid_sizes:
        raise BadSpecValue("Size must be one of the valid units", first=min_size, second=max_size, valid=valid_sizes)
    return valid_sizes[min([valid_sizes.index(min_size), valid_sizes.index(max_size)])]

def convert_amount(old_size, new_size, old_num):
    now = datetime.utcnow()
    class seconds_diff(relativedelta):
        def _fix(self):
            pass

    if old_size == Sizes.WEEK.value and new_size == Sizes.YEAR.value and old_num % 52 == 0:
        old_num += 1

    delta = relativedelta(**{"{0}s".format(old_size): old_num})
    if new_size == Sizes.MONTH.value:
        return relativedelta(now+delta, now).months
    elif new_size == Sizes.YEAR.value:
        return relativedelta(now+delta, now).years

    diff = seconds_diff(now+delta, now).seconds

    if new_size == Sizes.SECOND.value:
        return diff
    elif new_size == Sizes.MINUTE.value:
        return diff / 60.0
    elif new_size == Sizes.HOUR.value:
        return diff / 3600.0
    elif new_size == Sizes.DAY.value:
        return diff / 3600.0 / 24.0
    elif new_size == Sizes.WEEK.value:
        return diff / 3600.0 / 24.0 / 7.0
    else:
        raise BadSpecValue("Sorry, can't convert amount", have=old_size, want=new_size)

