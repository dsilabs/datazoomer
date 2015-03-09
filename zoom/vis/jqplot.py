
from zoom import system
import re
import json
import uuid


css = """
    .chart {
        height:300px; 
    }
    .jqplot-axis {
        font-size: 0.8em;
    }
    .jqplot-xaxis {
        padding-top: 10px;
    }
    .jqplot-yaxis {
        padding-right: 10px;
    }
    .content .jqplot-table-legend {
        border: none; 
        padding: 0.4em 1.0em;
    }
    .content td.jqplot-table-legend-label {
        padding: 0;
    }
    div.jqplot-table-legend-swatch-outline {
        padding: 0;
    }
"""
css = css

scripts = [
    "/static/dz/jqplot/excanvas.js",
    "/static/dz/jqplot/jquery.jqplot.min.js",
    "/static/dz/jqplot/plugins/jqplot.highlighter.min.js",
    "/static/dz/jqplot/plugins/jqplot.cursor.min.js",
    "/static/dz/jqplot/plugins/jqplot.dateAxisRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.canvasTextRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.canvasAxisTickRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.barRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.categoryAxisRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.pointLabels.min.js",
    "/static/dz/jqplot/plugins/jqplot.pieRenderer.min.js",
    "/static/dz/jqplot/plugins/jqplot.meterGaugeRenderer.min.js",
        ]

styles = [
    "/static/dz/jqplot/jquery.jqplot.min.css"
        ]

chart_tpl = """
    <div id="chart_%(name)s" class="chart"></div>
    <script class="code" type="text/javascript">
        $(document).ready(function(){
            var data = %(data)s;
            var options = %(options)s;
            var plot1 = $.jqplot('chart_%(name)s', data, options);
          });
    </script>
"""

chart_tpl = """
    <div id="chart_%(name)s" class="chart"></div>
"""

chart_js = """
        $(document).ready(function(){
            var data = %(data)s;
            var options = %(options)s;
            var plot1 = $.jqplot('chart_%(name)s', data, options);
          });
"""

def merge_options(a, b):
    """Merges two sets of options"""
    if hasattr(a,'keys') and hasattr(b,'keys'):
        c = {}
        for k in a:
            c[k] = a[k]
        for k in b:
            if k in c:
                c[k] = merge_options(c[k],b[k])
            else:
                c[k] = b[k]
        return c
    else:
        return b

PLUGIN = '\"\$\.jqplot\.(.*)"' 

def render_options(default_options, options, k={}):
    """Merges options with default options and inserts plugins"""
    combined = merge_options(merge_options(default_options, options), k)
    result = json.dumps(combined, sort_keys=True, indent=4)
    return re.sub(PLUGIN, lambda a: '$.jqplot.'+a.group(1), result)


def chart(v):
    system.libs = system.libs | scripts
    system.styles = system.styles | styles
    system.js.add(chart_js % v)
    system.css.add(css)
    return chart_tpl % v


def line(data, legend=None, options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = zip(*data)

    default_options = {
            'highlighter': {
                'show': True,
                'sizeAdjust': 7.5,
                'tooltipSeparator': ' - ',
                'tooltipAxes': 'y',
                },
            'axes': {
                'xaxis': {
                    'renderer': '$.jqplot.CategoryAxisRenderer',
                    }
                }
            }

    if len(data)>1:  
        labels, data = data[0], data[1:]
        default_options['axes']['xaxis']['ticks'] = labels

    if legend:
        default_options['legend'] = dict(show='true', placement='insideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    v = dict(
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
        )

    return chart(v)


def bar(data, legend=None, options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = zip(*data)

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.BarRenderer',
            'rendererOptions': { 'fillToZero': True, 'useNegativeColors': False }
            },
        }

    if len(data)>1:  
        labels, data = data[0], data[1:]
        options['axes'] = dict(
                xaxis=dict(
                    renderer='$.jqplot.CategoryAxisRenderer',
                    ticks=labels,
                    )
                )

    if legend:
        options['legend'] = dict(show='true', placement='outsideGrid')
        options['series'] = [dict(label=label) for label in legend]

    v = dict (
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
    )

    return chart(v)


def hbar(data, legend=None, options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = zip(*data)

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.BarRenderer',
            'rendererOptions': {
                'barDirection': 'horizontal',
                }
            },
        }

    if len(data)>1:  
        labels, data = data[0], data[1:]
        options['axes'] = dict(
                yaxis=dict(
                    renderer='$.jqplot.CategoryAxisRenderer',
                    ticks=labels,
                    )
                )

    if legend:
        options['legend'] = dict(show='true', placement='outsideGrid')
        options['series'] = [dict(label=label) for label in legend]

    v = dict (
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
    )

    return chart(v)


def pie(data, legend=None, options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = [[row[:2] for row in data]] # can only handle one series right now

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.PieRenderer',
            'rendererOptions': {
                'showDataLabels': True,
                'sliceMargin': 5,
                'shadow': False,
                }
            },
        }

    if legend:
        options['legend'] = dict(show='true', location='e')

    v = dict (
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
    )

    return chart(v)


def gauge(data, label=None, intervals=None, interval_colors=None, options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = [[data]];

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.MeterGaugeRenderer',
            'rendererOptions': {
                'min': 0,
                'max': 5,
                }
            },
        }

    if label:
        default_options['seriesDefaults']['rendererOptions']['label'] = label

    if intervals:
        default_options['seriesDefaults']['rendererOptions']['intervals'] = intervals
        default_options['seriesDefaults']['rendererOptions']['labelPosition'] = 'bottom'

    if interval_colors:
        default_options['seriesDefaults']['rendererOptions']['intervalColors'] = interval_colors

    v = dict (
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
    )

    return chart(v)


def time_series(data, legend=None, time_format='%b %e', options={}, *a, **k):

    chart_name = uuid.uuid4().hex

    data = [[[r[0].strftime('%m/%d/%Y %H:%M:%S')]+list(r[n+1:n+2]) for r in data] for n in range(len(data[0])-1)]
    min_date = min(r[0] for r in data[0])
    max_date = max(r[0] for r in data[0])

    default_options = {
            'highlighter': {
                'show': True,
                'sizeAdjust': 2.5,
                'tooltipSeparator': ' - ',
                'tooltipAxes': 'y',
                },
            'axes': {
                'xaxis': {
                    'renderer': '$.jqplot.DateAxisRenderer',
                    'tickOptions': { 'formatString': time_format },
                    'min': min_date,
                    'max': max_date,
                    }
                }
            }

    if legend:
        default_options['legend'] = dict(show='true', placement='insideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    v = dict(
        name = chart_name,
        data = json.dumps(data),
        options = render_options(default_options, options, k),
        )

    return chart(v)


