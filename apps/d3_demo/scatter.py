from views import *


class MyView(View):
    def index(self):
        content = scatter_wrapper
        chart = scatter(view_for_data = url_for_page('scatter_data'), selector='chart')
        # js chart options
        chart.options = dict(
            x="function(d) { return d.income; }",
            y="function(d) { return d.lifeExpectancy; }",
            radius="function(d) { return d.population; }",
            radiusFormat="function(d) { return d3.format('0,.2f')(d/1000000000)+'B'; }",
            color="function(d) { return d.region; }",
            key="function(d) { return d.name; }",
        )
        return page(content + str(chart), title='Scatter Plot', css=css)

view = MyView()
