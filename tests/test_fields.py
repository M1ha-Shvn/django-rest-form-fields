"""
This file contains tests for fields.py
"""

import datetime
import json
import random
import re
import uuid
from io import BytesIO
from unittest import TestCase

import six
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware, utc

from src.compatibility import to_timestamp
from src.fields import RestBooleanField, LowerCaseEmailField, TimestampField, DateUnitField, ColorField, \
    TruncatedCharField, JsonField, ArrayField, UrlField, RestCharField, RestChoiceField, RestIntegerField, RegexField, \
    UUIDField, DateTimeField, MonthField, FileField, RestFloatField


class LowerCaseEmailFieldTest(TestCase):
    def test_to_lower(self):
        f = LowerCaseEmailField()
        self.assertEqual(f.clean('TeSt@mail.ru1'), 'test@mail.ru1')

    def test_required(self):
        f = LowerCaseEmailField(required=False)
        self.assertEqual(None, f.clean(None))

        f = LowerCaseEmailField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        f = LowerCaseEmailField(required=False, initial='test@mail.ru')
        self.assertEqual('test@mail.ru', f.clean(None))


class RestBooleanFieldTest(TestCase):
    def test_true(self):
        f = RestBooleanField()
        self.assertEqual(True, f.clean('true'))

    def test_1(self):
        f = RestBooleanField()
        self.assertEqual(True, f.clean('1'))

    def test_false(self):
        f = RestBooleanField()
        self.assertEqual(False, f.clean('false'))

    def test_0(self):
        f = RestBooleanField()
        self.assertEqual(False, f.clean('0'))

    def test_empty_string(self):
        f = RestBooleanField()
        self.assertEqual(False, f.clean(''))

    def test_not_empty_string(self):
        f = RestBooleanField()
        self.assertEqual(True, f.clean('some_text'))

    def test_None(self):
        f = RestBooleanField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_not_required_true(self):
        f = RestBooleanField(required=False)
        self.assertEqual(True, f.clean('true'))

    def test_not_required_1(self):
        f = RestBooleanField(required=False)
        self.assertEqual(True, f.clean('1'))

    def test_not_required_false(self):
        f = RestBooleanField(required=False)
        self.assertEqual(False, f.clean('false'))

    def test_not_required_0(self):
        f = RestBooleanField(required=False)
        self.assertEqual(False, f.clean('0'))

    def test_not_required_empty_string(self):
        f = RestBooleanField(required=False)
        self.assertEqual(False, f.clean(''))

    def test_not_required_not_empty_string(self):
        f = RestBooleanField(required=False)
        self.assertEqual(True, f.clean('some_text'))

    def test_not_required_None(self):
        f = RestBooleanField(required=False)
        self.assertEqual(None, f.clean(None))

    def test_initial_true(self):
        f = RestBooleanField(required=False, initial=True)
        self.assertEqual(True, f.clean(None))

    def test_initial_false(self):
        f = RestBooleanField(required=False, initial=False)
        self.assertEqual(False, f.clean(None))

    def test_required(self):
        f = RestBooleanField()
        with self.assertRaises(ValidationError):
            f.clean(None)


class RestIntegerFieldTest(TestCase):
    def test_correct(self):
        f = RestIntegerField()
        self.assertEqual(1, f.clean(1))
        f = RestIntegerField()
        self.assertEqual(123, f.clean(123))
        f = RestIntegerField()
        self.assertEqual(0, f.clean(0))
        f = RestIntegerField()
        self.assertEqual(-10, f.clean(-10))
        f = RestIntegerField()
        self.assertEqual(1, f.clean('1'))
        f = RestIntegerField()
        self.assertEqual(123, f.clean('123'))
        f = RestIntegerField()
        self.assertEqual(0, f.clean('0'))
        f = RestIntegerField()
        self.assertEqual(-10, f.clean('-10'))

    def test_required(self):
        f = RestIntegerField(required=True)
        with self.assertRaises(ValidationError):
            f.clean(None)

        f = RestIntegerField(required=False)
        self.assertEqual(None, f.clean(None))

    def test_initial(self):
        f = RestIntegerField(required=True, initial=123)
        with self.assertRaises(ValidationError):
            f.clean(None)

        f = RestIntegerField(required=False, initial=123)
        self.assertEqual(123, f.clean(None))


