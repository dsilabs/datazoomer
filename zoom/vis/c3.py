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


def line(data, options=None, **kwargs):
    """produce a line chart"""

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = kwargs.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = zip(*data)

    default_options = {}
    options = merge_options(kwargs, default_options)

    legend = options.get('legend', None)
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

    # pylint: disable=star-args
    # It's reasonable in this case.

    chart_id = kwargs.pop('chart_id', 'chart_' + uuid.uuid4().hex)

    data = zip(*data)

    default_options = {}
    options = merge_options(kwargs, default_options)

    legend = options.get('legend', None)
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
                columns: %(data)s,
                type: 'bar'
            },
            bar: {
                width: {
                    ration: 0.5
                }
            },
            axis: {
                x: {
                    type: 'category'
                }
            },
            legend: {
                position: 'inset'
            }
        });
    });
    """ % dict(
        chart_id=chart_id,
        data=json.dumps(rows),
        title=kwargs.get('title', ''),
    )
    return component(content, js=js, libs=libs, styles=styles, css=css)
