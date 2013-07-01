
Zoom 
====
The python web platform that does less.

Zoom is a small application platform for building dynamic web sites quickly.


History
----
This library was originally Developed in 2004 as DataZoomer by Dynamic Solutions as
an internal solution for the quick prototyping and development of websites for data 
management, sharing and analysis for our clients.  It was used to drive a wide variety 
of web based solutions from e-commerce, to vertical applications, to complex reporting 
and data analysis systems.

Dynamic Solutions didn't intentionally set out to create another Python web framework. 
In 2010 we realized that many new frameworks had appeared since we started ours so we 
did a survey of many of the popular Python web frameworks to see if one of them
would do what we had been doing with ours, in the hopes that we could retire some
of our code and contribute to a shared project.

We really like the web.py framework and so decided to try to port our platform to run
on top of web.py and retire much of the DataZoomer library.  As much as we liked
web.py we found that at this point there was just not much that we would be able
to retire and much of our apps would require almost complete rewrites, so, for now
we have decided to put that move off.

Since then, web.py has influenced some of our thinking and we have adopted some of
the techniques and patterns we liked the most.

In 2012 we renamed our internal DataZoomer library to Zoom.  The Zoom library is 
found on github at https://github.com/hlainchb/python-zoom and the DataZoomer name 
is used to refer to our instance of the library which runs as a service at 
datazoomer.com and is used to power our commercial solutions.  DataZoomer is 
implemented using this Zoom library and other libraries developed by other open 
source development firms.

In 2013 we combined all of our Zoom modules and published them to the new githib 
location.


License
----
Zoom is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

Zoom is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

