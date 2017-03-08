#!/usr/bin/env python
# -*- coding: utf-8 -*- 
'''
Make interactive OSM map with markers
Adapted from https://openlayers.org/en/latest/examples/icon-color.html; 17.02.2017.
and http://gis.stackexchange.com/questions/166613/openlayers-3-10-1-feature-popup; 17.02.2017.

Example:
    with open("map.html","w") as f:
        f.write(osmView([(51.0666351,13.7418938)]))

Authr: timo
'''

import os, shutil

dir_path = os.path.dirname(os.path.realpath(__file__))

def osmView(points=[], centre=None, zoom=14, lines=[], arrows=[], circles=[]):
    """
    points list, [{lat: float, lon: float, name: String, colour: String}]
    circles list, [{lat: float, lon: float, r: float, name: String, colour: String}]
    lines list, [{lat1: float, lon1: float, lat2: float, lon2: float, name: String, colour: String}]
    arrows list, [{lat1: float, lon1: float, lat2: float, lon2: float, name: String, colour: String}]
    centre Coordinates
    zoom int
    lines list, [(lat1 float, lon1 float, lat2 float, lon2 float, name String, colour_as_hex String)]
    returns html String
    """
    
    def clean_e(e):
        e["colour"] = e.get("colour","#0099ff")
        e["name"] = unicode(e.get("name","")).replace("\n","\\n")
        e["r"] = e.get("r",100)
        return e
    markersHtml = []
    
    if centre is None:
            e = (points+lines+arrows+circles)[0]
            if "lat" in e:
                centre=(e["lat"],e["lon"])
            elif "lat1" in e:
                centre=(e["lat1"],e["lon1"])
    
    # points:
    markersHtml.extend(["""
      (function (){
      var point = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([%(lon)f, %(lat)f])),
        name: "%(name)s"
      });
      point.setStyle(new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
          color: '%(colour)s',
          crossOrigin: 'anonymous',
          src: 'https://openlayers.org/en/v4.0.1/examples/data/dot.png'
        }))
      }));
      return point;
      })()
    """%clean_e(e) for e in points])
    
    # circles:
    markersHtml.extend(["""
      (function (){
      var point = new ol.Feature({
        geometry: new ol.geom.Circle(ol.proj.fromLonLat([%(lon)f, %(lat)f]),%(r)d),
        name: "%(name)s"
      });
      return point;
      })()
    """%clean_e(e) for e in circles])
        
    # lines:
    markersHtml.extend(["""
      (function (){
      var point = new ol.Feature({
        geometry: new ol.geom.LineString([ol.proj.fromLonLat([%(lon1)f, %(lat1)f]),ol.proj.fromLonLat([%(lon2)f, %(lat2)f])]),
        name: "%(name)s"
      });
      point.setStyle(new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '%(colour)s',
            width: 2
        })
      }));
      return point;
      })()
    """%clean_e(e) for e in lines])
    
    # arrows:
    markersHtml.extend(["""
      (function (){

      var start = ol.proj.fromLonLat([%(lon1)f, %(lat1)f])
      var end   = ol.proj.fromLonLat([%(lon2)f, %(lat2)f])
      var dx = end[0] - start[0];
      var dy = end[1] - start[1];
      var rotation = Math.atan2(dy, dx);
      
      var line = new ol.geom.LineString([start,end]);
      var point = new ol.Feature({
        geometry: line,
        name: "%(name)s"
      });
      iconStyle = new ol.style.Icon({
              src: 'arrow_blue.png',
              anchor: [0.75, 0.5],
              rotateWithView: true,
              rotation: -rotation,
              scale: 1.0
      })
      point.setStyle([
      //styles.push([
        new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: '%(colour)s',
                width: 2
            }),
        }),
        new ol.style.Style({
            geometry: new ol.geom.Point(end),
            image: iconStyle
        })
      ]);
      iconStyles.push(iconStyle);
      return point;
      })()
    """%clean_e(e) for e in arrows])

    if len(arrows) > 0:
        for f in ['arrow_blue.png']:
            shutil.copyfile(os.path.join(dir_path,f),os.path.join(os.getcwd(),f))
    return html%(",".join(markersHtml),centre[1],centre[0],zoom)
        

html = """
<!DOCTYPE html>
<html>
  <head>
    <title>OSM Markers</title>
    <link rel="stylesheet" href="https://openlayers.org/en/v4.0.1/css/ol.css" type="text/css">
    <!-- The line below is only needed for old environments like Internet Explorer and Android 4.x -->
    <script src="https://cdn.polyfill.io/v2/polyfill.min.js?features=requestAnimationFrame,Element.prototype.classList,URL"></script>    
    <script src="https://openlayers.org/en/v4.0.1/build/ol.js"></script>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <style>
#map {
  position: relative;
}

#info {
  position: absolute;
  height: 1px;
  width: 1px;
  z-index: 100;
}

.tooltip.in {
  opacity: 1;
  filter: alpha(opacity=100);
}

.tooltip.top .tooltip-arrow {
  border-top-color: white;
}

.tooltip-inner {
  border: 2px solid white;
}
    </style>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
  </head>
  <body>
    <div id="map" class="map"><div id="info"></div></div>
    <script>
      var iconStyles = [];
      var styles = [];
      
      var vectorSource = new ol.source.Vector({
        features: [%s]
      });

      var stylesFunction = function(feature, resolution) {
        var scale = 2;
        for(var iconStyle in iconStyles) {
            iconStyle.setScale(scale);
        }
        return styles;
      }
      
      var map = new ol.Map({
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            new ol.layer.Vector({
                source: vectorSource,
                //style: stylesFunction
            })            
        ],
        target: document.getElementById('map'),
        view: new ol.View({
          center: ol.proj.fromLonLat([%f,%f]),
          zoom: %d
        })
      });
      
var info = $('#info');
info.tooltip({
    animation: false,
    trigger: 'manual'
});

var displayFeatureInfo = function(pixel) {
    info.css({
        left: pixel[0] + 'px',
        top: (pixel[1] - 15) + 'px'
    });
    var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
    });
    if (feature) {
        info.tooltip('hide')
            .attr('data-original-title', feature.get('name'))
            .tooltip('fixTitle')
            .tooltip('show');
    } else {
        info.tooltip('hide');
    }
};

map.on('pointermove', function(evt) {
    if (evt.dragging) {
        info.tooltip('hide');
        return;
    }
    displayFeatureInfo(map.getEventPixel(evt.originalEvent));
});
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    with open("map.html","w") as f:
        points=[dict(lat=51.0666351,lon=13.7418938,name="Test"),dict(lat=51.0666351,lon=13.7418938,name="Test2")]
        circles=[dict(lat=51.0666351,lon=13.7418938,name="Test",r=5e3),dict(lat=51.0666351,lon=13.7418938,name="Test2")]
        points=[]
        lines=[dict(lat1=51.0666351,lon1=13.7418938,lat2=51.0666351,lon2=12.7418938,name="Test2")]
        lines=[]
        f.write(osmView(circles=circles,arrows=lines))
    
