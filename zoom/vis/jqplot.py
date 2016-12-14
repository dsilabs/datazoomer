"""
    jqplot wrapper
"""

import re
import json
import uuid

from zoom import system
from zoom.vis.utils import merge_options


JQPLOT_SCRIPTS = [
    "/static/dz/jqplot/excanvas.js",
    "/static/dz/jqplot/jquery.jqplot.min.js",
    "/static/dz/jqplot/plugins/jqplot.highlighter.js",
    "/static/dz/jqplot/plugins/jqplot.cursor.js",
    "/static/dz/jqplot/plugins/jqplot.dateAxisRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.canvasTextRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.canvasAxisTickRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.barRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.categoryAxisRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.pointLabels.js",
    "/static/dz/jqplot/plugins/jqplot.pieRenderer.js",
    "/static/dz/jqplot/plugins/jqplot.meterGaugeRenderer.js",
]

JQPLOT_STYLES = [
    "/static/dz/jqplot/jquery.jqplot.min.css"
]

JQPLOT_JS = """
        $(document).ready(function(){
            var data = %(data)s;
            var options = %(options)s;
            $("#%(chart_id)s").jqplot(data, options);

            $( window ).resize(function() {
              // work around unpatched jqplot bug for bar width resize
              $.each($("#%(chart_id)s").data('jqplot').series, function(index, series) {
                if ( !(options.width && options.height)  ) {
                    series.barWidth = undefined;
                }
              });
              $("#%(chart_id)s").data('jqplot').replot( { resetAxes: true } );
            });

            %(apply_theme)s

            %(image_js)s
          });
"""

CHART_TPL = """
    <div class="dz-jqplot">
        <div id="%(chart_id)s" class="chart"></div>
        %(image_html)s
    </div>
"""

IMAGE_JS_TPL = """
            var imgData = $('#%(chart_id)s').jqplotToImageStr({});
            var imgElem = $('<img/>').attr('src', imgData);
            $('#img_%(chart_id)s').append(imgElem);
"""

IMAGE_HTML_TPL = """
        <button type="button" class="btn btn-info modal-button" data-toggle="modal" data-target="#chartModal_%(chart_id)s">Copy this Chart</button>
        <div id="chartModal_%(chart_id)s" class="modal fade" role="dialog">
            <div class="modal-dialog">

                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 class="modal-title">Right click on the image to copy.</h4>
                    </div>
                    <div class="modal-body">
                        <div id="img_%(chart_id)s" class="chart_img"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
"""




def render_options(default_options, options, k=None):
    """Merges options with default options and inserts plugins"""
    is_plugin = r'\"\$\.jqplot\.(.*)"'
    combined = merge_options(merge_options(default_options, options), k)
    result = json.dumps(combined, sort_keys=True, indent=4)
    return re.sub(is_plugin, lambda a: '$.jqplot.'+a.group(1), result)


def chart(parameters):
    """assemble chart components"""

    def install_theme(parameters):
        """adds a theme to the chart parameters if necessary

        Themes are provided as a (name, data) tuple where name
        is just lowercase name with no hyphens or spaces and data
        is a json object as specified in the jqplot docs.
        """
        chart_theme = parameters.pop('chart_theme', None)
        chart_id = parameters['chart_id']
        if chart_theme:
            name, data = chart_theme
            code = """
            // apply theme
            {name} = {data};
            console.log($("#{chart_id}").data('jqplot'));
            {name} = $("#{chart_id}").data('jqplot').themeEngine.newTheme('{name}', {name});
            $("#{chart_id}").data('jqplot').activateTheme('{name}');
            """.format(name=name, data=data, chart_id=chart_id)
        else:
            code = ""
        parameters['apply_theme'] = code

    install_theme(parameters)

    if parameters.pop('with_image', False):
        parameters['image_js'] = IMAGE_JS_TPL % parameters
        parameters['image_html'] = IMAGE_HTML_TPL % parameters
    else:
        parameters['image_js'] = ''
        parameters['image_html'] = ''

    system.libs = system.libs | JQPLOT_SCRIPTS
    system.styles = system.styles | JQPLOT_STYLES
    system.js.add(JQPLOT_JS % parameters)
    return CHART_TPL % parameters


