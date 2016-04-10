"""
    render a guide
"""
import os

import zoom
from zoom import page
from zoom.mvc import View
from zoom import markdown, trim, load
from zoom.html import div, ul

from views import guide, generate_index

table_of_guides = \
    [
#        (
#            'Start Here',
#            [
#                'Introduction',
#                'Getting Started with DataZoomer',
#            ]
#        ),
#        (
#            'Models',
#            [
#                'Dynamic Record Basics',
#            ]
#        ),
#        (
#            'Views',
#            [
#                'Layouts and Rendering',
#                'Fields',
#            ]
#        ),
#        (
#            'Controllers',
#            [
#                'Dynamic Controller Overview',
#                'DataZoomer Routing',
#            ]
#        ),
#        (
#            'Tools and Utilities',
#            [
#                'Dynamic Controller Overview',
#                'DataZoomer Routing',
#            ]
#        ),
        (
            'Data Analysis',
            [
                'Data Visualization',
            ]
        ),
    ]


BREAKER = '-- section break --'

class MyView(View):

    def index(self, *a, **k):

        def load_document(name):
            filename = 'docs/{}.md'.format(name)
            feature, body = '', ''
            if os.path.exists(filename):
                body = load(filename)
                if BREAKER in body:
                    feature, body = body.split(BREAKER)
            return feature, body

        def format_message(m):
            return markdown(trim(m))

        messages = [
            """
            <div class="bg-warning">
            This document is under construction.
            </div>
            """,
            """
            <div class="bg-success">
            The DataZoomer data application platform is written by volunteers
            in various places.
            </div>
            """
        ]

        toc = generate_index(table_of_guides)

        feature, body = load_document('index')

        feature = markdown(feature.format(
            version=zoom.__version__,
        ))
        content = markdown(body.format(
            toc=toc,
            version=zoom.__version__,
        ))

        side_panel = ul(format_message(m) for m in messages)

        return guide(
            feature,
            side_panel,
            content,
        )

view = MyView()

