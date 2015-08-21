from model import data as scatter_data, data_list_generator
from views import *


class MyView(View):

    def index(self):
        return redirect_to(url_for_page('scatter'))

    def cdn(self):
        css = tools.load('style.css')
        content = tools.load_content('scatter')
        return page(content, title='Scatter Plot via CDN', css=css)

    def nations(self):
        data = tools.load('nations.json')
        return JSONResponse(data)

    def scatter_data(self):
        return JSONResponse(json.dumps(scatter_data))

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
