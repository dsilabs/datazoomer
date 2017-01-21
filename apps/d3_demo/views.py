

from zoom import *
from zoom.response import TextResponse
from zoom.vis.d3 import calendar



class JSONResponse(TextResponse):
    def __init__(self, content):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/json;charset=utf-8'
