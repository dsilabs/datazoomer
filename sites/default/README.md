
Zoom Site Specific Settings
=====
These options are specified on a per site basis.

site.ini
----
General settings for sites.  The system will first look in the site.ini file stored in the 
site folder corresponding to the domain name of the site being accessed.  If the value
being looked for is not found there then config.ini file in the 'default' site folder
is used.

settings.py
----
Specifies which apps are part of the system menu

menus.py
----
Specifies the main nav menu and other user defined menus.

content
----
The content folder is where uploaded files are stored.  The web 
user (www-data for example) needs to have write permission to this 
directory and this is the only folder where write access is required.

for example:

        > chgrp -R www-data content
        > chmod -R g+rw content
    
