"""
    d3 demo application
"""

from zoom import App

app = App()

app.menu = [
    'Scatter',
    'Calendar',
    'Force',
    'Treemap',
    ('brewer', 'ColorBrewer Palettes', 'brewer'),
    ('tests', 'Various Visual Tests', 'tests'),
]
