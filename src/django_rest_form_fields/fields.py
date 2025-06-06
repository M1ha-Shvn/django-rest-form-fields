"""
This file contains a number of custom fields to validate data with django forms
"""

import json
from datetime import timezone, datetime, date
from typing import Any, Optional, Union

import os
import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import NullBooleanSelect, Textarea
from django.utils.timezone import make_aware, now

from .compatibility import to_timestamp, PatternType, string_types
from .exceptions import FileSizeError, FileTypeError
from .validators import URLValidatorWithUnderscoreDomain


class BaseField(forms.Field):
    """
    All library fields are inherited from this base
    Adds source
    """

    def __init__(self, *args, **kwargs):
        self.source = kwargs.pop('source', None)
        super(BaseField, self).__init__(*args, **kwargs)


class InitialFixMixin(BaseField):
    """
    Fixes problem with initial not returned by some form fields
    """

    def clean(self, value):  # type: (Any) -> Any
        value = super(InitialFixMixin, self).clean(value)
        return self.initial if value is None else value


class EmptyStringFixMixing(BaseField):
    """
    Fixes some fields error, returning empty string (not None) when value is not provided
    """
    # All empty values are considered by django as "No value" by default.
    # This causes a list of errors in REST model:
    # 1) JsonField and child classes don't allow to pass empty arrays and dicts if required=True
    # 2) RestCharField and child classes don't allow to pass empty string if required=True
    # 3) run_validators() method is not called if value is in empty_values, so min_length validation doesn't work
    #    for RestCharField and value=''
    empty_values = [None]

    def to_python(self, value):  # type: (Any) -> Optional[str]
        return None if value is None else super(EmptyStringFixMixing, self).to_python(value)

    def clean(self, value):  # type: (Any) -> Optional[str]
        """
        Returns initial value, when value is not provided
        :param value: value to clean
        :return: cleaned value
        """
        if value is None:
            value = self.to_python(value)
            self.validate(value)
            # BUG I don't call self.run_validators() here, as they don't expect None, but empty string
            return self.initial
        else:
            return super(EmptyStringFixMixing, self).clean(value)

    def validate(self, value):  # type: (Optional[str]) -> None
        """
        Fixes None value validation when required is True
        :param value: value to validate
        :return: None
        """
        if value is None and self.required:
            raise ValidationError(self.error_messages['required'], code='required')

        super(EmptyStringFixMixing, self).validate(value)


class RestCharField(EmptyStringFixMixing, forms.CharField):
    """
    Wraps django.forms.forms.CharField:
    + Changes default value - None, not empty string
    + Fixes initial value bug (CharField returns empty string, ignoring 'initial' parameter)
    """
    pass


class RegexField(RestCharField):
    """
    Wraps CharField to validate via regular expression
    """

    def __init__(self, *args, **kwargs):
        self.regex = kwargs.pop('regex', None)
        self.flags = kwargs.pop('flags', 0)

        assert self.regex is None or isinstance(self.regex, (string_types, PatternType)), \
            'regex must be string if given'
        assert isinstance(self.flags, int), 'flags must be integer'

        super(RegexField, self).__init__(*args, **kwargs)
        self._match = None

    def validate(self, value):  # type: (Optional[str]) -> None
        super(RegexField, self).validate(value)
        if value is not None and self.regex:
            self._match = re.match(self.regex, str(value), self.flags)
            if not self._match:
                raise ValidationError('Value don\'t match regexp "{0}"'.format(self.regex))

    @property
    def match(self):
        return self._match


class RestChoiceField(EmptyStringFixMixing, forms.ChoiceField):
    """
    Wraps django.forms.forms.ChoiceField:
    + Changes default value - None, not empty string
    + Fixes initial value bug (CharField returns empty string, ignoring 'initial' parameter)
    + Gives opportunity to set 'choices' as iterable of values, not iterable of tuples
    """

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        if choices is not None:
            kwargs['choices'] = [ch if isinstance(ch, (list, tuple)) else (ch, ch) for ch in choices]

        EmptyStringFixMixing.__init__(self, *args, **kwargs)

        # This parameter was processed above, but was not removed
        kwargs.pop('source', None)

        forms.ChoiceField.__init__(self, *args, **kwargs)

    def validate(self, value):
        # Fixes bug with empty string passing choices
        if value is not None and self.choices and not self.valid_value(value):
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )
        super(RestChoiceField, self).validate(value)


class RestIntegerField(InitialFixMixin, forms.IntegerField):
    """
    Wraps django.forms.forms.IntegerField, fixing 'initial' property ignore
    """
    pass


class RestFloatField(InitialFixMixin, forms.FloatField):
    """
    Wraps django.forms.forms.FloatField, fixing 'initial' property ignore
    """
    pass


