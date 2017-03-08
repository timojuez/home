"""
    Make long queries reusable and keep an easy overview!
    
    This activates and joins the results of a set of SQL queries.
    This helps to encapsulate and modularise parts of a query.
    
    It is very useful if you create a big table with plenty of joins where
    you also may want to normalise its values.
    
    Example:
        tables = dict(
            previousCustomers=dict(
                query='''
                    SELECT c.id, (SELECT count(*) FROM customers x WHERE x.id<c.id) AS count 
                    FROM customers c
                    GROUP BY c.id
                ''',
                join=['customers.id']
            ),
        )
        with TableModules(tables) as (select, join):
            # tables exist in this block
            db.sql('''
                SELECT customers.name, %(select)s -- selects name, previousCustomers, previousCustomers_float
                FROM customers %(join)s WHERE name like '%Maier%'
            '''%dict(select=select, join=join))
    
    tables: table_name -> {"query":sql_query, "join": list of another table's attributes to join on}
    The program will create temporary table featureTable_@table_name with the content of
        @sql_query: The query will be joined on postFeatureGeneration The normalised value
        of its attribute "count" will be added as a feature. Easy!
        In each query SELECT the attributes you want to do the left join on and the 
        attribute "count".
        @join: This is a list of strings. Each string contains an attribute of another table in the 
            form "tablename.attribute". An attribute with the same name has to appear in
            the SELECT statement in @sql_query.
        You can refer to the normalised feature later as @table_name+"_float"
        and to the absolute value as @table_name.
        Ignores table names that start with _

@author Timo
"""


class TableModules(object):
    def __init__(self, db, *args):
        self.db = db
        self.args = args
        self.tableNames = []
        
    def __enter__(self):
        return self.createFeatureTables(*self.args)

    def createFeatureTables(self, featureTables, create=True):
        """
        @featureTables dict
        @create Bool, if False, do not create the tables, assume they already 
            exist and just calculate the return variable
        @returns Str select, Str joins
        """
        select = ""
        joins = ""
        for i, (featureName, data) in enumerate(featureTables.items()):
            if featureName[0:1] == "_": continue
            tableName = "featureTable_%s"%featureName.replace(" ","_")
            self.tableNames.append(tableName)

            select += """
                COALESCE(%(table)s.count, 0 ) -- (SELECT avg(count) FROM %(table)s)
                    *1.0/(SELECT max(count) FROM %(table)s) AS %(name)s_float, -- default:(SELECT avg(count) FROM %(table)s)
                COALESCE(%(table)s.count, 0 ) 
                    AS %(name)s,
            """%dict(table=tableName, name=featureName)
            
            create_query = data["query"]
            joins += "\nLEFT JOIN %(table)s ON "%dict(table=tableName)
            joins += " AND ".join(["%(table)s.%(src)s=%(dest)s"%dict(
                        table=tableName,src=j.split(".",1)[1],dest=j)
                        for j in data["join"]
                        ])

            if create == False: continue
            print("\t(%d/%d) %s"%(i+1,len(featureTables),featureName))
            # create table
            self.db.query("DROP TABLE IF EXISTS %s"%tableName)
            try:
                self.db.query("CREATE TEMP TABLE %s AS (%s)"%(tableName,create_query))
            except Exception as e: 
                print(e)
                raise
        return select, joins

    def __exit__(self,*args):
        for table in self.tableNames: 
            self.db.query("DROP TABLE IF EXISTS %s"%table)