class RestFloatFieldTest(TestCase):
    def test_correct(self):
        f = RestFloatField()
        self.assertEqual(1, f.clean(1))
        f = RestFloatField()
        self.assertEqual(123.456, f.clean(123.456))
        f = RestFloatField()
        self.assertEqual(0, f.clean(0))
        f = RestFloatField()
        self.assertEqual(-10.123, f.clean(-10.123))
        f = RestFloatField()
        self.assertEqual(1, f.clean('1'))
        f = RestFloatField()
        self.assertEqual(123, f.clean('123.0'))
        f = RestFloatField()
        self.assertEqual(0, f.clean('0'))
        f = RestFloatField()
        self.assertEqual(-10, f.clean('-10'))

    def test_required(self):
        f = RestFloatField(required=True)
        with self.assertRaises(ValidationError):
            f.clean(None)

        f = RestFloatField(required=False)
        self.assertEqual(None, f.clean(None))

    def test_initial(self):
        f = RestFloatField(required=True, initial=123.0)
        with self.assertRaises(ValidationError):
            f.clean(None)

        f = RestFloatField(required=False, initial=123.0)
        self.assertEqual(123, f.clean(None))


class RestCharFieldTest(TestCase):
    def test_required(self):
        f = RestCharField(required=False)
        self.assertEqual(None, f.clean(None))

        f = RestCharField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        test_data = "test_string"
        f = RestCharField(required=False, initial=test_data)
        self.assertEqual(test_data, f.clean(None))


class RegexFieldTest(TestCase):
    def test_required(self):
        f = RegexField(required=False, regex=r'.*')
        self.assertEqual(None, f.clean(None))

        f = RegexField(regex=r'.*')
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        test_data = "test_string"
        f = RegexField(required=False, initial=test_data, regex=r'.*')
        self.assertEqual(test_data, f.clean(None))

    def test_regex_valid(self):
        test_data = "test_string"
        f = RegexField(regex=r'^test.*$')
        self.assertEqual(test_data, f.clean(test_data))

    def test_regex_invalid(self):
        test_data = "test_string"
        f = RegexField(regex=r'^test1.*$')
        with self.assertRaises(ValidationError):
            f.clean(test_data)

    def test_init_assertions(self):
        with self.assertRaises(AssertionError):
            RegexField(regex=[])

        with self.assertRaises(AssertionError):
            RegexField(regex=r'', flags=None)

        with self.assertRaises(AssertionError):
            RegexField(regex=r'', flags=[])

    def test_flags(self):
        f = RegexField(regex=r'^test.*$')
        self.assertEqual("test_string", f.clean("test_string"))
        with self.assertRaises(ValidationError):
            f.clean("tESt_string")

        f = RegexField(regex=r'^test.*$', flags=re.I)
        self.assertEqual("test_string", f.clean("test_string"))
        self.assertEqual("tESt_string", f.clean("tESt_string"))


class RestChoiceFieldTest(TestCase):
    def test_choices_array(self):
        f = RestChoiceField(choices=["a", "b", "c"])
        self.assertEqual("a", f.clean("a"))

    def test_choices_tuples(self):
        f = RestChoiceField(choices=[("a", "a"), ("b", "b"), ("c", "c")])
        self.assertEqual("c", f.clean("c"))

    def test_choices_mixed(self):
        f = RestChoiceField(choices=[("a", "a"), "b", ("c", "c")])
        self.assertEqual("b", f.clean("b"))

    def test_invalid(self):
        f = RestChoiceField(choices=[("a", "a"), "b", ("c", "c")])
        with self.assertRaises(ValidationError):
            f.clean("d")

    def test_empty_string(self):
        f = RestChoiceField(required=False)
        self.assertEqual('', f.clean(''))

    def test_required(self):
        f = RestChoiceField(required=False)
        self.assertEqual(None, f.clean(None))

        f = RestChoiceField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        test_data = "test_string"
        f = RestChoiceField(required=False, initial=test_data)
        self.assertEqual(test_data, f.clean(None))


