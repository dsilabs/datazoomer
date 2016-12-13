
import datetime

from zoom import system, load, markdown, load_content, link_to, page
from zoom.mvc import View
from inspect import getsource, getmembers, ismethod
from zoom.html import div, ul

css = """
.content div.row ul {
    list-style-type: none;
}
.content div.row .thumbnails ul li {
    width: 50%;
    display: inline-block;
    padding: 10px;
}
.content div.row .thumbnails ul li div.thumbnail {
    height: 250px;
    overflow: hidden;
    margin: 0;
}
.thumbnail {
    position: relative;
}
.thumbnail .chart {
    height: 100%;
}
.thumbnail .dz-jqplot .modal-button {
    position: absolute;
    bottom: 0;
    padding: 4px;
    font-size: 0.75em;
}
.visualization {
    position: relative;
    min-height: 320px;
    clear: both;
}
.visualization .modal-button {
    position: absolute;
    bottom: 0;
}
"""

toc = """
C3 Charts
----
* [Line]({path}/c3-line)

JQPlot Charts
----
* [Line]({path}/jqplot-line)
* [Bar]({path}/jqplot-bar)
* [Horizontal Bar]({path}/jqplot-hbar)
* [Pie]({path}/jqplot-pie)
* [Gauge]({path}/jqplot-gauge)
* [Time Series]({path}/jqplot-ts)
* [Theme]({path}/jqplot-theme)
* [Image]({path}/jqplot-image)

Leaflet
----
* [Simple Map]({path}/leaflet-simple)
* [Map Markers]({path}/leaflet-markers)

Sparklines
----
* [Sparkline Line]({path}/sparkline)
* [Sparkline Bar]({path}/sparkbar)
""".format(path='/'+'/'.join([
    system.app.name,
    'data-visualization',
]))

tpl = load_content('visualization-layout')


def get_code(method):
    source = getsource(method)
    lines = [l[4:] for l in source.splitlines()[1:-1]]
    selection = '\n'.join(lines)
    return markdown(selection)


