# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
# coding=utf8
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

"""Fields for HTML forms"""
import uuid
import types
import locale
import datetime
from decimal import Decimal

from validators import *
from utils import name_for, tag_for
from tools import htmlquote, websafe, markdown, has_iterator_protocol, wrap_iterator
from helpers import attribute_escape, link_to
from request import route
from zoom import system

HINT_TPL = \
        """
        <table class="transparent">
            <tr>
                <td%(wrap)s>%(widget)s</td>
                <td>
                    <div class="hint">%(hints)s</div>
                </td>
            </tr>
        </table>
        """

FIELD_TPL = \
'<div class="field"><div class="field_label">%(label)s</div><div class="field_%(mode)s">%(content)s</div></div>'


def div(content, **attributes):
    return tag_for('div', content, **attributes)

def layout_field(label, content, edit=True):
    """
        Layout a field (usually as part of a form).

        >>> layout_field('Name','<input type=text value="John Doe">',True)
        '<div class="field"><div class="field_label">Name</div><div class="field_edit"><input type=text value="John Doe"></div></div>'

        >>> layout_field('Name','John Doe',False)
        '<div class="field"><div class="field_label">Name</div><div class="field_show">John Doe</div></div>'

    """
    mode = bool(edit) and 'edit' or 'show'
    return FIELD_TPL % locals()

