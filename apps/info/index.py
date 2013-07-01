
import os 
from zoom import system, manager, page, markdown

def view():
    d = system.__dict__

    lib_path = system.lib_path
    instance_path = system.instance_path
    site_path = system.config.site_path
    theme_path = system.themes_path
    app_paths = manager.app_paths

    return page(markdown("""
Paths
----
<pre>
lib_path......: %(lib_path)s
instance_path.: %(instance_path)s
site_path.....: %(site_path)s
theme_path....: %(theme_path)s
app_path......: %(app_paths)s
</pre>

Context
----
<dz:status_info>
    """) % locals(), title='Overview')
    
    
