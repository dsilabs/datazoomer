
import os
from zoom import *

css = """
<style>

ul.icon_list { 
    list-style-type: none; 
    margin: 0; 
    padding: 0; 
}

ul.icon_list li {
    list-style-type: none;
    margin: 5px 5px 5px 0;
    padding: 1px;
    float: left;
    width: 90px;
    height: 90px;
    text-align: center;
}

img.icon {
    border: 0;
    height: 50px;
    margin: 10px;
    }

div.icon-standardizer {
    height: 70px;
    width: 90px;
    text-align: center;
}

.ui-state-default, .ui-widget-content .ui-state-default, .ui-widget-header .ui-state-default {
    border: 0;
    background: none;
    font-size: 0.8em;
    font-weight: normal;
}

</style>
"""

list_tpl = """

<ul class="icon_list">
%s
</ul>
<div style="clear:both"></div>

"""

item_tpl = """
    <li class="ui-state-default">
        <div class="icon-standardizer">
            <img class="icon buggy_ie_icon" src="%(url)s/static/dz/icons/%(name)s">
        </div>
        %(name)s
    </li>
"""

js = """
    $(function(){
        $('.icon_list').sortable();
        $('.icon_list').disableSelection();
    });
"""


def generate_icon_list(icon_dir):
    url = system.site.url
    icons = [dict(url=url, name=filename[0:-4]) for filename in sorted(os.listdir(icon_dir)) if filename.endswith('.png')]
    return list_tpl % ''.join(item_tpl % icon for icon in icons)

def app():
    path = os.path.join(system.root,'www','static','icons')
    t = 'Icons available on this system.\n%s' % generate_icon_list(path)
    return page(t, title='Icons', js=js, css=css)
    
