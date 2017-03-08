def randstr(length):
   return ''.join(choice("  %s"%string.lowercase) for i in range(length))
   
def randdate():
    return datetime.datetime.fromordinal(randint(733624,736245))
    
def randbool():
    return randint(0,1)==0

import decimal, sys
def readTable(db, table, key=None, **xargs):
        """ transform table form database to dict[key] -> {x:[], y:[]} """
        query = "SELECT * FROM %s"%(table)
        db.query(query)
        d=dict()
        dKey=0
        while True:
            r = db.cursor.fetchone()
            if r is None: break
            if key is not None: 
                dKey = r[key]
            if dKey not in d:
                d[dKey] = dict([(k,[]) for k,v in xargs.items()])
            for k, v in xargs.items():
                value = r[v]
                if isinstance(value, decimal.Decimal):
                    value = float(value)
                d[dKey][k].append(value)
        if len(d) == 0: 
            sys.stderr.write("Warning: readTable() returns empty dict.\n")
        return d

        
from collections import OrderedDict
def readTableComplete(db, table, keyColumnName="key"):
        """ transform table form database to dict[key] -> {x:[], y:[]} """
        query = "SELECT * FROM %s"%(table)
        db.query(query)
        d=OrderedDict()
        while True:
            r = db.cursor.fetchone()
            if r is None: break
            r = dict(r)
            dKey = r.pop(keyColumnName, 0)
            if dKey not in d:
                d[dKey] = dict([(k,[]) for k,v in r.items()])
            for k, value in r.items():
                if isinstance(value, decimal.Decimal):
                    value = float(value)
                d[dKey][k].append(value)
        if len(d) == 0: 
            sys.stderr.write("Warning: readTable() returns empty dict.\n")
        return d
        
#def readTableComplete(db, table, vars):
#    return readTable(db,table,**dict([(var,var) for var in vars]))
    
