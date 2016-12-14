"""
    sparkline.py

    Sparkline charts library interface
"""

from uuid import uuid4

from zoom import system, json
from zoom.component import component

libs = [
    "/static/dz/jquery/jquery-migrate-1.2.1.min.js",
    "/static/dz/jqsparkline/jquery.sparkline.min.js",
        ]

js = """
    $(function(){

        /** This code runs when everything has been loaded on the page */
        /* Inline sparklines take their values from the contents of the tag */
        $('.inlinesparkline').sparkline('html', <<options>>);

        /* Use 'html' instead of an array of values to pass options
        to a sparkline with data in the tag */
        $('.inlinebar').sparkline('html', {type: 'bar', barColor: 'red'} );

    });
"""

responsive_js = """
    $(function() {

        var %(script_var)s = function() {
            $('.%(script_var)s').sparkline( %(data)s, %(options)s );
        }
        var sparkResize%(script_var)s;

        $(window).resize(function(e) {
            clearTimeout(sparkResize%(script_var)s);
            sparkResize%(script_var)s = setTimeout(%(script_var)s, 100);
        });
        %(script_var)s();
    });
"""


def chart(selector, data, options):
    return component(
        '<span class="{} inojs">{}</span>'.format(selector, repr(data)[1:-1]),
        js=js.replace('<<options>>', repr(options)),
        libs=libs
    )


def responsive_chart(selector, data, options):
    system.libs = system.libs | libs
    script_var = 'spark_%s' % uuid4().hex
    data = json.dumps(data)
    options = json.dumps(options)
    system.js.add(responsive_js % (locals()))
    return '<span class="{} {} inojs">&nbsp;</span>'.format(selector, script_var)


def line(data, options={}):
    selector = 'inlinesparkline'
    return chart(selector, data, options)


def bar(data, options={}):
    return chart('inlinebar', data, options)
