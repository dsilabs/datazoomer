// Extend
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
String.prototype.endswith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};
String.prototype.name_for = function() {
    return this.replace(/_/g, ' ').capitalize();
};
String.prototype.plural = function(cnt) {
    if ( Math.abs(cnt) ==1 ) { return this.slice(); }
    if ( this.endswith('y') ) { return this.slice(0,-1) + 'ies'; }
    return this+'s';
}

Number.prototype.format = function(n, x) {
    // format the given Number() with "n" decimals and a comma every "x" places
    // this will round
    var re = '\\d(?=(\\d{' + (x || 3) + '})+' + (n > 0 ? '\\.' : '$') + ')';
    return this.toFixed(Math.max(0, ~~n)).replace(new RegExp(re, 'g'), '$&,');
};

// Create a namespace for general use
dz = {}

dz.uniques = function(value, index, self) {
    return self.indexOf(value) === index;
}
dz.getKey = function(obj, value) {
  for (var key in obj) {
    if( obj.hasOwnProperty(key) && obj[key]===value ) {
      return key;
    }
  }
}
dz.range = function(start, stop) {
    var arr = [],
        c = stop - start + 1;
    while ( c-- ) {
        arr[c] = stop--;
    }
    return arr;
}
dz.flattenNest = function(data) {
    // flatten the "values" from a d3.nest() data set
    flat = data.map(function(d) {
        var t = {key: d.key};
        Object.keys(d.values).forEach(function(j) { t[j] = d.values[j]; });
        return t;
    });
    return flat;
}

dz.seedLabels = function(aggData, data) {
    // check aggData for new keys and add them to data.labels
    if (aggData.length<=0 || !(data.labels)) { return false; }
    Object.keys(aggData[0]).forEach(
        function(k) {
            if (!(k in data.labels)) {
                data.labels[k] = k.name_for();
            }
        }
    );
}

// get scale options
dz.scaleChoices = function() {
    var t = [];
    for (var s in d3.scale) { t.push(s); }
    return t
}
// boxplot
dz.boxplot = function(d, accessor) {
    var t = d.map(accessor);
    t.sort(d3.ascending);

    var q1 = d3.quantile(t,.25),
        q3 = d3.quantile(t,.75),
        iqr = q3 - q1,
        k = 1.5,
        lw = q1 - (k * iqr),
        uw = q3 + (k * iqr);
    return {
        min: d3.min(d, accessor),
        lw: t.filter(function(d) {return d>=lw;})[0],
        q1: q1,
        q2: d3.median(d, accessor),
        median: d3.median(d, accessor),
        q3: q3,
        uw: t.filter(function(d) {return d<=uw;}).reverse()[0],
        max: d3.max(d, accessor)
    };
}

// Create a d3 charts namespace
if (typeof d3 === "undefined") { d3={}; }
d3.charts = { version: "0.1" };

