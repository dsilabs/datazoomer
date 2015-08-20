
from zoom import system
import json
import uuid

head = """
<link rel="stylesheet" href="/static/dz/leaflet/leaflet.css" />
<!--[if lte IE 8]>
    <link rel="stylesheet" href="/static/dz/leaflet/leaflet.ie.css" />
<![endif]-->
<script src="/static/dz/leaflet/leaflet.js"></script>
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
        var bIcon = L.Icon.Default;
        %(icons)s
        var map = L.map('%(name)s').setView(%(center)s, %(zoom)s);
        L.tileLayer('<dz:protocol>://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
        %(additions)s
    </script>
"""

CANADA_LL = [55,-95]

class Icon(object):

    def __init__(self, name, icon_url, shadow_url=None):
        self.name = name
        self.icon_url = icon_url
        self.shadow_url = shadow_url and (", shadowUrl: '%s'" % shadow_url) or ''

    def render(self):
        name = self.name
        options = "{iconUrl: '%s' %s}" % (self.icon_url, self.shadow_url)
        return "var %(name)sIcon = new bIcon(%(options)s);" % locals()

    def __str__(self):
        return self.render()
    
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

    def __init__(self, center=CANADA_LL, zoom=3, markers=[], klass=None, icons=[], geojson=None, bounds=None):
        self.center = center
        self.zoom = zoom
        self.markers = markers
        self.klass = klass
        self.icons = icons
        self.geojson = geojson
        self.bounds = bounds

    def render(self):
        vis_name = uuid.uuid4().hex

        klass = 'class="%s"' % (self.klass or 'leaflet-map')

        system.head.add(head)
        system.css.add(css)

        a = []
        a.append(''.join(str(m) for m in self.markers))

        if self.geojson:
            geo_data = """
            var geojson_featureset = {};
            """.format(self.geojson)
            a.append(geo_data)
            code = """
            L.geoJson(geojson_featureset, {}).addTo(map);
            """
            a.append(code)

        if self.bounds:
            a.append('map.fitBounds({});'.format(self.bounds))

        b = ''.join(str(i) for i in self.icons)

        return tpl % dict(self.__dict__, additions=''.join(a), icons=b, name=vis_name, klass=klass)

    def __str__(self):
        return self.render()

