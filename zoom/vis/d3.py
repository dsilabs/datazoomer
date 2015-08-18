"""d3.js tools"""
from zoom import system

d3_libs = ["/static/dz/d3/d3.min.js", "/static/dz/d3.charts.js"]
d3_styles = []

def chain_methods(options):
    return ''.join(['.{}({})'.format(method,value) for method,value in options.items()])

class scatter(object):
    """d3.js scatter plot"""
    _declare_ = """
    <script>
        var %(ref)s = d3.charts.scatter()%(methods)s;
        d3.json("%(view)s", function(data) {
            d3.select("%(selector)s")
              .datum(data)
              .call(%(ref)s);
        });
    </script>
    """
    name = property(lambda self: '%s_%s' % (self.__class__.__name__, id(self)))
    ref = property(lambda self: self.name, doc="the reference to the object")
    libs = ["/static/dz/d3/lib/tip/d3.tip.js", "/static/dz/d3/lib/jquery.dropdown.js"]

    def __init__(self, view_for_data, selector="chart"):
        self.view = view_for_data
        self.selector = selector.startswith('#') and selector or '#{}'.format(selector)
    def __str__(self):
        libs = d3_libs + self.libs
        system.libs = system.libs | libs
        system.styles = system.styles | ['/static/dz/d3/lib/jquery.dropdown.min.css']
        ref = self.ref
        view = self.view
        selector = self.selector
        methods = chain_methods(self.options)
        system.tail = system.tail | [self._declare_ % (locals())]
        return ''

class calendar(object):
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

    def __init__(self, view_for_data, selector="chart"):
        self.view = view_for_data
        self.selector = selector.startswith('#') and selector or '#{}'.format(selector)
        self.options = {}
    def __str__(self):
        libs = d3_libs + self.libs
        system.libs = system.libs | libs
        system.styles = system.styles | ['/static/dz/d3/lib/colorbrewer/colorbrewer.css']
        ref = self.ref
        view = self.view
        selector = self.selector
        methods = chain_methods(self.options)
        system.tail = system.tail | [self._declare_ % (locals())]
        return ''
