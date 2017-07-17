# -*- coding: utf-8 -*- 
'''
Math functions on gis calculations

The functions expect coordinates as type Decimal or DEG(float(...))

Authr: timo
'''

import sys, random, math
import numpy as np
from collections import OrderedDict
from decimal import *

STEP=Decimal('3e-6') # Berechnen aller Stellen alle @step°N bei der Wahrscheinlichkeitsdichte
# STEP >= COORD_MIN !

STEP_FIND_POLYGONS=8
POLYGON_BY_BB_MAX_TRIES = 5

POLYGON_CACHE=1500 # objects

COORD_MIN = Decimal('1e-7')
R_ERDE = 6371*1000 # Meter


# Float to degree
DEG = Context(prec=9).create_decimal
#DEG = lambda x: x

# Decimal to degree, for output of overpy
TYPE = lambda x: x # == Decimal
#TYPE = float

# int to real for division
DIV = lambda x: x

class Common(object):

    def __repr__(self):
        return "<%s %d>"%(self.__class__.__name__,self.wayId)
    
    def _wayLen(self, x_w1, y_w1, x_w2, y_w2):
        a = abs(y_w1-y_w2)
        #if x_w1==x_w2: return a
        b = abs(x_w1-x_w2)
        return math.sqrt(a**2+b**2)
    
    @classmethod
    def _w(self, x_w1, y_w1, x_w2, y_w2, x):
                """ y-Wert der Gerade w durch die zwei gegebenen Punkte an der Stelle x """
                # Gerade berechnen, w(x) = m*x+b
                if x_w2-x_w1 == 0: return None
                else: m = (y_w2-y_w1)/DIV((x_w2-x_w1))
                b = y_w2-m*x_w2
                #w=eval("lambda x:%f*x+%f"%(m,b)) #w=lambda x:m*x+b
                return DEG(m*x+b)
    
    @classmethod
    def _getAllWays(self, ways_raw, remove_vertical=False):
        """
        @ways_raw: List of ways, e.g. result by getBuildingNodes()["outer"]
        @remove_vertical: If True, remove all vertical straight lines with an infinite pitch
        returns: Für jeden Weg aus @ways_raw eine Liste der Geraden durch seine Strecken
            #in der Form [[(Gerade function, lat_1, lat_2)]]
            in der Form [[(lat_1, lon_1, lat_2, lon_2)]]
        """
        ways = []
        for way in ways_raw:
            strecken = [] # Liste der Geraden durch Strecken, Schema: [(lat1, lon1, lat2, lon2)]
            for i in xrange(len(way)-1):
                x_w1,y_w1 = way[i]
                x_w2,y_w2 = way[i+1]
                if remove_vertical and x_w2-x_w1 == 0: continue
                strecken.append((x_w1,y_w1,x_w2,y_w2))
            ways.append(strecken)
        return ways


def weighted_choice(a,*args,**xargs):
    choice = np.random.choice(range(len(a)),*args,**xargs)
    if isinstance(choice,np.ndarray):
        return [a[i] for i in choice]
    else: return choice


class Street(Common):

    def __init__(self,overpass,street,postcodeOrBB):
        if isinstance(postcodeOrBB, BB):
            ways_raw = Overpass.getWaysOfStreetByBB(overpass,street,postcodeOrBB)
        else:
            ways_raw = Overpass.getWaysOfStreetByPostcode(overpass,street,postcodeOrBB)
        self._init(ways_raw)
    
    def _init(self,ways_raw):
        """ 
        @ways_raw: Overpy query result that contains all nodes of this way
        """
        self.wayId = min(ways_raw.keys())
        self.strecken = [strecke for way in self._getAllWays(ways_raw.values(),remove_vertical=False) for strecke in way]
        streckenLengths = [self._wayLen(*strecke) for strecke in self.strecken]
        self.len = sum(streckenLengths)
        self._strecken_p = [x/float(self.len) for x in streckenLengths]

    def getRandomPoints(self,amount=1):
        """ Returns [(lat|lon)] of randomly picked spots in the street """
        ways = weighted_choice(self.strecken,size=amount,p=self._strecken_p)
        ret = []
        for x1,y1,x2,y2 in ways:
            if x1==x2:
                x=x1
                y=random.randrange(int(min(y1,y2)/COORD_MIN),int(max(y1,y2)/COORD_MIN))*COORD_MIN
            else:
                x = random.randrange(int(min(x1,x2)/COORD_MIN),int(max(x1,x2)/COORD_MIN))*COORD_MIN
                y = self._w(x1,y1,x2,y2,x)
            ret.append((x,y))
        return ret