class TimestampFieldTest(TestCase):
    def test_now(self):
        now = make_aware(datetime.datetime.now().replace(microsecond=0), utc)
        now_ts = to_timestamp(now)
        f = TimestampField()
        res = f.clean(now_ts)
        self.assertEqual(now, res)

    def test_timezones(self):
        dt = datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=utc)
        ts = to_timestamp(dt)
        f = TimestampField()
        res = f.clean(ts)
        self.assertEqual(dt, res)

        dt = datetime.datetime(2017, 1, 1, 0, 0, 0)
        ts = to_timestamp(dt)
        f = TimestampField()
        res = f.clean(ts)
        dt = dt.replace(tzinfo=utc)
        self.assertEqual(dt, res)

    def test_bounds(self):
        f = TimestampField(in_future=True)
        f.clean(0)
        f.clean(100000000)
        f.clean(2147483647)
        with self.assertRaises(ValidationError):
            f.clean(-random.randint(1, 2147483648))

        with self.assertRaises(ValidationError):
            f.clean(random.randint(2147483648, 4000000000))

    def test_in_future(self):
        f = TimestampField()
        future = make_aware(datetime.datetime.now().replace(microsecond=0), utc) + datetime.timedelta(hours=1)
        with self.assertRaises(ValidationError):
            f.clean(future)

    def test_initial(self):
        now = make_aware(datetime.datetime.utcnow().replace(microsecond=0), utc)
        f = TimestampField(initial=now, required=False)
        res = f.clean(None)
        self.assertEqual(now, res)
        f = TimestampField(initial=to_timestamp(now), required=False)
        res = f.clean(None)
        self.assertEqual(now, res)

    def test_required(self):
        f = TimestampField(required=False)
        self.assertEqual(None, f.clean(None))

        f = TimestampField()
        with self.assertRaises(ValidationError):
            f.clean(None)


class DateTimeFieldTest(TestCase):
    def test_now(self):
        now = make_aware(datetime.datetime.now().replace(microsecond=0), utc)
        f = DateTimeField()
        res = f.clean(now.strftime("%Y-%m-%dT%H:%M:%S"))
        self.assertEqual(now, res)

    def test_initial(self):
        now = make_aware(datetime.datetime.now().replace(microsecond=0), utc)
        f = DateTimeField(initial=now, required=False)
        res = f.clean(None)
        self.assertEqual(now, res)

    def test_required(self):
        f = DateTimeField(required=False)
        self.assertEqual(None, f.clean(None))

        f = DateTimeField()
        with self.assertRaises(ValidationError):
            f.clean(None)


class MonthFieldTest(TestCase):
    def test_now(self):
        now = make_aware(datetime.datetime.now().replace(microsecond=0), utc)
        f = MonthField()
        res = f.clean(now.strftime("%Y-%m"))
        self.assertEqual(now.date().replace(day=1), res)

    def test_initial(self):
        f = MonthField(initial='2017-01', required=False)
        res = f.clean(None)
        self.assertEqual(datetime.date(2017, 1, 1), res)

    def test_required(self):
        f = MonthField(required=False)
        self.assertEqual(None, f.clean(None))

        f = MonthField()
        with self.assertRaises(ValidationError):
            f.clean(None)


