from views import *


class MyView(View):
    def index(self):
        t = tools.load_content('colorbrewer')
        return page(t, title='ColorBrewer Scales')

view = MyView()