class MyView(View):

    def index(self):
        def get_title(method):
            code = getsource(method)
            title = method.__doc__.splitlines()[0]
            return title
        thumbnails = []
        for name, method in getmembers(self, predicate=ismethod):
            if not name.startswith('_') and not name in ['index', 'show']:
                link = link_to(get_title(method), name)
                thumbnails.append(method()['visualization'])
        content = ul(div(t, Class='thumbnail') for t in thumbnails)
        return page(
            div(
                div(
                    markdown(toc),
                    Class="col-md-3",
                ) + div(
                    content,
                    Class="col-md-9 thumbnails",
                ),
                Class='row',
            ), css=css)

    def __call__(self, vis=None):
        system.app.menu.append('Data Visualization')
        if vis:
            method = getattr(self, vis.replace('-','_'))
            result = method()
            result['side_panel'] = markdown(toc)
            result['doc'] = method.__doc__
            result['code'] = get_code(method)
            result['data'] = ''
            return page(tpl, callback=result.get, css=css)

        else:
            return self.index()

    def c3_line(self):
        """c3 Line

        Example showing how to generate a line chart using c3 module.
        """

        from random import randint
        from zoom.vis.c3 import line

        page_title = 'C3 Line Chart'

        xaxis_label = 'Month'

        legend = 'North', 'South'
        labels = (
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        )

        data = [(m, randint(1, 100), randint(1, 100)) for m in labels]

        visualization = line(data, legend=legend, title='Page Hits by Month')

        return locals()

    def jqplot_line(self):
        """jqPlot Line

        Example showing how to generate a line chart using jqplot module.
        """

        from random import randint
        from zoom.vis.jqplot import line

        page_title = 'JQPlot Line Chart'

        xaxis_label = 'Month'

        legend = 'North', 'South'
        labels = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'

        data   = [(m, randint(1,100), randint(1,100)) for m in labels]

        options = dict(axes=dict(xaxis=dict(label=xaxis_label, tickInterval=2)))

        visualization = line(data, legend=legend, title='Page Hits by Month', options=options)

        return locals()


    def jqplot_bar(self):
        """jqPlot Bar

        Example showing how to generate a bar chart using jqplot module.
        """

        from random import randint
        from zoom.vis.jqplot import bar

        page_title = 'JQPlot Bar Chart'

        legend = 'Page1', 'Page2'
        months = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'
        data = [(m, randint(-2500,5000), randint(1,10000)) for m in months]

        visualization = bar(
            data,
            title='Page Hits by Month',
            seriesColors=['red','#cc88aa'],
            legend=legend,
        )

        return locals()

    def jqplot_hbar(self):
        """jqPlot Horizontal Bar Chart

        Example showing how to generate a horizontal bar chart using jqplot module.
        """

        from random import randint
        from zoom.vis.jqplot import hbar

        page_title = 'JQPlot Horizontal Bar Chart'

        legend = 'Page1', 'Page2'
        months = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'
        data = [(m, randint(1, 10000), randint(1, 10000)) for m in months]

        visualization = hbar(
            data,
            title='Page Hits by Month',
            seriesColors=['red', '#cc88aa'],
            legend=legend,
        )

        return locals()


    def jqplot_pie(self):
        """jqPlot Pie Chart

        Example showing how to generate a pie chart using jqplot module.
        """

        from random import randint
        from zoom.vis.jqplot import pie

        page_title = 'JQPlot Pie Chart'

        sources = 'Facebook', 'Twitter', 'LinkedIn', 'Other'
        data = [(s, randint(1, 10000)) for s in sources]

        visualization = pie(
                data,
                chart_id='my_pie_chart',
                title='Visits by Source',
                legend=sources,
                )

        return locals()

    def jqplot_gauge(self):
        """jqPlot Gauge Chart

        Example showing how to generate a gauge chart using jqplot module.
        """

        from random import randint
        from zoom.vis.jqplot import gauge

        page_title = 'JQPlot Guage'

        data = float(randint(1, 100))/20

        visualization = gauge(
            data,
            title='Average Load Time',
            min=1,
            max=10,
            intervals=[5, 8, 10],
            label='average load time in seconds',
            interval_colors=['#66cc66', '#E7E658', '#cc6666'],
        )

        return locals()

    def jqplot_ts(self):
        """jqPlot TimeSeries Chart

        Example showing how to generate a time series chart using jqplot
        module.
        """

        from random import randint
        from zoom.vis.jqplot import time_series

        page_title = 'JQPlot Time Series Chart'

        xaxis_label = 'Date'
        time_format = '%b %#d, %#I %p'

        start_date = datetime.datetime(2014, 1, 1)
        delta = datetime.timedelta(days=1)
        data = [(start_date + n * delta, randint(1, 100), randint(1, 100))
                for n in range(60)]

        legend = 'North', 'South'

        options = dict(axes=dict(xaxis=dict(label=xaxis_label)))

        visualization = time_series(
            data,
            chart_id='ts1',
            legend=legend,
            time_format=time_format,
            title='Page Hits by Month',
            options=options
        )

        return locals()


    def jqplot_theme(self):
        """jqPlot Theme

        Example showing how to add a theme to a jqPlot chart.
        """

        from random import randint
        from zoom.vis.jqplot import line

        page_title = 'JQPlot Line Chart'

        xaxis_label = 'Month'

        legend = 'North', 'South'
        labels = (
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        )

        data = [(m, randint(1, 100), randint(1, 100)) for m in labels]
        options = dict(axes=dict(xaxis=dict(label=xaxis_label, tickInterval=2)))

        theme = 'chocolate', load('assets/chocolate-line.js')

        visualization = line(data, legend=legend, title='Page Hits',
                             theme=theme, options=options)

        return locals()

    def jqplot_image(self):
        """jqPlot Image

        Example showing how to render a jqPlot chart that is accompanied by a
        chart Image that can be used for copying and pasting, and printing.
        """

        from random import randint
        from zoom.vis.jqplot import line

        page_title = 'JQPlot Line Chart with Image'

        xaxis_label = 'Month'

        legend = 'North', 'South'
        labels = (
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        )

        data = [(m, randint(1, 100), randint(1, 100)) for m in labels]
        options = dict(axes=dict(xaxis=dict(label=xaxis_label, tickInterval=2)))

        visualization = line(data, legend=legend, title='Page Hits',
                             with_image=True, options=options)

        return locals()

    def leaflet_simple(self):
        """Simple Leaflet Map

        Example showing how to generate a simple map using leaflet module.
        """

        from zoom.vis.leaflet import Map

        page_title = 'Simple Map'

        BC_LL = [55, -125]

        visualization = Map(BC_LL, zoom=4).render()

        return locals()

    def leaflet_markers(self):
        """Leaflet Map with Markers

        Example showing how to generate a map with markers using leaflet
        module.
        """

        from zoom.vis.leaflet import Map, Marker

        page_title = 'Simple Map'

        VANCOUVER_MARKER = Marker([49.25, -123.1], 'Vancouver')
        EDMONTON_MARKER = Marker([53.53, -113.5], 'Edmonton')
        CALGARY_MARKER = Marker([51.5, -114], 'Calgary')
        REGINA_MARKER = Marker([50.5, -104.6], 'Regina')
        WINNIPEG_MARKER = Marker([49.9, -97.1], 'Winnipeg')
        TORONTO_MARKER = Marker([43.7, -79.4], 'Toronto')
        OTTAWA_MARKER = Marker([45.4, -75.7], 'Ottawa')

        markers = [
            VANCOUVER_MARKER,
            EDMONTON_MARKER,
            CALGARY_MARKER,
            REGINA_MARKER,
            WINNIPEG_MARKER,
            TORONTO_MARKER,
            OTTAWA_MARKER,
        ]

        visualization = Map(markers=markers).render()
        return locals()

    def sparkline(self):
        """Sparkline Chart

        Example showing how to generate a line sparkline chart using
        sparkline module.
        """
        from random import randint
        import zoom.vis.sparkline as sparkline

        page_title = 'Sparkline Line Example'

        data = [randint(1, 50) for i in range(25)]
        text = 'This {} is an example of a sparkline for the data <br>{}'
        visualization = text.format(sparkline.line(data), data)

        return locals()

    def sparkbar(self):
        """Sparkbar Chart

        Example showing how to generate a bar sparkline chart using
        sparkline module.
        """

        from random import randint
        import zoom.vis.sparkline as sparkline

        page_title = 'Sparkline Line Example'

        data = [randint(1, 50) for i in range(20)]
        text = 'This {} is an example of a sparkline for the data<br>{}'
        visualization = text.format(sparkline.bar(data), data)

        return locals()


view = MyView()
