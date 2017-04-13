"""
    vis.js wrapper
"""

import uuid
import json

from zoom.component import component
from zoom.vis.utils import merge_options

styles = [
    '/static/dz/visjs/dist/vis-timeline-graph2d.min.css',
    '/static/dz/visjs/dist/vis.min.css',
]

libs = [
    '/static/dz/visjs/dist/vis-timeline-graph2d.min.js',
    '/static/dz/visjs/dist/vis.min.js'
]

css = """
.dz-visjs-chart {
    height: 100%;
    width: 100%;
}
"""


def get_chart_id(**kwargs):
    return kwargs.pop('chart_id', 'chart_' + uuid.uuid4().hex)

def timeline(data, options=None, **kwargs):
    """produce a gantt timeline chart"""

    chart_id = get_chart_id(**kwargs)

    title = kwargs.pop('title', None)
    title = title and '<div class="visjs-title">{}</div>'.format(title) or ''

    default_options = {
        'editable': 'false',
    }

    options = merge_options(merge_options(default_options, options), kwargs)

    content = """
        %s
        <div class="dz-visjs-chart placeholder" id="%s"></div>
    """ % (title, chart_id)

    js = """
    $(function(){
        var container = document.getElementById("%(selector)s");
        var chart = new vis.DataSet(
            %(data)s
        );

        var options = %(options)s;

        var timeline = new vis.Timeline(container, chart, options);
        // make the object accessible later
        $("#%(selector)s").data('visjs-chart', chart);
    });
    """ % dict(selector=chart_id, data=data, options=json.dumps(options, indent=4))
    return component(content, js=js, libs=libs, styles=styles, css=css)
