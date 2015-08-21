from zoom import App, system
app = App()

system.app.menu = [
        ('scatter', 'Scatter Plot', 'scatter'),
        ('calendar', 'Calendar', 'calendar'),
        ('brewer', 'ColorBrewer Palettes', 'brewer'),
        ('cdn', 'via CDN', 'cdn'),
        ('tests', 'Various Visual Tests', 'tests'),
    ]