d3.charts.scatter =
    function() {
        /* A scatter plot chart

        i. reusable
        i. responsive grammar
        i. x vs. y vs. z vs. color vs. size
        i. maintain object constancy
        i. aggregate lines (median, mean, ...)
        i. on hover (grey out everything else - create layers)
        i. change scales (log, exp, linear)


        TODO:
            i. add test app to ensure enter/update/exit of grammar components (remove, just svg?)
            i. add test app data generator
            i. enhance zaxis to support more than just integers (or convert other things to ints)
            i. override dynamic scale choices
            i. IQR axis labels
            i. summarize panel/section
            i. axis rugs
            i. Show values on hover
            i. add/remove grammar as we resize
            i. z-axis selector input box (e.e. select a year)

        */

        var margin = {top: 40, right: 30, bottom: 41, left: 40},
            width = 960 - margin.right,
            height = 500 - margin.top - margin.bottom,
            ratio = 2.15,   // ratio used for resize function
            xScale = d3.scale.log().range([0, width]),
            yScale = d3.scale.linear().range([height, 0]),
            zScale = d3.scale.linear().clamp(true),
            radiusScale = d3.scale.sqrt().range([0, 40]),
            radiusFormat = d3.format("0,.2f"),
            colorScale = d3.scale.category10().range(d3.scale.category10().range().reverse()),
            xAxis = d3.svg.axis().orient("bottom").scale(xScale).ticks(12, d3.format(",d")),
            xiqrAxis = d3.svg.axis().orient("top").scale(xScale).innerTickSize(3).outerTickSize(0),
            yAxis = d3.svg.axis().scale(yScale).orient("left"),
            yiqrAxis = d3.svg.axis().orient("right").scale(yScale).innerTickSize(3).outerTickSize(0),
            xZoom = undefined, yZoom = undefined,
            summary = {},
            axis_buffer = 0.12
            scale_choices = dz.scaleChoices(),
            agg_choices = ['max', 'mean', 'median', 'min'],
            metadata = {'title': 'Scatter Demo'},
            disableResize = false,
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-6, 0])
                .html(function(d) {
                    return "<strong>" + key(d) + "</strong>" + "<ul>" +
                        "<li>" + getLabel(x) + ":" + x(d) + "</li>" +
                        "<li>" + getLabel(y) + ":" + y(d) + "</li>" +
                        "<li>" + getLabel(radius) + ":" + radius(d) + "</li>" +
                        "<li>" + getLabel(color) + ":" + color(d) + "</li>" +
                        "</ul>"
                    ;
                });

        // Various accessors that specify the four dimensions of data to visualize.
        function x(d) { return d.x; }
        function y(d) { return d.y; }
        function z(d) { return d[0]; }
        function atZ(d) { return d[1]; }
        function radius(d) { return d.radius; }
        function color(d) { return d.color; }
        function key(d) { return d.name; }
        function getLabel(fn, dir) {
            var l = fn(metadata.labels);
            dir = typeof dir !== 'undefined' ? " " + dir : '';
            l = typeof l !== 'undefined' ? l + dir : undefined;
            return l;
        }

        function my(selection) {
          selection.each(function(chartdata, i) {
            metadata.title = chartdata.title || metadata.title;
            metadata.description = chartdata.description || '';
            metadata.labels = chartdata.labels || {x:'x-axis', y:'y-axis', radius:'radius', color:'color', key: 'name'};
            data = chartdata.data || chartdata;
            // TODO: investigate the chart being responsive (add/remove graph grammar depending on size)
            //console.log(parseInt(d3.select(this).style("width")));
            summarize(data);

            // Set the domains and scales based on the data
            xScale.domain([summary.default_minx, summary.maxx]).nice();
            yScale.domain([summary.default_miny, summary.maxy]).nice();
            zScale.domain([summary.minz, summary.maxz]);
            radiusScale.domain([summary.minr, summary.maxr]);

            // Create the SVG container and set the origin.
            var svg = d3.select(this).selectAll("svg").data([data]);
            var cont = svg.enter().append("svg").append("g");
            svg.call(tip);
            svg.attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom);
            svg.select("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            // Add the year label; the value is set on transition.
            // Put the label and overlay first so they are "behind" axis etc
            var label = cont.append("text")
                .attr("class", "year label")
                .attr("text-anchor", "end")
                .text(summary.minz);
            svg.select("svg g text.year.label")
                .attr("y", height - 24)
                .attr("x", width);

            // redo with a similar pattern to dot... (see adding the title after)
            var summaries = cont.append("g").attr("class", "summary");
            summaries.append("g").attr("class", "x summary").each(function() {
                d3.select(this).append("text").attr("class", "x summary label");
                d3.select(this).append("line").attr("class", "x summary");
            });
            summaries.append("g").attr("class", "y summary").each(function() {
                d3.select(this).append("text")
                    .attr("class", "y summary label")
                    .attr("data-jq-dropdown", "#jq-dropdown-agg")
                    ;
                d3.select(this).append("line").attr("class", "y summary");
            });
            var summary_lines = svg.select("svg g").selectAll("g.summary").data([{'hi':1}]);

            // Add legends
            cont.append("g").attr("class", "legends").append("g").attr("class", "circle legend");
            d3.select("g.legends g.circle.legend")
              .datum([{value: summary.maxr*.5}, {value: summary.maxr}])
                .call(d3.charts.circleLegend().title(getLabel(radius)).label(radiusFormat));

            var overlay = undefined;
            addZOverlay();  // enter and update of the z overlay

            // Add the IQR axis
            cont.append("g").attr("class", "xiqr axis");
            svg.select("svg g g.xiqr.axis")
                .attr("transform", "translate(0," + (height) + ")")
                .call(xiqrAxis);
            // Add the x-axis.
            cont.append("g").attr("class", "x axis");
            svg.select("svg g g.x.axis")
                .attr("transform", "translate(0," + height + ")")
                .call(xAxis);

            // Add the IQR axis
            cont.append("g").attr("class", "yiqr axis");
            svg.select("svg g g.yiqr.axis").call(yiqrAxis);
            // Add the y-axis.
            cont.append("g").attr("class", "y axis");   //enter
            svg.select("svg g g.y.axis").call(yAxis);   //update

            // Add an x-axis label.
            cont.append("text")
                .attr("class", "x label")
                .attr("text-anchor", "end")
                .attr("x", width)
                .on("click", function() { toggleIn("#x_axis_description", "down"); });
            svg.select("svg > g > text.x.label")
                .attr("x", width)
                .attr("y", height + 36)
                .text( getLabel(x, '↑') )
                .call(function() { addAxisPopup("#x_axis_description"); });

            // Add a y-axis label.
            cont.append("text")
                .attr("class", "y label")
                .attr("text-anchor", "end")
                .attr("y", -36)
                .attr("dy", ".75em")
                .attr("transform", "rotate(-90)")
                .on("click", function() { toggleIn("#y_axis_description", "left"); });
            svg.select("svg > g > text.y.label")
                .text( getLabel(y, '↓') )
                .call(function() { addAxisPopup("#y_axis_description"); });

            // Add xy axis overlays to bind events to (vs. the tick/line paths)
            addAxisOverlay('.x.axis')
            addAxisOverlay('.y.axis')

            cont.append("text").attr("class", "title");
            svg.select("svg g text.title")
              .call(addTitle);

            // A bisector since many nation's data is sparsely-defined.
            var bisect = d3.bisector(function(d) { return d[0]; });

            // Add a dot per nation. Initialize the data and set the colors.
            cont.append("g").attr("class", "dots");
            var dot = svg.select("svg g g.dots")
                .selectAll(".dot")
                  .data(interpolateData(summary.minz), key);
            dot.enter().append("circle")
                  .attr("class", "dot")
                .style("fill", function(d) { return colorScale(color(d)); })
                  .on('mouseover', function(d) {
                    tip.show(d);
                    d3.select(this).classed("active", true);
                  })
                  .on('mouseout', function(d) {tip.hide(d); d3.select(this).classed("active", false);})
                  .call(position)
                  .sort(order);
            displayYear();   // update the dots once the interaction is done

            // Add a title. - changed to d3.tooltip
            //dot.append("title")
            //    .text(function(d) { return d.name; });

            // Start a transition that interpolates the data based on year.
            cont.transition()
              .duration(30000)
              .ease("linear")
              .tween("year", tweenYear)
              .each("end", enableInteraction);

            //addScaleMenu({'id': "jq-dropdown-ys", 'choices': scale_choices, 'align': 'left'});
            //addScaleMenu({'id': "jq-dropdown-xs", 'choices': scale_choices, 'align': 'right'});
            addScaleMenu({'id': "jq-dropdown-agg", 'choices': agg_choices, 'active': 'median', 'callback': displayYear});

            // support responsive by default
            if (!disableResize) { d3.select(window).on('resize', resizeContainer); }

            // Summarize the data
            function summarize(data) {
                summary.minx = d3.min(data, function(d) {return d3.min(x(d), atZ);});
                summary.maxx = d3.max(data, function(d) {return d3.max(x(d), atZ);});

                summary.miny = d3.min(data, function(d) {return d3.min(y(d), atZ);});
                summary.maxy = d3.max(data, function(d) {return d3.max(y(d), atZ);});

                summary.minz = d3.min(data, function(d) {return d3.min(x(d), z);});
                summary.maxz = d3.max(data, function(d) {return d3.max(y(d), z);});

                summary.minr = d3.min(data, function(d) {return d3.min(radius(d), atZ);});
                summary.maxr = d3.max(data, function(d) {return d3.max(radius(d), atZ);});

                summary.default_minx = ('base' in d3.scale.log() && 'base' in xScale) ? 1 : 0;
                summary.default_miny = ('base' in d3.scale.log() && 'base' in yScale) ? 1 : 0;
                summary.default_minz = ('base' in d3.scale.log() && 'base' in zScale) ? 1 : 0;
                //console.log(summary);
            }

            // Toggle the axis scale between 0 (or close to zero) and the data domain minimum (e.g. zoom)
            function toggleScale() {
                var isY = d3.select(this).classed('y axis');
                var sel = isY ? ".y.axis" : ".x.axis";
                var scale = isY ? yScale : xScale;
                var tmax = isY ? summary.maxy : summary.maxx;
                var tmin = isY ? (scale.domain()[0]==summary.default_miny ? summary.miny : summary.default_miny) : (scale.domain()[0]==summary.default_minx ? summary.minx : summary.default_minx);
                // Cancel the current transition, if any.
                cont.transition()
                    .duration(0)
                    .each("end", function(d) {
                        scale.domain([tmin, tmax]).nice();
                        displayYear();
                        d3.select(sel)
                          .transition().duration(1500)
                            .call(isY ? yAxis : xAxis);
                    });
            }

                // Rescale the axis
                function rescaleAxis(xy, fn) {
                    fn = typeof fn !== 'undefined' ? fn : "linear";
                    if (!(fn in d3.scale) || (typeof xy == 'undefined')) { return false; }

                    var isY = d3.select("text."+xy).classed('y label'),
                        axis = isY ? yAxis : xAxis,
                        iqraxis = isY ? yiqrAxis : xiqrAxis,
                        sel = isY ? ".y.axis" : ".x.axis",
                        iqrsel = isY ? ".yiqr.axis" : ".xiqr.axis",
                        scale = isY ? yScale : xScale,
                        domain = scale.domain();
                    if (fn=='log' && domain[0]==0) { domain[0] = 1; }
                    if (!(fn=='log') && domain[0]==1) { domain[0] = 0; }

                    cont.transition()
                        .duration(0)
                        .each("end", function(d) {;
                            if (isY) {
                                yScale = d3.scale[fn]().range(scale.range()).domain(scale.domain())
                                if ('nice' in yScale) { yScale.nice(); }
                            } else {
                                xScale = d3.scale[fn]().range(scale.range()).domain(scale.domain());
                                if ('nice' in xScale) { xScale.nice(); }
                            }
                            axis.scale( isY ? yScale : xScale );
                            iqraxis.scale( isY ? yScale : xScale );
                            d3.select(sel)
                              .transition().duration(1500)
                                .call(axis);
                            d3.select(iqrsel)
                              .transition().duration(1500)
                                .call(iqraxis);

                            displayYear();
                        });

                }

                // Add an overlay for the year label.
                function addZOverlay() {
                    if ( typeof zScale === 'undefined' ) { return false; }
                    var box = d3.select(".year.label").node().getBBox();
                    // Set the scale range based on the bounding box for the lable
                    zScale.range([box.x + 10, box.x + box.width - 10]).clamp(true);
                    var hack = 40;  // hack
                    overlay = cont.append("rect")
                        .attr("class", "overlay")
                        .on("mouseover", function() {
                            label.classed("active", true);
                            enableInteraction(); });
                    svg.select("svg g rect.overlay")
                        .attr("x", box.x)
                        .attr("y", box.y + hack)
                        .attr("width", box.width)
                        .attr("height", box.height - (100+hack));
                }

                // Add an overlay for an axis (allow axis action not just on the tick/line path)
                function addAxisOverlay(selector) {
                    if ( typeof selector === 'undefined' ) { return false; }
                    var box = d3.select(selector).node().getBBox();
                    var axisname = selector.replace(/[.]/g, " " ).trim();
                    var overlay = cont.append("rect")
                        .attr("class", axisname + " overlay")
                        .on("click", toggleScale);
                    svg.select("g rect" + selector)
                        .attr("x", box.x)
                        .attr("y", selector=='.x.axis' ? height-1 : box.y)
                        .attr("width", box.width)
                        .attr("height", box.height);
                }

                // Add a change scale dropdown menu
                function addScaleMenu(o) {
                    var tid = o.id || 'missing_id';
                    var d = d3.select("body").selectAll("div#"+tid).data([data]);
                    d.enter().append("div")
                        .attr("id", tid)
                        //.attr("class", "jq-dropdown jq-dropdown-anchor-right")
                        .attr("class", "jq-dropdown")
                      .append("ul")
                        .attr("class", "jq-dropdown-menu")
                      .selectAll("li")
                        .data(o.choices || scale_choices)
                      .enter().append("li")
                        .on("click", function() {
                            $(this).parent("ul").find('li').removeClass('active');
                            $(this).addClass('active');
                            $(this).parent("div.jq-dropdown").jqDropdown('hide');
                            if (o.callback) {
                                o.callback()
                            } else {
                                rescaleAxis(tid[tid.length-2], $(this).text());   // --hack
                            }
                        })
                        .attr("class", function(d) {return d==(o.active || 'linear') ? "active" : ""})
                        .text(function(d) { return d; });
                }

                // Add the title.
                function addTitle(selector) {
                    selector
                        .attr("text-anchor", "end")
                        .attr("x", width)
                        .classed('linkable', metadata.description === '' ? false : true)
                        .on("click", function() { toggleIn("#description", "up"); })
                        .text(metadata.title)
                      .append("tspan")
                        .attr("class", "svg_glyphicon")
                        .text(metadata.description === '' ? '' : ' \ue159');    //.text('\ue252'); // but requires newer bootstrap
                        // TODO: add this via css?
                    var d = d3.select("body").selectAll("div#description").data(metadata.description ? [metadata.description] : '');
                    d.enter()
                      .append("div")
                        .attr("id", "description")
                        .attr("data-id", "#description");
                    d.html(function(d) {return d;});
                }

                // Add an axis popup
                function addAxisPopup(id_selector) {
                    var d = d3.select("body").selectAll(id_selector).data([metadata]),
                        xy = id_selector.slice(1,2)
                        isScaleFn = function(d) { return d3.scale[d]().toLocaleString() === my[xy+'Scale']().toLocaleString(); };

                    function contents(d) {
                        d.append("h1")
                            .html('<span class="glyphicon glyphicon-edit" aria-hidden="true"></span> ' + id_selector.slice(1,7).capitalize().replace(/_/g,' '));
                        d.append("p")
                            .text('Change the scale: ')
                          .append('span')
                          .append("select")
                            .attr("class", "form-control")
                            .on("change", function() {
                                $(this).find('option').removeClass('active');
                                $(this).find('option:selected').addClass('active');
                                rescaleAxis(id_selector.slice(1,2), $(this).find('option:selected').text());   // --hack
                            })
                          .selectAll("option")
                            .data(scale_choices)
                          .enter().append("option")
                            .attr("class", function(d) {return (isScaleFn(d) ? "active" : null);})
                            .attr("selected", function(d) {return (isScaleFn(d) ? "selected" : null);})
                            .text(function(d) { return d; });

                        d.append("p")
                            .text('Change the dimension: ')
                          .append('span')
                          .append("select")
                            .attr("class", "form-control")
                            .on("change", function() {
                                var val = $(this).find('option:selected').text();
                                $(this).find('option').removeClass('active');
                                $(this).find('option:selected').addClass('active');
                                my[xy](function(d) {return d[val];});
                                selection
                                  .datum(chartdata)
                                  .call(my);
                            })
                          .selectAll("option")
                            .data(Object.keys(metadata.labels))
                          .enter().append("option")
                            .attr("class", function(d) {return (metadata.labels[d]==my[xy]()(metadata.labels) ? "active" : null);})
                            .attr("selected", function(d) {return (metadata.labels[d]==my[xy]()(metadata.labels) ? "selected" : null);})
                            .text(function(d) { return d; });
                    }
                    d.enter()
                      .append("div")
                        .attr("id", id_selector.slice(1))
                        .attr("data-id", id_selector)
                        .call(contents);
                }

                // Positions the dots based on data.
                function position(dot) {
                    dot.attr("cx", function(d) { return xScale(x(d)); })
                      .attr("cy", function(d) { return yScale(y(d)); })
                      .attr("r", function(d) { return radiusScale(radius(d)); });
                }

                // Position the summary lines based on data
                function position_summary(s) {
                    s.select("g.y.summary line")
                        .attr("x1", 0)
                        .attr("x2", width)
                        .attr("y1", function(d) { return d.y; })
                        .attr("y2", function(d) { return d.y; });
                    s.select("g.y.summary text")
                        .attr("text-anchor", "end")
                        .attr("x", width)
                        .attr("dy", -2)
                        .attr("y", function(d) { return d.y; })
                        .text(function(d) { return d.label || ''; });
                     s.select("g.x.summary line")
                        .attr("x1", function(d) { return d.x; })
                        .attr("x2", function(d) { return d.x; })
                        .attr("y1", 0)
                        .attr("y2", height);
                }

                // Defines a sort order so that the smallest dots are drawn on top.
                function order(a, b) {
                    return radius(b) - radius(a);
                }

              // After the transition finishes, you can mouseover to change the year.
              function enableInteraction() {
                var yearScale = zScale;

                // Cancel the current transition, if any.
                cont.transition().duration(0);

                overlay
                    .on("mouseover", mouseover)
                    .on("mouseout", mouseout)
                    .on("mousemove", mousemove)
                    .on("touchmove", mousemove);

                function mouseover() {
                  label.classed("active", true);
                }

                function mouseout() {
                  label.classed("active", false);
                }

                function mousemove() {
                  displayYear(yearScale.invert(d3.mouse(this)[0]));
                }
              }

              // Tweens the entire chart by first tweening the year, and then the data.
              // For the interpolated data, the dots and label are redrawn.
              function tweenYear() {
                var year = d3.interpolateNumber(summary.minz, summary.maxz);
                return function(t) { displayYear(year(t)); };
              }

              // Updates the display to show the specified year.
              function displayYear(year) {
                var dur = typeof year !== 'undefined' ? 0 : 1500;
                year = typeof year !== 'undefined' ? year : svg.select("text.year.label").text();
                var d = interpolateData(year),
                    notdone = d3.select("#jq-dropdown-agg li.active").empty(),
                    m =  ! notdone ? d3.select("#jq-dropdown-agg li.active").text() : 'median' || 'median';
                dot.data(d, key).transition().duration(dur).call(position).sort(order);
                label.text(Math.round(year));
                summary_lines.data([
                    {'x': xScale(d3[m](d, x)),
                     'y': yScale(d3[m](d, y)),
                     'label': m,
                    }]).transition().duration(dur).call(position_summary);
                xbox = dz.boxplot(d,x);
                ybox = dz.boxplot(d,y);
                xiqrAxis.tickValues([xbox.lw, xbox.q1, xbox.q2, xbox.q3, xbox.uw]);
                yiqrAxis.tickValues([ybox.lw, ybox.q1, ybox.q2, ybox.q3, ybox.uw]);
                svg.select(".xiqr.axis")
                  .transition().duration(dur)
                    .call(xiqrAxis);
                svg.select(".yiqr.axis")
                  .transition().duration(dur)
                    .call(yiqrAxis);
              }

              // Interpolates the dataset for the given (fractional) year.
              function interpolateData(year) {
                return data.map(function(d) {
                    var out = {}
                    out[dz.getKey(metadata.labels, getLabel(key))] = key(d);
                    out[dz.getKey(metadata.labels, getLabel(color))] = color(d);
                    out[dz.getKey(metadata.labels, getLabel(x))] = interpolateValues(x(d), year);
                    out[dz.getKey(metadata.labels, getLabel(radius))] = interpolateValues(radius(d), year);
                    out[dz.getKey(metadata.labels, getLabel(y))] = interpolateValues(y(d), year);
                  return out;
                });
              }

              // Finds (and possibly interpolates) the value for the specified year.
              function interpolateValues(values, year) {
                var i = bisect.left(values, year, 0, values.length - 1),
                    a = values[i];
                if (i > 0) {
                  var b = values[i - 1],
                      t = (year - a[0]) / (b[0] - a[0]);
                  return a[1] * (1 - t) + b[1] * t;
                }
                return a[1];
              }

            function resizeContainer() {
                var cwidth = parseInt(selection.style("width"));
                cwidth = cwidth - parseInt(selection.style("padding-left")) - parseInt(selection.style("padding-left"));

                my.width(cwidth - margin.right).height(cwidth / ratio);
                xScale.range([0, width]);
                yScale.range([height, 0]);
                selection
                  .datum(chartdata)
                  .call(my);
                $("#description, #x_axis_description, #y_axis_description").hide();
            }

            function toggleIn(selector, direction) {
                //TODO: remove jquery depends
                var d = $(selector),
                    m = parseInt(d.css("padding-left"));    // assumes uniform

                d.css("width", width - margin.left + 15);
                d.css("left", $("svg").offset().left + margin.left + 30);
                d.css("top", $("svg").offset().top + margin.top + 10);
                d.css("height", height - margin.top + 10);
                if ( d.css("display") !== "block" ) {
                    if ( d.effect ) {
                        d.css("display", "block").effect("slide", {"direction":direction});
                    } else {
                        d.show().css("display", "block");
                    }
                } else {
                    if ( d.effect ) {
                        //d.slideUp();
                        d.toggle("slide", {"direction":direction})
                    } else {
                        d.hide();
                    }
                }
            }

          }); /* end for each */

        } /* end-chart */

        // Dimensions
        my.margin = function(value) {
            if (!arguments.length) return margin;
            margin = value;
            return my;
        };
        my.width = function(value) {
            if (!arguments.length) return width;
            width = value - margin.right;
            return my;
        };
        my.height = function(value) {
            if (!arguments.length) return height;
            height = value - margin.top - margin.bottom;
            return my;
        };
        my.aspect_ratio = function(value) {
            if (!arguments.length) return ratio;
            ratio = value;
            return my;
        };

        // Accessors
        my.x = function(fn) {
            if (!arguments.length) return x;
            x = fn;
            return my;
        };
        my.y = function(fn) {
            if (!arguments.length) return y;
            y = fn;
            return my;
        };
        my.z = function(fn) {
            if (!arguments.length) return z;
            z = fn;
            return my;
        };
        my.valueatZ = function(fn) {
            if (!arguments.length) return atZ;
            atZ = fn;
            return my;
        };
        my.radius = function(fn) {
            if (!arguments.length) return radius;
            radius = fn;
            return my;
        };
        my.color = function(fn) {
            if (!arguments.length) return color;
            color = fn;
            return my;
        };
        my.key = function(fn) {
            if (!arguments.length) return key;
            key = fn;
            return my;
        };
        my.tooltip = function(fn) {
            if (!arguments.length) return tooltip;
            tooltip = fn;
            return my;
        };

        // Scales
        my.xScale = function(scale) {
            if (!arguments.length) return xScale;
            xScale = scale;
            return my;
        };
        my.yScale = function(scale) {
            if (!arguments.length) return yScale;
            yScale = scale;
            return my;
        };
        my.zScale = function(scale) {
            if (!arguments.length) return zScale;
            zScale = scale;
            return my;
        };
        my.radiusScale = function(scale) {
            if (!arguments.length) return radiusScale;
            radiusScale = scale;
            return my;
        };
        my.colorScale = function(scale) {
            if (!arguments.length) return colorScale;
            colorScale = scale;
            return my;
        };

        // Formatters
        my.radiusFormat = function(value) {
            if (!arguments.length) return radiusFormat;
            radiusFormat = value;
            return my;
        };

        // Axis
        my.xAxis = function(value) {
            if (!arguments.length) return xAxis;
            xAxis = value;
            return my;
        };
        my.yAxis = function(value) {
            if (!arguments.length) return yAxis;
            yAxis = value;
            return my;
        };

        // Options
        my.scale_choices = function(value) {
            if (!arguments.length) return scale_choices;
            scale_choices = value;
            return my;
        };
        my.agg_choices = function(value) {
            if (!arguments.length) return agg_choices;
            agg_choices = value;
            return my;
        };
        my.disableResize = function(value) {
            if (!arguments.length) return disableResize;
            disableResize = value;
            return my;
        };

        return my;
    }  /* end scatter chart */

