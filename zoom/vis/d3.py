"""d3.js tools"""

from os.path import join, split, abspath

from zoom import system
from zoom.jsonz import dumps
from zoom.tools import load
from zoom.component import component
from zoom.vis.utils import merge_options

d3_libs = [
    '/static/dz/d3/d3.v3.min.js',
    '/static/dz/d3/d3.charts.js'
    ]
d3_styles = []


def chain_methods(options):
    return ''.join(['.{}({})'.format(method, value)
                    for method, value in options.items()])


def as_selector(name):
    return name.startswith('#') and name or '#{}'.format(name)


def load_asset(name):
    path, _ = split(abspath(__file__))
    with open(join(path, name)) as f:
        result = f.read()
    return result


class Scatter(object):
    """d3.js scatter plot"""

    libs = [
        '/static/dz/d3/lib/tip/d3.tip.js',
        '/static/dz/d3/lib/jquery.dropdown.js',
    ]
    styles = [
        '/static/dz/d3/lib/jquery.dropdown.min.css'
    ]

    name = property(lambda self: '%s_%s' % (self.__class__.__name__, id(self)))
    ref = property(lambda self: self.name, doc="the reference to the object")

    def __init__(self, data, options=None, **kwargs):
        self.view = data
        self.selector = as_selector(kwargs.pop('selector', 'chart'))
        self.options = options or {}

    def __str__(self):
        return self.render()

    def render(self):
        html = '<div class="dz-d3-vis" id="chart"></div>'
        css = load_asset('scatter_plot.css')
        js = load_asset('scatter_plot.js') % dict(
            ref=self.ref,
            view=self.view,
            selector=self.selector,
            methods=chain_methods(self.options)
        )
        return component(
            html,
            js=js,
            css=css,
            libs=d3_libs + self.libs,
            styles=self.styles,
        )


def scatter(data, options=None, **kwargs):
    return str(Scatter(data, options, **kwargs))


class Calendar(object):
    """d3.js calendar plot"""
    _declare_ = """
    <script>
        var %(ref)s = d3.charts.calendar()%(methods)s;
        d3.json("%(view)s", function(data) {
            d3.select("%(selector)s")
              .datum(data)
              .call(%(ref)s);

            d3.select("#description p.dropdown.brewer select")
                .on("click", function() {
                    var p = d3.select(this).select(":checked").text();
                    d3.select("%(selector)s").selectAll("svg")
                        .attr("class", p);
            });
        });
    </script>
    """
    name = property(lambda self: '%s_%s' % (self.__class__.__name__, id(self)))
    ref = property(lambda self: self.name, doc="the reference to the object")
    libs = ["/static/dz/d3/lib/tip/d3.tip.js", "/static/dz/d3/lib/colorbrewer/colorbrewer.js"]

    def __init__(self, data, options=None, **kwargs):
        self.view = data
        self.selector = as_selector(kwargs.pop('selector', 'chart'))
        self.options = options or {}
        self.kwargs = kwargs

    def __str__(self):
        return self.render()

    def render(self):
        default_options = {
            'palette': '"Greens"',
            'color': """
                    d3.scale.quantize().range(
                        d3.range(9).map(
                            function(d) { return "q" + d + "-9"; }
                        )
                    )
            """,
        }
        options = merge_options(merge_options(default_options, self.options), self.kwargs)

        libs = d3_libs + self.libs
        system.libs = system.libs | libs
        system.styles = system.styles | ['/static/dz/d3/lib/colorbrewer/colorbrewer.css']
        ref = self.ref
        view = self.view
        selector = self.selector
        methods = chain_methods(options)
        system.tail = system.tail | [self._declare_ % (locals())]
        return component(
            '<div id="chart"></div>',
            css=load_asset('calendar_plot.css'),
        )

def calendar(data, options=None, **kwargs):
    return str(Calendar(data, options, **kwargs))


class Force(object):
    """produce a force diagram from a list of edges"""

    styles = ['/static/dz/d3/assets/force.css']

    def __init__(self, edges):
        self.edges = edges

    def __str__(self):
        code = join(system.lib_path, '..', 'setup', 'www', 'static', 'dz', 'd3',
                'assets', 'force.js')
        links = [dict(source=source, target=target) for source, target in self.edges]
        system.js |= ['\nvar links = %s;\n' % dumps(links) + load(code)]
        system.libs |= d3_libs
        system.styles |= self.styles
        return '<div id="visual" class="iefallback"></div>'
