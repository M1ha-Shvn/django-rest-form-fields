"""
This file contains functions for different python and django version compatibility
"""
from time import mktime

import datetime

import pytz
from django.utils.timezone import make_aware, utc


def to_timestamp(dt):  # type: (datetime.datetime) -> float
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = make_aware(dt, utc)
    else:
        dt = dt.astimezone(pytz.utc)

    # dt.timestamp() does not work before python 3.3
    if hasattr(dt, 'timestamp'):
        return dt.timestamp()
    else:
        # BUG This can get improper dst (summer time) for Russia, so time may differ in 1 hour
        # Seems that this is a pytz bug
        return mktime(dt.timetuple()) + dt.microsecond / 1e6
