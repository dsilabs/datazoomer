

from zoom import *

def callback(method, timeout=5000):
    app_name = system.app.name
    js = """
        jQuery(function($){
          setInterval(function(){
            $.get('/%(app_name)s/%(method)s', function( content ){
              $('#%(method)s').html( content );
            });
          }, %(timeout)s);
        });
    """ % locals()
    return js

class ActivityView(View):
    
    def index(self):
        js = callback('activity')
        save_logging = system.logging
        content = '<div id="activity">%s</div>' % self.activity()
        system.logging = save_logging
        return page(content, title='Activity', js=js)

    def activity(self):
        feed = db('select * from log where status="A" order by timestamp desc limit 100')
        tpl = '<div class="activity"><div class="message">%s</div><div class="meta">%s</div></div>' 
        result = ''.join(tpl % (a.message.decode('utf8'), how_long_ago(a.timestamp)) for a in feed)
        system.logging = False
        return result or 'no activity'


view = ActivityView()

