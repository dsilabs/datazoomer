$(function(){
  var %(ref)s = d3.charts.scatter()%(methods)s;
  d3.json("%(view)s", function(data) {
      d3.select("%(selector)s")
        .datum(data)
        .call(%(ref)s);
  });
});
