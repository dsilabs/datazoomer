"""
    c3 wrapper
"""

import uuid
import json

from zoom.component import component
from zoom.vis.utils import merge_options
from zoom.mvc import DynamicView

styles = [
    '/static/dz/c3/c3.css',
]

libs = [
    '/static/dz/d3/d3.v3.min.js',
    '/static/dz/c3/c3.min.js',
]

css = """
.dz-c3-chart {
    height: 100%;
    width: 100%;
}
"""


def get_chart_id(**kwargs):
    return kwargs.pop('chart_id', 'chart_' + uuid.uuid4().hex)


def line(data, legend=None, options=None, **kwargs):
    """produce a line chart"""

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = kwargs.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = zip(*data)

    default_options = {
        'legend': {
            'position': 'inset'
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)

    #legend = options.get('legend', None)
    labels = data[0]

    rows = []
    rows.append(['x'] + list(labels))
    if legend:
        if len(legend) != len(data) - 1:
            msg = '{} legend must match number of data columns'
            raise Exception(msg.format(__file__))
        for n, label in enumerate(legend):
            rows.append([label] + list(data[n + 1]))

    content = """
        <div class="dz-c3-chart placeholder" id="%s"></div>
    """ % chart_id

    js = """
    $(function(){
        var chart = c3.generate({
            bindto: '#%(chart_id)s',
            title: {text: '%(title)s'},
            data: {
                x: 'x',
                columns: %(data)s
            },
            axis: {
                x: {
                    type: 'category'
                }
            }
        });
    });
    """ % dict(
        chart_id=chart_id,
        data=json.dumps(rows),
        title=kwargs.get('title', ''),
    )
    return component(content, js=js, libs=libs, styles=styles, css=css)


def bar(data, options=None, **kwargs):
    """produce a line chart"""

    chart_id = get_chart_id(**kwargs)

    data = zip(*data)
    legend = kwargs.pop('legend', None)
    labels = data[0]
    rows = []
    rows.append(['x'] + list(labels))
    if legend:
        if len(legend) != len(data) - 1:
            msg = '{} legend must match number of data columns'
            raise Exception(msg.format(__file__))
        for n, label in enumerate(legend):
            rows.append([label] + list(data[n + 1]))

    default_options = {
        'data': {
            'x': 'x',
            'columns': rows,
            'type': 'bar'
        },
        'legend': {
            'position': 'inset'
        },
        'bar': {
            'width': {
                'ratio': 0.5
            }
        },
        'axis': {
            'x': {
                'type': 'category'
            }
        },
        'legend': {
            'position': 'inset'
        },
        'bindto': '#' + chart_id
    }
    options = merge_options(merge_options(default_options, options), kwargs)

    content = """
        <div class="dz-c3-chart placeholder" id="{}"></div>
    """.format(chart_id)

    js = """
    $(function(){
        var chart = c3.generate(%(options)s);
    });
    """ % dict(options=json.dumps(options, indent=4))

    return component(content, js=js, libs=libs, styles=styles, css=css)


def hbar(data, options=None, **kwargs):
    default_options = {
        'axis': {
            'rotated': True,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return bar(data, options, **kwargs)


def gauge(data,
          label=None,
          intervals=None,
          interval_colors=None,
          options=None,
          **kwargs):
    """produce a gauge chart"""

    chart_id = get_chart_id(**kwargs)

    min_value = kwargs.pop('min', 0)
    max_value = kwargs.pop('max', 100)

    default_options = {
        'data': {
            'columns': [['', data]],
            'type': 'gauge',
        },
        'gauge': {
            'units': label,
            'min': min_value,
            'max': max_value,
            'label': {
                'show': True,
                'format': '<<formatter>>',
            },
        },
        'color': {
            'pattern': interval_colors,
            'threshold': {
                'values': intervals
            }
        },
        'bindto': '#' + chart_id,
    }
    options = default_options

    content = """
        <div class="dz-c3-chart placeholder" id="{}"></div>
    """.format(chart_id)


    formatter = 'function(value, ratio) { return value; }'
    options = json.dumps(options, indent=4).replace('"<<formatter>>"', formatter)
    js = """
    $(function(){
        var chart = c3.generate(%(options)s);
    });
    """ % dict(options=options)

    return component(content, js=js, libs=libs, styles=styles, css=css)
