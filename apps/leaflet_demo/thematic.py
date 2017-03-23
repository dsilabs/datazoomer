""" thematic """
from zoom import page
from zoom.mvc import View
from zoom.vis.map import ThematicMap


class MyView(View):
    """ default thematic map test view """

    def index(self):
        """ the default thematic map view """

        # create lookup for the layers
        ha_layer = dict(title="Health Authorities (geoJSON)", data='ha_2013.json', key="HA_NAME")

        # Thematic Map
        thematic = ThematicMap(
            layers=[ha_layer, ],  # TODO: support for url callback
            zoom=14,
            width="100%",
            height=700,
        )

        return page(thematic, title='Thematic Map')


view = MyView()
