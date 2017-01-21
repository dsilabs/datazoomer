"""
    d3 calendar chart example
"""

import zoom
import zoom.tools
import zoom.vis.d3


class MyView(zoom.View):
    def index(self):

        wrapper = zoom.tools.load_content('calendar_wrapper')

        data = zoom.url_for_page('calendar_data')

        chart = zoom.vis.d3.calendar(data, palette='"RdYlGn"')

        content = wrapper.format(chart=chart)

        return zoom.page(content, title='Calendar of Events')

view = MyView()
