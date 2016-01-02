""" pivottable.js helper

    reference: https://github.com/nicolaskruchten/pivottable

    TODO
        i. inline .js support? (vs. tail)
        i. consider support for inline data (vs. url)
        i. support specifying object name for additional/complex options
        i. look into options for resize

        i. ensure unique vars (GUID) for multiple pivots per page
"""
from zoom import system, json

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
                    pivotdata = data;
                    $("#%(selector)s").%(js_obj)s(data, pivotoptions%(extended)s);
                });
             });
        </script>
"""

def add_libs(styles=True):
    """ put the standard libs and styles into the page """
    system.libs = system.libs | ["/static/dz/pivottable/pivot.min.js"]
    if styles: system.styles = system.styles | ["/static/dz/pivottable/pivot.css"]

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
    options = json.dumps(options, sort_keys=True, indent=4)
    selector = selector.startswith('#') and selector[1:] or selector
    options_passthrough="{}"
    js_obj = 'pivot'
    extended = ''

    add_libs(styles=True)
    mytail = pivot_tpl % (locals())
    system.tail.add(mytail)
    return bind_object(selector, classed = inline and 'inojs' or 'nojs', inline=inline)

def pivot_ui( datasource, selector="#pivottable", options={}, options_passthrough="{}", inline=False, **kwargs ):
    """ setup the pivot table on the page """
    options = json.dumps(options, sort_keys=True, indent=4)
    selector = selector.startswith('#') and selector[1:] or selector
    js_obj = 'pivotUI'
    extended = ', '.join([json.dumps(kwargs.get(k)) for k in kwargs.keys() if k in ['overwrite', 'locale']])
    extended = extended and ', {}'.format(extended) or extended

    add_libs(styles=True)
    mytail = pivot_tpl % (locals())
    system.tail.add(mytail)
    return bind_object(selector, classed = inline and 'inojs' or 'nojs', inline=inline)


pivot = pivot_ui
