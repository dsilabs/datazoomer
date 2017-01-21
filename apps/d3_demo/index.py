"""
    d3 demo application index
"""

from zoom import redirect_to, page

from model import get_scatter_data, data_list_generator, get_calendar_data
from views import *


class MyView(View):

    def index(self):
        return redirect_to(url_for_page('scatter'))

    def nations(self):
        return JSONResponse(tools.load('nations.json'))

    def scatter_data(self):
        return JSONResponse(json.dumps(get_scatter_data()))

    def calendar_data(self, obs=1000, metrics=3, dims=2):
        data = get_calendar_data(obs, metrics, dims)
        return JSONResponse(json.dumps(data))

    def tests(self):
        return page(
            tools.load_content('tests'),
            title='Visual tests for the smaller components',
            css=tools.load('style.css'),
        )

    def generate(self, obs=1000, metrics=3, dims=2):
        metadata = data_list_generator(obs, metrics, dims)
        return JSONResponse(json.dumps(metadata))


view = MyView()
