"""
    sparkline.py

    Sparkline charts library interface
"""

from zoom import system

css = """
    sparkline { width: 200px; }
"""

head = """
    <script type="text/javascript" src="/static/jqsparkline/jquery.sparkline.js"></script>
    <script type="text/javascript">
    $(function() {
        /** This code runs when everything has been loaded on the page */
        /* Inline sparklines take their values from the contents of the tag */
        $('.inlinesparkline').sparkline();
    
        /* Use 'html' instead of an array of values to pass options 
        to a sparkline with data in the tag */
        $('.inlinebar').sparkline('html', {type: 'bar', barColor: 'red'} );
    
        $.fn.sparkline.defaults.common.width = 200;
    });
    </script>
"""

def line(data):
    system.head.add(head)
    system.css.add(css)
    return '<span class="inlinesparkline">%s</span>' % repr(data)[1:-1]
    
def bar(data):
    system.head.add(head)
    system.css.add(css)
    return '<span class="inlinebar">%s</span>' % repr(data)[1:-1]
