"""
    c3 wrapper
"""

import uuid
import json

from zoom.component import component
from zoom.vis.utils import merge_options

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


def line(data, options=None, **kwargs):
    """produce a line chart"""

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = get_chart_id(**kwargs)
    legend = kwargs.pop('legend', None)

    data = zip(*data)

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
        },
        'legend': {
            'position': 'inset',
        },
        'axis': {
            'x': {
                'type': 'category'
            },
        },
        'bindto': '#' + chart_id
    }
    options = merge_options(merge_options(default_options, options), kwargs)

    content = """
        <div class="dz-c3-chart placeholder" id="%s"></div>
    """ % chart_id

    js = """
    $(function(){
        var chart = c3.generate(%(options)s);
    });
    """ % dict(options=json.dumps(options, indent=4))
    return component(content, js=js, libs=libs, styles=styles, css=css)


def spline(data, options=None, **kwargs):
    """produce a spline chart"""

    default_options = {
        'data': {
            'type': 'spline',
        },
    }

    options = merge_options(merge_options(default_options, options), kwargs)
    return line(data, options, **kwargs)


def area(data, options=None, **kwargs):
    """produce an area chart"""

    default_options = {
        'data': {
            'type': 'area',
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return line(data, options, **kwargs)


def area_spline(data, options=None, **kwargs):
    """produces spline area chart"""

    default_options = {
        'data': {
            'type': 'area-spline',
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return area(data, options, **kwargs)


def stacked_area(data, options=None, **kwargs):
    """produces a stacked area chart"""
    stacks = kwargs.pop('stacks', [])

    default_options = {
        'data': {
            'groups': stacks,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return area(data, options, **kwargs)


def stacked_area_spline(data, options=None, **kwargs):
    """produces a stacked area chart"""
    stacks = kwargs.pop('stacks', [])

    default_options = {
        'data': {
            'type': 'area-spline',
            'groups': stacks,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return area(data, options, **kwargs)


def bar(data, options=None, **kwargs):
    """produce a bar chart"""

    default_options = {
        'data': {
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
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return line(data, options, **kwargs)


def hbar(data, options=None, **kwargs):
    default_options = {
        'axis': {
            'rotated': True,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return bar(data, options, **kwargs)


def stacked_bar(data, options=None, **kwargs):
    """produce a stacked bar chart"""
    stacks = kwargs.pop('stacks', [])

    default_options = {
        'data': {
            'groups': stacks,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return bar(data, options, **kwargs)


def stacked_hbar(data, options=None, **kwargs):
    default_options = {
        'axis': {
            'rotated': True,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return stacked_bar(data, options, **kwargs)


def step(data, options=None, **kwargs):
    """produce a bar chart"""

    default_options = {
        'data': {
            'type': 'area-step'
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return line(data, options, **kwargs)


def stacked_step(data, options=None, **kwargs):
    """produces a stacked area chart"""
    stacks = kwargs.pop('stacks', [])

    default_options = {
        'data': {
            'groups': stacks,
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return step(data, options, **kwargs)


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
    options = json.dumps(options, indent=4).replace(
        '"<<formatter>>"', formatter)
    js = """
    $(function(){
        var chart = c3.generate(%(options)s);
    });
    """ % dict(options=options)

    return component(content, js=js, libs=libs, styles=styles, css=css)


def donut(data, options=None, **kwargs):
    """produce a donut chart"""

    chart_id = get_chart_id(**kwargs)

    default_options = {
        'data': {
            'columns': data,
            'type': 'donut',
        },
        'tooltip': {
            'format': {
                'value': '<<formatter>>',
            },
        },
        'bindto': '#' + chart_id,
    }
    options = merge_options(merge_options(default_options, options), kwargs)

    content = """
        <div class="dz-c3-chart placeholder" id="{}"></div>
    """.format(chart_id)
    formatter = 'function(x){return x}'
    options = json.dumps(options, indent=4).replace(
        '"<<formatter>>"', formatter)
    js = """
    $(function(){
        var chart = c3.generate(%(options)s);
    });
    """ % dict(options=options)

    return component(content, js=js, libs=libs, styles=styles, css=css)


def pie(data, options=None, **kwargs):
    """produce a pie chart"""

    default_options = {
        'data': {
            'type': 'pie',
        },
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return donut(data, options, **kwargs)


def scatter(data, options=None, **kwargs):
    """produce a scatter plot"""
    rotate_axis = kwargs.pop('rotate_axis', False)

    default_options = {
        'data': {
            'type': 'scatter',
        },
        'axis': {
            'rotated': rotate_axis
        }
    }
    options = merge_options(merge_options(default_options, options), kwargs)
    return line(data, options, **kwargs)
