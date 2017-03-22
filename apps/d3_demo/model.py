from views import *

from random import randint, uniform
from faker import Faker

""" fake data """
XRANGE = randint(1000,10000)
fake = Faker()

# metrics
ints = lambda: randint(10,100)
floats = lambda: uniform(1,100)
dollars = lambda: round(uniform(1,1000),2)

# dimensions
_d = [fake.safe_color_name() for i in range(11)]
colors = lambda: _d[randint(0,10)]
_c = [fake.country() for i in range(15)]
country = lambda: _c[randint(0,14)]

# dates
years = range(1990, 2015)
def seq_dates(obs=XRANGE):
    d = [fake.date_time_this_decade() for i in range(obs)]
    d.sort()
    return d
def seq_times(obs=XRANGE):
    t = [fake.date_time_this_month() for i in range(obs)]
    t.sort()
    return t

def get_scatter_data():
    return {
        'title': 'd3.js Scatter Demo',
        'description': tools.load_content('scatter_description'),
        'labels': {
            'income': "income per capita, inflation-adjusted (dollars)",
            'lifeExpectancy': "life expectancy (years)",
            'population': "population (total)",
            'region': "geographic region",
            'name': "country"
        },
        'data': json.loads(tools.load('nations.json')),
    }



system_data = {
    'title': '{} {}'.format(system.config.get('site','name','Site'), 'System Log'),
    'description': "A visual view of the system log",
    'labels': {'value': 'Number of hits on the site'},
    'data': [dict(date=a.strftime('%Y-%m-%d'), value=b) for a,b in system.db("select date(timestamp), count(*) as hits from log group by 1;")],
}

def data_list_generator(obs=1000, metrics=3, dims=2):
    obs=int(obs)
    metrics = [ [ints, floats, dollars][randint(0,2)] for i in range(int(metrics)) ]
    dims = [ [colors, country][randint(0,1)] for i in range(int(dims)) ]

    labels = dict([(fake.word(), fake.sentence(nb_words=3, variable_nb_words=True)) for i in range(len(metrics)+len(dims))])
    data = []
    for i, date in enumerate(seq_dates(obs)):
        date = [("date", date.strftime("%Y-%m-%d"))]
        v = [("value",metrics[0]())]
        m = [(a,b()) for a,b in zip(labels, metrics+dims)]
        data.append(dict(date+v+m))
    labels['value'] = 'some value'
    metadata = {
        'title': fake.catch_phrase(),
        'description': "".join(fake.paragraphs(nb=3)),
        'labels': labels,
        'data': data
    }
    return metadata

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


def get_calendar_data(obs, metrics, dims):
    """ return calendar of events (fake data) """
    metadata = data_list_generator(obs=obs, metrics=metrics, dims=dims)
    metadata['description'] = "{}{}".format(metadata['description'], calendar_eg)
    return metadata


def get_treemap_data(obs):
    """ return system log data for the treemap view """
    return {
        'title': '{} {}'.format(system.config.get('site', 'name', 'Site'), 'System Log'),
        'description': "A visual view of the system log",
        'labels': {'app': 'Application Name', 'route': 'Application Route', 'hit': 'Application Hits', 'elapsed': 'Elapsed Time (ms)'},
        'data': list(system.db("select app, route, 1 as hit, elapsed from log limit {}".format(obs)))
    }
