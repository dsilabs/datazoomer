
Getting Started
====

This guide covers getting up and running with DataZoomer.

After reading this guide, you will know:

* How to install DataZoomer, create a new DataZoomer app, and connect your app
  to a database.
* The general layout of a DataZoomer application

-- section break --

<ul>
  <li>
    <div class="infobox bg-warning">
        This document is under construction.
    </div>
  </li>
  <li>
     <div class="infobox bg-success">
     The <a href="http://www.datazoomer.com">DataZoomer</a> platform is developed and
     maintained by <a href="https://www.dynamic-solutions.com">Dynamic
     Solutions Inc.</a>.
     </div>
  </li>
</ul>

-- section break --

#Installation

DataZoomer can run in a wide variety of environments and configurations.  The
following steps are meant to serve only as a guideline.  Each of the steps may
need to be slightly different depending on the environment and configuration
being implemented.

DataView is capable of running multiple sites on a single instance.  Each site
can have it's own theme, apps, database and other compontents, or they can share
them.  It's up to you.  In the steps that follow we'll cover creating a basic
installation by creating an instance with one site and one app running on that
site.  We'll assume you want to run your DataZoomer in a directory called
~/work on a Linux machine.

Requirements:
    This example requires that you already have a MySQL database server running
    and that you have sufficicent admin credentials so you can create a new
    database.

1. clone DataZoomer into a working folder

    <code>
    $ mkdir -p ~/work/source/libs && cd ~/work/source/libs<br>
    $ git@github.com:dsilabs/datazoomer.git
    </code>

1. create a MySQL database for your DataZoomer site

    <code>
    pushd ~/work/source/libs/datazoomer/setup/database<br>
    mysql -u {{username}} -p{{password}} zoomdata < setup_mysql.sql<br>
    popd<br>
    </code>

    where {{username}} and {{password}} are the admin credentials for your
    MySQL database server.

1. create a directory for DataZoomer to run.  Create subfolders for the sites,
apps, themes and a <code>www</code> for the main instance script.

    <code>
    $ mkdir ~/work/web && cd ~/work/web<br>
    $ mkdir -p sites/default<br>
    $ mkdir apps<br>
    $ mkdir themes<br>
    $ mkdir www<br>
    </code>

1. install the default theme

    <code>
    cd ~/work/web/themes && ln -s ~/work/source/libs/datazoomer/themes/default
    </code>

1. copy the default configuration file to the default site folder

    <code>
    cp ~/work/source/libs/datazoomer/sites/default/site.ini ~/work/web/sites/default/site.ini
    </code>

1. install the main DataZoomer instance script in the www directory and make it
executable

    <code>
    cd ~/work/web/www && ln -s ~/work/source/libs/datazoomer/setup/www/index.py
    chmod +x ~/work/source/libs/datazoomer/setup/www/index.py
    </code>

