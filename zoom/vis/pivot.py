""" pivottable.js helper

    reference: https://github.com/nicolaskruchten/pivottable

    TODO
        i. inline .js support? (vs. tail)
        i. consider support for inline data (vs. url)
        i. support specifying object name for additional/complex options
        i. look into options for resize

        i. ensure unique vars (GUID) for multiple pivots per page
"""
import re

from zoom import system, json
from .d3 import d3_libs

object_inline = "span"
object_block  = "div"

pivot_tpl = """
        <script type="text/javascript">
            var pivoturl,
                pivotdata,
                pivotoptions;

            $(function() {
                var derivers = $.pivotUtilities.derivers;
                var tpl      = $.pivotUtilities.aggregatorTemplates;
                pivoturl = "%(datasource)s";

                pivotoptions = %(options)s;
                // passed through or previously defined
                if (typeof getCustomOptions === 'function') {
                    var customoptions = getCustomOptions();
                } else {
                    var customoptions = %(options_passthrough)s;
                }
                $.extend( pivotoptions, customoptions );

                $.getJSON(pivoturl, function(data) {
                    pivotdata = data.data || data;
                    $("#%(selector)s").%(js_obj)s(pivotdata, pivotoptions%(extended)s);
                });
             });
        </script>
"""

d3_css = """
.node {
  border: solid 1px white;
  font: 10px sans-serif;
  line-height: 12px;
  overflow: hidden;
  position: absolute;
  text-indent: 2px;
}
"""

# mapping to a pivottable renderer name
renderers_lookup = dict(
        base = '$.pivotUtilities.renderers',
        renderers = '$.pivotUtilities.renderers',
        export_renderers = '$.pivotUtilities.export_renderers',
        export = '$.pivotUtilities.export_renderers',
        d3_renderers = '$.pivotUtilities.d3_renderers',
        d3 = '$.pivotUtilities.d3_renderers',
    )
renderer_name_lookup = {'Treemap': 'd3', 'TSV Export': 'export'}


def add_libs(styles=True, renderers=None):
    """ put the standard libs and styles into the page """
    def has_renderer_string(s):
        return filter(lambda a: renderers_lookup.get(s) in a, renderers)

    libs = ["/static/dz/pivottable/pivot.min.js"]
    if renderers is not None:
        if 'd3' in renderers or 'd3_renderers' in renderers or has_renderer_string('d3'):
            libs.extend(d3_libs)
            libs.append("/static/dz/pivottable/d3_renderers.min.js")
            if styles:
                system.css = system.css | [d3_css]
        if 'export' in renderers or 'export_renderers' in renderers or has_renderer_string('export'):
            libs.append("/static/dz/pivottable/export_renderers.min.js")
    system.libs = system.libs | libs
    if styles: system.styles = system.styles | ["/static/dz/pivottable/pivot.min.css"]

def bind_object(selector, classed='nojs', inline=False):
    """ return the html object to bind the pivottable into """
    foucs = ['inojs', 'nojs']
    fouc = inline and 'inojs' or 'nojs'
    obj = inline and object_inline or object_block
    classed = hasattr(classed, '__iter__') and classed or [classed]
    classed = ' '.join([fouc if c in foucs else c for c in classed])
    return """<{} id="{}" class="{}"></{}>""".format(obj, selector, classed, obj)

def pivot_simple( datasource, selector="#pivottable", options={}, inline=False, *args ):
    """ setup the pivot table on the page """
    renderer = options.get('renderer')
    options = escape_options(options)
    selector = selector.startswith('#') and selector[1:] or selector
    options_passthrough="{}"
    js_obj = 'pivot'
    extended = ''

    add_libs(styles=True, renderers=[renderer])
    mytail = pivot_tpl % (locals())
    system.tail.add(mytail)
    return bind_object(selector, classed = inline and 'inojs' or 'nojs', inline=inline)

def escape_options(options):
    options = json.dumps(options, sort_keys=True, indent=4)
    return re.sub(r'\"\$\.(.*)"', lambda a: '$.'+a.group(1), options)

def decode_options(options, **kwargs):
    """ decode the supplied options

        options: handle/escape any necessary options as the options parameter is expected to be passed onto the .js object
        kwargs: handle python helper arguments that encode to a given .js object "option"
    """
    def js_extend(a,b):
        """ create a jQuery object/properties extend string """
        if not a or not b:
            return a or b
        return "$.extend({0}, {1})".format(a,b)
    renderer_name = renderer_name_lookup.get(options.get('rendererName'))
    renderers_string = options.get('renderers')
    py_renderers = kwargs.get('renderers')
    if py_renderers:
        """ python helper received a renderers argument, try and decode it """
        r = filter(bool, map(renderers_lookup.get, py_renderers))
        if r:
            renderers_string = reduce(js_extend, filter(bool, [renderers_string] + r))
            options['renderers'] = renderers_string
    if renderer_name:
        renderer_name_renderer = renderers_lookup.get(renderer_name)
        options['renderers'] = renderers_string and js_extend(renderers_string, renderer_name_renderer) or renderer_name_renderer
    selected_renderers = filter(bool, kwargs.get('renderers',[]) + [renderer_name, renderers_string])

    return (escape_options(options), selected_renderers)

def pivot_ui( datasource, selector="#pivottable", options={}, options_passthrough="{}", inline=False, **kwargs ):
    """ setup the pivot table on the page """
    options, selected_renderers = decode_options(options, **kwargs)
    selector = selector.startswith('#') and selector[1:] or selector
    js_obj = 'pivotUI'
    extended = ', '.join([json.dumps(kwargs.get(k)) for k in kwargs.keys() if k in ['overwrite', 'locale']])
    extended = extended and ', {}'.format(extended) or extended

    add_libs(styles=True, renderers=selected_renderers)
    mytail = pivot_tpl % (locals())
    system.tail.add(mytail)
    return bind_object(selector, classed = inline and 'inojs' or 'nojs', inline=inline)


pivot = pivot_ui