class DateUnitFieldTest(TestCase):
    def test_day(self):
        f = DateUnitField()
        self.assertEqual('day', f.clean('day'))

    def test_hour(self):
        f = DateUnitField()
        self.assertEqual('hour', f.clean('hour'))

    def test_week(self):
        f = DateUnitField()
        self.assertEqual('week', f.clean('week'))

    def test_invalid(self):
        f = DateUnitField()
        with self.assertRaises(ValidationError):
            f.clean('something')

    def test_required(self):
        f = DateUnitField(required=False)
        self.assertEqual(None, f.clean(None))

        f = DateUnitField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        f = DateUnitField(required=False, initial='day')
        self.assertEqual('day', f.clean(None))


class ColorFieldTest(TestCase):
    def test_color(self):
        f = ColorField()
        self.assertEqual('afafaf', f.clean('afafaf'))

    def test_invalid(self):
        f = ColorField()
        with self.assertRaises(ValidationError):
            f.clean('test')

    def test_required(self):
        f = ColorField(required=False)
        self.assertEqual(None, f.clean(None))

        f = ColorField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        f = ColorField(required=False, initial='afafaf')
        self.assertEqual('afafaf', f.clean(None))


class TruncatedCharFieldTest(TestCase):
    def test_short_string(self):
        f = TruncatedCharField()
        self.assertEqual('afafaf', f.clean('afafaf'))

    def test_no_max(self):
        test_str = 't' * 10000
        f = TruncatedCharField(truncate_length=None)
        self.assertEqual(test_str, f.clean(test_str))

    def test_long_string(self):
        f = TruncatedCharField()
        self.assertEqual(f.clean('t' * 100500), 't' * 255)

    def test_required(self):
        f = TruncatedCharField(required=False)
        self.assertEqual(None, f.clean(None))

        f = TruncatedCharField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        f = TruncatedCharField(required=False, initial='afafaf')
        self.assertEqual('afafaf', f.clean(None))


class JsonFieldTest(TestCase):
    TEST_SCHEMA = {
        'type': 'object',
        'properties': {
            'test': {
                'type': 'integer',
                'minimum': 1
            }
        }
    }

    def test_json_correct(self):
        test_data = {'test': 1}
        f = JsonField(json_schema=self.TEST_SCHEMA)
        self.assertDictEqual(test_data, f.clean(json.dumps(test_data)))

    def test_json_incorrect(self):
        test_data = {'test': 0}
        f = JsonField(json_schema=self.TEST_SCHEMA)
        with self.assertRaises(ValidationError):
            f.clean(json.dumps(test_data))

    def test_required(self):
        f = JsonField(required=False)
        self.assertEqual(None, f.clean(None))

        f = JsonField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        test_data = {'inital': True}
        f = JsonField(required=False, initial=test_data)
        self.assertEqual(test_data, f.clean(None))


class ArrayFieldTest(TestCase):
    def test_json_valid(self):
        f = ArrayField()
        self.assertListEqual([1, 2, 3], f.clean('[1, 2, 3]'))

    def test_json_object(self):
        f = ArrayField()
        with self.assertRaises(ValidationError):
            f.clean('{}')

    def test_json_invalid(self):
        f = ArrayField()
        with self.assertRaises(ValidationError):
            f.clean('[1,2,3')

    def test_comma_separated(self):
        f = ArrayField()
        self.assertListEqual(['1', '2', '3'], f.clean('1,2,3'))

    def test_items_valid(self):
        test_data = [{'test': 1}, {'test': 2}]
        f = ArrayField(item_schema=JsonFieldTest.TEST_SCHEMA)
        self.assertListEqual(test_data, f.clean(json.dumps(test_data)))

    def test_items_invalid(self):
        test_data = [{'test': 1}, {'test': 0}]
        f = ArrayField(item_schema=JsonFieldTest.TEST_SCHEMA)
        with self.assertRaises(ValidationError):
            f.clean(json.dumps(test_data))

    def test_min_items_valid(self):
        test_data = [{'test': 1}]
        f = ArrayField(min_items=1)
        self.assertListEqual(test_data, f.clean(json.dumps(test_data)))

    def test_min_items_invalid(self):
        test_data = []
        f = ArrayField(min_items=1)
        with self.assertRaises(ValidationError):
            f.clean(json.dumps(test_data))

    def test_max_items_valid(self):
        test_data = [{'test': 1}, {'test': 1}]
        f = ArrayField(max_items=2)
        self.assertListEqual(test_data, f.clean(json.dumps(test_data)))

    def test_max_items_invalid(self):
        test_data = [{'test': 1}, {'test': 1}, {'test': 1}]
        f = ArrayField(max_items=2)
        with self.assertRaises(ValidationError):
            f.clean(json.dumps(test_data))

    def test_required(self):
        f = ArrayField(required=False)
        self.assertEqual(None, f.clean(None))

        f = ArrayField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        test_data = [1, 2, 3]
        f = ArrayField(required=False, initial=test_data)
        self.assertEqual(test_data, f.clean(None))


