"""
    render a guide
"""
import os

import zoom
from zoom import page
from zoom.mvc import View
from zoom import markdown, trim, load
from zoom.html import div, ul

from views import guide, generate_index, doc

table_of_guides = \
    [
        (
            'Start Here',
            [
                'Introduction',
                #'Getting Started with DataZoomer',
            ]
        ),
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


class MyView(View):

    def index(self, *a, **k):

        toc = generate_index(table_of_guides)
        args = dict(
            version = zoom.__version__,
            toc = toc,
        )

        return doc('index', args)


    def introduction(self):
        zoom.system.app.menu.append('Introduction')
        args = dict(
            side_panel='side panel'
        )
        return doc('introduction', args)

view = MyView()

