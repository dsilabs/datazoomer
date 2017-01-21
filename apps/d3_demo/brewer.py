"""
    d3 color brewer example
"""

import zoom


class MyView(zoom.View):
    def index(self):
        libs = [
            '/static/dz/d3/d3.v3.min.js',
            '/static/dz/d3/lib/colorbrewer/colorbrewer.js',
        ]
        styles = [
            "/static/dz/d3/lib/colorbrewer/colorbrewer.css"
        ]

        content = zoom.component(
            zoom.tools.load_content('color_brewer'),
            css=zoom.tools.load('color_brewer.css'),
            js=zoom.tools.load('color_brewer.js'),
            libs=libs,
            styles=styles,
        )

        return zoom.page(
            content,
            title='ColorBrewer Scales',
        )

view = MyView()