def line(data, legend=None, options=None, **k):
    """produce a line chart"""

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

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

    if len(data) > 1:
        labels, data = data[0], data[1:]
        default_options['axes']['xaxis']['ticks'] = labels

    if legend:
        default_options['legend'] = dict(show='true', placement='insideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
        with_image=k.pop('with_image', False)
        )

    return chart(parameters)


def bar(data, legend=None, options=None, **k):
    """produce a bar chart"""
    # pylint: disable=blacklisted-name
    # It's reasonable in this case.

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = zip(*data)

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.BarRenderer',
            'rendererOptions': {'fillToZero': True, 'useNegativeColors': False}
        },
        'axes': {
            'xaxis': {
                'label': '&nbsp',
            },
        },
    }

    if len(data) > 1:
        labels, data = data[0], data[1:]
        default_options['axes'].setdefault('xaxis', {})
        default_options['axes']['xaxis'].setdefault('renderer',
                                            '$.jqplot.CategoryAxisRenderer')
        default_options['axes']['xaxis'].setdefault('ticks', labels)

    if legend:
        default_options['legend'] = dict(show='true', placement='outsideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
    )

    return chart(parameters)


def hbar(data, legend=None, options=None, **k):
    """produce a horizontal bar chart"""

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = zip(*data)

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.BarRenderer',
            'rendererOptions': {
                'barDirection': 'horizontal',
            }
        },
        'axes': {
            'xaxis': {
                'label': '&nbsp',
            },
        },
    }

    if len(data) > 1:
        labels, data = data[0], data[1:]
        default_options['axes'].setdefault('yaxis', {})
        default_options['axes']['yaxis'].setdefault('renderer',
                                            '$.jqplot.CategoryAxisRenderer')
        default_options['axes']['yaxis'].setdefault('ticks', labels)

    if legend:
        default_options['legend'] = dict(show='true', placement='outsideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
    )

    return chart(parameters)


def pie(data, legend=None, options=None, **k):
    """produce a pie chart"""

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

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
        default_options['legend'] = dict(show='true', location='e')

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
    )

    return chart(parameters)


def gauge(data,
          label=None,
          intervals=None,
          interval_colors=None,
          options=None,
          **k):
    """produce a gauge chart"""

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = [[data]]

    default_options = {
        'seriesDefaults': {
            'renderer': '$.jqplot.MeterGaugeRenderer',
            'rendererOptions': {
                'min': 0,
                'max': 5,
                }
            },
        }

    renderer_options = default_options['seriesDefaults']['rendererOptions']
    if label:
        renderer_options['label'] = label

    if intervals:
        renderer_options['intervals'] = intervals
        renderer_options['labelPosition'] = 'bottom'

    renderer_options['min'] = k.pop('min', 0)
    renderer_options['max'] = k.pop('max', 5)

    if interval_colors:
        renderer_options['intervalColors'] = interval_colors

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
    )

    return chart(parameters)


def time_series(data, legend=None, time_format='%b %e', options=None, **k):
    """produce a time series chart"""

    chart_id = k.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    fmt = '%m/%d/%Y %H:%M:%S'
    min_date = min(r[0] for r in data).strftime(fmt)
    max_date = max(r[0] for r in data).strftime(fmt)
    data = [
        [[r[0].strftime(fmt)]+list(r[n+1:n+2]) for r in data]
        for n in range(len(data[0])-1)
    ]

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
                'tickOptions': {'formatString': time_format},
                'min': min_date,
                'max': max_date,
                'label': '&nbsp',
            }
        }
    }

    if legend:
        default_options['legend'] = dict(show='true', placement='insideGrid')
        default_options['series'] = [dict(label=label) for label in legend]

    parameters = dict(
        chart_id=chart_id,
        chart_theme=k.pop('theme', None),
        data=json.dumps(data),
        options=render_options(default_options, options, k),
        )

    return chart(parameters)