d3.charts.calendar =
    function() {
        /* A calendar plot chart

        i. reusable
        i. responsive grammar

        TODO:
            i. add/remove grammar as we resize
            i. vary color scale (min/max, center on zero, center on "x", [0..1], ...)
            i. add events

        */

        var margin = {top: 20, right: 40, bottom: 20, left: 50},
            width = 960 - margin.right,
            height = 156 - margin.top - margin.bottom,
            cellSize = 17,
            labelFormat = d3.format(",g"),
            dateFormat = d3.time.format("%Y-%m-%d"),
            palette = "RdYlGn",
            colorScale = d3.scale.quantize().range(d3.range(11).map(function(d) { return "q" + d + "-11"; })),
            summary = {},
            disableResize = false,
            metadata = {'title': 'Calendar Demo'},
            daysofweek = ['Su','M', 'Tu', 'W', 'Th', 'F', 'Sa'],
            months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-6, 0])
                .html(tooltip),
            colorAxis = d3.charts.colorLegend()
                .scale(colorScale)
                .height(50)
                .width(200)
                .label(labelFormat)
                .tooltip(function(d) { return d.map(Math.round); })
                .title(function() { return getLabel(x); });

        // Various accessors that specify the four dimensions of data to visualize.
        function x(d) { return d.value; }
        function key(d) { return d.date; }
        function tooltip(d) { return "<strong>" + d + "</strong>"; }
        function getLabel(fn, dir) {
            var l = fn(metadata.labels);
            dir = typeof dir !== 'undefined' ? dir : '';
            l = typeof l !== 'undefined' ? l + " " + dir : undefined;
            return l;
        }

        function my(selection) {
          selection.each(function(chartdata, i) {
            metadata.title = chartdata.title || metadata.title;
            metadata.description = chartdata.description || '';
            metadata.labels = chartdata.labels || {};
            metadata.daysofweek = chartdata.daysofweek || daysofweek;
            metadata.months = chartdata.months || months;
            data = chartdata.data || chartdata;
            summarize(data);

            // Set the domains and scales based on the data
            colorScale.domain([summary.x[0]<0 ? summary.x[0] : 0, summary.x[1]]);

            // Create chart title and controls
            var controls = d3.select(this).selectAll("h1.title").data([data]);
            controls.enter().append("h1").attr("class", "title").each(resizeContainer);
            controls.call(addTitle);
            d3.select("#description").call(brewerSelector);

            // Create the SVG container and set the origin.
            var svg = d3.select(this).selectAll("svg.calendar").data(dz.range(summary.years[0], summary.years[1]));
            var cont = svg.enter().append("svg").attr("class", "calendar").append("g").each(function() {
                var d = d3.select(this);
                d.append("g").attr("class", "labels").append("text");
                d.append("g").attr("class", "days");
                d.append("g").attr("class", "months");
                d.append("g").attr("class", "events");
                d.append("g").attr("class", "legend").append("g");
            });
            svg.call(tip);
            svg.attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .attr("class", "calendar " + palette);
            svg.select("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            // Update the week/month/year labels
            svg.select("g g.labels text")
                .attr("transform", "translate(-10," + (cellSize/2) + ")")
                .style("text-anchor", "end")
                .text(function(d) { return d; });
            var monthlabel = selection.select("g.labels").selectAll(".monthlabel").data(metadata.months);
            monthlabel.enter()
              .append("text")
                .attr("class", "monthlabel")
                .style("text-anchor", "start");
            monthlabel
                .attr("dy", -1*(cellSize/4))
                .attr("x", function(d,i) {
                    var t0 = new Date(summary.years[0], i + 1, 0),
                        w0 = d3.time.weekOfYear(t0);
                    return ((w0)*(cellSize)) - (cellSize/4);
                })
                .text(function(d) { return d; });
            var weekday = selection.select("g.labels").selectAll(".dayofweek").data(metadata.daysofweek);
            weekday.enter()
              .append("text")
                .attr("class", "dayofweek")
                .style("text-anchor", "start");
            weekday
                .attr("dy", -1*(cellSize/4))
                .attr("y", function(d,i) { return (i+1)*(cellSize) ;})
                .attr("x", width + 6)
                .text(function(d) { return d; });

            // Enter/Update the days
            var rect = svg.select("g.days").selectAll(".day")
                .data(function(d) { return d3.time.days(new Date(d, 0, 1), new Date(d + 1, 0, 1)); });
            rect.enter().append("rect")
                .attr("class", "day");
            rect
                .attr("width", cellSize)
                .attr("height", cellSize)
                .attr("x", function(d) { return d3.time.weekOfYear(d) * cellSize; })
                .attr("y", function(d) { return d.getDay() * cellSize; })
                .on('mouseover', tip.show)
                .on('mouseout', tip.hide)
                .datum(dateFormat);

            // Enter/Update the months
            var month = svg.select("g.months").selectAll(".month")
                .data(function(d) { return d3.time.months(new Date(d, 0, 1), new Date(d + 1, 0, 1)); });
            month.enter().append("path").attr("class", "month");
            month.attr("d", monthPath);

            // Update the days for our data
            var displayData = d3.nest()
              .key(key)
              .rollup(function(d) { return x(d[0]); })
                .map(data);
            rect.filter(function(d) { return d in displayData; })
                .attr("class", function(d) { return "day " + colorScale(displayData[d]); })
                .on("mouseover", function(d) { return tip.show(d + ": " + labelFormat(displayData[d])); })
                .on("mouseout", tip.hide);

            // Add the legend
            var legend = d3.select(this).selectAll("svg.legend").data([1]);
            legend.enter().insert("svg", "svg").attr("class", "legend").append("g");
            legend
                .attr("class", "legend " + palette)
                .attr("width", colorAxis.fullWidth())
                .attr("height", colorAxis.height());
            legend.select("g")
                .call(colorAxis);

            // support responsive by default
            if (!disableResize) { d3.select(window).on('resize', resizeContainer); }

            // Generate the path for a month
            function monthPath(t0) {
              var t1 = new Date(t0.getFullYear(), t0.getMonth() + 1, 0),
                  d0 = t0.getDay(), w0 = d3.time.weekOfYear(t0),
                  d1 = t1.getDay(), w1 = d3.time.weekOfYear(t1);
              return "M" + (w0 + 1) * cellSize + "," + d0 * cellSize
                  + "H" + w0 * cellSize + "V" + 7 * cellSize
                  + "H" + w1 * cellSize + "V" + (d1 + 1) * cellSize
                  + "H" + (w1 + 1) * cellSize + "V" + 0
                  + "H" + (w0 + 1) * cellSize + "Z";
            }

            // Summarize the data
            function summarize(data) {
                summary.x = d3.extent(data,x);
                summary.key = d3.extent(data,key);
                summary.years = summary.key.map(function(d) {return dateFormat.parse(d).getFullYear();});
                //summary.box = dz.boxplot(data, x);
                //console.log(summary);
            }

            // Add the title.
            function addTitle(selector) {
                selector
                    .classed('linkable', metadata.description === '' ? false : true)
                    .classed('down',true)
                    .on("click", function() { toggleIn("#description", "up"); })
                    .text(metadata.title)
                var d = d3.select("body").selectAll("div#description").data(metadata.description ? [metadata.description] : '');
                d.enter()
                  .append("div")
                    .attr("id", "description")
                    .attr("data-id", "#description");
                d.html(function(d) {return "<h1>Calendar</h1><p>" + d + "</p>";});
            }

            // Resize the chart container
            function resizeContainer() {
                var cwidth = parseInt(selection.style("width"));
                cwidth = cwidth - parseInt(selection.style("padding-left")) - parseInt(selection.style("padding-left"));

                cellSize = (cwidth - margin.left - margin.right) / 53;
                my.width(cwidth - margin.left - 1);
                selection
                  .datum(chartdata)
                  .call(my);
                $("#description").hide();
            }

            function toggleIn(selector, direction) {
                //TODO: remove jquery depends
                var ts = ".title",
                    t = selection.select(ts),
                    d = $(selector),
                    m = parseInt(d.css("padding-left"));    // assumes uniform

                // toggle the icon direction
                t.classed('down',!t.classed('down'));
                t.classed('up',!t.classed('up'));

                // toggle the panel
                var top = ($(ts).offset().top + parseInt($(ts).css("padding-top")) + parseInt($(ts).height()));
                d.css("width", width + margin.left + margin.right);
                d.css("left", $("#chart").offset().left );
                d.css("top", top );
                d.css("height", $("#chart").height() - parseInt($(ts).css("margin-top")) - parseInt($(ts).css("padding-top")) - $(ts).height());
                if ( d.css("display") !== "block" ) {
                    if ( d.effect ) {
                        d.css("display", "block").effect("slide", {"direction":direction});
                    } else {
                        d.show().css("display", "block");
                    }
                } else {
                    if ( d.effect ) {
                        //d.slideUp();
                        d.toggle("slide", {"direction":direction})
                    } else {
                        d.hide();
                    }
                }
            }

            // ColorBrewer selector component
            function brewerSelector(selection, brewerSize) {
                brewerSize = typeof brewerSize !== 'undefined' ? brewerSize : colorScale.range().length;
                if (typeof colorbrewer == 'undefined') { return false; }

                var pal = Object.keys(colorbrewer).filter(function(d) {return brewerSize.toString() in colorbrewer[d]; }),
                    activePal = function(p) { return p==palette; }
                var cont = selection.selectAll("p.dropdown.brewer").data([pal]);
                cont.enter()
                  .append("p")
                    .attr("class", "dropdown brewer")
                    .text("Change Palette:")
                    .append("select")
                        .attr("class", "form-control")
                        .selectAll("option")
                          .data(pal)
                            .enter().append("option")
                                .attr("selected", function(d) {return (activePal(d) ? "selected" : null);})
                                .text(function(d) { return d; });

            }

          }); /* end for each */

        } /* end-chart */

        // dimensions
        my.width = function(value) {
            if (!arguments.length) return width;
            width = value - margin.right;
            return my;
        };

        my.height = function(value) {
            if (!arguments.length) return height;
            height = value - margin.top - margin.bottom;
            return my;
        };

        my.margin = function(value) {
            if (!arguments.length) return margin;
            margin = value;
            return my;
        };

        // accessors
        my.x = function(fn) {
            if (!arguments.length) return x;
            x = fn;
            return my;
        };

        my.key = function(fn) {
            if (!arguments.length) return key;
            key = fn;
            return my;
        };

        my.tooltip = function(fn) {
            if (!arguments.length) return tooltip;
            tooltip = fn;
            tip.html(tooltip);
            return my;
        };

        my.color = function(scale) {
            if (!arguments.length) return colorScale;
            colorScale = scale;
            colorAxis.scale(colorScale);
            return my;
        };

        my.palette = function(value) {
            if (!arguments.length) return palette;
            palette = value;
            return my;
        };

        my.legend = function(value) {
            if (!arguments.length) return colorAxis;
            colorAxis = value;
            return my;
        };

        // options
        my.label = function(value) {
            if (!arguments.length) return labelFormat;
            labelFormat = value;
            colorAxis.label(labelFormat);
            return my;
        };

        my.date = function(value) {
            if (!arguments.length) return dateFormat;
            dateFormat = value;
            return my;
        };

        my.week_label = function(value) {
            if (!arguments.length) return daysofweek;
            daysofweek = value;
            return my;
        };

        my.month_label = function(value) {
            if (!arguments.length) return months;
            months = value;
            return my;
        };

        my.disableResize = function(value) {
            if (!arguments.length) return disableResize;
            disableResize = value;
            return my;
        };

        return my;
    }  /* end calendar chart */

