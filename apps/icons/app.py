
import os
from zoom import *


class Icon(zoom.mvc.DynamicView):
    url = system.site.url


class IconList(zoom.mvc.DynamicView):

    @property
    def icons(self):
        def is_png(name):
            return name.endswith('.png')
        names = sorted(filter(is_png, os.listdir(self.path)))
        return component(*list(Icon(name=name) for name in names))

def app():
    path = os.path.join(system.root, 'www', 'static', 'dz', 'icons')
    icons = IconList(path=path)
    content = 'Icons available on this system.<br>\n{}'.format(icons)
    return page(content, title='Icons')
