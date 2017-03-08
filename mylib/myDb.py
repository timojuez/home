import re, sys
import psycopg2
import psycopg2.extras
import psycopg2.extensions

"""
Don't do:

sql = "INSERT INTO TABLE_A (COL_A,COL_B) VALUES (%s, %s)" % (val1, val2)
cursor.execute(sql)

Do:

sql = "INSERT INTO TABLE_A (COL_A,COL_B) VALUES (%s, %s)"
cursor.execute(sql, (val1, val2))
cursor.execute('SELECT * FROM stocks WHERE symbol=?', t)
"""

params = {
 'cursor_factory': psycopg2.extras.DictCursor,
}

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)


class DB(object):

    def __init__(self, database, commitOnClose=False, **xargs):
        super(DB, self).__init__()
        self._commitOnClose = commitOnClose
        #if len(xargs)==0: xargs=params
        args = params.copy()
        args.update(xargs)
        args["database"] = database
        self.database = database
        self.dbconnection = psycopg2.connect(**args)
        self.cursor = self.dbconnection.cursor()
        #self.execute = self.cursor.execute
        #self.cursor = self.dbconnection.cursor()
        
        
    def __del__(self):
        if self._commitOnClose:
            self.dbconnection.commit()
        self.dbconnection.close()
        
    def commit(self): self.dbconnection.commit()
    
    def rollback(self): self.dbconnection.rollback() 
    
    def execute(self, *args, **kwargs):
        """ 
        this function is being replaced by cursor.execute 
        """
        try:
            self.cursor.execute(*args,**kwargs)
        except Exception as e:
            if len(args)>0: print(args[0])
            raise

    query=execute


class ExtendedDB(DB):
    
    def update(self, table, where, returnkey=None, **x):
        """
        table String
        where Dict
        returnkey String or None
        x args key=val
        """
        keys=[] # keep order of keys and vals
        values=[]
        for k,v in x.items():
            keys.append(k)
            values.append(v)
        
        setq = ",".join(["%s=%s"%(k,"%s") for k in keys])
        wherekeys=[]
        for key, val in where.items():
            wherekeys.append(key)
            values.append(val)
        whereq = " AND ".join(["%s="%key+"%s" for key in wherekeys])
        q = "UPDATE %s SET %s WHERE %s"%(table,setq,whereq)
        args = tuple(values)
        if returnkey: q = "%s RETURNING %s"%(q, returnkey)
        self.query(q,args)
        if returnkey: 
            r = self.cursor.fetchone()
            return r[0]
        else: return None

    def save(self, table, returnkey=None, WHERE=None, **x):
        """ 
        Put data into database according schema of @table 
        @table String table name
        @x key=value, [key2=value2, [...]]
        """
        keys=[] # keep order of keys and vals
        values=[]
        for k,v in x.items():
            keys.append(k)
            values.append(v)
        
        q="INSERT INTO "+table+" ("+",".join(keys)+") SELECT %s"+\
        ",%s"*(len(x)-1)+""
        args = tuple(values)
        if WHERE: q = "%s WHERE %s"%(q, WHERE)
        if returnkey: q = "%s RETURNING %s"%(q, returnkey)
        self.query(q,args)
        if returnkey: 
            r = self.cursor.fetchone()
            return r[0]
        else: return None
        
    def execute_program(self, queries):
        queries = re.sub(re.compile("/\*.*?\*/",re.DOTALL ) ,"" ,queries) # remove all occurance streamed comments (/*COMMENT */) from string # FIXME: dont replace in string
        queries = re.sub(re.compile("--.*?\n" ) ,"" ,queries) # remove all occurance singleline comments (//COMMENT\n ) from string

        queries = queries.split(";")[:-1]
        for i,q in enumerate(queries):
            self.query(q)
            
    def get(self,*args,**xargs):
        self.query(*args,**xargs)
        r = self.cursor.fetchone()
        if r is None: return None
        return r[0]

    def execute_file(self, path):
        with open(path) as f:
            return self.execute_program(f.read())
        