d3.charts.colorLegend = function() {
    /* A legend/axis for a color scale

    TODO:
        i. support on hover (hover in visual shows where in the axis it fits)
        i. orientation
    */

    var width = 300,
        height = 44,
        margin = 10,
        labelFormat = function(d) { return d3.format(",d")(100*d); },
        title = 'Color Scale',
        colorScale = d3.scale.threshold().domain([.11, .22, .33, .50]).range(["#6e7c5a", "#a0b28f", "#d8b8b3", "#b45554", "#760000"]),
        x = d3.scale.linear().domain([0, 1]).range([0, width]),
        xAxis = d3.svg.axis().scale(x).orient("bottom").tickSize(13)
            .tickValues(colorScale.domain())
            .tickFormat(labelFormat),
        tip = d3.tip()
            .attr('class', 'd3-tip color-axis')
            .offset([-6, 0])
            .html(tooltip);

    // Various accessors
    function tooltip(d) { return "<strong>" + d + "</strong>"; }

    function my(g) {
      g.each(function(data, i) {

        // Update the domain
        if (colorScale.domain().length == 2) {
            x.domain(colorScale.domain());
            xAxis.tickValues(colorScale.domain());
        } else {
            x.domain([0,1]);
            xAxis.tickValues(colorScale.domain());
        }

        // Add the tip container
        g.call(tip);

        // Create the color bands
        g.attr("class", "color legend")
            .attr("width", width + margin*2).attr("height", height)
            .attr("transform", "translate(" + margin + "," + height / 2.5 + ")");
        g.selectAll("rect")
            .data(colorScale.range().map(function(color) {
              var d = colorScale.invertExtent(color);
              if (d[0] == null) d[0] = x.domain()[0];
              if (d[1] == null) d[1] = x.domain()[1];
              return d;
            }))
          .enter().append("rect")
            .attr("height", 8)
            .attr("x", function(d) { return x(d[0]); })
            .attr("width", function(d) { return x(d[1]) - x(d[0]); })
            .attr("class", function(d) {
                var k = colorScale(d[0]);
                return k[0] == '#' ? null : k;
            })
            .style("fill", function(d) {
                var k = colorScale(d[0]);
                return k[0] == '#' ? k : null;
            })
            .on("mouseover", tip.show)
            .on("mouseout", tip.hide);

        g.call(xAxis);
        var caption = g.selectAll("text.caption").data([1]);
        caption.enter()
          .append("text")
            .attr("class", "caption");
        caption
            .attr("class", "caption")
            .attr("y", -6)
            .text(title);

      }); /* end for each */

    } /* end-grammar */

    // a required scale to work on
    my.scale = function(value) {
        if (!arguments.length) return colorScale;
        colorScale = value;
        return my;
    };
    my.xaxis = function(value) {
        if (!arguments.length) return xAxis;
        xAxis = value;
        return my;
    };

    // dimensions
    my.fullWidth = function() {
        return width + margin*2;
    };

    my.margin = function(value) {
        if (!arguments.length) return margin;
        margin = value;
        return my;
    };

    my.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return my;
    };

    my.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        x.range([0,width]);
        return my;
    };

    // options
    my.label = function(value) {
        if (!arguments.length) return labelFormat;
        labelFormat = value;
        xAxis.tickFormat(labelFormat);
        return my;
    };

    my.title = function(value) {
        if (!arguments.length) return title;
        title = value;
        return my;
    };

    // accessors
    my.tooltip = function(value) {
        if (!arguments.length) return tooltip;
        tooltip = value;
        tip.html(tooltip);
        return my;
    };

    return my;
}  /* end color scale axis */

