
from zoom import * 
from zoom.vis.leaflet import Marker, Map

BC_LL = [55,-125]
CANADA_LL = [55,-95]

VANCOUVER_MARKER = Marker([49.25, -123.1],'Vancouver')
EDMONTON_MARKER = Marker([53.53, -113.5],'Edmonton')
CALGARY_MARKER = Marker([51.5, -114],'Calgary')
REGINA_MARKER = Marker([50.5, -104.6],'Regina')
WINNIPEG_MARKER = Marker([49.9, -97.1],'Winnipeg')
TORONTO_MARKER = Marker([43.7, -79.4],'Toronto')
OTTAWA_MARKER = Marker([45.4, -75.7],'Ottawa')

def view():

    m1 = Map(center=CANADA_LL, zoom=3, 
            markers=[
                VANCOUVER_MARKER,
                EDMONTON_MARKER,
                CALGARY_MARKER,
                REGINA_MARKER,
                WINNIPEG_MARKER,
                TORONTO_MARKER,
                OTTAWA_MARKER,
                ])

    m2 = Map(center=BC_LL, zoom=4, 
            markers=[
                VANCOUVER_MARKER,
                ])

    content = markdown("""
Map of Canada
----
%s

Map of BC
----
%s
    """) % (m1.render(), m2.render())

    return page(content, title='Leaflet Demo', css='.leaflet-map { margin-bottom: 10px; }')


