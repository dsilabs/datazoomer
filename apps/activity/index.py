

from zoom import *

class ActivityView(View):
    
    def index(self):

        feed = db('select * from log where status="A" order by timestamp desc limit 100')

        tpl = '<div class=activity>%s</div><div class=meta>%s</div><br>' 
        result = ''.join(tpl % (a.message, how_long_ago(a.timestamp)) for a in feed)

        return page(markdown(result), title='Activity')

view = ActivityView()

