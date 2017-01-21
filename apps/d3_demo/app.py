"""
    d3 demo application
"""

from zoom import App

app = App()

app.menu = [
        ('scatter', 'Scatter', 'scatter'),
        ('calendar', 'Calendar', 'calendar'),
        ('brewer', 'ColorBrewer Palettes', 'brewer'),
        'Force',
        # ('cdn', 'via CDN', 'cdn'),
        ('tests', 'Various Visual Tests', 'tests'),
    ]
