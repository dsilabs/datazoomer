function onEachFeature(feature, layer) {
  if (feature.properties && feature.properties.HA_NAME) {
    layer.bindPopup(feature.properties.HA_NAME);
  }
};

function colorFeature(feature) {
  // color brewer - spectral diverging scale
  var spectral = ["#9e0142","#d53e4f","#f46d43","#fdae61","#fee08b","#ffffbf","#e6f598","#abdda4","#66c2a5","#3288bd","#5e4fa2"].reverse();
  return {color: spectral[feature.properties.HA_NUM-1], weight: 1};
};