class SimplePolygon(Common):
    """
    This is a polygon shaped house, optionally with one or more polygon shaped inner gardens.
    Considers multipolygons.
    
    Attributes:
        wayId int,
        f function lat->[lon],
        lat_min, lat_max, lon_min, lon_max
    """
    _cache=OrderedDict()
    
    def __new__(cls, wayId=None, *args, **xargs):
        if wayId in cls._cache:
            return cls._cache[wayId]
        if len(cls._cache) >= POLYGON_CACHE:
            cls._cache.popitem(False)
        p=super(SimplePolygon,cls).__new__(cls, wayId, *args, **xargs)
        if wayId is not None: cls._cache[wayId] = p
        return p
        
    def __init__(self, ways, wayId=None):
        self.wayId = wayId
        ways_ = self._getAllWays(ways, remove_vertical=True)
        del ways
        self._setPolygonFunction(ways_)
        
    def _setPolygonFunction(self, ways):
        """
        @ways: Result by _getAllWays()
        Returns an instance of Polygon.
        """
        allNodes = [(lat,lon) for way in ways for (lat_w1, lon_w1, lat_w2, lon_w2) in way for lat,lon in [(lat_w1,lon_w1),(lat_w2,lon_w2)]]
        Lat = [lat_ for lat_,lon_ in allNodes]
        Lon = [lon_ for lat_,lon_ in allNodes]
        self.lat_min = min(Lat)
        self.lat_max = max(Lat)
        self.lon_min = min(Lon)
        self.lon_max = max(Lon)
        del allNodes
        del Lat
        del Lon
        
        def f(lat_):
            """ Längengrade aller Geraden aus ws ausgeben für den Breitengrad lat_
                in der Form [lon].
            The functions result [lon] is ordered and its length is even.
            """
            lat_ = DEG(lat_)
            ret = []
            for strecken in ways:
                strecken_hier=[]
                for i in xrange(len(strecken)):
                    lat1, lon1, lat2, lon2 = strecken[i]
                    min_ = min(lat1,lat2)
                    max_ = max(lat1,lat2)
                    if lat_ < min_ or lat_ > max_: continue # nicht im def.-bereich
                    elif lat_==lat1 and lat1==lat2: # kommt z.z. nicht vor
                        # senkrechte behandeln
                        #strecken_hier.extend([lon1,lon2])
                        continue
                    elif lat_ == lat1: continue # nicht im def.-bereich
                    lon = self._w(lat1,lon1,lat2,lon2,lat_)
                    if lat_ == lat2: 
                        # if lat_ == lat2 and ist spitze Ecke: append doppelt
                        #                      (eigentlich: if ist keine stumpfe Ecke)
                        # Nachfolger ist g': if (lat1<lat2 and lat2'<lat2 or lat2<lat1 and lat2<lat2')
                        (lat21, lon21, lat22, lon22) = strecken[(i+1)%len(strecken)]
                        #lat21 == lat2, lon21==lon2
                        if not (lat1<lat2 and lat21<lat22 or lat1>lat2 and lat21>lat22):
                            strecken_hier.append(lon)
                    strecken_hier.append(lon)
                ret += strecken_hier
            if len(ret)%2 == 1:
                    values = "\n".join(["(%f, %f)"%(lat_,x) for x in sorted(ret)])
                    raise Exception("Polygon %s is not a complete graph. (Error at lat=%f: f(lat) contains %s)"%(self.wayId,lat_,values))
            return sorted(ret)
        self.f = f
    
    def isInPolygon(self, lat, lon):
        """ 
        Returns True if (lat|lon) is inside this.
        """
        if lat < self.lat_min or lat > self.lat_max \
                or lon < self.lon_min or lon > self.lon_max:
            return False
        
        Lon = self.f(lat)
        for i in range(len(Lon)/2):
                lon1 = Lon[i*2]
                lon2 = Lon[i*2+1]
                if lon >= lon1 and lon <= lon2: return True # “<=” instead of “<” to be more tolerant
        return False
    
    def getRandomPoints(self, amount=1):
        """ 
        Returns a list l with len(l) == amount. Schema of l: [(lat,lon)].
        """
        def d(lat_):
            ret = 0
            Lon = self.f(lat_)
            for i, e in enumerate(Lon):
                if i%2==0:
                    ret -= e
                else:
                    ret += e
            return ret

        #x=floatrange(self.lat_min,self.lat_max,STEP)
        Lat=[e*COORD_MIN+COORD_MIN for e in range(int(self.lat_min/COORD_MIN),int(self.lat_max/COORD_MIN),int(STEP/COORD_MIN))] # äquivalent zu: von -inf bis +inf
        P_lat = [d(lat_) for lat_ in Lat]
        P_sum = DIV(sum(P_lat))
        p_lat = [P/P_sum for P in P_lat]
        Lat_ap2 = np.random.choice(Lat, size=amount, p=p_lat)
        ret = []
        for lat_ap2 in Lat_ap2:
            Lon = self.f(lat_ap2)
            lon_ = random.randrange(int(d(lat_ap2)/COORD_MIN))*COORD_MIN
            lon_ap2 = None
            for i in xrange(len(Lon)/2):
                lon1 = Lon[2*i]
                lon2 = Lon[2*i+1]
                # lon1 < lon2 !
                lon_ += lon1
                if lon_ >= lon1 and lon_ < lon2:
                    lon_ap2 = lon_
                    break
                lon_ -= lon2
            if lon_ap2 is None: raise
            ret.append((lat_ap2,lon_ap2))
        return ret
        

