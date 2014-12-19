# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
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
import datetime, types
from validators import *

from utils import name_for, tag_for
from tools import htmlquote, websafe, markdown
from request import route

HINT_TPL = \
        """
        <table class="transparent">
            <tr>
                <td nowrap>%(widget)s</td>
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

class Field:
    js_init = ''
    js = ''
    value = ''
    options=[]
    label=''
    hint=''
    default = ''
    msg = ''
    required = False
    visible = True
    validators = []
    style = ''

    def __init__(self,label='',*validators,**keywords):
        self.__dict__ = keywords
        if 'value' in keywords:
            self.assign(keywords['value'])
        self.label = label
        self.validators = validators
        self.id = self.name

    def show(self):
        return self.visible and self.display_value()

    def edit(self):
        return self.visible and self.display_value()

    def __getattr__(self,name):
        if name == 'name' and hasattr(self,'label'):
            return name_for(self.label)
        raise AttributeError             

    def initialize(self,**values):
        self.assign(values.get(self.name.lower(), self.default))

    def update(self,**values):
        for value in values:
            if value.lower() == self.name.lower():
                self.assign(values[value])

    def assign(self, value):
        self.value = value

    def evaluate(self):
        """
        Return the value of the field expressed as a key value pair (dict)
        ususally to be combined with other fields.
        """
        return {self.name: self.value or self.default}

    def as_dict(self):
        return {self.name: self}

    def __repr__(self):
        return '%s: %s' % (self.name, self.value)

    def display_value(self):
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
        self.update(*a, **k)
        return self.valid()

    def requires_multipart_form(self):
        return False

class SimpleField(Field):
    def show(self):
        return self.visible and (bool(self.value) or bool(self.default)) and \
                layout_field(self.label, self.display_value(), edit=False) or ''


class TextField(SimpleField):
    """
    Text Field

        >>> TextField('Name',value="John Doe").show()
        u'<div class="field"><div class="field_label">Name</div><div class="field_show">John Doe</div></div>'

        >>> TextField('Name',value='John Doe').edit()
        '<div class="field"><div class="field_label">Name</div><div class="field_edit"><INPUT NAME="NAME" VALUE="John Doe" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" /></div></div>'

        >>> TextField('Name',value="Dan").show()
        u'<div class="field"><div class="field_label">Name</div><div class="field_show">Dan</div></div>'

        >>> TextField('Name',default="Dan").show()
        '<div class="field"><div class="field_label">Name</div><div class="field_show">Dan</div></div>'

        >>> TextField('Name',hint="required").edit()
        '<div class="field"><div class="field_label">Name</div><div class="field_edit"><INPUT NAME="NAME" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" /><span class="hint">required</span></div></div>'

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

    def edit(self):
        input = tag_for(
            'input', 
            name = self.name,
            id = self.id,
            size = self.size,
            maxlength=self.maxlength,
            value = self.value or self.default,
            Type = self._type,
            Class = self.css_class,
        )
        return layout_field( self.label, ''.join([input,self.render_msg(),self.render_hint()]) )


class Hidden(SimpleField):
    visible = False
    size=maxlength=40
    def edit(self):
        return tag_for('input',name=self.name,id=self.id,value=self.value or self.default,Type='hidden')


class EmailField(TextField):

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

    size = maxlength = 7

    def __init__(self, label='Postal Code', *validators, **keywords):
        TextField.__init__(self, label, valid_postal_code, *validators, **keywords)



class TwitterField(TextField):

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
        if not self.trim and not (text.startswith('http://') or text.startswith('ftp:')):
            text = 'http://' + text
        if self.trim and text.startswith('http://'):
            text = text[7:]
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

        >>> PasswordField('Password').edit()
        '<div class="field"><div class="field_label">Password</div><div class="field_edit"><INPUT NAME="PASSWORD" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="password" ID="PASSWORD" SIZE="40" /></div></div>'
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

        >>> NumberField('Size').edit()
        '<div class="field"><div class="field_label">Size</div><div class="field_edit"><INPUT NAME="SIZE" VALUE="" CLASS="number_field" MAXLENGTH="10" TYPE="text" ID="SIZE" SIZE="10" /></div></div>'

        >>> n = NumberField('Size')
        >>> n.assign('2')
        >>> n.value
        2

        >>> n = NumberField('Size')
        >>> n.assign('2,123')
        >>> n.value
        2123
    """

    size = maxlength = 10
    css_class = 'number_field'

    def evaluate(self):
        return {self.name: str(self.value)}

    def assign(self, value):
        try:
            if type(value) == str and ',' in value:
                value = value.replace(',','')
            self.value = int(value)
        except:
            self.value = None


class IntegerField(TextField):
    """
    Integer Field

        >>> IntegerField('Count',value=2).show()
        u'<div class="field"><div class="field_label">Count</div><div class="field_show">2</div></div>'

        >>> IntegerField('Count').edit()
        '<div class="field"><div class="field_label">Count</div><div class="field_edit"><INPUT NAME="COUNT" VALUE="" CLASS="number_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" /></div></div>'
 
        >>> n = IntegerField('Size')
        >>> n.assign('2')
        >>> n.value
        2
    """

    size = maxlength = 10
    css_class = 'number_field'
    value = 0

    def assign(self, value):
        self.value = int(value)

class FloatField(TextField):
    """
    Float Field

        >>> FloatField('Count',value=2.1).show()
        u'<div class="field"><div class="field_label">Count</div><div class="field_show">2.1</div></div>'

        >>> FloatField('Count').edit()
        '<div class="field"><div class="field_label">Count</div><div class="field_edit"><INPUT NAME="COUNT" VALUE="" CLASS="float_field" MAXLENGTH="10" TYPE="text" ID="COUNT" SIZE="10" /></div></div>'
 
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

    def assign(self, value):
        if value == '':
            self.value = None
        else:
            self.value = float(value)

    def evaluate(self):
        return {self.name: self.value}

    #def evaluate(self):
        #if value == None:
            #return {self.name: self.value}
        #else:
            #return {self.name: self.value}



