"""
    d3 demo application index
"""

from zoom.response import JSONResponse
from zoom import redirect_to, page

from model import get_scatter_data, data_list_generator
from views import *


class MyView(View):

    def index(self):
        return redirect_to(url_for_page('scatter'))

    def nations(self):
        return JSONResponse(tools.load('nations.json'))

    def scatter_data(self):
        return JSONResponse(json.dumps(get_scatter_data()))

    def calendar_data(self, obs=1000, metrics=3, dims=2):
        metadata = data_list_generator(obs=obs, metrics=metrics, dims=dims)
        metadata['description'] = "{}{}".format(metadata['description'], calendar_eg)
        return JSONResponse(json.dumps(metadata))

    def tests(self):
        css = tools.load('style.css')
        content = tools.load_content('tests')
        return page(content, title='Visual tests for the smaller components', css=css)

    def generate(self, obs=1000, metrics=3, dims=2):
        metadata = data_list_generator(obs, metrics, dims)
        return JSONResponse(json.dumps(metadata))


view = MyView()
