
from zoom import system
import json
import uuid

head = """
<link rel="stylesheet" href="/static/leaflet/leaflet.css" />
<!--[if lte IE 8]>
    <link rel="stylesheet" href="/static/leaflet/leaflet.ie.css" />
<![endif]-->
<script src="/static/leaflet/leaflet.js"></script>
"""

css = """
div.leaflet-map {
    height: 250px;
    width: 420px;
    border: 1px solid grey;
}
.leaflet-container .leaflet-control-attribution { font-size: 9px; }
"""

tpl = """
    <div id="%(name)s" %(klass)s></div>
    <script>
        var map = L.map('%(name)s').setView(%(center)s, %(zoom)s);
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
        %(additions)s
    </script>
"""

CANADA_LL = [55,-95]

class Marker(object):

    def __init__(self, ll, text=None, icon=None):
        self.ll = ll
        self.text = text
        self.icon = icon

    def render(self):
        ll = list(self.ll)
        icon = self.icon is not None and ', {icon: %sIcon}' % self.icon or ''
        text = self.text and self.text.replace('"','\\"')
        if text:
            tpl = '\n        L.marker(%(ll)s%(icon)s).addTo(map).bindPopup("%(text)s");'
        else:
            tpl = '\n        L.marker(%(ll)s%(icon)s).addTo(map);'
        return tpl % locals()

    def __str__(self):
        return self.render()

class Map(object):

    def __init__(self, center=CANADA_LL, zoom=3, markers=[], klass=None):
        self.center = center
        self.zoom = zoom
        self.markers = markers
        self.klass = klass

    def render(self):
        vis_name = uuid.uuid4().hex

        klass = 'class="%s"' % (self.klass or 'leaflet-map')

        system.head.add(head)
        system.css.add(css)

        a = []
        a.append(''.join(str(m) for m in self.markers))
        return tpl % dict(self.__dict__, additions=''.join(a), name=vis_name, klass=klass)

    def __str__(self):
        return self.render()

