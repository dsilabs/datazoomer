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


def add_script_tag(source):
    """ wrap the source file in a script tag """
    return """<script src="{}" type="text/javascript"></script>""".format(source)


class D3Object(object):
    """ Base class for d3.js helper classes """
    libs = []  # custom libs (for the page tail)
    styles = []  # custom styles
    css = ""  # component specific css
    js = ""  # component specific js
    name = property(lambda self: '%s_%s' % (self.__class__.__name__, id(self)))
    ref = property(lambda self: self.name, doc="the reference to the object")
    wrapper = '<div class="dz-d3-vis" id="{}"></div>'

    def __init__(self, data, options=None, **kwargs):
        """ Initialize the d3 object class

            data -- data for the chart
            options -- chart spcific options (passthrough)
            kwargs -- kwargs used by the helper object to build the component (class specific)
        """
        self.view = data
        self.selector = as_selector(kwargs.pop('selector', 'chart'))
        self.options = options or {}

    def __str__(self):
        return self.render()

    def render(self):
        """ return the web component for the chart """
        css = self.css % dict(selector=self.selector)
        js = self.js % dict(
            ref=self.ref,
            view=self.view,
            selector=self.selector,
            methods=chain_methods(self.options)
        )
        js = map(add_script_tag, d3_libs + self.libs) + [
            """<script type="text/javascript">{}</script>""".format(js),
        ]
        return component(
            self.wrapper.format(self.selector[1:]),
            css=css,
            tail=js,
            styles=self.styles,
        )


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
        return self.render()

    def render(self):
        code = join(system.lib_path, '..', 'setup', 'www', 'static',
                    'dz', 'd3', 'assets', 'force.js')
        links = [dict(source=source, target=target) for source, target in self.edges]
        return component(
            '<div id="visual" class="iefallback"></div>',
            js='var links = %s;' % dumps(links) + load(code),
            styles=self.styles,
            libs=d3_libs,
        )


class HtmlTreemap(D3Object):
    """ d3.js treemap component """
    libs = ['/static/dz/d3/lib/tip/d3.tip.js', ]

    css = """
    /* treemap */
    body {
      -webkit-print-color-adjust: exact; }
    %(selector)s { margin-top: 10px; }
    %(selector)s .grandparent {
        position: relative;
        margin-left: 1px;
        padding-left: 5px; }
    %(selector)s .grandparent,
    %(selector)s g.grandparent rect {
        background-color: #eee;
        fill: #38c0ef; }
    %(selector)s g.grandparent text { fill: black; font-weight: bold; }
    %(selector)s .node {
      border: solid 1px white;
      font: 10px sans-serif;
      line-height: 12px;
      overflow: hidden;
      position: absolute;
      text-indent: 2px; }

    %(selector)s text {
      pointer-events: none; }
    rect {
      fill: #eee;
      stroke-width: 1px;
      stroke: white; }

    rect.parent,
    .grandparent rect {
      stroke-width: 2px; }

    .children rect.parent,
    .grandparent rect {
      cursor: pointer; }

    .children rect.parent {
      fill: #ddd;
      fill-opacity: .5; }

    .children:hover rect.child {
      fill: #ddd; }

    @media print {
      %(selector)s .node {
        background-color: #cdcdcd !important;
        -webkit-print-color-adjust: exact; }}

    .d3-tip {
        line-height: 1;
        font-weight: bold;
        padding: 12px;
        background: rgba(0, 0, 0, 0.8);
        color: #fff;
        border-radius: 2px;
        -webkit-transition: display 1s;
        /* For Safari 3.1 to 6.0 */
        transition: opacity .5s;
    }


    /* Creates a small triangle extender for the tooltip */
    .d3-tip:after {
        box-sizing: border-box;
        display: inline;
        font-size: 10px;
        width: 98%%;
        line-height: 1;
        color: rgba(0, 0, 0, 0.8);
        content: "\\25BC";
        position: absolute;
        text-align: center;
    }


    /* Style northward tooltips differently */
    .d3-tip.n:after {
        margin: -1px 0 0 0;
        top: 98%%;
        left: 0;
    }

    """

    js = """
    $(function(){
      var %(ref)s = d3.charts.html_treemap()%(methods)s;
      d3.json("%(view)s", function(data) {
          d3.select("%(selector)s")
            .datum(data)
            .call(%(ref)s);

          window.dispatchEvent(new Event('resize'));
      });
    });"""


class TreemapBrewer(HtmlTreemap):
    """ d3.js treemap component with color brewer support """
    libs = [
        '/static/dz/d3/lib/tip/d3.tip.js',
        '/static/dz/d3/lib/colorbrewer/colorbrewer.js'
    ]


def treemap(data, options=None, **kwargs):
    """ return a treemap component given the supplied data and config options """
    return str(HtmlTreemap(data, options, **kwargs))


class Treemap(HtmlTreemap):
    """ An explorable Treemap heirarchy plot with a custom .js treedata function """
    js = """
    $(function(){
      var %(ref)s = d3.charts.treemap()%(methods)s;
      d3.json("%(view)s", function(data) {

            // override here and format data (via d3.nest) if necessary

          d3.select("%(selector)s")
            .datum(data)
            .call(%(ref)s);

          window.dispatchEvent(new Event('resize'));
      });
    });"""
