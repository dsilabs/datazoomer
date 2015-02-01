from zoom import *
from zoom.vis.map import Leaflet as Map
from zoom.vis.map import *
from random import randrange, uniform

BC_LL = [55,-125]
CANADA_LL = [55,-95]

# custom icon
orange = Icon(iconUrl = '/static/dz/leaflet/images/marker-icon.orange.png', iconRetinaUrl = '/static/dz/leaflet/images/marker-icon-2x.orange.png')

# we will use awesome icons for colors
blue = AwesomeIcon(icon='map-marker', markerColor='blue', iconColor='white')
green = AwesomeIcon(icon='map-marker', markerColor='green', iconColor='white')
link = AwesomeIcon(icon='link', markerColor='red', iconColor='white')
plane = AwesomeIcon(icon='plane',markerColor='blue', iconColor='black')

# examples of markers
VANCOUVER_MARKER = Marker([49.25, -123.1], 'Vancouver', link)
EDMONTON_MARKER = Marker([53.53, -113.5],'Edmonton', link)
CALGARY_MARKER = Marker([51.05, -114.06],'Calgary', link)
REGINA_MARKER = Marker([50.5, -104.6],'Regina', link)
WINNIPEG_MARKER = Marker([49.9, -97.1],'Winnipeg', link)
TORONTO_MARKER = Marker([43.7, -79.4],'Toronto', link)
OTTAWA_MARKER = Marker([45.4, -75.7],'Ottawa', link)

def generate_pins(around=BC_LL, dist=2.1, num=10):
    """return a random sample of pins"""
    class adict(dict):
        def __getattr__(self, attr):
            return self.get(attr)
        __setattr__= dict.__setitem__
        __delattr__= dict.__delitem__

    for i in range(num):
        yield adict(latitude=uniform(around[0]-dist,around[0]+dist), longitude=uniform(around[1]-dist,around[1]+dist))

# example pin collections
victoria = [48.4222, -123.3657]
poly_bbox = [[50.2814,-123.9436], [50.2814,-122.1391], [49.5092, -122.1391], [49.5092, -123.9436]]
cities = [VANCOUVER_MARKER, EDMONTON_MARKER, CALGARY_MARKER,
            REGINA_MARKER, WINNIPEG_MARKER, TORONTO_MARKER, OTTAWA_MARKER]
bc_places = [(p.latitude,p.longitude) for p in generate_pins()]
historical_locations = [(p.latitude,p.longitude) for p in generate_pins()]

class MyView(View):

    def index(sefl):
        """test the vis\map module of datazoomer"""
        # basic map and set a tile set
        vicmap = Map(centroid=[48.420561, -123.359308], zoom=14, height=300, width=900)
        vicmap.set_tiles(['Stamen Watercolor'])

        # map, just given pins (not markers)
        simple = Map(zoom=4, height=100, width=900)
        simple.markers = bc_places

        # Awesome Markers
        iconmap = Map(zoom=4, height=200, width=900)
        iconmap.markers = [Marker(pin, 'awesome popup', i%2 and link or plane) for i,pin in enumerate(bc_places)]
        iconmap.control = {'collapsed': True, 'position': 'bottomleft'}

        # layers
        layermap = Map(zoom=4, height=200, width=900)
        layer1 = LayerGroup(layers=[Marker(pin, 'popup', blue) for pin in bc_places])
        layer1.description="My Funky Pins"
        layer2 = LayerGroup(layers=[Marker(pin, 'popup', green) for pin in historical_locations])
        layer2.title = "Get it right <b><u>hi</u></b>"
        canlayer = LayerGroup(layers=cities)
        canlayer.title = "Canadain Cities"
        layermap.set_tiles(['Open Street Map','Stamen Watercolor'])
        layermap.overlays([layer1, layer2, canlayer])
        layermap.control = {'collapsed': True}

        # Heat Map
        heat = Map(zoom=3, height=200, width=900)
        heatlayer = HeatLayer(layers=[(pin[0],pin[1],randrange(1000,1000004)) for pin in bc_places])
        heatlayer.description = "Population Numbers"
        heat.set_tiles(['Stamen Watercolor', 'DeLorme', 'World Topographic'])
        heat.overlays([heatlayer])
        heat.control = {'collapsed': True}
        circle = Circle(victoria, 55000, {'color': 'red', 'fillColor': '#f03', 'fillOpacity': 0.75},
            text='<a href="http://en.wikipedia.org/wiki/Victoria,_British_Columbia">Victoria, BC</a>'
          )
        poly = Polygon(poly_bbox, text="Garibaldi Provincial Park area")
        polylayer = LayerGroup(layers=[circle, poly])
        polylayer.description = "Example poly shapes"
        heat.overlays([heatlayer, polylayer])

        # Thematic Map
        thematic = Map(zoom=14, height=200, width=900)
        dr_layer = ThematicLayer(layers=load('ha_2013.json'))
        dr_layer.handlers = load('thematic_onfeature.js')
        dr_layer.props = """{style: colorFeature, onEachFeature: onEachFeature}"""
        dr_layer.description = "Health Authorities (geoJSON)"
        thematic.overlays([dr_layer])
        thematic.actions = """var fg = L.featureGroup([%s]); %s.fitBounds(fg.getBounds());""" % (dr_layer.ref,thematic.ref)

        content = markdown("""
basic with custom tile set
----
%s

simple markers (defaults)
----
%s

custom markers (incl. awesome markers, marker properties)
----
%s

layers (multiple layers)
----
%s

heat map and polygon layers (selectable heat map layer)
----
%s

thematic map
----
%s
""" ) % (vicmap, simple, iconmap, layermap, heat, thematic)

        return page(content, title='a Leaflet Demo')

view = MyView()
