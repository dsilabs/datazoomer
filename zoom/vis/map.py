"""map tools

feature support:
    map
        marker / pin
            popups
            icon
        tiles supported (base maps)
            attribution tag
        layer group / feature group (overlays)
            markers
                popups
                icon
        heat map
        popups
        control options (collapsable)

TODO:
    i. refactor to try and use __dict__ for string replacement of html
    i. support collections
    i. support "exceptions" lists automatically (+ ability to disable)
    i. consider support match/search or require the object passed in to support it
        collections for example, if a collection does not support it should we
    i. consider http://leaflet-extras.github.io/leaflet-providers/preview/
        for available tile sets
    i. rename set_tiles to basemap?

NOTES:
    BC Environment GIS Working Group has chosen a standard projection and datum for all spatial data stored in ARC/INFO.
    The projection is Albers Equal Area Conic, with parameters of :

    Central meridian: -126.0 (126:00:00 West longitude)
    First standard parallel: 50.0 (50:00:00 North latitude)
    Second standard parallel: 58.5 (58:30:00 North latitude)
    Latitude of projection origin: 45.0 (45:00:00 North latitude)
    False northing: 0.0
    False easting: 1000000.0 (one million metres)
    The datum is NAD83, based on the GRS80 ellipsoid.
"""
from os.path import isfile

import json
from zoom import id_for, system, load
from zoom.component import component
from zoom.tools import wrap_iterator


