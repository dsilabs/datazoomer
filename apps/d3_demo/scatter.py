"""
    d3 scatter chart example
"""

import zoom
import zoom.tools
import zoom.vis.d3


class MyView(zoom.View):
    def index(self):

        layout = zoom.tools.load_content('scatter_preamble')

        data = zoom.url_for_page('scatter_data')
        options = dict(
            x="function(d) { return d.income; }",
            y="function(d) { return d.lifeExpectancy; }",
            radius="function(d) { return d.population; }",
            radiusFormat="""
                function(d) { return d3.format('0,.2f')(d/1000000000)+'B'; }
            """,
            color="function(d) { return d.region; }",
            key="function(d) { return d.name; }",
        )

        chart = zoom.vis.d3.scatter(data, options=options)

        return zoom.page(layout.format(chart=chart), title='Scatter Plot')

view = MyView()