d3.charts.circleLegend = function() {
    /* A legend/scale for circles

    TODO:
        i. support on hover (hover in visual shows where in the axis it fits)
        i. ensure circle domain/range matches the source
    */

    var margin = {top: 60, right: 0, bottom: 0, left: 90},
        width = 120,
        height = 100,
        labelFormat = d3.format(",d"),
        title = 'Circle Scale',
        radiusScale = d3.scale.linear().domain([0, 1]).range([0, 40]);

    // Various accessors
    function radius(d) { return d.value; }

    function my(g) {
      g.each(function(data, i) {
        // Set the domain based on the data.
        radiusScale.domain([0,d3.max(data, radius)]);
        max_radius = radiusScale.range()[1];
        radius_offset = 10;

        // Variable definitions.
        var caption = g.selectAll("text.caption").data([data]),
            captionEnter = caption.enter(),
            circles = g.selectAll("g.circle").data(data),
            circlesEnter = circles.enter();

        // Set the container origin.
        g.attr("class", "circle legend")
            .attr("width", width).attr("height", height)
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Handle the circles for the keys.
        circlesEnter
          .append("g")
          .attr("class", "circle")
          .call(addKey)
          .sort(order);

        circles
            .attr("transform", function(d) {
                var offset = -1 * (radiusScale(radius(d)) - max_radius);
                return "translate(0," + offset + ")";
            });
        circles.select("line")
            .attr("x1", function(d) { return -1 * (radiusScale(radius(d)));} )
            .attr("x2", function(d) { return -1 * (max_radius+radius_offset);} )
            .attr("y1", 0)
            .attr("y2", 0);
        circles.select("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", function(d) { return radiusScale(radius(d)); });
        circles.select("text")
            .attr("text-anchor", "end")
            .attr("transform", "translate(" + -1*(max_radius+(radius_offset*1.1)) + ",0)")
            .text(function(d) { return labelFormat(radius(d)); });

        // Handle the legend title/caption.
        captionEnter.append("text")
            .attr("class", "caption");
        caption
            .attr("class", "caption")
            .attr("text-anchor", "middle")
            .attr("dy", -6)
            .attr("transform", "translate(0," + -1*max_radius + ")")
            .text(title);

        function addKey(sel) {
            sel.append("circle");
            sel.append("line");
            sel.append("text");
        };

        function order(a, b) {
            return radius(b) - radius(a);
        }

      }); /* end for each */

    } /* end-grammar */

    // a required scale to work on
    my.scale = function(value) {
        if (!arguments.length) return radiusScale;
        radiusScale = value;
        return my;
    };

    // dimensions
    my.margin = function(value) {
        if (!arguments.length) return margin;
        margin = value;
        return my;
    };

    my.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return my;
    };

    my.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return my;
    };

    // options
    my.label = function(value) {
        if (!arguments.length) return labelFormat;
        labelFormat = value;
        return my;
    };

    my.title = function(value) {
        if (!arguments.length) return title;
        title = value;
        return my;
    };

    return my;
}  /* end circle scale */