available_tilesets = {
    # (service, attribution)
    'DeLorme': ['<dz:protocol>://server.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}', 'Tiles &copy; Esri &mdash; Copyright: &copy;2012 DeLorme'],
    'Open Street Map': ['<dz:protocol>://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'],
    'Open Street Map BW': ['<dz:protocol>://{s}.tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'],
    'World Topographic': ['<dz:protocol>://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'],
    'Terrain Imagery': ['<dz:protocol>://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'],
    'Stamen Watercolor': ['http://{s}.tile.stamen.com/watercolor/{z}/{x}/{y}.png', 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>', ],
}

leaflet_script = ["/static/dz/leaflet/leaflet.js"]
leaflet_style = ["/static/dz/leaflet/leaflet.css"]
leaflet_head = """    <script src="/static/dz/leaflet/leaflet.js"></script>
    <link rel="stylesheet" href="/static/dz/leaflet/leaflet.css" />"""


def var_for(s):
    """return JavaScript variable name"""
    return id_for(s).replace('-', '_')


def tile_for(provider):
    """Lookup the given provider within available_tilesets"""
    return available_tilesets.get(provider, 'Open Street Map')


def valid_mark(mark):
    """given a mark, does it appear to be valid"""
    if hasattr(mark, 'll'):
        mark = mark.ll
    try:
        x, y = float(mark[0]), float(mark[1])
    except:
        return False
    return True


def leaflet_bind(e, addbind=None, popup=None):
    """return the javascript for a leaflet bind popup command"""
    popup = (popup is not None and popup or "<h2>%(link)s</h2><p>%(description)s</p>") % e
    popup = popup.replace('"', "'").replace('\n', '<br/>').replace('\r', '')
    return addbind is None and popup or '.bindPopup("%s")' % popup


class JS(object):
    """Base calss for rendering a given object in javascript"""
    _inline_ = "%s"
    _declare_ = 'var %s = %s;'
    name = property(lambda self: '%s_%s' % (self.__class__.__name__, id(self)))
    ref = property(lambda self: '%s' % self.name, doc="the reference to the object")

    def __init__(self):
        self.description = None

    def set_title(self, title):
        self.description = title

    title = property(lambda self: self.description and self.description or self.__doc__, fset=set_title, doc="title for an object, often displayed to the user")

    def inline(self):
        """declare the object "inline"""
        return self._inline_ % self

    def declare(self):
        """standard/full declaration"""
        return self._declare_ % (self.ref, self.inline())

    def render(self):
        return self.declare()

    def __str__(self):
        return self.render()


class Leaflet(JS):
    """A leaflet map object

    http://leafletjs.com/
    """
    centroid_bc = [55, -125]
    default_zoom = 5
    default_height = 550
    default_width = 600
    default_tiles = ['Open Street Map']
    default_css = """
        div#%(id)s {
            height: %(height)spx;
            width: %(width)spx;
            border: 1px solid grey;
            margin: 10px auto;
        }
        """
    scripts = leaflet_script
    styles = leaflet_style

    def __init__(
            self,
            centroid=centroid_bc,
            zoom=default_zoom,
            height=default_height,
            width=default_width,
            control=None
    ):
        self.centroid = centroid
        self.tiles = self.default_tiles
        self.zoom = zoom
        self.height = height
        self.width = width
        self.markers = []
        self.control = control or {'collapsed': False}
        self._overlays = []

    def __str__(self):
        return self.render()

    def render(self):
        return component(
            self.html(),
            css=self.css(),
            libs=self.scripts,
            styles=self.styles
        )

    def html(self):
        """ return the html for the object """
        id = self.ref
        icons, layers, overlays, tails, show_layers = {}, [], [], [], [var_for(self.tiles[0])]
        for l in self._overlays:
            show_layers.append(l.name)
            for i in l.layers:
                if hasattr(i, 'icon') and i.icon not in icons:
                    icons[str(i.icon)] = None
            layers.append(unicode(l))
            overlays.append("'%s': %s" % (l.title, l.name))
            if hasattr(l, 'tail'):
                tails.append(l.tail())
        map_props = "{center: %s, zoom: %s, layers: [%s]}" % (list(self.centroid), self.zoom, ','.join('%s' % l for l in show_layers))
        icons = '\n'.join(icons.keys())
        tiles = self.tilesets()
        layers = '\n'.join(layers)
        markers = self._markers()
        basemaps = self.basemaps()
        overlays = ', '.join(overlays)
        addtomap = self.addtomap()
        control = json.dumps(self.control)
        map_actions = hasattr(self, 'actions') and self.actions or ''
        map_actions = '%s%s' % (map_actions, '\n'.join(tails))
        html = """
            <div id="%(id)s"></div>
            <script>
                %(icons)s
                %(tiles)s
                %(layers)s

                var %(id)s_basemaps = {%(basemaps)s};
                var %(id)s_overlays = {%(overlays)s};

                var %(id)s = L.map('%(id)s', %(map_props)s);

                %(markers)s

                %(addtomap)s
                var %(id)s_control = L.control.layers(%(id)s_basemaps, %(id)s_overlays, %(control)s);
                %(id)s_control.addTo(%(id)s);
                %(map_actions)s
            </script>
            <div style="clear:both"></div>
        """
        return html % locals()

    def css(self, custom=''):
        """return the css for the map"""
        id = self.ref
        height = self.height
        width = self.width
        css = self.default_css % locals()
        return '%s%s' % (css, custom)

    def _markers(self):
        """return individual markers - not on a layer"""
        tpl = 'var marker%s = L.marker([%s, %s]).addTo(%s);'
        marks, addto = [], []
        icons = {}
        id = self.ref
        for i, mark in enumerate(filter(lambda m: valid_mark(m), self.markers)):
            if hasattr(mark, 'render'):
                marks.append(str(mark))
            if hasattr(mark, 'icon'):
                icons[str(mark.icon)] = None
            else:
                marks.append(tpl % (i, mark[0], mark[1], self.ref))
            if hasattr(mark, 'inline'):
                addto.append('%s.addTo(%s);' % (mark.name, id))
        content = '%s\n%s\n%s' % (
            '\n'.join(icons.keys()),
            '\n'.join(marks),
            '\n'.join(addto)
        )
        return content % locals()

    def addtomap(self):
        """return the js string for adding the default items to the map"""
        return '%s.addTo(%s);' % (var_for(self.tiles[0]), self.ref)

    def set_tiles(self, tiles):
        """ set the tiles """
        t = []
        for tile in tiles:
            if tile in available_tilesets.keys():
                t.append(tile)
        self.tiles = len(t) == 0 and self.default_tiles or t

    def tilesets(self):
        """return the js string for a tile set"""
        return '\n'.join(
            [
                'var %s = L.tileLayer("%s", {attribution: \'%s\' });' % (
                    var_for(provider),
                    tile_for(provider)[0],
                    tile_for(provider)[1]
                ) for provider in self.tiles
            ]
        )

    def basemaps(self):
        """return the js string for the base maps within the control"""
        return ','.join(['"%s": %s' % (provider, var_for(provider)) for provider in self.tiles])

    def overlays(self, overlays=[]):
        self._overlays = overlays


class Icon(JS):
    """leaflet icon"""
    _inline_ = "%s"
    _declare_ = """
    var bIcon = L.Icon.Default;
    var %(name)s = new bIcon(%(properties)s);
    """

    def __init__(self, **kwargs):
        JS.__init__(self)
        self.kwargs = kwargs

    def declare(self):
        name = self.ref
        properties = repr(self.kwargs)
        return self._declare_ % locals()


class AwesomeIcon(Icon):
    """Icon for an Awesome Marker

    https://github.com/lvoogdt/Leaflet.awesome-markers
    """

    scripts = ["/static/dz/leaflet/leaflet.awesome-markers.min.js"]
    styles = ["/static/dz/leaflet/leaflet.awesome-markers.css"]
    _declare_ = "var %(name)s = L.AwesomeMarkers.icon(%(properties)s);"

    def render(self):
        system.libs |= self.scripts
        system.styles |= self.styles
        return Icon.render(self)

    def declare(self):
        return Icon.declare(self)


class Marker(JS):
    """Custom Marker"""
    _declare_ = 'var %(var)s = L.marker(%(ll)s%(icon)s)%(popup)s;'
    _popup_ = '.bindPopup("%s")'

    def __init__(self, ll, text=None, icon=None):
        JS.__init__(self)
        self.ll = ll
        self.text = text
        self.icon = icon

    def declare(self):
        ll = list(self.ll)
        icon = self.icon is not None and ', {icon: %s}' % self.icon.name or ''
        text = self.text and self.text.replace('"', '\\"')
        var = self.ref
        popup = text and self._popup_ % text or ''
        return self._declare_ % locals()


class Circle(Marker):
    """Map circles"""
    _declare_ = 'var %(var)s = L.circle(%(ll)s, %(radius)s, %(options)s)%(popup)s;'

    def __init__(self, ll, radius_meters, options={}, text=None):
        JS.__init__(self)
        self.ll = list(ll)
        self.radius = radius_meters
        self.options = options
        self.text = text

    def declare(self):
        ll = list(self.ll)
        radius = self.radius
        options = json.dumps(self.options)
        text = self.text and self.text.replace('"', '\\"')
        var = self.ref
        popup = text and self._popup_ % text or ''
        return self._declare_ % locals()


class Polygon(Marker):
    """Map Polygon"""
    _declare_ = 'var %(var)s = L.polygon(%(ll)s)%(popup)s;'

    def __init__(self, ll, options={}, text=None):
        JS.__init__(self)
        self.ll = list(ll)
        self.options = options
        self.text = text

    def declare(self):
        ll = list(self.ll)
        options = json.dumps(self.options)
        text = self.text and self.text.replace('"', '\\"')
        var = self.ref
        popup = text and self._popup_ % text or ''
        return self._declare_ % locals()


class LayerGroup(JS):
    """Layer Group"""
    _inline_ = "L.layerGroup([%s])"

    def __init__(self, layers):
        JS.__init__(self)
        self.layers = layers

    def inline(self):
        c = (
            ', '.join(
                [hasattr(l, 'name') and (callable(l.name) and l.name or l.name) or str(l) for l in self.layers])
        ).replace(';', '')
        return self._inline_ % c

    def declare(self):
        depends = '\n'.join(str(i) for i in self.layers)
        return '%s\n%s' % (depends, JS.declare(self))


class HeatLayer(LayerGroup):
    """ Heat Map

        reference: http://www.patrick-wied.at/static/heatmapjs/
    """
    _inline_ = 'HeatmapOverlay({radius: 2, maxOpacity: 0.8, scaleRadius: true, useLocalExtrema: false})'
    _declare_ = 'var %(var)s = new %(inline)s;'
    _tail_ = '%(var)s.setData( {data: [%(pins_layergroup)s] });'
    _data_ = '{lat: %s, lng: %s, value: %s}'
    scripts = ["/static/dz/heatmap.js/heatmap.min.js", "/static/dz/heatmap.js/leaflet-heatmap.js"]

    def render(self):
        system.libs = system.libs | self.scripts
        return LayerGroup.render(self)

    def inline(self):
        return None

    def declare(self):
        var = self.ref
        inline = self._inline_
        return self._declare_ % locals()

    def tail(self):
        var = self.ref
        pins_layergroup = ', '.join([self._data_ % l for l in self.layers])
        return self._tail_ % locals()


# Handlers and map operations need access to the variable names (e.g. border and lookup)
class ThematicLayer(LayerGroup):
    """Thematic Layer"""
    _inline_ = 'L.geoJson(%s_border, %s)'
    _declare_ = """
    var %(var)s_border = %(geojson_boundary)s;

    %(handlers)s

    var %(var)s = %(inline)s;
    """
    def __init__(self, layers):
        self.key = 'KEY'
        LayerGroup.__init__(self, layers=layers)
        self.handlers = [
            """
                function onEachFeature%(key)s(feature, layer) {
                  if (feature.properties && '%(key)s' in feature.properties && feature.properties['%(key)s']) {
                    layer.bindPopup(feature.properties['%(key)s']);
                  }
                };""",
            """
            color = d3.scale.category10();
            function colorFeature%(key)s(feature) {
                if (feature.properties && '%(key)s' in feature.properties && feature.properties['%(key)s']) {
                  return {color: color(feature.properties['%(key)s']), weight: 1};
                }
              return {color: color(1), weight: 1};
            };
            """
        ]
        self.props = """{style: colorFeature%(key)s, onEachFeature: onEachFeature%(key)s}"""

    def render(self):
        system.libs = system.libs | ["/static/dz/d3/d3.min.js", ]
        return self.declare()

    def inline(self):
        return self._inline_ % (self.ref, self.props % dict(key=self.key))

    def declare(self):
        handlers = wrap_iterator(self.handlers)
        var = self.ref
        inline = self.inline()
        geojson_boundary = self.layers
        handlers = ''.join([handle % dict(key=self.key) for handle in handlers])
        return self._declare_ % locals()


class ThematicMap(Leaflet):
    """ Leaflet map with a thematic overlay """
    def __init__(self, layers=None, **kwargs):
        Leaflet.__init__(self, **kwargs)
        self.actions = ""

        layer_objects = []
        for layer in layers or []:
            if isinstance(layer, ThematicLayer):
                thematic_layer = layer
            else:
                geo = layer['data']
                thematic_layer = ThematicLayer(layers=isfile(geo) and load(geo) or geo)
                thematic_layer.description = layer['title']
                thematic_layer.key = layer.get('key', 'KEY')
            layer_objects.append(thematic_layer)

        layer_objects = filter(bool, layer_objects)
        if layer_objects:
            self.overlays(layer_objects)
            self.actions = self.actions + """var fg = L.featureGroup([%s]); %s.fitBounds(fg.getBounds());""" % (layer_objects[0].ref, self.ref)
