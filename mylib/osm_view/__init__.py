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

def _tget(t,i,default=None):
    """ return element #i from tuple t. If t[i] does not exist, return default. """
    try:
        return t[i]
    except IndexError:
        return default

def osmView(points=[], centre=(51.0666351,13.7418938), zoom=14, lines=[], arrows=[]):
    """
    points list, Coordinates [(lat float, lon float, name String, colour_as_hex String)]
    centre Coordinates
    zoom int
    lines list, [(lat1 float, lon1 float, lat2 float, lon2 float, name String, colour_as_hex String)]
    returns html String
    """
    
    markersHtml = []
    markersHtml.extend(["""
      (function (){
      var point = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([%f, %f])),
        name: "%s"
      });
      point.setStyle(new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
          color: '%s',
          crossOrigin: 'anonymous',
          src: 'https://openlayers.org/en/v4.0.1/examples/data/dot.png'
        }))
      }));
      return point;
      })()
    """%(e[1],e[0],unicode(_tget(e,2,"")).replace("\n","<br/>"),_tget(e,3,"#0099ff")) for e in points])
    markersHtml.extend(["""
      (function (){
      var point = new ol.Feature({
        geometry: new ol.geom.LineString([ol.proj.fromLonLat([%f, %f]),ol.proj.fromLonLat([%f, %f])]),
        name: "%s"
      });
      point.setStyle(new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '%s',
            width: 2
        })
      }));
      return point;
      })()
    """%(e[1],e[0],e[3],e[2],unicode(_tget(e,4,"")).replace("\n","<br/>"),_tget(e,5,"#0099ff")) for e in lines])
    markersHtml.extend(["""
      (function (){

      var start = ol.proj.fromLonLat([%f, %f])
      var end   = ol.proj.fromLonLat([%f, %f])
      var dx = end[0] - start[0];
      var dy = end[1] - start[1];
      var rotation = Math.atan2(dy, dx);
      
      var line = new ol.geom.LineString([start,end]);
      var point = new ol.Feature({
        geometry: line,
        name: "%s"
      });
      point.setStyle([new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '%s',
            width: 2
        }),
      }),
      new ol.style.Style({
            geometry: new ol.geom.Point(end),
            image: new ol.style.Icon({
              src: 'arrow_blue.png',
              anchor: [0.75, 0.5],
              rotateWithView: true,
              rotation: -rotation
            })
      })]);
      return point;
      })()
    """%(e[1],e[0],e[3],e[2],unicode(_tget(e,4,"")).replace("\n","<br/>"),_tget(e,5,"#0099ff")) for e in arrows])
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
      var vectorSource = new ol.source.Vector({
        features: [%s]
      });

      var map = new ol.Map({
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),
            new ol.layer.Vector({
                source: vectorSource,
                //style: styles
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
        points=[(51.0666351,13.7418938,"Test"),(51.0666351,13.7418938,"Test2")]
        points=[]
        lines=[(51.0666351,13.7418938,51.0666351,12.7418938,"Test2")]
        f.write(osmView(points=points,arrows=lines))
    
