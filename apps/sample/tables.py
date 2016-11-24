
from faker import factory
import json

from zoom.browse import browse
from zoom.mvc import DynamicView
from zoom.page import page
from zoom.response import JSONResponse
from zoom.component import component


class Model(object):

    name = 'Joe'

    data = json.load(open('testdata.json'))

    @property
    def as_json(self):
        return JSONResponse(self.data)


class MyView(DynamicView):

    def index(self):
        footer = '{} records'.format(len(self.data))
        content = component(
            browse(self.data, title="Browse", footer=footer),
            #browse(self.data, title="Table", footer=footer),
        )
        return page(content, title='Tables')

view = MyView(Model())