class PositiveIntegerField(RestIntegerField):
    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param with_zero: If true, than integer can be equal to zero, else - not.
        :param kwargs: Named arguments
        """
        with_zero = kwargs.pop('with_zero', False)
        kwargs['min_value'] = kwargs.get('min_value', 0 if with_zero else 1)
        super(PositiveIntegerField, self).__init__(*args, **kwargs)


class IdField(PositiveIntegerField):
    """
    This field validates id (integer >= 1)
    """

    def __init__(self, *args, **kwargs):
        from django.conf import settings
        max_value = getattr(settings, "ID_FIELD_MAX_VALUE", None)
        kwargs['with_zero'] = kwargs.get('with_zero', False)
        if max_value is not None:
            kwargs['max_value'] = kwargs.get('max_value', max_value)

        super(IdField, self).__init__(*args, **kwargs)


class TimestampField(RestFloatField):
    """
    Form field, containing timestamp integer. Converts given value to datetime object
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes field.
        :param args: Positional arguments
        :param in_future: Boolean. If flag is false, validates, that given date is not greater than now
        :param kwargs: Named arguments
        """
        in_future = kwargs.pop('in_future', True)

        assert type(in_future) is bool, "in_future must be boolean"
        self._in_future = in_future

        # Converts initial to timestamp, if it is given as datetime
        if 'initial' in kwargs:
            assert isinstance(kwargs['initial'], (datetime, int, float)), \
                "initial must be int, float or datetime instance"
            dt = kwargs['initial']
            if isinstance(dt, datetime):
                kwargs['initial'] = to_timestamp(dt)

        super(TimestampField, self).__init__(*args, min_value=0, max_value=2147483647, **kwargs)

    def clean(self, value):  # type: (Any) -> Optional[datetime]
        value = super(TimestampField, self).clean(value)
        if value == 0:
            # Fix python 3.6 issue with Invalid argument value=0
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
        elif value is not None:
            dt = datetime.utcfromtimestamp(value)
            return make_aware(dt, timezone.utc)
        else:
            return value

    def validate(self, value):  # type: (Optional[int]) -> None
        super(TimestampField, self).validate(value)
        if value is not None:
            if not self._in_future and value > to_timestamp(now()):
                raise ValidationError("You can't search time in future")


class DateTimeField(RestCharField):
    """
    Parses given string as datetime by given mask with datetime.strptime() method
    """
    base_type = datetime

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param mask: Mask to parse datetime string with datetime.strptime() method
        :param kwargs: Named arguments
        """
        mask = kwargs.pop("mask", "%Y-%m-%dT%H:%M:%S")
        assert isinstance(mask, string_types), "'mask' parameter must be string"

        super(DateTimeField, self).__init__(*args, **kwargs)

        self.mask = mask

    def clean(self, value):  # type: (Any) -> datetime
        value = super(DateTimeField, self).clean(value)
        if value is not None and not isinstance(value, self.base_type):
            try:
                dt = datetime.strptime(value, self.mask)
            except (ValueError, TypeError):
                raise ValidationError("Invalid value format (%s)" % self.mask)

            return make_aware(dt, timezone.utc)
        else:
            return value


