$(function(){
  
  var sequential = {Blues: true, BuGn: true, BuPu: true, GnBu: true, Greens: true, Greys: true,
      Oranges: true, OrRd: true, PuBu: true, PuBuGn: true, PuRd: true, Purples: true, RdPu: true,
      Reds: true, YlGn: true, YlGnBu: true, YlOrBr: true, YlOrRd: true
  };
  // colorblind safe EXCEPT for 9 classes?: BrBG
  var diverging = {BrBG: true, PiYG: true, PRGn: true, PuOr: true, RdBu: true, RdYlBu: true,
      RdGy: false, RdYlGn: false, Spectral: false
  };
  // colorblind safe to 3 classes only: Dark2, Paired, Set2
  // colorblind safe to 4 classes only: Paired
  var qualitative = {Dark2: true, Paired: true, Set2: true,
      Accent: false, Pastel1: false, Pastel2: false, Set1: false, Set3: false

  };
  var colorblind_notes = {BrBG: 'Except set of 9', Dark2: 'Safe to set of 3 only', Set2: 'Safe to set of 3 only', Paired: 'safe to set of 4 only'};
  var schemes = [
      {type: 'Sequential', colorblind: sequential, colorbrewer: d3.entries(colorbrewer).filter(function (d) {return d.key in sequential;}), notes:null},
      {type: 'Diverging', colorblind: diverging, colorbrewer: d3.entries(colorbrewer).filter(function (d) {return d.key in diverging;}),
          notes:{BrBG: 'Except set of 9'}},
      {type: 'Qualitative', colorblind: qualitative, colorbrewer: d3.entries(colorbrewer).filter(function (d) {return d.key in qualitative;}),
          notes:{Dark2: 'Safe to set of 3 only', Set2: 'Safe to set of 3 only', Paired: 'safe to set of 4 only'}},
  ];
  var iscolorblind = function(p) {
      if (p in sequential) return sequential[p];
      if (p in diverging) return diverging[p];
      if (p in qualitative) return qualitative[p];
      return false;
  };

  d3.select("div.visual")
    .selectAll(".scheme.type")
      .data(schemes)
    .enter().append("p")
      .attr("class", "scheme type")
      .attr("title", function(s) { return s.type; })
    .selectAll(".palette")
      .data(function(d) { return d.colorbrewer; })
    .enter().append("span")
      .attr("class", function(d) { return !iscolorblind(d.key) ? "palette notcolorblind" : "palette";})
      .attr("title", function(d) { return d.key; })
    .selectAll(".swatch")
      .data(function(d) { return d.value[d3.keys(d.value).map(Number).sort(d3.descending)[0]]; })
    .enter().append("span")
      .attr("class", "swatch")
      .style("background-color", function(d) { return d; });

  scheme_selection = function(name) {
      d3.selectAll(".scheme.type")
          .classed("non highlight", true);
      d3.selectAll(".scheme.type[title=" + name + "]")
          .classed("non highlight", false);
  };
  displayDetails = function(d) {
      ttype = function(p) {
          if (p in sequential) return 'Sequential';
          if (p in diverging) return 'Diverging';
          return 'Qualitative';
      };
      type = 'Scheme type: ' + ttype(d.key) + '<br/>';
      name = 'Scheme name: ' + d.key + '<br/>';
      blind = 'Colorblind Safe: ' + iscolorblind(d.key) + (d.key in colorblind_notes ? ' *(' + colorblind_notes[d.key] + ')' : '') + '<br/><br/>';
      title = 'Sets: <br/>';
      data = d3.values(d.value).map(JSON.stringify).join("<br/>");
      d3.select("div.reference")
          .html(type + name + blind + title + data);
      d3.selectAll("span.palette")
          .classed("paletteselection", false);
      d3.selectAll("span.palette[title=" + d.key + "]")
          .classed("paletteselection", true);
  };

  // enable filter interactions
  d3.select("select").on("change", function () {
      if (this.value==="All") d3.selectAll(".scheme.type").classed("non highlight", false);
      else scheme_selection(this.value);
  });
  d3.select("input[type=checkbox]").on("change", function () {
      if ( d3.select(this).property("checked") ) {
          d3.selectAll(".palette.notcolorblind").classed("non highlight", false);
          d3.selectAll(".palette.notcolorblind").classed("non highlight", true);
      }
      else d3.selectAll(".palette.notcolorblind").classed("non highlight", false);
  });
  d3.selectAll("span.palette").on("click", displayDetails);
  
});
