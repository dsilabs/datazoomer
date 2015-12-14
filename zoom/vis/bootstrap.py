""" bootstrap helpers

    reference: http://getbootstrap.com/css/

"""
from zoom import system, datetime
from time import strptime
from zoom.helpers import attribute_escape

def html_classed(c):
    """ return an html class string from a trusted source

    >>> html_classed('myclass')
    'myclass'
    >>> html_classed(['myclass'])
    'myclass'
    >>> html_classed(['myclass', 'active'])
    'myclass active'
    """
    return hasattr(c, '__iter__') and ' '.join(c) or c

def contain(content, classed = ''):
    c = classed and ' {}'.format(html_classed(classed)) or classed
    return """<div class="container-fluid{}">{}</div>""".format(c, content)

def glyphicon(icon, button_text='', button_context='default'):
    wrap = button_text and """<button type="button" class="btn btn-{}">{} {}</button>""".format(button_context, "{}", button_text) or "{}"
    return wrap.format("""<span class="glyphicon glyphicon-{}" aria-hidden="true"></span>""".format(icon))

def label(l, modifier=None):
    return modifier and """<span class="label label-{}">{}</span>""".format(modifier,l) or l

def badge(num=''):
    return """<span class="badge">{}</span>""".format(num)

def hero(content, rounded=True):
    content = rounded and content or """<div class="container">{}</div>""".format(content)
    return """
<div class="jumbotron">
  {}
</div>""".format(content)
jumbotron = hero

def listgroup(listing, as_list=True):
    if as_list:
        wrap = """<ul class="list-group">{}</ul>"""
        item = """<li class="list-group-item">{}</li>"""
        listing = ''.join(item.format(i) for i in listing)
    else:
        wrap = """<div class="list-group">{}</div>"""
        item = """<a href="{}" class="list-group-item">{}</a>"""
        listing = ''.join(item.format(i[0],i[1]) for i in listing)
    return wrap.format(listing)

def panel(content, countent_outside='', title='', footer='', context='default', heading=''):
    """ return a bootstrap panel

        content: panel body content
        countent_outside: panel content outside the body for seamless design
        title: title
        footer: footer
        context: bootstrap context state class
        heading: if you want a heading, but without the title

    """
    footer = footer and """<div class="panel-footer">{}</div>""".format(footer) or ""
    heading = heading and heading or ''

    return """
<div class="panel panel-{context}">
  <div class="panel-heading">
    <h3 class="panel-title">{title}</h3>
    {heading}
  </div>
  <div class="panel-body">
    {content}
  </div>
  {countent_outside}
  {footer}
</div>
""".format(**locals())

def date_filter_form(f,t):
    return """
<form class="form-inline pull-right nojs">
  <div class="form-group">
    <label for="DFROM">From</label>
    <input type="text" class="form-control input-sm" id="DFROM" name="DFROM" placeholder="From Date" value="%s">
  </div>
  <div class="form-group">
    <label for="DTO">To</label>
    <input type="text" class="form-control input-sm" id="DTO" name="DTO" placeholder="To Date" value="%s">
  </div>
  <button type="submit" class="btn btn-default btn-sm">Apply Filter</button>
</form>""" % (f,t)

class DateFilter(object):
    """ interface for an inline bootstrap date range selector """
    def __init__(self, data_min, data_max):
        self.min = data_min
        self.max = data_max

    def js(self):
        return """
        <script type="text/javascript">
            $(function() {
                var dmin = "%(dmin)s".split('-').map(function(d) { return parseInt(d); });
                var dmax = "%(dmax)s".split('-').map(function(d) { return parseInt(d); });
                var dfrom = "%(from_at)s".split('-').map(function(d) { return parseInt(d); });
                var dto = "%(to_at)s".split('-').map(function(d) { return parseInt(d); });
                var f = $("#DFROM").val();
                var t = $("#DTO").val();
                if (t) t = t.split('-').map(function(d) { return parseInt(d); })
                if (f) f = f.split('-').map(function(d) { return parseInt(d); })
                $( "#DFROM" ).datepicker( {
                  dateFormat: "d MM yy",
                  defaultDate: new Date(dfrom[0], dfrom[1] - 1, dfrom[2]),
                  changeMonth: true,
                  changeYear: true,
                  numberOfMonths: 1,
                  showOtherMonths: true,
                  selectOtherMonths: true,
                  showAnim: "slideDown",
                  showButtonPanel: true,
                  minDate: new Date(dmin[0], dmin[1] - 1, dmin[2]),
                  maxDate: new Date(dmax[0], dmax[1] - 1, dmax[2])
                }).focus(function( ) {
                    $('.ui-datepicker-close').click(function() {
                        var month = $("#ui-datepicker-div .ui-datepicker-month :selected").val();
                        var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
                        var day = $("#ui-datepicker-div .ui-datepicker-day :selected").val();
                        var selectedDate =  new Date(year, month, day);
                        $( "#DFROM" ).datepicker('setDate', selectedDate);
                    });
                });
                if (f) $( "#DFROM" ).datepicker('setDate', new Date(f[0], f[1] -1, f[2]));

                $( "#DTO" ).datepicker( {
                  dateFormat: "d MM yy",
                  defaultDate: new Date(dto[0], dto[1] - 1, dto[2]),
                  changeMonth: true,
                  changeYear: true,
                  numberOfMonths: 1,
                  showOtherMonths: true,
                  selectOtherMonths: true,
                  showAnim: "slideDown",
                  showButtonPanel: true,
                  minDate: new Date(dmin[0], dmin[1] - 1, dmin[2]),
                  maxDate: new Date(dmax[0], dmax[1] - 1, dmax[2])
                }).focus(function( ) {
                    $('.ui-datepicker-close').click(function() {
                        var month = $("#ui-datepicker-div .ui-datepicker-month :selected").val();
                        var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
                        var selectedDate =  new Date(year, month, 1);
                        $( "#DTO" ).datepicker('setDate', selectedDate);
                    });
                });
                if (t) $( "#DTO" ).datepicker('setDate', new Date(t[0], t[1] - 1, t[2]));
              });
        </script>"""

    def parse(self, DFROM=None, DTO=None):
        """ parse the form vars or use the min/max from the data """
        dt_from = DFROM and datetime.datetime(*strptime(DFROM, "%d %B %Y")[:3]).strftime('%Y-%m-%d') or self.min
        dt_to = DTO and datetime.datetime(*strptime(DTO, "%d %B %Y")[:3]).strftime('%Y-%m-%d') or self.max
        return (dt_from, dt_to)

    def at(self, DFROM, DTO):
        """ given DFROM and DTO setup the form """
        # parse the form vars or use the min/max from the data
        f,t = self.parse(DFROM, DTO)

        # handle js
        js = self.js() % ( dict(dmin=self.min, from_at=f, dmax=self.max, to_at=t) )
        system.tail.add(js)
        return date_filter_form(f,t)