class OSM_Polygon(SimplePolygon):

    def __init__(self, wayId, b):
        super(OSM_Polygon,self).__init__(wayId=wayId, ways=b["outer"]+b["inner"])

    @classmethod
    def getPolygonByCoords(cls, overpass, lat, lon):
        for p in Overpass.getBuildingsByBB(overpass, lat, lon):
            if p.isInPolygon(lat,lon):
                return p


Polygon = OSM_Polygon

        
class OSM_Error(Exception): 

    def __init__(self, msg, errorcode=0):
        super(OSM_Error,self).__init__(msg)
        self.errorcode=errorcode
        
        
from collections import namedtuple
Coord = namedtuple("Coord", ["lat","lon"])

class Overpass(object):
    """ Functions related to the overpass api """

    @classmethod
    def _concatWays(self, wayList):
        """ 
        Concat several OSM ways and return one way.
        Example:
            Way1 = Node1,Node2,Node3
            Way2 = Node3,Node4,Node1
            Input: [Way1,Way2]
            Output: Node1,Node2,Node3,Node4,Node1
        """
        starts = {}
        ends = {}
        for i,way in enumerate(wayList):
            starts[Coord(*way[0])] = starts.get(Coord(*way[0]),set()).union([i])
            ends[Coord(*way[-1])] = ends.get(Coord(*way[-1]),set()).union([i])

        wayIdx = 0
        way = wayList[wayIdx]
        merged = []
        for i in xrange(len(wayList)):
            if i==len(wayList)-1:
                merged.extend(way)
                break
            end = way[-1]
            merged.extend(way[:-1])
            
            successors = starts.get(Coord(*end),set()).difference([wayIdx])
            successorsReversed = ends.get(Coord(*end),set()).difference([wayIdx])
                
            if len(successors)==1:
                wayIdx = successors.pop()
                way = wayList[wayIdx]
            elif len(successorsReversed)==1:
                wayIdx = successorsReversed.pop()
                way = list(reversed(wayList[wayIdx]))
            else:
                raise Exception("Input error. Not exactly one possible successor at %s, %s."%end)
            pass
        return merged
    
    @classmethod
    def getBuildingsByBB(cls, overpass, lat, lon, max_tries=POLYGON_BY_BB_MAX_TRIES, step=STEP_FIND_POLYGONS, try_=1, output=None):
        """
        Returns an iterator of all instances of Polygon that are within @d meters from lat|lon.
            The bounding box increases each iteration until @max_tries*@step.
        """
        if output is None: output=set()
        bb=BB(lat,lon,try_*step)
        q = OVERPASS_QUERY%(bb.lat_min,bb.lon_min,bb.lat_max,bb.lon_max)
        ret = overpass.query(q)
        
        buildings=cls.getBuildingNodes(ret)
        for wayId,b in buildings.items():
            if wayId not in output:
                output.add(wayId)
                yield Polygon(wayId,b)
        if try_ < max_tries:
            sys.stdout.write(".");sys.stdout.flush()
            for e in cls.getBuildingsByBB(overpass,lat,lon,max_tries,step,try_+1,output): yield e

    @classmethod
    def getBuildingByRelationId(cls, overpass, id_):
        ret = overpass.query('(relation(%d););(._;>;);out body;>;<;(._;>;);out skel;'%id_)
        buildings = cls.getBuildingNodes(ret)
        return Polygon(*buildings.items()[0])

    @classmethod
    def getPolygonByRelationId(cls, overpass, id_):
        ret = overpass.query('relation(%d);(._;>;);out body;'%id_)
        b = cls.getWayNodes(ret)
        return Polygon(*b.items()[0])

    @classmethod
    def getPolygonByWayId(cls, overpass, id_):
        ret = overpass.query('way(%d);(._;>;);out body;'%id_)
        b = cls.getWayNodes(ret)
        return Polygon(*b.items()[0])
    
    @classmethod
    def getBuildingNodes(cls, ret):
        """
        returns inner and outer borders (OSM ways) of all buildings in the Overpass answer @ret
            as {building_id: dict(outer=[[(lat,lon)], ...], inner=[...])}.
            Building_id is the way_id of the outer edge of the building.
        """
        def condition(tags): return "building" in tags
        def relationkey(rel,outerWayId): return outerWayId
        return cls.getWayNodes(ret, relationkey_func=relationkey, condition_func=condition)
        
    @classmethod
    def getWayNodes(cls, ret, relationkey_func=None, condition_func=None):
        """
        returns inner and outer borders (OSM ways) of all relations in 
            overpass result @ret
            as {object_id: dict(outer=[[(lat,lon)], ...], inner=[...])}.
            Object_id is the way_id of the outer edge of the building or the relation id.
        relationkey_func(relation, outerWayId) is a function that is being called when setting
            the object_id. It maps relations to an id, additionally the function is given the
            relation's outerWayId.
            
        """
        import overpy
        def condition_func_default(tags): return True
        if condition_func is None: condition_func=condition_func_default
        def relationkey_func_default(rel,outerWayId): return rel.id
        if relationkey_func is None: relationkey_func=relationkey_func_default
        
        r={}
        relationWays = set()
        relations = list(ret.relations)
        while len(relations)>0: #for rel in ret.relations:
            rel = relations.pop()
            if not condition_func(rel.tags): continue
            d=dict(outer=[],inner=[])
            outerWayId = None
            wayIds = set()
            for m in rel.members:
                    try:
                        member = m.resolve()
                    except overpy.exception.DataIncomplete as e:
                        # Incomplete map. Do not add this relation to output
                        print("Warning: %s"%e)
                        outerWayId=None
                        break
                    if isinstance(member,overpy.Node): continue
                    elif isinstance(member,overpy.Relation) and m.role=='outline':
                        # A subrelation has the data. Do not add the current relation to output
                        relations.append(member)
                        outerWayId=None
                        break
                    elif not isinstance(member,overpy.Way):
                        print("Warning: relation %s does not consist of ways, but contains %s %s instead."%(rel.id,way.__class__.__name__,m.ref))
                        exit()
                    else:
                        way = member
                    #if "building" not in way.tags: continue

                    if m.role=='inner': role='inner'
                    elif m.role in ["outer","outline"]: role='outer'
                    else:
                        sys.stderr.write("Warning: Way %s's role '%s' cannot be handled. (relation %s)\n"%(way.id,m.role,rel.id))
                        continue
                    #if m.role not in ['inner','outer','outline']:
                    #    raise Exception("Way %s's role '%s' cannot be handled. (relation %s)"%(way.id,m.role,rel.id))

                    if role=='outer':
                        outerWayId = way.id
                    d[role].append([(TYPE(n.lat),TYPE(n.lon)) for n in way.nodes])
                    wayIds.add(way.id)
            if outerWayId is not None:
                if len(d["outer"]) > 1:
                    d["outer"] = [cls._concatWays(d["outer"])]
                key_ = relationkey_func(rel,outerWayId)
                r[key_] = d
                relationWays.update(wayIds)
        for way in ret.ways:
            if way.id in relationWays or not condition_func(way.tags): continue
            r[way.id]=dict(outer=[[(TYPE(n.lat),TYPE(n.lon)) for n in way.nodes]],inner=[])
        return r

    @classmethod
    def getWaysOfStreetByPostcode(self, overpass, street, postcode):
        """ Return all osm-ways that belong to a street as {wayId: [(lat,lon)]} """
        q = """[out:json];area[postal_code="%s"]; way(area)["name"~"%s"]; (._;>;); out body;"""%(postcode,street)
        ret = overpass.query(q)
        if len(ret.ways) == 0: raise OSM_Error("OSM has no streets listed as '%s', '%s'."%(street,postcode))
        return dict([(way.id, [(TYPE(n.lat),TYPE(n.lon)) for n in way.nodes]) for way in ret.ways])

    @classmethod
    def getWaysOfStreetByBB(self, overpass, street, bb):
        """ 
        @bb Instance of BB
        Return all osm-ways that belong to a street as {wayId: [(lat,lon)]} 
        """
        q = """[bbox:%f,%f,%f,%f][out:json];way["name"~"%s"]; (._;>;); out body;"""%(bb.lat_min,bb.lon_min,bb.lat_max,bb.lon_max,street)
        ret = overpass.query(q)
        if len(ret.ways) == 0: raise OSM_Error("OSM has no streets listed as '%s' in %s."%(street,repr(bb)))
        return dict([(way.id, [(TYPE(n.lat),TYPE(n.lon)) for n in way.nodes]) for way in ret.ways])


