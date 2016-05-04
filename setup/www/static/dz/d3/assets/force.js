/*
 * adapted from d3 examples
 * https://d3js.org/
 */
$(function(){
    var nodes = {};

    // Compute the distinct nodes from the links.
    links.forEach(function(link) {
      link.source = nodes[link.source] || (nodes[link.source] = {name: link.source});
      link.target = nodes[link.target] || (nodes[link.target] = {name: link.target});
    });

    var w = $("div#visual").width(),
        h = $("div#visual").height(),
        r = 6,
        r2 = 20;

    var force = d3.layout.force()
        .nodes(d3.values(nodes))
        .links(links)
        .size([w, h])
        .linkDistance(80)
        .gravity(.2)
        .charge(-300)
        .on("tick", tick)
        .start();

    var svg = d3.select("#visual").append("svg:svg")
        .attr("overflow", "hidden")
        .attr("width", w)
        .attr("height", h);

    // Per-type markers, as they don't inherit styles.
    svg.append("svg:defs").selectAll("marker")
        .data(["direct", "retweet", "mention"])
      .enter().append("svg:marker")
        .attr("id", String)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", -1.5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
      .append("svg:path")
        .attr("d", "M0,-5L10,0L0,5");

    var path = svg.append("svg:g").selectAll("path")
        .data(force.links())
      .enter().append("svg:path")
        .attr("class", function(d) { return "link " + d.type; })
        .attr("marker-end", function(d) { return ((document.documentMode || 100) <= 11) ? "none" : "url(#" + d.type + ")"; });

    var circle = svg.append("svg:g").selectAll("circle")
        .data(force.nodes())
      .enter().append("svg:circle")
        .attr("r", r)
        .call(force.drag);

    var text = svg.append("svg:g").selectAll("g")
        .data(force.nodes())
      .enter().append("svg:g");

    // A copy of the text with a thick white stroke for legibility.
    text.append("svg:text")
        .attr("x", 8)
        .attr("y", ".31em")
        .attr("class", "shadow")
        .text(function(d) { return d.name; });

    text.append("svg:text")
        .attr("x", 8)
        .attr("y", ".31em")
        .text(function(d) { return d.name; });

    // Use elliptical arc path segments to doubly-encode directionality.
    function tick() {
      path.attr("d", function(d) {
        var dx = Math.max(r,Math.min(w-r,d.target.x - d.source.x)),
            dy = Math.max(r,Math.min(h-r,d.target.y - d.source.y)),
            dr = Math.sqrt(dx * dx + dy * dy);
        return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
      });

      circle.attr("transform", function(d) {
        return "translate(" + Math.max(r, Math.min(w-r,d.x)) + "," + Math.max(r, Math.min(h-r,d.y)) + ")";
      });

      text.attr("transform", function(d) {
        return "translate(" + Math.max(r, Math.min(w-r,d.x)) + "," + Math.max(r, Math.min(h-r,d.y)) + ")";
      });
    };
});


