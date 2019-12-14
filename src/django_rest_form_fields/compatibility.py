"""
This file contains functions for different python and django version compatibility
"""
import datetime

import pytz
import re
from django.utils.timezone import make_aware, utc

if hasattr(re, 'Pattern'):
    PatternType = re.Pattern
else:
    PatternType = re._pattern_type


def to_timestamp(dt):  # type: (datetime.datetime) -> float
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = make_aware(dt, utc)
    else:
        dt = dt.astimezone(pytz.utc)

    # dt.timestamp() does not work before python 3.3
    if hasattr(dt, 'timestamp'):
        return dt.timestamp()
    else:
        return (dt - datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc)).total_seconds()
