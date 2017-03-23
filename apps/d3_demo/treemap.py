""" treemap.py

    d3.js treemap chart example
"""
import zoom
import zoom.tools
import zoom.vis.d3


class Treemap(zoom.vis.d3.Treemap):
    """ An explorable Treemap heirarchy plot with a custom .js treedata function """
    js = """
    $(function(){
      var %(ref)s = d3.charts.treemap()%(methods)s;
      d3.json("%(view)s", function(data) {

            treedata = {
                "name": data.title || 'Treemap',
                "children": d3.nest()
                              .key(function(d) { return d[0];}).sortKeys(d3.ascending)
                              .key(function(d) { return '/' + d[1].split('/').splice(1).join('/');}).sortKeys(d3.ascending)
                              .rollup(function(d) { return d3.sum(d, function(g) {return +g[2]; }) })
                              .entries(data.data),  // 'name':d.key, 'size':d.values.value, 'values':d.values
            };

          d3.select("%(selector)s")
            .style("margin-top", "3em")
            .datum(treedata)
            .call(%(ref)s);

          window.dispatchEvent(new Event('resize'));
      });
    });"""


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

        chart1 = zoom.vis.d3.treemap(data, options=options)  # flat treemap plot
        chart2 = str(Treemap(data, options=dict(width=1600), selector='chart2'))  # heirarchy
        chart = ''.join([chart1, chart2])
        content = TreemapDynamicView(chart)

        return zoom.page(content, title='Treemap Plot')


view = TreeMapView()