class DateField(SimpleField):
    """
    Date Field

        >>> DateField("Start Date").edit()
        '<div class="field"><div class="field_label">Start Date</div><div class="field_edit"><INPUT NAME="START_DATE" VALUE="" ID="START_DATE" MAXLENGTH="12" TYPE="text" CLASS="date_field" /></div></div>'
    """

    value = default = None
    size=maxlength=12
    format = '%b %d, %Y'
    _type = 'date'
    css_class = 'date_field'

    def display_value(self):
        return self.value and self.value.strftime(self.format) or ''

    def assign(self,value):
        if type(value)==types.StringType:
            try:
                self.value = datetime.datetime.strptime(value,self.format).date()
            except:
                self.value = None                
        else:
            self.value = value            

    def edit(self):
        value = self.value and self.value.strftime(self.format) or self.default and self.default.strftime(self.format) or ''
        return layout_field(
                self.label,
                tag_for(
                    'input',
                    name=self.name,
                    id=self.id,
                    maxlength=self.maxlength,
                    value=value,
                    Type='text',
                    Class=self.css_class,
                    )+self.render_msg()+self.render_hint()
                )

    def show(self):
        return self.visible and bool(self.value) and layout_field(self.label,self.display_value()) or ''

    def evaluate(self):
        return {self.name: self.value or self.default}


class BirthdateField(DateField):
    size=maxlength=10


class CheckboxesField(Field):

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

    def edit(self):
        content = HINT_TPL % dict(widget=self.widget(), hints=self.render_msg() + self.render_hint())
        return layout_field(self.label, content)

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

    """
    options = ['yes','no']
    default = None

    def widget(self):
        checked = self.value and 'checked ' or ''
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

    def edit(self):
        content = HINT_TPL % dict(widget=self.widget(), hints=self.render_msg() + self.render_hint())
        return layout_field(self.label, content)

    def display_value(self):
        return self.value in ['yes','on',True] and self.options[0] or self.options[1] or ''

    def show(self):
        return layout_field(self.label, self.display_value(), False)

    def evaluate(self):
        if self.value in [True,'yes','on']:
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
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value=""></option><option value="One" selected>One</option><option value="Two">Two</option></select>'

        >>> f = PulldownField('Type',value='One',options=[('One','uno'),('Two','dos')])
        >>> f.widget()
        '<select class="pulldown" name="TYPE" id="TYPE">\\n<option value=""></option><option value="uno" selected>One</option><option value="dos">Two</option></select>'

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
    """

    def evaluate(self):
        for option in self.options:
            if type(option) in [types.ListType, types.TupleType] and len(option)==2:
                label, value = option
                if self.value == label:
                    return {self.name:value}
        return {self.name: self.value}

    def display_value(self):
        t = self.value
        if t:
            for option in self.options:
                if type(option) in [types.ListType, types.TupleType] and len(option)==2:
                    label, value = option
                    if t == value:
                        return label
        return t or ''

    def assign(self,new_value):
        self.value = new_value
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
                if new_value == label:
                    self.value = value

    def widget(self):
        current_value = self.value or self.default or ''
        result = []
        name = self.name
        result.append('<select class="pulldown" name="%s" id="%s">\n'%(name,name))
        if not current_value:
            result.append('<option value="" selected></option>')
        else:
            result.append('<option value=""></option>')
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
            else:
                label, value = option, option 
            if value == current_value:
                result.append('<option value="%s" selected>%s</option>' % (value,label))
            else:
                result.append('<option value="%s">%s</option>' % (value,label))
        result.append('</select>')
        return ''.join(result)

    def edit(self):
        content = HINT_TPL % dict(widget=self.widget(), hints=self.render_msg() + self.render_hint())
        return layout_field(self.label, content)


