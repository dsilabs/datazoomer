# -*- coding: utf-8 -*-

"""
    test the fields module
"""

import unittest
import logging

from zoom.fields import *
from zoom.tools import unisafe

logger = logging.getLogger('zoom.fields')


class TextTests(object):

    def setUp(self, field_type):
        self.field_type = field_type
        self.show_css_class = self.css_class = self.field_type.css_class
        self.basic_text = 'test text'
        self.encoded_text = 'A “special character” & quote test.'
        self.show_template = '<div class="{self.show_css_class}">{text}</div>'
        self.edit_template = '{widget}'

    def compare(self, expected, got):
        def strify(text):
            if type(text) is unicode:
                return text.encode('utf8')
            return text
        logger.debug('expected: %s', repr(strify(expected)))
        logger.debug('.....got: %s', repr(strify(got)))
        self.assertEqual(strify(expected), strify(got))

    def test_initialize(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        show_value = self.show_template.format(self=self, text=self.basic_text)
        t = (
            '<div class="field">'
            '<div class="field_label">Field1</div>'
            '<div class="field_show">'
            '{show_value}'
            '</div></div>'
        ).format(self=self, show_value=show_value)
        self.compare(t, f.show())

    def test_widget(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.basic_text})
        t = self.widget_template.format(self=self, text=self.basic_text)
        self.compare(t, f.widget())

    def test_widget_with_unicode(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.encoded_text})
        t = self.widget_template.format(self=self, text=htmlquote(self.encoded_text))
        self.compare(t, f.widget())

    def test_edit_with_unicode(self):
        f = self.field_type('Field1')
        f.initialize({'field1': self.encoded_text})
        widget = self.widget_template.format(self=self, text=htmlquote(self.encoded_text))
        edit = self.edit_template.format(widget=widget)
        t = (
            '<div class="field">'
                '<div class="field_label">Field1</div>'
                '<div class="field_edit">'
                    '{edit}'
                '</div>'
            '</div>'
        ).format(self=self, edit=edit)
        self.compare(t, f.edit())

    def test_show_with_unicode(self):
        def strsafe(value):
            if value is None:
                result = ''
            elif isinstance(value, unicode):
                result = htmlquote(value).encode('utf8')
            elif isinstance(value, str):
                result = htmlquote(value)
            else:
                result = str(value)
            return result
        f = self.field_type('Field1')
        f.initialize({'field1': self.encoded_text})
        logger.debug(repr(self.encoded_text))
        v = strsafe(self.encoded_text)
        show_value = self.show_template.format(self=self, text=v)
        t = (
            '<div class="field">'
            '<div class="field_label">Field1</div>'
            '<div class="field_show">'
            '{show_value}'
            '</div></div>'
        ).format(self=self, show_value=show_value)
        self.compare(t, f.show())


class TestMemoField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, MemoField)
        self.show_css_class = 'textarea'
        self.show_template = '<div class="{self.show_css_class}">{text}</div>'
        self.edit_template = '{widget}'
        self.widget_template = (
            '<TEXTAREA ROWS="6" NAME="FIELD1" COLS="60" ID="FIELD1" '
            'CLASS="{self.css_class}" SIZE="10">{text}</TEXTAREA>'
        )


class TestEditField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, EditField)
        self.show_css_class = 'textarea'
        self.show_template = '<div class="{self.show_css_class}">{text}</div>'
        self.edit_template = '{widget}'
        self.widget_template = (
            '<TEXTAREA HEIGHT="6" CLASS="{self.css_class}" SIZE="10" '
            'NAME="FIELD1" ID="FIELD1">{text}</TEXTAREA>'
        )


class TestTextField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, TextField)
        self.show_template = '{text}'
        self.edit_template = """
        <table class="transparent">
            <tr>
                <td nowrap>{widget}</td>
                <td>
                    <div class="hint"></div>
                </td>
            </tr>
        </table>
        """
        self.widget_template = (
            '<INPUT NAME="FIELD1" VALUE="{text}" '
            'CLASS="{self.css_class}" MAXLENGTH="40" '
            'TYPE="text" ID="FIELD1" SIZE="40" />'
        )


class TestEmailField(unittest.TestCase, TextTests):

    def setUp(self, *a, **k):
        TextTests.setUp(self, EmailField)
        self.show_template = '<{text}>'
        self.edit_template = """
        <table class="transparent">
            <tr>
                <td nowrap>{widget}</td>
                <td>
                    <div class="hint"></div>
                </td>
            </tr>
        </table>
        """
        self.widget_template = (
            '<INPUT NAME="FIELD1" VALUE="{text}" '
            'CLASS="{self.css_class}" MAXLENGTH="40" '
            'TYPE="text" ID="FIELD1" SIZE="40" />'
        )


