from zoom import *
from zoom.response import TextResponse
from zoom.vis.d3 import *

class JSONResponse(TextResponse):
    def __init__(self, content):
        TextResponse.__init__(self,content)
        self.headers['Content-type'] = 'application/json;charset=utf-8'


css = tools.load('style.css')

calendar_wrapper = tools.load_content('calendar_wrapper')

calendar_eg = """<p>Example usage:</p>
  <pre>

    cal = d3.charts.calendar()
            .margin({top: 20, right: 40, bottom: 20, left: 70})
            .height(256)
            .key(function(d) {return d.key;})
            .x(function(d) {return d.hits;})
            .label(d3.format(",.2g"))
            .color(d3.scale.quantize().range(d3.range(9).map(function(d) { return "q" + d + "-9"; })))
            .palette("Greens");

    d3.select("#chart")
          .datum(data)
          .call(cal);
  </pre>
"""
