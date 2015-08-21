from views import *


class MyView(View):
    def index(self):
        content = calendar_wrapper
        chart = calendar(view_for_data = url_for_page('calendar_data'), selector='chart')
        chart.options = dict(palette="'Greens'", color='d3.scale.quantize().range(d3.range(9).map(function(d) { return "q" + d + "-9"; }))')
        page_contents = "{}{}".format(content, chart)
        return page(page_contents, title='Calendar of Events', css=css + "#chart { min-height: 1100px; }")

view = MyView()