class DateField(DateTimeField):
    """
    Parses month with datetime.strptime() method. Default format is %Y-%m.
    Returns datetime.date with first day of month.
    """
    base_type = date

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param mask: Mask to parse month string with datetime.strptime() method
        :param kwargs: Named arguments
        """
        mask = kwargs.pop("mask", "%Y-%m-%d")
        super(DateField, self).__init__(*args, mask=mask, **kwargs)

    def clean(self, value):  # type (Any) -> datetime.date
        value = super(DateField, self).clean(value)
        return value.date() if isinstance(value, datetime) else value


class MonthField(DateTimeField):
    """
    Parses month with datetime.strptime() method. Default format is %Y-%m.
    Returns datetime.date with first day of month.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param mask: Mask to parse month string with datetime.strptime() method
        :param kwargs: Named arguments
        """
        mask = kwargs.pop("mask", "%Y-%m")
        super(MonthField, self).__init__(*args, mask=mask, **kwargs)

    def clean(self, value):  # type (Any) -> date
        value = super(MonthField, self).clean(value)
        return value.date() if isinstance(value, datetime) else value


class TimezoneField(RestCharField):
    """
    A field containing one of standard pytz timezone names
    """

    def validate(self, value):  # type: (Optional[str]) -> None
        super(TimezoneField, self).validate(value)
        try:
            import pytz
        except ImportError as ex:
            raise ImportError('pytz is required  for TimezoneField') from ex

        if value and value not in pytz.all_timezones:
            raise ValidationError("Invalid timezone '{0}'".format(value))


class DateUnitField(RestChoiceField):
    """
    A field that validates one of date unit choices: hour, day or week
    """
    UNIT_CHOICES = ('hour', 'day', 'week')

    def __init__(self, *args, **kwargs):
        super(DateUnitField, self).__init__(*args, choices=self.UNIT_CHOICES, **kwargs)


class NullBooleanSelectWidget(NullBooleanSelect):
    """
    bf.data here calls widget.value_from_datadict(self.data, self.files, html_name)
    It does some strange tricky thing with value, converting it to boolean with rules other than we have
    That's why I take original value here
    """
    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value is None:
            return None

        elif isinstance(value, string_types) and value.lower() in ('false', '0', ''):
            value = False

        else:
            value = bool(value)

        return value


class RestBooleanField(RestCharField):
    """
    Standard BooleanField is based on /django/forms/widgets.py CheckboxInput.value_from_datadict(value)
    It works improperly for REST model: required=True + value=False => ValidationError
    This filed fixes this issue, giving opportunity to send (required or not):
    + None as default value
    + 'false', '0', '' (ignoring case) as False
    + Everything else is parsed with standard bool function
    """
    widget = NullBooleanSelectWidget

    def to_python(self, value):  # type: (Any) -> Optional[bool]
        """Returns a Python boolean object."""
        if value is None:
            return None
        elif isinstance(value, string_types) and value.lower() in ('false', '0', ''):
            value = False
        else:
            value = bool(value)
        return value


class LowerCaseEmailField(forms.EmailField):
    """
    Wraps django.forms.forms.EmailField:
    + Converts all emails to lowercase
    + Fixes initial value bug (CharField returns empty string, ignoring 'initial' parameter)
    + Changes default value - None, not empty string
    """

    def to_python(self, value):  # type: (Any) -> Optional[str]
        return value.lower() if isinstance(value, string_types) else value

    def clean(self, value):
        if value is not None:
            return forms.EmailField.clean(self, value)
        elif self.required:
            raise ValidationError(self.error_messages['required'], code='required')
        else:
            return self.initial


class ColorField(RestCharField):
    """
    This field validates color as six hex characters
    """

    def validate(self, value):  # type: (Optional[str]) -> None
        super(ColorField, self).validate(value)
        if value and not re.match('^[0-9a-f]{6}$', value):
            raise ValidationError("Color '{0}' is invalid".format(value))


class TruncatedCharField(RestCharField):
    """
    This field truncates string by given length
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param truncate_length: A positive integer, setting number of symbols to truncate input
        :param kwargs: Named arguments
        """
        truncate_length = kwargs.pop('truncate_length', 255)
        assert truncate_length is None or type(truncate_length) is int and truncate_length > 0, \
            "'truncate_length' parameter must be positive integer"

        self._truncate_length = truncate_length

        super(TruncatedCharField, self).__init__(*args, **kwargs)

    def to_python(self, value):  # type: (Any) -> Optional[str]
        if value and self._truncate_length is not None:
            value = value[:self._truncate_length]
        return super(TruncatedCharField, self).to_python(value)


class JsonField(RestCharField):
    """
    This field Json serialized string with jsonschema
    """
    widget = Textarea

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param json_schema: jsonschema library validation schema
        :param kwargs: Named arguments
        """

        self._json_schema = kwargs.pop('json_schema', None)
        super(JsonField, self).__init__(*args, **kwargs)

    def to_python(self, value):  # type: (Any) -> Optional[Union[dict, list]]
        if value is None or isinstance(value, (list, dict)):
            return value
        elif isinstance(value, string_types):
            try:
                return json.loads(value)
            except Exception as e:
                raise ValidationError("Json was not parsed [{0}]".format(str(e)))
        else:
            raise ValidationError("Invalid JSON value [{0}]".format(str(value)))

    def validate(self, value):  # type: (Optional[Union[dict, list]]) -> None
        super(JsonField, self).validate(value)
        if self._json_schema and value is not None:
            try:
                import jsonschema
            except ImportError as ex:
                raise ImportError("jsonschema library is not required for this operation") from ex

            try:
                jsonschema.validate(value, self._json_schema)
            except jsonschema.exceptions.ValidationError as ex:
                raise ValidationError(ex.message)


