# Copyright (c) 2005-2013 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re, imghdr, cgi

class Validator:
    """A content validator."""

    def __init__(self, msg, test):
        self.msg = msg
        self.test = test

    def valid(self, value): 
        return self.test(value)

    def __call__(self, value):
        return self.valid(value)


class RegexValidator(Validator):
    """
    A regular expression validator

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('1')
        True

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('')
        True

        >>> is_valid = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> is_valid('')
        True
        >>> is_valid('*')
        False

        >>> validator = RegexValidator('invalid input', r'^[a-zA-Z0-9]+$')
        >>> validator.valid('-')
        False
        >>> validator.msg
        'invalid input'
    """

    def __init__(self, msg, regex):
        self.msg = msg
        self.test = re.compile(regex).match

    def valid(self, value):
        # only test if value exists
        return not value or bool(Validator.valid(self, value))


class URLValidator(Validator):
    """
    A URL Validator

        >>> validator = URLValidator()
        >>> validator.valid('http://google.com')
        True

        >>> validator = URLValidator()
        >>> validator.valid('test123')
        False

    """
    
    def __init__(self):
        Validator.__init__(
            self,
            'Enter a valid URL',
            re.compile(r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE).match
        )

    def valid(self, value):
        # only test if value exists
        return not value or bool(Validator.valid(self, value))

class PostalCodeValidator(RegexValidator):
    """
    A Postal Code Validator

        >>> validator = PostalCodeValidator()
        >>> validator.valid('V8X 1G1')
        True

        >>> validator = PostalCodeValidator()
        >>> validator.valid('V8X1G1')
        True

        >>> validator = PostalCodeValidator()
        >>> validator.valid('V8X XG1')
        False

        >>> validator = PostalCodeValidator()
        >>> validator.valid('8X XG1')
        False

        >>> validator = PostalCodeValidator()
        >>> validator.valid('V8X 1g1')
        True

    """
    def __init__(self):
        e = '^[A-Za-z][0-9][A-Za-z]\s*[0-9][A-Za-z][0-9]$'
        RegexValidator.__init__(self, 'enter a valid postal code', e)

class MinimumLength(Validator):
    """A minimum length validator"""

    def __init__(self, min_length, empty_allowed=False):
        self.empty_allowed = empty_allowed
        self.msg = 'minimum length %s' % min_length
        self.test = lambda a: (self.empty_allowed and a=='') or not len(a) < min_length


class MinimumValue(Validator):
    """
    Minimum value validator

        >>> v = MinimumValue(100)
        >>> v.valid(50)
        False
        >>> v.valid(120)
        True
    """
    def __init__(self, min_value, empty_allowed=True):
        self.empty_allowed = empty_allowed
        self.msg = 'value must be at least %s' % min_value
        self.test = lambda a: (self.empty_allowed and a=='') or not a < min_value


class MaximumValue(Validator):
    """
    Maximum value validator

        >>> v = MaximumValue(100)
        >>> v.valid(50)
        True
        >>> v.valid(120)
        False
    """
    def __init__(self, min_value, empty_allowed=True):
        self.empty_allowed = empty_allowed
        self.msg = 'value must be at most %s' % min_value
        self.test = lambda a: (self.empty_allowed and a=='') or not a > min_value


def email_valid(email):
    if email=='': return True
    email_re = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
    return email_re.match(email)

def image_mime_type_valid(s):
    # check upload file against the more commonly browser supported mime types
    accept = ['gif','jpeg','png','xbm','bmp']
    if isinstance(s, cgi.FieldStorage) and s.file and imghdr.what('a',s.file.read()) in accept: return True
    if not s or isinstance(s, (str,unicode)) and imghdr.what('a',s) in accept: return True
    return False


def number_valid(s):
    """
        >>> number_valid(0)
        True
        >>> number_valid(-1)
        True
        >>> number_valid(1.12039123)
        True
        >>> number_valid('1.12039123')
        True
        >>> number_valid('x1.12039123')
        False
        >>> number_valid('t')
        False
        >>> number_valid('')
        True
        >>> number_valid(False) # not sure if this is what's we want
        True
    """
    if s == '': return True
    try:
        float(s)
        return True
    except:
        return False


def latitude_valid(s):
    if s == '': return True
    try:
        v = float(s)
        if v >= -90 and v <= 90:
            return True
    except:
        return False


def longitude_valid(s):
    if s == '': return True
    try:
        v = float(s)
        if v >= -180 and v <= 180:
            return True
    except:
        return False


# Common Validators
# ----------------------------
# Error messages should suggest what the user needs to do for the value
# to be considered value (i.e. "enter a numeric value").

notnull = Validator("required", bool)
required = Validator("required", lambda a: bool(a) and not (hasattr(a,'isspace') and a.isspace()))
valid_name = MinimumLength(2)
valid_email = Validator('enter a valid email address', email_valid)
valid_phone = RegexValidator('invalid phone number', '^\(?([2-9][0-8][0-9])\)?[-. ]?([2-9][0-9]{2})[-. ]?([0-9]{4})$')
valid_username = RegexValidator('letters and numbers only', r'^[a-zA-Z0-9.@\\]+$')
valid_password = MinimumLength(6)
valid_new_password = MinimumLength(8)
valid_url = URLValidator()
valid_postal_code = PostalCodeValidator()
image_mime_type = Validator("a supported image is required (gif, jpeg, png)", image_mime_type_valid)
valid_number = Validator("enter a numeric value", number_valid)
valid_latitude = Validator("enter a number between -90 and 90", latitude_valid)
valid_longitude = Validator("enter a number between -180 and 180", longitude_valid)
