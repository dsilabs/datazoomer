""" treemap.py

    d3.js treemap chart example
"""
import zoom
import zoom.tools
import zoom.vis.d3


class TreemapDynamicView(zoom.mvc.DynamicView):
    """ Dynamic View for the Treemap demonstration """
    @property
    def treemap(self):
        """ return the treemap markup """
        return self.model


class TreeMapView(zoom.View):
    """ MVC View class for the Treemap """

    def index(self):
        """ default/index route for the view """
        data = zoom.url_for_page('treemap_data')
        options = dict(
            width=1600,
            key_accessor="function(d) { return d[0]; }",
            value_accessor="function(d) { return d[2]; }",
        )

        chart = zoom.vis.d3.treemap(data, options=options)
        content = TreemapDynamicView(chart)

        return zoom.page(content, title='Treemap Plot')


view = TreeMapView()