class BB(object):
    """
    Calculate a bounding box, given coordinates and a radius in meters.
    """

    def __init__(self, lat, lon, r):
        self.lat_max, self.lat_min, self.lon_max, self.lon_min = \
            self._calcBB(lat,lon,r)
            
    def __repr__(self):
        bb=self
        return "<BB Bounding box %f, %f, %f, %f>"%(bb.lat_min,bb.lon_min,bb.lat_max,bb.lon_max)

    def _calcBB(self, lat, lon, r):
        latDegreePerMeter = 360.0/2/math.pi/R_ERDE
        lonDegreePerMeter = lambda lat: math.degrees(1.0/(R_ERDE*math.cos(math.radians(lat))))

        lat = float(lat)
        lon = float(lon)
        
        d1 = latDegreePerMeter*r
        #d2 = math.degrees(math.acos((math.cos(float(r)/R_ERDE)-math.sin(math.radians(lat))**2)/math.cos(math.radians(lat))**2)) # dies ist der weg über den Großkreis. Besser Breitenkreis verwenden
        
        if lat > 0: latOuter=lat+d1 # d2 am breitengrad berechnen, der dichter am polarpol ist
        else: latOuter=lat-d1
        d2 = r*lonDegreePerMeter(latOuter)
        return (DEG(lat+d1),DEG(lat-d1),DEG(lon+d2),DEG(lon-d2))


def latDegree2meter(lat):
    return lat/(360.0/2/math.pi/R_ERDE)

def lonDegree2meter(lon,lat):
    return R_ERDE*math.cos(math.radians(lat))*math.radians(lon)


OVERPASS_QUERY="""[bbox:%f, %f, %f, %f][out:json];(node["building"];way["building"];relation["building"];);(._;>;);out body;>;<;(._;>;);out skel;"""

