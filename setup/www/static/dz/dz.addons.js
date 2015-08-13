// Extend
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
String.prototype.endswith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
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

// get scale options
function scaleChoices() {
    var t = [];
    for (var s in d3.scale) { t.push(s); }
    return t
}
// boxplot
function boxplot(d, accessor) {
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

// dsi namespace
var dsi = {
    scatter: function() {
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
            radiusScale = d3.scale.sqrt().domain([0, 5e8]).range([0, 40]),
            colorScale = d3.scale.category10().range(d3.scale.category10().range().reverse()),
            xAxis = d3.svg.axis().orient("bottom").scale(xScale).ticks(12, d3.format(",d")),
            xiqrAxis = d3.svg.axis().orient("top").scale(xScale).innerTickSize(3).outerTickSize(0),
            yAxis = d3.svg.axis().scale(yScale).orient("left"),
            yiqrAxis = d3.svg.axis().orient("right").scale(yScale).innerTickSize(3).outerTickSize(0),
            xZoom = undefined, yZoom = undefined,
            summary = {},
            axis_buffer = 0.12
            scale_choices = scaleChoices(),
            agg_choices = ['max', 'mean', 'median', 'min'],
            metadata = {'title': 'Scatter Demo'},
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-6, 0])
                .html(function(d) {
                    return "<strong>" + key(d) + "</strong>";
                });

        // Various accessors that specify the four dimensions of data to visualize.
        function x(d) { return d.income; }
        function y(d) { return d.lifeExpectancy; }
        function z(d) { return d[0]; }
        function atZ(d) { return d[1]; }
        function radius(d) { return d.population; }
        function color(d) { return d.region; }
        function key(d) { return d.name; }
        function getLabel(fn, dir) {
            var l = fn(metadata.labels);
            l = typeof l !== 'undefined' ? l + " " + dir : undefined;
            return l;
        }

        function my(selection) {
          selection.each(function(chartdata, i) {
            metadata.title = chartdata.title || metadata.title;
            metadata.description = chartdata.description || '';
            metadata.labels = chartdata.labels || {};
            data = chartdata.data || chartdata;
            // TODO: investigate the chart being responsive (add/remove graph grammar depending on size)
            //console.log(parseInt(d3.select(this).style("width")));
            summarize(data);

            // Set the domains and scales based on the data
            xScale.domain([summary.default_minx, summary.maxx]).nice();
            yScale.domain([summary.default_miny, summary.maxy]).nice();
            zScale.domain([summary.minz, summary.maxz]);

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
                  //.on("click", function(d) {console.log($(this)); $(this).tooltip({title:'hi', container:'body', 'placement': 'top'});})
                  .on('mouseover', function(d) {
                    tip.show(d);
                    d3.select(this).classed("active", true);
                  })
                  .on('mouseout', function(d) {tip.hide(d); d3.select(this).classed("active", false);})
                  .call(position)
                  .sort(order);
            displayYear();   // update the docst once the interaction is done

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
            d3.select(window).on('resize', resizeContainer);

            // Summarize the data
            function summarize(data) {
                summary.minx = d3.min(data, function(d) {return d3.min(x(d), atZ);});
                summary.maxx = d3.max(data, function(d) {return d3.max(x(d), atZ);});

                summary.miny = d3.min(data, function(d) {return d3.min(y(d), atZ);});
                summary.maxy = d3.max(data, function(d) {return d3.max(y(d), atZ);});

                summary.minz = d3.min(data, function(d) {return d3.min(x(d), z);});
                summary.maxz = d3.max(data, function(d) {return d3.max(y(d), z);});

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
                            console.log(iqraxis);
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
                xbox = boxplot(d,x);
                ybox = boxplot(d,y);
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
                  return {
                    name: d.name,
                    region: d.region,
                    income: interpolateValues(d.income, year),
                    population: interpolateValues(d.population, year),
                    lifeExpectancy: interpolateValues(d.lifeExpectancy, year)
                  };
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

        return my;
    },  /* end scatter chart */
};
