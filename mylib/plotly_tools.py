# -*- coding: utf-8 -*- 

exportmode=False
img_width=500
img_height=300

import plotly, os, datetime
from plotly.graph_objs import Scatter, Layout, Bar, Box, Figure
from mylib.sql_tools import readTableComplete as read


def _plotly(data, *args, **xargs):
    return _plotly2(Figure(data=data),*args,**xargs)

def _plotly2(figure, table, title=None, xTitle=None, yTitle=None, zTitle=None, filename=None, scene=None, xRange=None, yRange=None, 
            image=False,**layoutargs):
        #if image: ext="png"
        #else: ext="html"
        if exportmode:
            image=True;title='';layoutargs=dict(width=img_width,height=img_height) # vorher: 800x600
        ext="html"
        if filename is None: 
            dir_ = "plotly"
            if not os.path.exists(dir_): os.mkdir(dir_)
            filename = os.path.join(dir_,'plot_%s.%s'%(table,ext))
        print("%s -> %s"%(table,filename))
        if title is None: title=table
        layout = dict(title=title, xaxis=dict(), yaxis=dict(), **layoutargs)
        if scene: layout["scene"] = scene
        if xTitle: layout["xaxis"]["title"] = xTitle
        if yTitle: layout["yaxis"]["title"] = yTitle
        if xRange: layout["xaxis"]["range"] = xRange
        if yRange: layout["yaxis"]["range"] = yRange

        figure.layout.update(layout)
        #figure = Figure(
        #    data=data,
        #    layout=Layout(**layout)
        #)
        plotargs = dict(auto_open=False, filename=filename)
        if image:
            plotargs.update(dict(image="svg",image_width=img_width,image_height=img_height))
        plotly.offline.plot(figure, **plotargs)


def plot(db,table,mode='lines+markers',**xargs):
        data = read(db,table)
        scatterData = [
            Scatter(name=k,mode=mode,**v)
            for k,v in data.items()]
        return _plotly(
            scatterData,
            table,**xargs)

def plotAnnotated(db,table,**xargs):
    #data=read(db,table,keyColumnName="y")
    d={}
    db.query("SELECT * FROM %s"%table)
    for r in db.cursor.fetchall():
        d[(r["x"],r["y"])] = r["text"]
    x = sorted(set([x_ for x_,y_ in d.keys()]))
    y = sorted(set([y_ for x_,y_ in d.keys()]))
    z_text = [[d.get((x_,y_),"").encode("ascii",errors="replace")[:7] for x_ in x]
        for y_ in y]
    
    x = [x_.strftime("%d.%m. ") if isinstance(x_,datetime.datetime) else x_ for x_ in x]

    # z erstellen mit hilfe von z_text
    z_dict = dict([(v,u) for u,v in enumerate(set([v for u in z_text for v in u]))]) # value_z_text -> int
    z = [[z_dict[v] for v in u] for u in z_text]
    
    fig=plotly.tools.FigureFactory.create_annotated_heatmap(
        z,x=x,y=y,annotation_text=z_text,colorscale='Viridis'
    )
    return _plotly2(fig,table,**xargs)

def plotTorte(db, table, **xargs):
        data = read(db,table)
        return _plotly(
            [dict(
                labels=data[0]["x"],
                values=data[0]["y"],
                type="pie",
                ) 
            ],
            table, **xargs)
            
def plotBalken(db,table,**xargs):
        data = read(db,table)
        return _plotly(
            #[Bar(**data[0])],
            [Bar(name=(k if k!=0 else None), **v) for k,v in data.items()],
            table, **xargs)

def plotBoxplot(db,table, **xargs):
        data = read(db,table)
        return _plotly(
            [Box(
                x=v.get("x",None),
                y=v["y"],
                name=k) 
            for k,v in data.items()],
            table, **xargs)
    
def plot3D(db, table, xTitle=None, yTitle=None, zTitle=None, **xargs):
    data = read(db,table)
    fill_colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854']
    return _plotly([dict(
        #type='surface',
        type='scatter3d',
        mode='lines',
        surfaceaxis=2,
        line=dict(color='black',width=4),
        surfacecolor=fill_colors[i%len(fill_colors)],
        name=(k if k!=0 else None),
        **v
        ) for i, (k,v) in enumerate(data.items())],
        table, scene=dict(
            xaxis=dict(title=xTitle),
            yaxis=dict(title=yTitle),
            zaxis=dict(title=zTitle),
            camera=dict(eye=dict(x=-1.7, y=-1.7, z=0.5)),
        ), **xargs)
        

def plotBubbles(db, table, **xargs):
    data=read(db,table)
    return _plotly([
        Scatter(name=k,mode='markers',marker=dict(
            size=v.pop("s",None),
            #sizemode='diameter',sizeref=1,
        ),**v)
        for k,v in data.items()],
        table, **xargs)
        
        
        
