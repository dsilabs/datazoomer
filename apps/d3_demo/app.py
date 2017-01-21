"""
    d3 demo application
"""

from zoom import App

app = App()

app.menu = [
        ('scatter', 'Scatter', 'scatter'),
        ('calendar', 'Calendar', 'calendar'),
        ('brewer', 'ColorBrewer Palettes', 'brewer'),
        # ('cdn', 'via CDN', 'cdn'),
        ('tests', 'Various Visual Tests', 'tests'),
    ]