class Field(object):
    js_init = ''
    js = ''
    css = ''
    value = ''
    options=[]
    label=''
    hint=''
    addon=''
    default = ''
    placeholder = None
    msg = ''
    required = False
    visible = True
    validators = []
    style = ''
    wrap = ' nowrap'

    def __init__(self, label='', *validators, **keywords):
        self.__dict__ = keywords
        if 'value' in keywords:
            self.assign(keywords['value'])
        self.label = label
        self.validators = list(validators) + self.validators
        self.id = self.name

    def show(self):
        return self.visible and self.display_value()

    def widget(self):
        return self.display_value()

    def edit(self):
        content = HINT_TPL % dict(
                widget=self.widget(),
                hints=self.render_msg() + self.render_hint(),
                wrap=self.wrap,
                )
        return layout_field(self.label, content)

    def __getattr__(self, name):
        if name == 'name' and hasattr(self, 'label'):
            return name_for(self.label)
        raise AttributeError

    def initialize(self, *a, **k):
        """
        Initialize field value.

            Set field value according to value passed in as parameter
            or if there is not value for this field, set it to the
            default value for the field.

            >>> f = Field('test', default='zero')

            >>> f.initialize(test='one')
            >>> f.value
            'one'

            >>> r = dict(test='two')
            >>> f.initialize(r)
            >>> f.value
            'two'

            >>> r = dict(not_test='two')
            >>> f.initialize(r)
            >>> f.value
            'zero'
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            self._initialize(values)

    def _initialize(self, values):
        self.assign(values.get(self.name.lower(), self.default))

    def update(self, **values):
        """
        Update field.

            >>> name_field = Field('Name', value='Sam')
            >>> name_field.value
            'Sam'
            >>> name_field.update(city='Vancouver')
            >>> name_field.value
            'Sam'
            >>> name_field.update(name='Joe')
            >>> name_field.value
            'Joe'
            >>> name_field.update(NaMe='Adam')
            >>> name_field.value
            'Adam'
        """
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])

    def assign(self, value):
        self.value = value

    def evaluate(self):
        """
        Evaluate field value.

            Return the value of the field expressed as key value pair (dict)
            ususally to be combined with other fields in the native type where
            the value is the native data type for the field type.
        """
        return {self.name: self.value or self.default}

    def as_dict(self):
        return {self.name: self}

    def __repr__(self):
        """
            >>> name_field = Field('Name', value='test')
            >>> print name_field
            NAME: test
        """
        return '%s: %s' % (self.name, self.value)

    def display_value(self):
        """
        Display field value.

            >>> name_field = Field('Name', default='default test')
            >>> name_field.display_value()
            'default test'

            >>> name_field = Field('Name', value='test')
            >>> name_field.display_value()
            u'test'

            >>> name_field = Field('Name', value='こんにちは')
            >>> name_field.display_value()
            u'\u3053\u3093\u306b\u3061\u306f'

            >>> name_field.visible = False
            >>> name_field.display_value()
            ''

        """
        return self.visible and websafe(self.value) or self.default or ''

    def render_hint(self):
        """
        Render hint.

        >>> name_field = TextField('Name',hint='Full name')
        >>> name_field.render_hint()
        '<span class="hint">Full name</span>'
        """
        if self.hint: return '<span class="hint">%s</span>' % self.hint
        else: return ''

    def render_msg(self):
        """
        Render validation error message.

        >>> name_field = TextField('Name',required)
        >>> name_field.update(NAME='')
        >>> name_field.valid()
        False
        >>> name_field.render_msg()
        '<span class="wrong">required</span>'
        """
        if self.msg: return '<span class="wrong">%s</span>' % self.msg
        else: return ''

    def valid(self):
        """
        Validate field value.

            >>> name_field = TextField('Name',required)
            >>> name_field.update(NAME='Fred')
            >>> name_field.valid()
            True
            >>> name_field.update(NAME='')
            >>> name_field.valid()
            False
            >>> name_field.msg
            'required'
        """

        for v in self.validators:
            if not v.valid(self.value):
                self.msg = v.msg
                return False
        return True

    def validate(self, *a, **k):
        """
        Update and validate a field.

            >>> name_field = TextField('Name',required)
            >>> name_field.validate(city='Vancouver')
            False
            >>> name_field.validate(name='Fred')
            True
        """
        self.update(*a, **k)
        return self.valid()

    def requires_multipart_form(self):
        return False


class SimpleField(Field):

    def show(self):
        return self.visible and (bool(self.value) or bool(self.default)) and \
                layout_field(self.label, self.display_value(), edit=False) or ''


class MarkdownText(object):
    """a markdown text object that can be placed in a form like a field

    >>> f = MarkdownText('One **bold** statement')
    >>> f.edit()
    u'<p>One <strong>bold</strong> statement</p>'
    """
    def __init__(self, text):
        self.value = text

    def edit(self):
        return markdown('%s\n' % self.value)

    def evaluate(self):
        return {}


class TextField(SimpleField):
    """
    Text Field

        >>> TextField('Name',value="John Doe").show()
        u'<div class="field"><div class="field_label">Name</div><div class="field_show">John Doe</div></div>'

        >>> TextField('Name',value='John Doe').widget()
        '<INPUT NAME="NAME" VALUE="John Doe" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" />'

        >>> TextField('Name',value="Dan").show()
        u'<div class="field"><div class="field_label">Name</div><div class="field_show">Dan</div></div>'

        >>> TextField('Name',default="Dan").show()
        '<div class="field"><div class="field_label">Name</div><div class="field_show">Dan</div></div>'

        >>> TextField('Name',hint="required").widget()
        '<INPUT NAME="NAME" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" />'

        >>> TextField('Name',placeholder="Jack").widget()
        '<INPUT NAME="NAME" PLACEHOLDER="Jack" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" />'

        >>> f = TextField('Title')
        >>> f.update(**{"TITLE": "Joe's Pool Hall"})
        >>> f.value
        "Joe's Pool Hall"
        >>> f.evaluate()
        {'TITLE': "Joe's Pool Hall"}


    """

    size = maxlength = 40
    _type = 'text'
    css_class = 'text_field'

    def widget(self):
        if self.placeholder:
            return tag_for(
                'input',
                name = self.name,
                id = self.id,
                size = self.size,
                maxlength=self.maxlength,
                value = self.value or self.default,
                Type = self._type,
                Class = self.css_class,
                placeholder = self.placeholder,
            )
        else:
            return tag_for(
                'input',
                name = self.name,
                id = self.id,
                size = self.size,
                maxlength=self.maxlength,
                value = self.value or self.default,
                Type = self._type,
                Class = self.css_class,
            )


class Hidden(SimpleField):
    """
    Hidden field.

        >>> Hidden('Hide Me').show()
        ''

        >>> Hidden('Hide Me', value='test').edit()
        '<INPUT TYPE="hidden" NAME="HIDE_ME" VALUE="test" ID="HIDE_ME" />'

    """
    visible = False
    size=maxlength=40
    def edit(self):
        return tag_for('input',name=self.name,id=self.id,value=self.value or self.default,Type='hidden')


class EmailField(TextField):
    """
    Email field.

        >>> EmailField('Email').widget()
        '<INPUT NAME="EMAIL" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="EMAIL" SIZE="40" />'
    """

    def __init__(self, label, *validators, **keywords):
        TextField.__init__(self, label, valid_email, *validators, **keywords)

    def display_value(self):
        def antispam_format(address):
            t = markdown('<%s>' % address)
            if t.startswith('<p>') and t.endswith('</p>'):
                return t[3:-4]
            return t
        address = self.value or self.default
        return self.visible and address and antispam_format(address) or ''


class PostalCodeField(TextField):
    """
    Postal code field.

        >>> PostalCodeField('Postal Code').widget()
        '<INPUT NAME="POSTAL_CODE" VALUE="" CLASS="text_field" MAXLENGTH="7" TYPE="text" ID="POSTAL_CODE" SIZE="7" />'
    """

    size = maxlength = 7

    def __init__(self, label='Postal Code', *validators, **keywords):
        TextField.__init__(self, label, valid_postal_code, *validators, **keywords)



class TwitterField(TextField):
    """
    Twitter field.

        >>> TwitterField('Twitter').widget()
        '<INPUT NAME="TWITTER" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="TWITTER" SIZE="40" />'

        >>> TwitterField('Twitter', value='dsilabs').display_value()
        '<a target="_window" href="http://www.twitter.com/dsilabs">@dsilabs</a>'
    """
    def display_value(self):
        twitter_id = (self.value or self.default).strip().strip('@')
        return self.visible and twitter_id and '<a target="_window" href="http://www.twitter.com/%(twitter_id)s">@%(twitter_id)s</a>' % locals() or ''


class URLField(TextField):
    """
    URL Field

        >>> URLField('Website', default='www.google.com').display_value()
        '<a target="_window" href="http://www.google.com">http://www.google.com</a>'

        >>> f = URLField('Website', default='www.google.com')
        >>> f.assign('www.dsilabs.ca')
        >>> f.display_value()
        u'<a target="_window" href="http://www.dsilabs.ca">http://www.dsilabs.ca</a>'

        >>> f = URLField('Website', default='www.google.com')
        >>> f.assign('http://www.dsilabs.ca')
        >>> f.display_value()
        u'<a target="_window" href="http://www.dsilabs.ca">http://www.dsilabs.ca</a>'

        >>> f = URLField('Website', default='www.google.com', trim=True)
        >>> f.assign('http://www.dsilabs.ca/')
        >>> f.display_value()
        u'<a target="_window" href="http://www.dsilabs.ca">www.dsilabs.ca</a>'

        >>> f = URLField('Website', default='www.google.com')
        >>> f.assign('https://www.dsilabs.ca/')
        >>> f.display_value()
        u'<a target="_window" href="https://www.dsilabs.ca/">https://www.dsilabs.ca/</a>'

        >>> f = URLField('Website', default='www.google.com', trim=True)
        >>> f.assign('https://www.dsilabs.ca/')
        >>> f.display_value()
        u'<a target="_window" href="https://www.dsilabs.ca">www.dsilabs.ca</a>'

    """

    size = 60
    maxlength = 120
    trim = False

    def __init__(self, label, *validators, **keywords):
        TextField.__init__(self, label, valid_url, *validators, **keywords)

    def display_value(self):
        url = text = websafe(self.value) or self.default
        if url:
            if not (url.startswith('http') or url.startswith('ftp:')):
                url = 'http://' + url
                if not self.trim:
                    text = 'http://' + text
        if self.trim and text.startswith('http://'):
            text = text[7:]
        if self.trim and text.startswith('https://'):
            text = text[8:]
        if self.trim and text.endswith('/'):
            text = text[:-1]
            url = url[:-1]
        return self.visible and url and ('<a target="_window" href="%s">%s</a>' % (url, text)) or ''

    def assign(self, value):
        self.value = value


class PasswordField(TextField):
    """
    Password Field

        >>> PasswordField('Password').show()
        ''

        >>> PasswordField('Password').widget()
        '<INPUT NAME="PASSWORD" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="password" ID="PASSWORD" SIZE="40" />'
    """

    size = maxlength = 40
    _type = 'password'

    def show(self):
        return ''


class NumberField(TextField):
    """
    Number Field

        >>> NumberField('Size',value=2).show()
        u'<div class="field"><div class="field_label">Size</div><div class="field_show">2</div></div>'

        >>> NumberField('Size').widget()
        '<INPUT NAME="SIZE" VALUE="" CLASS="number_field" MAXLENGTH="10" TYPE="text" ID="SIZE" SIZE="10" />'

        >>> n = NumberField('Size')
        >>> n.assign('2')
        >>> n.value
        2

        >>> n = NumberField('Size', units='units')
        >>> n.assign('2,123')
        >>> n.value
        2123
        >>> n.evaluate()
        {'SIZE': '2123'}
        >>> n.display_value()
        u'2,123 units'

        >>> n.assign(None)
        >>> n.value == None
        True
        >>> n.display_value()
        u''

    """

    size = maxlength = 10
    css_class = 'number_field'
    units = ''
    converter = int

    def evaluate(self):
        #TODO: This method is unexpected.  Could be that it is meant to be a numeric
        #      text field, in which case the name could be NumericTextField.
        #      If it's meant to be able to be used as a number then it should just
        #      return the number as it is stored (int).
        #      It's heavily (mis-)used so will not change it now.  If you want an actual
        #      integer field, then use IntegerField.
        return {self.name: str(self.value)}

    def assign(self, value):
        try:
            if type(value) == str:
                value = ''.join(c for c in value if c in '0123456789.-')
            self.value = self.converter(value)
        except:
            self.value = None

    def widget(self):
        w = tag_for(
                    'input',
                    name = self.name,
                    id = self.id,
                    size = self.size,
                    maxlength=self.maxlength,
                    value = self.value or self.default,
                    Type = self._type,
                    Class = self.css_class,
                )

        if self.units:
            return """
            <div class="input-group">
              {w}
              <span class="input-group-addon">{u}</span>
            </div>
            """.format(w=w, u=self.units)
        else:
            return w

    def display_value(self):
        units = self.units and (' ' + self.units) or ''
        value = self.value and ('{:,}{}'.format(self.value, units)) or ''
        return websafe(value)


class IntegerField(TextField):
    """
    Integer Field

        >>> IntegerField('Count',value=2).show()
        u'<div class="field"><div class="field_label">Count</div><div class="field_show">2</div></div>'

        >>> IntegerField('Count').widget()
        '<INPUT NAME="COUNT" VALUE="" CLASS="number_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" />'

        >>> n = IntegerField('Size')
        >>> n.assign('2')
        >>> n.value
        2
        >>> n.evaluate()
        {'SIZE': 2}

        >>> n = IntegerField('Size', units='meters')
        >>> n.assign('22234')
        >>> n.value
        22234
        >>> n.display_value()
        u'22,234 meters'
    """

    size = maxlength = 10
    css_class = 'number_field'
    value = 0
    units = ''

    def assign(self, value):
        self.value = int(value)

    def display_value(self):
        units = self.units and (' ' + self.units) or ''
        value = self.value and ('{:,}{}'.format(self.value, units)) or ''
        return websafe(value)

class FloatField(NumberField):
    """
    Float Field

        >>> FloatField('Count',value=2.1).show()
        u'<div class="field"><div class="field_label">Count</div><div class="field_show">2.1</div></div>'

        >>> FloatField('Count').widget()
        '<INPUT NAME="COUNT" VALUE="" CLASS="float_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" />'

        >>> n = FloatField('Size')
        >>> n.assign(2.1)
        >>> n.value
        2.1

        >>> n.assign(0)
        >>> n.value
        0.0

        >>> n.assign('0')
        >>> n.value
        0.0

        >>> n.assign('2.1')
        >>> n.value
        2.1

        >>> n.assign('')
        >>> n.evaluate()
        {'SIZE': None}
    """

    size = maxlength = 10
    css_class = 'float_field'
    value = 0
    converter = float

    def evaluate(self):
        return {self.name: self.value}


class DecimalField(NumberField):
    """
    Decimal Field

        >>> DecimalField('Count',value="2.1").show()
        u'<div class="field"><div class="field_label">Count</div><div class="field_show">2.1</div></div>'

        >>> DecimalField('Count', value=Decimal('10.24')).widget()
        '<INPUT NAME="COUNT" VALUE="10.24" CLASS="decimal_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" />'

        >>> DecimalField('Count').widget()
        '<INPUT NAME="COUNT" VALUE="" CLASS="decimal_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" />'

        >>> n = DecimalField('Size')
        >>> n.assign('2.1')
        >>> n.value
        Decimal('2.1')

        >>> n.assign(0)
        >>> n.value
        Decimal('0')

        >>> n.assign('0')
        >>> n.value
        Decimal('0')

        >>> n.assign('2.1')
        >>> n.value
        Decimal('2.1')

        >>> n.assign('')
        >>> n.evaluate()
        {'SIZE': None}

        >>> DecimalField('Hours').evaluate()
        {'HOURS': 0}
    """

    size = maxlength = 10
    css_class = 'decimal_field'
    value = 0
    converter = Decimal

    def evaluate(self):
        return {self.name: self.value}


class MoneyField(DecimalField):
    """
    Money Field

        >>> f = MoneyField("Amount")
        >>> f.widget()
        '<div class="input-group"><span class="input-group-addon">$</span><INPUT NAME="AMOUNT" VALUE="" CLASS="decimal_field" MAXLENGTH="10" TYPE="text" ID="AMOUNT" SIZE="10" /></div>'
        >>> f.display_value()
        u'$0.00'
        >>> f.assign(Decimal(1000))
        >>> f.display_value()
        u'$1,000.00'

        >>> from platform import system
        >>> l = system()=='Windows' and 'eng' or 'en_GB.utf8'
        >>> f = MoneyField("Amount", locale=l)
        >>> f.display_value()
        u'\\xa30.00'

        >>> f.assign(Decimal(1000))
        >>> f.display_value()
        u'\\xa31,000.00'
        >>> f.show()
        u'<div class="field"><div class="field_label">Amount</div><div class="field_show">\\xa31,000.00</div></div>'
        >>> f.widget()
        '<div class="input-group"><span class="input-group-addon">\\xc2\\xa3</span><INPUT NAME="AMOUNT" VALUE="1000" CLASS="decimal_field" MAXLENGTH="10" TYPE="text" ID="AMOUNT" SIZE="10" /></div>'
        >>> f.units = 'per month'
        >>> f.display_value()
        u'\\xa31,000.00 per month'
        >>> f.units = ''
        >>> f.display_value()
        u'\\xa31,000.00'
        >>> f.assign('')
        >>> f.display_value()
        ''
        >>> f.assign('0')
        >>> f.display_value()
        u'\\xa30.00'
        >>> f.assign(' ')
        >>> f.display_value()
        ''

        >>> f = MoneyField("Amount", placeholder='0')
        >>> f.widget()
        '<div class="input-group"><span class="input-group-addon">$</span><INPUT NAME="AMOUNT" TYPE="text" VALUE="" CLASS="decimal_field" MAXLENGTH="10" PLACEHOLDER="0" ID="AMOUNT" SIZE="10" /></div>'
    """

    locale = None
    symbol = '$'

    def widget(self):
        if self.locale:
            locale.setlocale(locale.LC_ALL, self.locale)
            self.symbol = locale.localeconv()['currency_symbol']
        t = '<div class="input-group"><span class="input-group-addon">{}</span>{}{}</div>'
        tu = '<span class="input-group-addon">{}</span>'
        if self.placeholder != None:
            return t.format(
                self.symbol,
                tag_for(
                    'input',
                    name = self.name,
                    id = self.id,
                    size = self.size,
                    placeholder = self.placeholder,
                    maxlength=self.maxlength,
                    value = self.value or self.default,
                    Type = self._type,
                    Class = self.css_class,
                ),
                self.units and tu.format(self.units) or '',
                )
        else:
            return t.format(
                self.symbol,
                tag_for(
                    'input',
                    name = self.name,
                    id = self.id,
                    size = self.size,
                    maxlength=self.maxlength,
                    value = self.value or self.default,
                    Type = self._type,
                    Class = self.css_class,
                ),
                self.units and tu.format(self.units) or '',
                )

    def display_value(self):
        if self.value == None: return ''
        if self.locale:
            locale.setlocale(locale.LC_ALL, self.locale)
            v = websafe(locale.currency(self.value, grouping=True))
        else:
            v = self.symbol + ('{:20,.2f}'.format(self.value)).strip()
        if self.units and self.value <> None:
            v += ' '+self.units
        return websafe(v)


class DateField(SimpleField):
    """
    Date Field

        DatField values can be either actual dates (datetime.date) or string
        representations of dates.  Values coming from databases or from code
        will typically be dates, while dates coming in from forms will
        typically be strings.

        DateFields always evaluate to date types and always display as string
        representations of those dates formatted according to the specified
        format.

        >>> DateField("Start Date").widget()
        '<INPUT NAME="START_DATE" VALUE="" CLASS="date_field" MAXLENGTH="12" TYPE="text" ID="START_DATE" />'

        >>> from datetime import date, datetime

        >>> f = DateField("Start Date")
        >>> f.display_value()
        ''
        >>> f.assign('')
        >>> f.display_value()
        ''

        >>> f = DateField("Start Date", value=date(2015,1,1))
        >>> f.value
        datetime.date(2015, 1, 1)

        >>> f = DateField("Start Date", value=datetime(2015,1,1))
        >>> f.value
        datetime.datetime(2015, 1, 1, 0, 0)
        >>> f.evaluate()
        {'START_DATE': datetime.date(2015, 1, 1)}

        >>> f.assign('Jan 01, 2015') # forms assign with strings
        >>> f.display_value()
        'Jan 01, 2015'
        >>> f.evaluate()
        {'START_DATE': datetime.date(2015, 1, 1)}

        >>> f.assign('2015-12-31') # forms assign with strings
        >>> f.display_value()
        'Dec 31, 2015'
        >>> f.evaluate()
        {'START_DATE': datetime.date(2015, 12, 31)}

        >>> f.assign(date(2015,1,31))
        >>> f.display_value()
        'Jan 31, 2015'

        >>> f.assign('TTT 01, 2015')
        >>> f.display_value()
        'TTT 01, 2015'
        >>> failed = False
        >>> try:
        ...     f.evaluate()
        ... except ValueError:
        ...     failed = True
        >>> failed
        True

        >>> DateField("Start Date", value=date(2015,1,1)).widget()
        '<INPUT NAME="START_DATE" VALUE="Jan 01, 2015" CLASS="date_field" MAXLENGTH="12" TYPE="text" ID="START_DATE" />'

    """

    value = default = None
    size=maxlength=12
    input_format = '%b %d, %Y'
    alt_input_format = '%Y-%m-%d'
    format = '%b %d, %Y'
    _type = 'date'
    css_class = 'date_field'
    validators = [valid_date]
    min = max = None

    def display_value(self, alt_format=None):
        format = alt_format or self.format
        if self.value:
            strftime = datetime.datetime.strftime
            try:
                result = strftime(self.evaluate()[self.name], format)
            except ValueError:
                result = self.value
        else:
            result = self.default and self.default.strftime(format) or ''
        return result

    def widget(self):
        value = self.display_value(self.input_format)
        parameters = dict(
                    name=self.name,
                    id=self.id,
                    maxlength=self.maxlength,
                    value=value,
                    Type='text',
                    Class=self.css_class,
                )
        if self.min != None:
            js = """
            $(function(){
                $('#%s').datepicker('option', 'minDate', '%s');
            });
            """
            system.js.add(js % (self.id, self.min.strftime(self.input_format)))

        if self.max != None:
            js = """
            $(function(){
                $('#%s').datepicker('option', 'maxDate', '%s');
            });
            """
            system.js.add(js % (self.id, self.max.strftime(self.input_format)))
        return tag_for('input', **parameters)

    def show(self):
        return self.visible and bool(self.value) and layout_field(self.label,self.display_value()) or ''

    def evaluate(self):
        if self.value:
            if type(self.value) == datetime.datetime:
                value = self.value.date()
            elif type(self.value) == datetime.date:
                value = self.value
            else:
                strptime = datetime.datetime.strptime
                try:
                    value = strptime(self.value, self.input_format).date()
                except ValueError:
                    value = strptime(self.value, self.alt_input_format).date()
            return {self.name: value or self.default}
        return {self.name: self.default}


class BirthdateField(DateField):
    size=maxlength=12
    css_class = 'birthdate_field'


class CheckboxesField(Field):
    """
    Checkboxes field.

        >>> cb = CheckboxesField('Select',values=['One','Two','Three'], hint='test hint')
        >>> cb.widget()
        '<ul class="checkbox_field"><li><INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="SELECT" VALUE="One" ID="SELECT" /><div>One</div></li><li><INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="SELECT" VALUE="Two" ID="SELECT" /><div>Two</div></li><li><INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="SELECT" VALUE="Three" ID="SELECT" /><div>Three</div></li></ul>'
    """

    def widget(self):
        result = []
        for value in self.values:
            checked = value in self.value and 'checked ' or ''
            tag = tag_for(
                    'input',
                    None,
                    checked,
                    name = self.name,
                    id = self.id,
                    Type='checkbox',
                    Class='checkbox_field',
                    value=value,
                    )
            result.append('<li>%s<div>%s</div></li>' % (tag, value))
        result = '<ul class="checkbox_field">%s</ul>' % (''.join(result))
        return result

    def show(self):
        return layout_field(self.label, ', '.join(self.value))

class CheckboxField(TextField):
    """
    Checkbox Field

        >>> CheckboxField('Done').show()
        '<div class="field"><div class="field_label">Done</div><div class="field_show">no</div></div>'

        >>> CheckboxField('Done', value=True).show()
        '<div class="field"><div class="field_label">Done</div><div class="field_show">yes</div></div>'

        >>> CheckboxField('Done').widget()
        '<INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'

        >>> f = CheckboxField('Done', value=True)
        >>> f.widget()
        '<INPUT CHECKED  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'
        >>> f.validate(**{'DONE': 'on'})
        True
        >>> f.evaluate()
        {'DONE': True}

        >>> f = CheckboxField('Done')
        >>> f.widget()
        '<INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'
        >>> f.evaluate()
        {'DONE': None}
        >>> f.validate(**{})
        True
        >>> f.evaluate()
        {'DONE': None}

        >>> f = CheckboxField('Done')
        >>> f.widget()
        '<INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'
        >>> f.evaluate()
        {'DONE': None}
        >>> f.validate(**{'DONE': 'on'})
        True
        >>> f.evaluate()
        {'DONE': True}

        >>> f = CheckboxField('Done', options=['yes','no'], value=False)
        >>> f
        DONE: False
        >>> f.validate(**{'done': True})
        True
        >>> f
        DONE: True
        >>> f.validate(**{'DoNE': False})
        True
        >>> f
        DONE: False
        >>> f.validate(**{'done': 'on'})
        True
        >>> f
        DONE: on
        >>> f.display_value()
        'yes'
        >>> f.evaluate()
        {'DONE': True}

        >>> f = CheckboxField('Done', options=['yep','nope'], default=True)
        >>> f.evaluate()
        {'DONE': True}
        >>> f.widget()
        '<INPUT CHECKED  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'
        >>> f.update(other='test')
        >>> f.widget()
        '<INPUT  CLASS="checkbox_field" TYPE="checkbox" NAME="DONE" ID="DONE" />'

        >>> f = CheckboxField('Done', options=['yep','nope'])
        >>> f.evaluate()
        {'DONE': None}
        >>> f.validate(**{'OTHERDATA': 'some value'})
        True
        >>> f.evaluate()
        {'DONE': False}

        >>> CheckboxField('Done', options=['yep','nope']).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=False).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=True).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], default=True).evaluate()
        {'DONE': True}

        >>> CheckboxField('Done', options=['yep','nope'], default=True, value=False).display_value()
        'nope'

        >>> CheckboxField('Done', options=['yep','nope'], value=True).display_value()
        'yep'

        >>> CheckboxField('Done', options=['yep','nope'], value=False).evaluate()
        {'DONE': False}

        >>> CheckboxField('Done', options=['yep','nope'], value='True').value
        'True'

    """
    options = ['yes','no']
    truthy = [True,'True','yes','on']
    default = None
    value = None

    def assign(self, value):
        self.value = value in self.truthy and value or False

    def widget(self):
        value = self.value is None and self.default or self.value
        checked = value and 'checked ' or ''
        tag = tag_for(
            'input',
            None,
            checked,
            name = self.name,
            id = self.id,
            Type='checkbox',
            Class='checkbox_field',
            )
        return tag

    def display_value(self):
        return self.value in self.truthy and self.options[0] or self.options[1] or ''

    def show(self):
        return layout_field(self.label, self.display_value(), False)

    def update(self,**values):
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])
                return
        if values:
            self.assign(False)

    def evaluate(self):
        if self.value in self.truthy:
            v = True
        elif self.value in [False]:
            v = False
        else:
            v = self.default
        return {self.name: v}

class RadioField(TextField):
    """
    Radio Field

        >>> RadioField('Choice',value='One',values=['One','Two']).show()
        u'<div class="field"><div class="field_label">Choice</div><div class="field_show">One</div></div>'

        >>> RadioField('Choice',value='One',values=['One','Two']).edit()
        '<div class="field"><div class="field_label">Choice</div><div class="field_edit"><span class="radio"><input type="radio" name="CHOICE" value="One" checked="Y" class="radio" />One</span><span class="radio"><input type="radio" name="CHOICE" value="Two" class="radio" />Two</span><br></div></div>'

        >>> RadioField('Choice',value='One',values=[('One','1'),('Two','2')]).edit()
        '<div class="field"><div class="field_label">Choice</div><div class="field_edit"><span class="radio"><input type="radio" name="CHOICE" value="1" class="radio" />One</span><span class="radio"><input type="radio" name="CHOICE" value="2" class="radio" />Two</span><br></div></div>'
    """
    values = []
    def edit(self):
        current_value = self.display_value()
        result = []
        name = self.name
        for option in self.values:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                text, value = option
            else:
                text = value = option
            label = self.label
            checked = (value == current_value) and 'checked="Y" ' or ''
            result.append('<span class="radio"><input type="radio" name="%s" value="%s" %sclass="radio" />%s</span>' % (name,value,checked,text))
        return layout_field(self.label,''.join(result)+'<br>'+self.render_msg()+self.render_hint())


class Pulldown(TextField):
    """
    Pulldown

        >>> Pulldown('Type',value='One',options=['One','Two']).edit()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option></select>'

        >>> f = Pulldown('Type',value='One',options=[('One','uno'),('Two','dos')])
        >>> f.edit()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value="uno" selected>One</option><option value="dos">Two</option></select>'
        >>> f.value
        'uno'
        >>> f.evaluate()
        {'TYPE': 'uno'}
        >>> f.value = 'One'
        >>> f.value
        'One'
        >>> f.evaluate()
        {'TYPE': 'uno'}
        >>> f.update(**{'TYPE':'dos'})
        >>> f.value
        'dos'
        >>> f.evaluate()
        {'TYPE': 'dos'}

        >>> f = Pulldown('Type',value='uno',options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One'
    """

    def evaluate(self):
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
                if self.value == label:
                    return {self.name:value}
        return {self.name:self.value}

    def edit(self):
        current_value = self.display_value()
        result = []
        name = self.name
        result.append('<select class="pulldown" name="%s" id="%s">\n'%(name,name))
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            if label == current_value:
                result.append('<option value="%s" selected>%s</option>' % (value,label))
            else:
                result.append('<option value="%s">%s</option>' % (value,label))
        result.append('</select>')
        result.append(self.render_msg()+self.render_hint())
        return ''.join(result)

    def assign(self,new_value):
        self.value = new_value
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
                if new_value == label:
                    self.value = value

    def display_value(self):
        t = self.value
        if t:
            for option in self.options:
                if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                    label, value = option
                    if t == value:
                        return label
        return t or ''


class PulldownField(TextField):
    """
    Pulldown Field

        >>> PulldownField('Type',value='One',options=['One','Two']).display_value()
        'One'

        >>> PulldownField('Type',value='One',options=['One','Two']).widget()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option></select>'

        >>> PulldownField('Type',options=['One','Two']).widget()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value=""></option><option value="One">One</option><option value="Two">Two</option></select>'

        >>> f = PulldownField('Type', options=[('',''),('One',1),('Two',2)])
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value="" selected></option><option value="1">One</option><option value="2">Two</option></select>

        >>> f.assign(2)
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value=""></option><option value="1">One</option><option value="2" selected>Two</option></select>

        >>> f.assign('2')
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value=""></option><option value="1">One</option><option value="2" selected>Two</option></select>

        >>> f = PulldownField('Type', options=[('',''),('One','1'),('Two','2')])
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value="" selected></option><option value="1">One</option><option value="2">Two</option></select>

        >>> f.assign(2)
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value=""></option><option value="1">One</option><option value="2" selected>Two</option></select>

        >>> f.assign('2')
        >>> print f.widget()
        <select class="pulldown" name="TYPE" id="TYPE">
        <option value=""></option><option value="1">One</option><option value="2" selected>Two</option></select>

        >>> f = PulldownField('Type',value='One',options=[('One','uno'),('Two','dos')])
        >>> f.widget()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value="uno" selected>One</option><option value="dos">Two</option></select>'

        >>> f.value
        'uno'
        >>> f.evaluate()
        {'TYPE': 'uno'}
        >>> f.value = 'One'
        >>> f.value
        'One'
        >>> f.evaluate()
        {'TYPE': 'uno'}
        >>> f.update(**{'TYPE':'dos'})
        >>> f.value
        'dos'
        >>> f.evaluate()
        {'TYPE': 'dos'}

        >>> f = PulldownField('Type',value='uno',options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One'

        >>> f = PulldownField('Type',default='uno',options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One'
        >>> f.evaluate()
        {'TYPE': 'uno'}

        >>> p = PulldownField('Date', name='TO_DATE', options=[('JAN','jan'), ('FEB','feb'),], default='feb')
        >>> p.evaluate()
        {'TO_DATE': 'feb'}
        >>> p.display_value()
        'FEB'
    """
    value = None

    def evaluate(self):
        for option in self.options:
            if type(option) in [types.ListType, types.TupleType] and len(option)==2:
                label, value = option
                if self.value == label:
                    return {self.name: value}
        return {self.name: self.value == None and self.default or self.value}

    def display_value(self):
        t = self.value == None and self.default or self.value
        if t:
            for option in self.options:
                if type(option) in [types.ListType, types.TupleType] and len(option)==2:
                    label, value = option
                    if t == value:
                        return label
        return t

    def assign(self,new_value):
        self.value = new_value
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
                if new_value == label:
                    self.value = value

    def widget(self):
        current_value = str(self.value or self.default) or ''
        result = []
        name = self.name
        found = False
        result.append('<select class="pulldown" name="%s" id="%s">\n'%(name,name))
        for option in self.options:
            if type(option) in [types.ListType, types.TupleType] and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            if str(value) == current_value:
                result.append('<option value="%s" selected>%s</option>' % (value,label))
                found = True
            else:
                result.append('<option value="%s">%s</option>' % (value,label))
        if not found and not current_value:
            blank_option = '<option value=""></option>'
            result.insert(1, blank_option)
        result.append('</select>')
        return ''.join(result)

class MultiselectField(TextField):
    """
    Multiselect Field

        >>> MultiselectField('Type',value='One',options=['One','Two']).display_value()
        'One'

        >>> f = MultiselectField('Type', default='One', options=['One','Two'])
        >>> f.evaluate()
        {'TYPE': []}
        >>> f.display_value()
        ''
        >>> f.widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option></select>'
        >>> f.value
        >>> f.assign([])
        >>> f.value
        []
        >>> f.evaluate()
        {'TYPE': []}
        >>> f.widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One">One</option><option value="Two">Two</option></select>'

        >>> MultiselectField('Type',value='One',options=['One','Two']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option></select>'

        >>> MultiselectField('Type',value=['One','Three'],options=['One','Two','Three']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option><option value="Three" selected>Three</option></select>'

        >>> MultiselectField('Type',default=['One'],options=['One','Two','Three']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option><option value="Three">Three</option></select>'

        >>> MultiselectField('Type',default=['One','Two'],options=['One','Two','Three']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two" selected>Two</option><option value="Three">Three</option></select>'

        >>> f = MultiselectField('Type',value='One',options=[('One','uno'),('Two','dos')])
        >>> f.widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="uno" selected>One</option><option value="dos">Two</option></select>'
        >>> f.value
        ['uno']
        >>> f.evaluate()
        {'TYPE': ['uno']}
        >>> f.value = ['One']
        >>> f.value
        ['One']
        >>> f.evaluate()
        {'TYPE': ['uno']}
        >>> f.update(**{'TYPE':['dos']})
        >>> f.value
        ['dos']
        >>> f.evaluate()
        {'TYPE': ['dos']}

        >>> f = MultiselectField('Type',value='uno',options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One'

        >>> f = MultiselectField('Type',value='uno',options=[('One','uno'),('One','dos')])
        >>> f.display_value()
        'One'
        >>> f.widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="uno" selected>One</option><option value="dos">One</option></select>'

        >>> f = MultiselectField('Type',value=['One','dos'],options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One; Two'
        >>> f.evaluate()
        {'TYPE': ['uno', 'dos']}

        >>> f = MultiselectField('Type',value=['uno','dos'],options=[('One','uno'),('Two','dos')])
        >>> f.display_value()
        'One; Two'
        >>> f.evaluate()
        {'TYPE': ['uno', 'dos']}
        >>> f.option_style('zero','nada')
        ''

        >>> s = lambda label, value: value.startswith('d') and 's1' or 's0'
        >>> f = MultiselectField('Type',value=['uno','dos'],options=[('One','uno'),('Two','dos')], styler=s)
        >>> f.widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option class="s0" value="uno" selected>One</option><option class="s1" value="dos" selected>Two</option></select>'
        >>> f.styler('test','dos')
        's1'
        >>> f.option_style('zero','nada')
        'class="s0" '

        # test for iterating over a string vs. a sequence type (iteration protocol)
        >>> m1 = MultiselectField('Type', default='11', options=[('One','1'),('Two','2'),('Elves','11'),]).widget()
        >>> m2 = MultiselectField('Type', default=('11',), options=[('One','1'),('Two','2'),('Elves','11'),]).widget()
        >>> assert m1 == m2

    """

    value = None
    default = []
    css_class = 'multiselect'
    styler = None

    def _scan(self, t, f):
        if t:
            t = wrap_iterator(t)
            result = []
            for option in self.options:
                if len(option)==2 and has_iterator_protocol(option):
                    label, value = option
                    if label in t or value in t:
                        result.append(f(option))
                elif option in t:
                    result.append(option)
            return result
        return []

    def evaluate(self):
        return {self.name: self._scan(self.value, lambda a: a[1])}

    def display_value(self):
        return '; '.join(self._scan(self.value, lambda a: a[0]))

    def assign(self, new_value):
        self.value = self._scan(new_value, lambda a: a[1])

    def update(self, **values):
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])
                return
        self.assign([])

    def option_style(self, label, value):
        if self.styler != None:
            return 'class="{}" '.format(self.styler(label, value))
        return ''

    def widget(self):
        if self.value == None:
            current_values = self.default
        else:
            current_values = self.value
        current_values = wrap_iterator(current_values)
        current_labels = self._scan(current_values, lambda a: a[0])
        result = []
        name = self.name
        tpl = '<select multiple="multiple" class="%s" name="%s" id="%s">\n'
        result.append(tpl%(self.css_class, name, name))
        for option in self.options:
            if has_iterator_protocol(option) and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            style = self.option_style(label, value)
            if value in current_values:
                result.append('<option %svalue="%s" selected>%s</option>' % (style,value,label))
            else:
                result.append('<option %svalue="%s">%s</option>' % (style,value,label))
        result.append('</select>')
        return ''.join(result)


class ChosenMultiselectField(MultiselectField):
    """
    Chosen Multiselect field.

        >>> f = ChosenMultiselectField('Choose', options=['One','Two','Three'], hint='test hint')
        >>> f.widget()
        '<select data-placeholder="Select Choose" multiple="multiple" class="chosen" name="CHOOSE" id="CHOOSE">\\n<option value="One">One</option><option value="Two">Two</option><option value="Three">Three</option></select>'

        >>> f = ChosenMultiselectField('Choose', options=['One','Two','Three'], hint='test hint', placeholder='my placeholder')
        >>> f.widget()
        '<select data-placeholder="my placeholder" multiple="multiple" class="chosen" name="CHOOSE" id="CHOOSE">\\n<option value="One">One</option><option value="Two">Two</option><option value="Three">Three</option></select>'


    """
    css_class = 'chosen'

    def __init__(self, *a, **k):
        MultiselectField.__init__(self, *a, **k)
        if not 'placeholder' in k:
            self.placeholder = 'Select ' + self.label

    def widget(self):
        if self.value == None:
            current_values = self.default
        else:
            current_values = self.value
        current_values = wrap_iterator(current_values)
        current_labels = self._scan(current_values, lambda a: a[0])
        result = []
        name = self.name
        tpl = '<select data-placeholder="{}" multiple="multiple" class="{}" name="{}" id="{}">\n'
        result.append(tpl.format(self.placeholder, self.css_class, name, name))
        for option in self.options:
            if has_iterator_protocol(option) and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            style = self.option_style(label, value)
            if value in current_values:
                result.append('<option %svalue="%s" selected>%s</option>' % (style, value,label))
            else:
                result.append('<option %svalue="%s">%s</option>' % (style,value,label))
        result.append('</select>')
        return ''.join(result)


class RecordListField(ChosenMultiselectField):
    separator = ', '
    url = None  # specify like: lambda _,v: url_for_app('groups', v)

    def display_value(self):
        if self.url:
            lookup = dict((v,k) for k,v in self.options)
            value = [link_to(lookup[v], self.url(v)) for v in self.value]
        else:
            value = self._scan(self.value, lambda a: a[0])
        return self.separator.join(value)

    def text_value(self):
        return self.display_value()


class Button(Field):
    """
    Button field.

        >>> Button('Save').show()
        ''

        >>> Button('Save').edit()
        '<INPUT STYLE="" NAME="SAVE_BUTTON" VALUE="Save" CLASS="button" TYPE="submit" ID="SAVE_BUTTON" />'

        >>> Button('Save', cancel='/app/cancel').edit()
        '<INPUT STYLE="" NAME="SAVE_BUTTON" VALUE="Save" CLASS="button" TYPE="submit" ID="SAVE_BUTTON" />&nbsp;<A HREF="/app/cancel">cancel</A>'
    """
    def __init__(self,caption='Save',**keywords):
        Field.__init__(self,caption+' Button',**keywords)
        self.caption = caption

    def show(self):
        return ""

    def edit(self):
        if hasattr(self,'cancel'):
            cancel_link = '&nbsp;' + tag_for('a', 'cancel', href=getattr(self,'cancel'))
        else:
            cancel_link = ''
        return tag_for('input',Type='submit',Class='button',name=self.name,style=self.style,id=self.id,value=self.caption) + cancel_link

    def evaluate(self):
        return {}

    def __repr__(self):
        return ''

class ButtonField(Button):
    """
    Button field.

        >>> ButtonField('Save').show()
        ''

        >>> ButtonField('Save').edit()
        '<div class="field"><div class="field_label">&nbsp;</div><div class="field_edit"><INPUT STYLE="" NAME="SAVE_BUTTON" VALUE="Save" CLASS="button" TYPE="submit" ID="SAVE_BUTTON" /></div></div>'

        >>> ButtonField('Save', cancel='/app/cancel').edit()
        '<div class="field"><div class="field_label">&nbsp;</div><div class="field_edit"><INPUT STYLE="" NAME="SAVE_BUTTON" VALUE="Save" CLASS="button" TYPE="submit" ID="SAVE_BUTTON" />&nbsp;<A HREF="/app/cancel">cancel</A></div></div>'
    """

    def edit(self):
        return layout_field('&nbsp;',Button.edit(self))

    def evaluate(self):
        return {}

    def __repr__(self):
        return ''

class Buttons(Field):
    """
    Buttons

        >>> Buttons(['Save','Publish','Delete']).show()
        ''

        >>> Buttons(['Save','Publish']).edit()
        '<div class="field"><div class="field_label">&nbsp;</div><div class="field_edit"><INPUT ID="SAVE_BUTTON" TYPE="submit" CLASS="button" VALUE="Save" NAME="SAVE_BUTTON" />&nbsp;<INPUT ID="PUBLISH_BUTTON" TYPE="submit" CLASS="button" VALUE="Publish" NAME="PUBLISH_BUTTON" /></div></div>'

        >>> Buttons(['Save'],cancel='/app/id').edit()
        '<div class="field"><div class="field_label">&nbsp;</div><div class="field_edit"><INPUT ID="SAVE_BUTTON" TYPE="submit" CLASS="button" VALUE="Save" NAME="SAVE_BUTTON" />&nbsp;<A HREF="/app/id">cancel</A></div></div>'
    """

    def __init__(self,captions=['Save'],**keywords):
        Field.__init__(self,**keywords)
        self.captions = captions

    def show(self):
        return ""

    def edit(self):
        buttons = [tag_for('input', Type='submit', Class='button', name=name_for(caption + ' button'), id=name_for(caption + ' button'), value=caption) for caption in self.captions]
        if hasattr(self,'cancel'):
            buttons.append(tag_for('a', 'cancel', href=getattr(self,'cancel','cancel')))
        return layout_field('&nbsp;','&nbsp;'.join(buttons))

    def evaluate(self):
        return {}

    def __repr__(self):
        return ''


class PhoneField(TextField):
    """
    Phone field

        >>> PhoneField('Phone').widget()
        '<INPUT NAME="PHONE" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="PHONE" SIZE="20" />'


    """
    size=20
    validators = [valid_phone]


class MemoField(Field):
    """
    Paragraph of text.

        >>> MemoField('Notes').edit()
        '<div class="field"><div class="field_label">Notes</div><div class="field_edit"><TEXTAREA ROWS="6" NAME="NOTES" COLS="60" ID="NOTES" CLASS="memo_field" SIZE="10"></TEXTAREA></div></div>'
    """
    value=''
    height=6
    size=10
    rows=6
    cols=60
    css_class = 'memo_field'

    def edit(self):
        input = tag_for(
                'textarea',
                content=self.value,
                name=self.name,
                id=self.id,
                size=self.size,
                cols=self.cols,
                rows=self.rows,
                Class=self.css_class,
                )
        if self.hint or self.msg:
            table_start  = '<table class="transparent" width=100%><tr><td width=10%>'
            table_middle = '</td><td>'
            table_end    = '</td></tr></table>'
            return layout_field(self.label, table_start + input  + table_middle + self.render_msg() + self.render_hint() + table_end )
        else:
            return layout_field(self.label, input)

    def show(self):
        return self.visible and (bool(self.value) or bool(self.default)) and layout_field(self.label,'<div class="textarea">%s</div>' % self.display_value(), edit=False) or ''

class MarkdownField(MemoField):
    """
    MarkdownField

        >>> f = MarkdownField('Notes', value='test **one** 23')
        >>> f.display_value()
        u'<p>test <strong>one</strong> 23</p>'

    """
    def display_value(self):
        return markdown(self.value)

class EditField(Field):
    """
    Large textedit.

        >>> EditField('Notes').edit()
        '<div class="field"><div class="field_label">Notes</div><div class="field_edit"><TEXTAREA HEIGHT="6" CLASS="edit_field" SIZE="10" NAME="NOTES" ID="NOTES"></TEXTAREA></div></div>'

    """
    value=''
    height=6
    size=10
    css_class = 'edit_field'

    def edit(self):
        input = tag_for(
                'textarea',
                content=self.value,
                name=self.name,
                id=self.id,
                size=self.size,
                Class=self.css_class,
                height=self.height
                )
        return layout_field(self.label, input)

    def show(self):
        return self.visible and (bool(self.value) or bool(self.default)) and layout_field(self.label,'<div class="textarea">%s</div>' % self.display_value(), edit=False) or ''

class RangeSliderField(IntegerField):
    """ jQuery UI Range Slider

        >>> r = RangeSliderField('Price', min=0, max=1500)
        >>> r.assign(0)
        >>> r.value
        (0, 1500)
        >>> r.assign((10, 20))
        >>> r.value
        (10, 20)
    """
    js_formatter = """var formatter = function(v) { return v;};"""
    js = """
    <script>
      $(function() {
        $( "#%(name)s" ).slider({
          range: true,
          min: %(tmin)s,
          max: %(tmax)s,
          values: [ %(minv)s, %(maxv)s ],
          change: function( event, ui ) {
            var v = ui.values,
                t = v[0] + ',' + v[1];
            $("input[name='%(name)s']").val(t);
            %(formatter)s
            $( "div[data-id='%(name)s'] span:nth-of-type(1)" ).html( formatter(ui.values[ 0 ]) );
            $( "div[data-id='%(name)s'] span:nth-of-type(2)" ).html( formatter(ui.values[ 1 ]) );
          },
          slide: function( event, ui ) {
            var v = ui.values;
            %(formatter)s
            $( "div[data-id='%(name)s'] span:nth-of-type(1)" ).html( formatter(ui.values[ 0 ]) );
            $( "div[data-id='%(name)s'] span:nth-of-type(2)" ).html( formatter(ui.values[ 1 ]) );
          }
        });
        $("#%(name)s").slider("values", $("#%(name)s").slider("values")); // set formatted label
      });
    </script>
    """
    min = 0
    max = 10
    show_labels = True
    css_class = 'range-slider'

    def assign(self, v):
        if v is None or not v or (isinstance(v,basestring) and v.strip()==','):
            self.value = (self.min, self.max)
        elif ',' in v:
            self.value = map(int, v.split(','))
        else:
            self.value = (int(v[0]), int(v[1]))

    def widget(self):
        name = self.name
        tmin, tmax = self.min, self.max
        minv, maxv = self.value or (tmin, tmax)

        formatter = self.js_formatter
        system.tail.add(self.js % locals())
        labels = """<div data-id="{}" class="{}"><span class="min pull-left">{}</span><span class="max pull-right">{}</span></div>""".format(
            name,
            not self.show_labels and "hidden" or "",
            minv, maxv
          )
        slider = '<div id="{}"><input type="hidden" name="{}" value="{}, {}"></div>'.format(name, name, minv, maxv)
        return '<div class="{}">{}{}</div>'.format(self.css_class, slider, labels)

class FieldIterator(object):

    def __init__(self, fields):
        self.field_list = [(n.lower(),v) for n,v in fields.evaluate().items()]
        self.current = 0
        self.high = len(self.field_list)

    def next(self):
        if self.current < self.high:
            self.current += 1
            return self.field_list[self.current - 1]
        else:
            raise StopIteration


class Fields(object):
    """
    A collection of field objects.


        >>> fields = Fields(TextField('Name'), PhoneField('Phone'))
        >>> fields.edit()
        '<div class="field"><div class="field_label">Name</div><div class="field_edit">\\n        <table class="transparent">\\n            <tr>\\n                <td nowrap><INPUT NAME="NAME" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" /></td>\\n                <td>\\n                    <div class="hint"></div>\\n                </td>\\n            </tr>\\n        </table>\\n        </div></div><div class="field"><div class="field_label">Phone</div><div class="field_edit">\\n        <table class="transparent">\\n            <tr>\\n                <td nowrap><INPUT NAME="PHONE" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="PHONE" SIZE="20" /></td>\\n                <td>\\n                    <div class="hint"></div>\\n                </td>\\n            </tr>\\n        </table>\\n        </div></div>'

        >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
        >>> fields.as_dict()
        {'PHONE': PHONE: 2234567890, 'NAME': NAME: Amy}

        >>> fields = Fields(TextField('Name'), ImagesField('Photos'))
        >>> fields.validate({'NAME': 'Test'})
        True
        >>> d = fields.evaluate()
        >>> d['NAME']
        'Test'
        >>> len(d['PHOTOS'])
        32
        >>> record = dict(name='Adam', photos='no photos')
        >>> record
        {'photos': 'no photos', 'name': 'Adam'}
        >>> record.update(fields)
        >>> record['name']
        'Test'
        >>> len(record['photos'])
        32


    """

    def __init__(self,*a):
        if len(a) == 1 and type(a[0]) == types.ListType:
            self.fields = a[0]
        else:
            self.fields = list(a)

    def show(self):
        return ''.join([field.show() for field in self.fields])

    def edit(self):
        return ''.join([field.edit() for field in self.fields])

    def as_dict(self):
        result = {}
        for field in self.fields:
            result = dict(result, **field.as_dict())
        return result

    def initialize(self, *a, **k):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.initialize(phone='987654321')
            >>> fields.as_dict()
            {'PHONE': PHONE: 987654321, 'NAME': NAME: }
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            for field in self.fields:
                field.initialize(values)

    def update(self,*a,**k):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.update(phone='987654321')
            >>> fields.as_dict()
            {'PHONE': PHONE: 987654321, 'NAME': NAME: Amy}
        """
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            for field in self.fields:
                field.update(**values)

    def display_value(self):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.display_value()
            {'PHONE': u'2234567890', 'NAME': u'Amy'}
        """
        result = {}
        for field in self.fields:
            if hasattr(field, 'name'):
                result = dict(result, **{field.name: field.display_value()})
            else:
                result = dict(result, **field.display_value())
        return result

    def as_list(self):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.as_list()
            [NAME: Amy, PHONE: 2234567890]
        """
        result = []
        for field in self.fields:
            if hasattr(field, 'name'):
                result.append(field)
            else:
                result.extend(field._fields())
        return result

    def _fields(self):
        result = []
        for field in self.fields:
            if hasattr(field, 'name'):
                result.append(field)
            else:
                result.extend(field._fields())
        return result

    def evaluate(self):
        """
            >>> fields = Fields(TextField('Name', value='Amy'), PhoneField('Phone', value='2234567890'))
            >>> fields.evaluate()
            {'PHONE': '2234567890', 'NAME': 'Amy'}
        """
        result = {}
        for field in self.fields:
            result = dict(result,**field.evaluate())
        return result

    def __iter__(self):
        return FieldIterator(self)

    def __repr__(self):
        return '\n'.join([repr(field) for field in self.fields if field.evaluate()])

    def valid(self):
        errors = 0
        for field in self.fields:
            if not field.valid():
                errors += 1
        return not errors

    def validate(self, *a, **k):
        self.update(*a, **k)
        return self.valid()

    def requires_multipart_form(self):
        for field in self.fields:
            if field.requires_multipart_form():
                return True


class Section(Fields):
    """
    A collection of field objects with an associated label.

        >>> Section('Personal',[TextField('Name',value='Joe')]).show()
        u'<H2>Personal</H2>\\n<div class="field"><div class="field_label">Name</div><div class="field_show">Joe</div></div>'
    """

    def __init__(self,label,fields,hint=''):
        Fields.__init__(self,fields)
        self.label = label
        self.hint = hint

    def render_hint(self):
        if self.hint: return '<span class="hint">%s</span>' % self.hint
        else: return ''

    def show(self):
        value = Fields.show(self)
        return bool(value) and ('<H2>%s</H2>\n%s' % (self.label,value)) or ''

    def edit(self):
        return '<H2>%s</H2>%s\n%s' % (self.label,self.render_hint(),Fields.edit(self))


class Fieldset(Fields):
    """
    A collection of field objects with an associated label.

        >>> Section('Personal',[TextField('Name',value='Joe')]).show()
        u'<H2>Personal</H2>\\n<div class="field"><div class="field_label">Name</div><div class="field_show">Joe</div></div>'
    """

    def __init__(self,label,fields,hint=''):
        Fields.__init__(self,fields)
        self.label = label
        self.hint = hint

    def render_hint(self):
        if self.hint: return '<span class="hint">%s</span>' % self.hint
        else: return ''

    def show(self):
        value = Fields.show(self)
        return bool(value) and ('<fieldset><legend>%s</legend>\n%s</fieldset>' % (self.label,value)) or ''

    def edit(self):
        return '<fieldset><legend>%s</legend>%s\n%s</fieldset>' % (self.label,self.render_hint(),Fields.edit(self))


class FileField(TextField):
    """
    File

        >>> FileField('Document').widget()
        '<INPUT NAME="DOCUMENT" VALUE="None" CLASS="file_field" MAXLENGTH="40" TYPE="file" ID="DOCUMENT" SIZE="40" />'
    """
    value = default = None
    _type = 'file'
    css_class = 'file_field'

    def requires_multipart_form(self): return True

    def assign(self, value):
        if hasattr(value, 'filename'):
            self.value = dict(filename=value.filename, value=value.value)


class ImageField(SimpleField):
    """ Display an image storage field

    >>> ImageField('Photo').initialize(None)
    >>> Fields([ImageField('Photo')]).initialize({'hi':'dz'})   # support dict
    >>> i = ImageField('Photo')
    >>> i.initialize({'photo':'data blob', 't':12})
    >>> i.value
    '<img class="image-field-image" alt="PHOTO" src="image?name=photo">'
    """
    size = maxlength = 40
    _type = 'file'
    css_class = 'image_field'
    no_image_url = '/static/dz/images/no_photo.png'
    binary_image_data = None

    def _initialize(self, values):
        name = self.name.lower()
        alt = self.name
        if hasattr(values, name) and getattr(values, name):
            url = values.url + '/image?name=' + name
            alt = values.name
        elif isinstance(values, dict) and values.get(name):
            # we do not know the route when passed as a dict, we just see the data blob
            url = 'image?name=' + name
        else:
            url = self.no_image_url
        self.value = '<img class="image-field-image" alt="{}" src="{}">'.format(
                alt,
                url,
                )

    def display_value(self):
        return self.value

    def edit(self):
        input = tag_for(
            'input',
            name = self.name,
            id = self.id,
            size = self.size,
            maxlength=self.maxlength,
            Type = self._type,
            Class = self.css_class,
        )
        delete_link = '<div class="image-field-delete-link"><a href="delete_image?name=%s">delete %s</a></div>' % (self.name.lower(), self.label.lower())
        if self.value:
            input += delete_link + self.display_value()
        return layout_field( self.label, ''.join([input,self.render_msg(),self.render_hint()]) )

    def requires_multipart_form(self):
        return True

    def assign(self, value):
        try:
            try:
                self.binary_image_data = value.value
            except AttributeError:
                self.value = value
        except AttributeError:
            self.value = None

    def evaluate(self):
        value = self.binary_image_data
        return value and {self.name: value} or {}



class ImagesField(SimpleField):
    """ Display a drag and drop multiple image storage field

    >>> ImagesField('Photo').initialize(None)
    >>> Fields([ImagesField('Photo')]).initialize({'hi':'dz'})   # support dict

    >>> i = ImagesField('Photos', value='newid')
    >>> i.display_value()
    '<div url="" field_name="PHOTOS" field_value="newid" class="images_field dropzone"></div>'
    >>> i.evaluate()
    {'PHOTOS': 'newid'}

    >>> i = ImagesField('Photos')
    >>> len(i.display_value())
    115
    >>> t = i.evaluate()
    >>> i.validate(**{'OTHERFIELD': 'test'})
    True
    >>> t == i.evaluate()
    True
    >>> i.validate(**{'PHOTOS': 'test'})
    True
    >>> i.evaluate()
    {'PHOTOS': 'test'}

    >>> i = ImagesField('Photos')
    >>> v1 = i.evaluate()
    >>> len(repr(v1))
    46
    >>> i.value
    >>> v1['PHOTOS'] == i.value
    False
    >>> i.validate(**{'PHOTOS': 'fromdatabase'})
    True
    >>> v2 = i.evaluate()
    >>> v1 <> v2
    True
    >>> v2
    {'PHOTOS': 'fromdatabase'}
    """
    _type = 'images'
    value = None
    default = uuid.uuid4().hex
    wrap = ''
    url = ''

    def display_value(self):
        t = '<div url="{url}" field_name="{name}" field_value="{value}" class="images_field dropzone"></div>'
        return t.format(url=self.url, name=self.name, value=self.value or self.default)

    def widget(self):
        t = """
        <div url="{url}" field_name="{name}" field_value="{value}" class="images_field dropzone"></div>
        <input type="hidden" name="{name}" value="{value}" id="{name}">
        """
        return t.format(url=self.url, name=self.name, value=self.value or self.default)

class Form(Fields):
    """
    An HTML form.

        >>> form = Form(TextField("Name"))
        >>> form.edit()
        '<form class="clearfix" action="" id="dz&#x5f;form" name="dz&#x5f;form" method="POST" enctype="application&#x2f;x&#x2d;www&#x2d;form&#x2d;urlencoded"><div class="field"><div class="field_label">Name</div><div class="field_edit">\\n        <table class="transparent">\\n            <tr>\\n                <td nowrap><INPUT NAME="NAME" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" /></td>\\n                <td>\\n                    <div class="hint"></div>\\n                </td>\\n            </tr>\\n        </table>\\n        </div></div></form>'

    """

    def __init__(self, *a, **k):

        if len(a) == 1 and type(a[0]) == types.ListType:
            self.fields = a[0]
        else:
            self.fields = list(a)

        self.enctype = 'application/x-www-form-urlencoded'
        for field in self.fields:
            try:
                if field.requires_multipart_form():
                    self.enctype = 'multipart/form-data'
            except AttributeError:
                pass

        params = k.copy()
        self.action = params.pop('action','')
        self.form_name = params.pop('form_name','dz_form')
        self.method = params.pop('method','POST')

    def edit(self):
        esc = attribute_escape
        return '<form class="clearfix" action="%s" id="%s" name="%s" method="%s" enctype="%s">%s</form>' % (
                esc(self.action),
                esc(self.form_name),
                esc(self.form_name),
                esc(self.method),
                esc(self.enctype),
                ''.join([field.edit() for field in self.fields])
                )



if __name__ == '__main__':

    import doctest
    doctest.testmod()