d3.charts.chosenSelect = function() {
    /* A chosen input/select box

    data format ['option group label', ['list', 'of', 'options'], [...]]
    */

    var tabindex = 1,
        multiple = false,
        placeholder = "Select an Option...",
        title = 'Single Select',
        selected = false;

    function my(g) {
      g.each(function(data, i) {
        if (!selected) { selected = data[0][0]; }

        // Variable definitions.
        var caption = g.selectAll("em").data([data]),
            captionEnter = caption.enter(),
            aselect = g.selectAll("select").data([data]),
            selectEnter = aselect.enter();

        // Create and update the containers.
        captionEnter.append("em");
        selectEnter.append("select").attr("class", "chosen-select");
        caption.text(title);
        aselect
            .attr("data-placeholder", placeholder)
            .attr("tabindex", tabindex)
            .attr("multiple", multiple ? true : null);

        // Handle the option groups.
        optionGroups = aselect.selectAll("optgroup").data(function(d) { return d; }),
        optionGroups.enter().append("optgroup");
        optionGroups.attr("label", function(d) { return d[0]; } );

        // Handle the options
        options = optionGroups.selectAll("option").data(function(d) { return d[1]; }),
        options.enter().append("option");
        options.attr("selected", function(d) { return d==selected ? "selected" : null; });
        options.classed("active", function(d) { return d==selected ? true : false; });
        options.text(function(d) { return d; });

      }); /* end for each */

    } /* end chosen select */

    // options
    my.selected = function(value) {
        if (!arguments.length) return selected;
        selected = value;
        return my;
    };
    my.tabindex = function(value) {
        if (!arguments.length) return tabindex;
        tabindex = value;
        return my;
    };
    my.multiple = function(value) {
        if (!arguments.length) return multiple;
        multiple = value;
        return my;
    };
    my.placeholder = function(value) {
        if (!arguments.length) return placeholder;
        placeholder = value;
        return my;
    };
    my.title = function(value) {
        if (!arguments.length) return title;
        title = value;
        return my;
    };

    return my;
}  /* end chosen select */
