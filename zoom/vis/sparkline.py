"""
    sparkline.py

    Sparkline charts library interface
"""

from zoom import system

scripts = [
    "/static/dz/jquery/jquery-migrate-1.2.1.min.js",
    "/static/dz/jqsparkline/jquery.sparkline.min.js",
        ]

js = """
    $(function(){

        /** This code runs when everything has been loaded on the page */
        /* Inline sparklines take their values from the contents of the tag */
        $('.inlinesparkline').sparkline('html',<<options>>);
    
        /* Use 'html' instead of an array of values to pass options 
        to a sparkline with data in the tag */
        $('.inlinebar').sparkline('html', {type: 'bar', barColor: 'red'} );
    
    });
"""

def chart(selector, data, options):
    system.libs = system.libs | scripts
    system.js.add(js.replace('<<options>>',repr(options)))
    return '<span class="{}">{}</span>'.format(selector, repr(data)[1:-1])

def line(data, options={}):
    selector = 'inlinesparkline'
    return chart(selector, data, options)
    
def bar(data, options={}):
    return chart('inlinebar', data, options)

