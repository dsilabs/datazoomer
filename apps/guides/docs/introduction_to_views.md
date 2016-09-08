
Views
====

Views are what determines how a DataZoomer app appears to the world.

After reading this guide, you will know:

* what a Dynamic View is
* what a Helper is

-- section break --

In DataZoomer, web requests are handled by a [[Dynamic Controller]] and a
[[Dynamic View]].  Typically, the Controller will be concerned with any requests that could potentially alter the state of the model or the system.  The View is responisble for compiling the response.

Dynamic View classes typically assemble content from a variety of sources including objects, files which contain HTML, css, javascript or any other kind of content, assembling these pieces into things to be sent to the browser.  To make this process easier and avoid duplicating commonly used code DataZoomer provides a wide variety of helpers that provide content for dates, numbers, user information, etc..  It's also easy to add helpers to your application as it
evolves.