class ArrayField(JsonField):
    """
    Field, that parses array from string. It can be passed in 2 forms:
    + strings, split by ',' symbol
    + json-encoded array
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes field
        :param args: Positional arguments
        :param item_schema: jsonschema dict to validate each item of the array
        :param min_items: Minimum number of items in the array
        :param max_items: Maximum number of items in the array
        :param kwargs: Named arguments
        """
        item_schema = kwargs.pop('item_schema', None)
        min_items = kwargs.pop('min_items', 0)
        max_items = kwargs.pop('max_items', None)
        json_schema = {
            "type": "array",
            "minItems": min_items
        }
        if max_items:
            json_schema['maxItems'] = max_items

        if item_schema:
            json_schema['items'] = item_schema

        kwargs['json_schema'] = json_schema
        super(ArrayField, self).__init__(*args, **kwargs)

    def to_python(self, value):  # type: (Any) -> Optional[list]
        if value is None or isinstance(value, list):
            return super(ArrayField, self).to_python(value)
        elif isinstance(value, dict):
            raise ValidationError('Value is expected to be JSON array, not object')
        elif isinstance(value, string_types):
            if value.startswith('[') or value.endswith(']'):
                return super(ArrayField, self).to_python(value)
            elif value.startswith('{') and value.endswith('}'):
                raise ValidationError('Value is expected to be JSON array, not object')
            else:
                # Comma separated list
                data = value.split(',')
                item_schema = self._json_schema.get('items') if self._json_schema else None
                if item_schema and item_schema.get('type') == 'integer':
                    try:
                        return [int(item) for item in data]
                    except (ValueError, TypeError):
                        raise ValidationError('Array of integers')
                else:
                    return data
        else:
            raise ValidationError("Invalid JSON value [{0}]".format(str(value)))


class IdArrayField(ArrayField):
    """
    Field, that parses array of ids from string. Each element is cleaned by IdField()
    """

    def clean(self, value):
        if isinstance(value, set):
            value = list(value)
        res = super(IdArrayField, self).clean(value)
        if isinstance(res, list):
            id_field = IdField()
            res = [id_field.clean(item) for item in res]
        return res


class IdSetField(IdArrayField):
    """
    Field, that parses set of ids from string. Duplicated ids are removed.
    Each element is cleaned by IdField()
    """

    def clean(self, value):
        res = super(IdSetField, self).clean(value)
        if isinstance(res, list):
            res = set(res)
        return res


class UrlField(RegexField):
    """
    Field validates url string
    """

    def __init__(self, *args, with_underscore_domain=True, **kwargs):  # type (bool) -> None
        super(UrlField, self).__init__(*args, **kwargs)
        self.with_underscore_domain = with_underscore_domain

    def to_python(self, value):  # type: (Any) -> Optional[str]
        if isinstance(value, string_types):
            value = value.strip()
        return super(UrlField, self).to_python(value)

    def validate(self, value):  # type: (Optional[str]) -> None
        super(UrlField, self).validate(value)
        if isinstance(value, string_types):
            validator_cls = URLValidatorWithUnderscoreDomain if self.with_underscore_domain else URLValidator
            v = validator_cls(schemes=['http', 'https'])
            v(value)


class HexField(RestCharField):
    """
    Field validates hexadecimal string
    """

    def validate(self, value):  # type: (Optional[str]) -> None
        super(HexField, self).validate(value)
        if isinstance(value, string_types) and not re.match(r'[a-z0-9]*', value):
            raise ValidationError("Field can contain only hexadecimal small characters (a-z, 0-9)")


class UUIDField(RegexField):
    """
    Field validates correct UUID string
    """

    def __init__(self, *args, **kwargs):
        kwargs['regex'] = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        super(UUIDField, self).__init__(*args, **kwargs)


class FileField(forms.FileField):
    """
    Wraps django.forms.forms.FileField, adding:
    + file size validation
    + file extension validation
    """

    def __init__(self, *args, **kwargs):
        max_size = kwargs.pop('max_size', None)
        valid_extensions = kwargs.pop('valid_extensions', None)

        self.valid_extensions = valid_extensions
        self.size = max_size

        if self.valid_extensions is not None:
            assert isinstance(self.valid_extensions, (tuple, set, list)), "valid_extensions must be tuple, list or set"
            assert len(self.valid_extensions) > 0, "valid_extensions can't be empty, if given"

        if self.size is not None:
            assert type(self.size) is int and self.size > 0, "size must be positive integer"

        super(FileField, self).__init__(*args, **kwargs)

    def validate(self, value):  # type (IO) -> None
        super(FileField, self).validate(value)
        if self.valid_extensions is not None and value:
            ext = os.path.splitext(value.name)[1][1:].lower()
            if ext not in self.valid_extensions:
                raise FileTypeError(ext, self.valid_extensions)

        if self.size is not None and value:
            if value.size > self.size:
                raise FileSizeError(self.size, value.size)

    def clean(self, data, initial=None):
        # FileField provides InitialFixMixin functionality with special parameter
        return super(FileField, self).clean(data, initial=initial if initial is not None else self.initial)
