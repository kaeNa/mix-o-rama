from collections import defaultdict
from datetime import datetime
from enum import Enum
from peewee import CharField
import logging

logger = logging.getLogger(__name__)


def make_timeout(delay_ms):
    starttime = datetime.now().timestamp()

    def time_is_out():
        return datetime.now().timestamp() > starttime + (delay_ms/1000)

    return time_is_out


class DefaultFactoryDict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError((key,))
        self[key] = value = self.default_factory(key)
        return value


class MaxObserver:
    value = 0

    def observe(self, observing):
        self.value = max(self.value, observing)
        return True


def is_enum(obj):
    """Determines whether the object is an enum.Enum."""
    try:
        return issubclass(obj, Enum) if isinstance(obj, type) \
            else isinstance(obj, Enum)
    except TypeError:
        return False


class EnumField(CharField):
    """CharField-based enumeration field."""

    def __init__(self, enum, *args, max_length=None, null=None, **kwargs):
        """Initializes the enumeration field with the possible values.

        :enum: The respective enumeration.
        :max_length: Ignored.
        :null: Ignored.
        """
        super().__init__(*args, max_length=max_length, null=null, **kwargs)
        self.enum = enum

    @property
    def enum(self):
        """Returns the enumeration values."""
        return self._enum

    @enum.setter
    def enum(self, enum):
        """Sets the enumeration values."""
        if is_enum(enum):
            self._enum = enum
        else:
            self._enum = set(enum)

    @property
    def values(self):
        """Yields appropriate database values."""
        if is_enum(self.enum):
            for item in self.enum:
                yield item.value
        else:
            for value in self.enum:
                yield value

    @property
    def max_length(self):
        """Derives the required field size from the enumeration values."""
        return max(len(value) for value in self.values if value is not None)

    @max_length.setter
    def max_length(self, max_length):
        """Mockup to comply with super class' __init__."""
        if max_length is not None:
            logger.warning(
                'Parameter max_length=%s will be ignored since it '
                'is derived from enumeration values.', str(max_length))

    @property
    def null(self):
        """Determines nullability by enum values."""
        return any(value is None for value in self.values)

    @null.setter
    def null(self, null):
        """Mockup to comply with super class' __init__."""
        if null is not None:
            logger.warning(
                'Parameter null=%s will be ignored since it '
                'is derived from enumeration values.', str(null))

    def db_value(self, value):
        """Coerce enumeration value for database."""
        if is_enum(value):
            if value in self.enum:
                return value.value
        elif value in self.values:
            return value

        raise InvalidEnumerationValue(value)

    def python_value(self, value):
        """Coerce enumeration value for python."""
        if is_enum(self.enum):
            for item in self.enum:
                if item.value == value:
                    return item
        elif value in self.values:
            return value

        raise InvalidEnumerationValue(value)


class InvalidEnumerationValue(ValueError):
    """Indicates that an invalid enumeration value has been specified."""

    def __init__(self, value):
        super().__init__('Invalid enum value: "{}".'.format(value))