class UrlFieldTest(TestCase):
    def test_url_valid(self):
        test_data = 'http://test.ru'
        f = UrlField()
        self.assertEqual(test_data, f.clean(test_data))

    def test_url_invalid(self):
        test_data = 'not_url'
        f = UrlField()
        with self.assertRaises(ValidationError):
            f.clean(test_data)

    def test_required(self):
        f = UrlField(required=False)
        self.assertEqual(None, f.clean(None))

        f = UrlField()
        with self.assertRaises(ValidationError):
            f.clean(None)

    def test_initial(self):
        f = UrlField(required=False, initial='http://test.ru')
        self.assertEqual('http://test.ru', f.clean(None))


class UUIDFieldTest(TestCase):
    def test_uuid_valid(self):
        test_data = str(uuid.uuid4())
        f = UUIDField()
        self.assertEqual(test_data, f.clean(test_data))

    def test_url_invalid(self):
        test_data = 'not_uuid'
        f = UUIDField()
        with self.assertRaises(ValidationError):
            f.clean(test_data)

    def test_required(self):
        f = UUIDField(required=False)
        self.assertEqual(None, f.clean(None))

    def test_initial(self):
        init = str(uuid.uuid4())
        f = UUIDField(required=False, initial=init)
        self.assertEqual(init, f.clean(None))


class FileFieldTest(TestCase):
    @staticmethod
    def _get_test_file(extension='txt'):
        f = BytesIO(six.b('test'))
        f.name = 'test.' + extension
        f.size = len(f.getvalue())
        return f

    def test_file_valid(self):
        test_data = self._get_test_file()
        f = FileField()
        self.assertEqual(test_data, f.clean(test_data))

    def test_file_invalid(self):
        f = FileField()
        with self.assertRaises(ValidationError):
            f.clean('123')

    def test_file_extensions(self):
        with self.assertRaises(AssertionError):
            FileField(valid_extensions="test")

        test_file = self._get_test_file('pdf')

        f = FileField(valid_extensions=["pdf", "png"])
        self.assertEqual(test_file, f.clean(test_file))

        test_file.name = 'TEST.PDF'
        self.assertEqual(test_file, f.clean(test_file))

        f = FileField(valid_extensions=["png", "jpg"])
        with self.assertRaises(ValidationError):
            f.clean(f)

    def test_file_size(self):
        with self.assertRaises(AssertionError):
            FileField(max_size="test")

        test_file = self._get_test_file('pdf')

        f = FileField(max_size=2*1024*1024)
        self.assertEqual(test_file, f.clean(test_file))

        test_file.size = 1*1024*1024
        self.assertEqual(test_file, f.clean(test_file))

        test_file.size = 2 * 1024 * 1024 - 1
        self.assertEqual(test_file, f.clean(test_file))

        test_file.size = 2 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            f.clean(f)

    def test_required(self):
        f = FileField(required=False)
        self.assertEqual(None, f.clean(None))

    def test_initial(self):
        init = self._get_test_file()
        f = FileField(required=False, initial=init)
        self.assertEqual(init, f.clean(None))