class MultiselectField(TextField):
    """
    Multiselect Field

        >>> MultiselectField('Type',value='One',options=['One','Two']).display_value()
        'One'

        >>> MultiselectField('Type',value='One',options=['One','Two']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option></select>'

        >>> MultiselectField('Type',value=['One','Three'],options=['One','Two','Three']).widget()
        '<select multiple="multiple" class="multiselect" name="TYPE" id="TYPE">\\n<option value="One" selected>One</option><option value="Two">Two</option><option value="Three" selected>Three</option></select>'

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
    """

    def _scan(self, t, f):
        SEQUENCE_TYPES = [types.ListType,types.TupleType]
        if t:
            if not type(t) == types.ListType:
                t = [t]
            result = []
            for option in self.options:
                if len(option)==2 and type(option) in SEQUENCE_TYPES:
                    label, value = option
                    if label in t or value in t:
                        result.append(f(option))
                elif option in t:
                    result.append(option)
            return result
        return []

    def evaluate(self):
        return {self.name:self._scan(self.value or self.default, lambda a: a[1])}

    def display_value(self):
        return '; '.join(self._scan(self.value or self.default, lambda a: a[0]))

    def assign(self, new_value):
        self.value = self._scan(new_value, lambda a: a[1])

    def widget(self):
        current_labels = self._scan(self.value or self.default, lambda a: a[0])
        result = []
        name = self.name
        result.append('<select multiple="multiple" class="multiselect" name="%s" id="%s">\n'%(name,name))
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            if label in current_labels:
                result.append('<option value="%s" selected>%s</option>' % (value,label))
            else:
                result.append('<option value="%s">%s</option>' % (value,label))
        result.append('</select>')
        return ''.join(result)

    def edit(self):
        content = HINT_TPL % dict(widget=self.widget(), hints=self.render_msg() + self.render_hint())
        return layout_field(self.label, content)

class ChosenMultiselectField(MultiselectField):

    def widget(self):
        current_labels = self._scan(self.value or self.default, lambda a: a[0])
        result = []
        name = self.name
        result.append('<select multiple="multiple" style="width:300px; margin-right:5px;" class="chosen" name="%s" id="%s">\n'%(name,name))
        for option in self.options:
            if type(option) in [types.ListType,types.TupleType] and len(option)==2:
                label, value = option
            else:
                label, value = option, option
            if label in current_labels:
                result.append('<option value="%s" selected>%s</option>' % (value,label))
            else:
                result.append('<option value="%s">%s</option>' % (value,label))
        result.append('</select>')
        return ''.join(result)


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
    size=20


class MemoField(Field):
    """Paragraph of text."""
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


class EditField(Field):
    """Large textedit."""
    value=''
    height=6
    size=10
    css_class = 'memo_field'

    def edit(self):
        intput = tag_for(
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


class FieldIterator:

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


class Fields:
    """A collection of field objects."""

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
        if a:
            values = a[0]
        elif k:
            values = k
        else:
            values = None
        if values:
            for field in self.fields:
                field.initialize(**values)

    def update(self,*a,**k):
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
        result = {}
        for field in self.fields:
            if hasattr(field, 'name'):
                result = dict(result, **{field.name: field.display_value()})
            else:
                result = dict(result, **field.display_value())
        return result

    def as_list(self):
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
    value = default = None
    _type = 'file'
    css_class = 'file_field'

    def requires_multipart_form(self): return True

    def assign(self, value):
        if hasattr(value, 'filename'):
            self.value = dict(filename=value.filename, value=value.value)


class ImageField(SimpleField):
    size = maxlength = 40
    _type = 'file'
    css_class = 'image_field'
    no_image_url = '/static/images/no_photo.png'

    def display_value(self):
        r = route[-1] == 'edit' and route[:-1] or route
        if self.value:
            url = '/' + '/'.join(r) + '/image?name=' + self.name.lower()
        else:
            url = self.no_image_url
        return '<img src="%(url)s">' % locals()

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
        delete_link = '<a href="delete_image?name=%s">delete %s</a>' % (self.name.lower(), self.label.lower())
        if self.value:
            input += '<br>' + delete_link + ' <br>' + self.display_value()
        return layout_field( self.label, ''.join([input,self.render_msg(),self.render_hint()]) )

    def requires_multipart_form(self):
        return True

    def assign(self, value):
        try:
            try:
                self.value = value.value
            except AttributeError:
                self.value = value
        except AttributeError:
            self.value = None

    def evaluate(self):
        return self.value and {self.name: self.value} or {}


class Form(Fields):
    """
    An HTML form.

        >>> form = Form(TextField("Name"))
        >>> form.edit()
        '<form action="" id="dz_form" name="dz_form" method="POST" enctype="application/x-www-form-urlencoded"><div class="field"><div class="field_label">Name</div><div class="field_edit"><INPUT NAME="NAME" VALUE="" CLASS="text_field" MAXLENGTH="40" TYPE="text" ID="NAME" SIZE="40" /></div></div></form>'

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
        return '<form action="%s" id="%s" name="%s" method="%s" enctype="%s">%s</form>' % (
                self.action,
                self.form_name,
                self.form_name,
                self.method,
                self.enctype,
                ''.join([field.edit() for field in self.fields])
                )



if __name__ == '__main__':

    import doctest
    doctest.testmod() 


