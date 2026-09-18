"""Independently authored ECC Buildings scene studies.

Run in an isolated Blender process, never against a live user scene.
All dimensions are inferred metres, Z up. Geometry is generated locally.
"""
import bpy, math, random, json, argparse, sys, time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
ROOM_VIEW=json.loads((ROOT/'web/components/landscape/room-view.json').read_text())
random.seed(784)
argsv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--scene", choices=["apartment","city","room","product"], default="apartment")
p.add_argument("--quality", choices=["gray","preview","final"], default="preview")
p.add_argument("--save-only", action="store_true")
p.add_argument("--view", default="main")
p.add_argument("--engine", default="CYCLES")
p.add_argument("--cpu", action="store_true", help="Use CPU when the platform panorama kernel is unavailable")
args = p.parse_args(argsv)

M = {}
def material(name, color, rough=.5, metal=0, noise=0, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if emit:
        bs.inputs["Emission Color"].default_value=(*color,1)
        bs.inputs["Emission Strength"].default_value=emit
    if noise:
        n=m.node_tree.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value=5 if name=="grass" else 90
        n.inputs["Detail"].default_value=3
        coord=m.node_tree.nodes.new("ShaderNodeTexCoord")
        m.node_tree.links.new(coord.outputs["Object"],n.inputs["Vector"])
        ramp=m.node_tree.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position=.18
        ramp.color_ramp.elements[0].color=(*(max(.005,c*(1-noise)) for c in color),1)
        ramp.color_ramp.elements[1].position=.82
        ramp.color_ramp.elements[1].color=(*(min(1,c*(1+noise)) for c in color),1)
        m.node_tree.links.new(n.outputs["Fac"],ramp.inputs[0])
        m.node_tree.links.new(ramp.outputs[0],bs.inputs["Base Color"])
        bump=m.node_tree.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.12; bump.inputs["Distance"].default_value=.025
        m.node_tree.links.new(n.outputs["Fac"],bump.inputs["Height"]); m.node_tree.links.new(bump.outputs[0],bs.inputs["Normal"])
    M[name]=m
    return m

def materials():
    for row in [
        ("white",(.79,.80,.79),.58,0,.06),("stone",(.56,.57,.55),.72,0,.12),
        ("concrete",(.69,.7,.69),.82,0,.09),("dark",(.026,.033,.035),.6,0,0),
        ("glass",(.04,.055,.06),.23,.25,.07),("silver",(.59,.62,.63),.28,.7,0),
        ("road",(.37,.39,.40),.86,0,.055),("paving",(.64,.65,.64),.84,0,.05),
        ("line",(.87,.87,.82),.8,0,0),("grass",(.135,.21,.046),.94,0,.44),
        ("soil",(.10,.076,.042),.98,0,.2),("bark",(.14,.095,.055),.95,0,.2),
        ("solar",(.047,.085,.15),.24,.32,0),("water",(.09,.20,.21),.17,.25,.16),
        ("red",(.64,.018,.014),.48,0,0),("yellow",(.82,.60,.035),.55,0,0),
        ("cabinet",(.62,.64,.63),.36,.22,.045),("cabinet_dark",(.29,.32,.32),.38,.35,0),
        ("epoxy",(.52,.56,.56),.48,0,.055),("green",(.05,.40,.15),.37,.1,0),
    ]:material(*row)
    for i,col in enumerate([(.14,.23,.042),(.21,.31,.066),(.27,.36,.087),(.09,.18,.025),(.33,.39,.11)]):material("leaf"+str(i),col,.88)
    material("paint",(.82,.83,.82),.23,.2)
    material("light",(.88,.94,1),.6,0,0,4)
    material("screen",(.025,.13,.16),.3,0,0,.25)

class Batch:
    def __init__(self,name):self.name=name;self.parts={}
    def add(self,mat,verts,faces):
        a,b=self.parts.setdefault(mat,([],[]));n=len(a);a.extend(verts);b.extend(tuple(n+i for i in f) for f in faces)
    def box(self,loc,size,mat="white",rot=0):
        x,y,z=loc;a,b,c=(v/2 for v in size);co,si=math.cos(rot),math.sin(rot)
        vv=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
        self.add(mat,vv,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    def cyl(self,loc,r,depth,mat="white",n=20,r2=None):
        if r2 is None:r2=r
        x,y,z=loc;vv=[]
        for zz,rr in [(z-depth/2,r),(z+depth/2,r2)]:
            vv += [(x+math.cos(i*2*math.pi/n)*rr,y+math.sin(i*2*math.pi/n)*rr,zz) for i in range(n)]
        self.add(mat,vv,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    def beam(self,a,b,r,mat="dark",n=8):
        a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=d.cross(Vector((0,1,0)))
        u.normalize();v=d.cross(u).normalized()
        vv=[tuple(c+r*(math.cos(i*2*math.pi/n)*u+math.sin(i*2*math.pi/n)*v)) for c in [a,b] for i in range(n)]
        self.add(mat,vv,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    def quad(self,verts,mat):self.add(mat,verts,[(0,1,2,3)])
    def finish(self,offset=(0,0,0),bevel=0):
        parent=bpy.data.objects.new(self.name,None);bpy.context.collection.objects.link(parent);parent.location=offset; parent["semantic_id"]=self.name
        for mat,(verts,faces) in self.parts.items():
            mesh=bpy.data.meshes.new(self.name+"."+mat);mesh.from_pydata(verts,[],faces);mesh.update()
            ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.data.materials.append(M[mat])
            if bevel and mat not in ["grass","water","glass"] and not mat.startswith("leaf"):
                mod=ob.modifiers.new("Manufactured edge highlights","BEVEL");mod.width=bevel;mod.segments=2
        return parent

def text(label,loc,size=.09,mat="dark",rotation=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(label,"FONT");cu.body=label;cu.size=size;cu.extrude=.0005;cu.align_x="LEFT"
    ob=bpy.data.objects.new(label,cu);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=rotation;cu.materials.append(M[mat])
    return ob

def windows(b,xs,y,z,h=2.15):
    for x,w in xs:
        b.box((x,y+.13,z+h/2),(w,.12,h),"glass")
        for xx in [x-w/2,x+w/2,x]:
            b.box((xx,y+.035,z+h/2),(.065,.22,h+.12),"dark")
        for zz in [z,z+h]:b.box((x,y+.02,zz),(w+.11,.23,.075),"dark")
        b.box((x,y-.06,z-.06),(w+.2,.42,.1),"white")

def apartment(origin=(0,0,0)):
    b=Batch("apartment")
    b.box((0,0,.16),(39,26,.32),"stone")
    # Two touching structural wings make the stepped front and one continuous building.
    for f in range(7):
        z=.34+f*3.15
        for cx,cy,w,d in [(-9.5,-1,17,24),(8.5,0,19,22)]:
            b.box((cx,cy,z+.18),(w,d,.36))
            b.box((cx,cy+d/2-.2,z+1.6),(w,.4,3.15))
        # Front ribbon windows, with genuine wall openings and deep spandrels.
        for cx,fw,front in [(-9.5,17,-13),(8.5,19,-11)]:
            b.box((cx,front+.18,z+.56),(fw,.36,.78))
            b.box((cx,front+.18,z+2.94),(fw,.36,.5))
            count=4 if cx<0 else 5; bw=fw/count
            for j in range(count+1):
                xx=cx-fw/2+j*bw;b.box((xx,front+.18,z+1.85),(.40,.36,2.4))
            windows(b,[(cx-fw/2+(j+.5)*bw,bw-.45) for j in range(count)],front,z+.96,1.73)
        # Enclosed core and circulation; side wall apertures on both returns.
        b.box((-.9,-1,z+1.7),(.45,24,2.9))
        for side in [-1,1]:
            sx=side*18
            side_y=-1 if side<0 else 0
            side_d=24 if side<0 else 22
            b.box((sx,side_y,z+.60),(.38,side_d,1.0))
            b.box((sx,side_y,z+2.91),(.38,side_d,.50))
            if side<0:b.box((sx,-11.9,z+1.8),(.38,2.6,2.5))
            b.box((sx,10.4,z+1.8),(.38,1.4,2.5))
            if side>0:b.box((sx,-10.85,z+1.8),(.38,.4,2.5))
            for yy in [-10.5,-6.5,-2.5,1.5,5.5,9.5]:b.box((sx,yy,z+1.7),(.38,.38,2.8))
            for yy in [-8.5,-4.5,-.5,3.5,7.5]:
                b.box((sx-side*.12,yy,z+1.82),(.10,3.6,1.83),"glass")
                for dy in [-1.8,0,1.8]:b.box((sx+side*.05,yy+dy,z+1.82),(.16,.065,1.91),"dark")
        # Alternating real balconies with slab, side returns and glass safety rails.
        if f>0:
            for x in [5.0,12.6]:
                y=-11.95-(.27 if f%2 else 0)
                b.box((x,y,z+.36),(3.25,2.25,.25))
                b.box((x,y-1.05,z+1.05),(3.1,.045,1.05),"glass")
                b.box((x,y-1.05,z+1.59),(3.25,.06,.05),"dark")
                for xx in [x-1.57,x+1.57]:
                    b.box((xx,y-.05,z+1.05),(.05,2.05,1.05),"glass")
                    b.box((xx,y-1.05,z+1.08),(.06,.06,1.1),"dark")
            for yy in [-7,2]:
                b.box((-19.04,yy,z+.36),(2.1,4.4,.24))
                b.box((-20.05,yy,z+1.05),(.06,4.35,1.10),"glass")
                b.box((-20.05,yy,z+1.6),(.06,4.4,.055),"dark")
    roof=.34+7*3.15
    b.box((-9.5,-1,roof+.05),(17.7,24.8,.28))
    b.box((8.5,0,roof+.05),(19.7,22.8,.28))
    # Setback top floor and terrace.
    b.box((0,1,roof+.3),(32,18,.35))
    for y in [-8,10]:
        b.box((0,y,roof+.52),(32,.28,.40))
        b.box((0,y,roof+2.91),(32,.28,.55))
        for x in [-16,-10.9,-6.5,-2.15,2.2,6.55,10.9,16]:b.box((x,y,roof+1.7),(.26,.28,2.6))
    for y in [-8.06,10.06]:
        b.box((0,y+.13,roof+1.7),(31.74,.06,2.25),"glass")
        windows(b,[(x,4.0) for x in [-13,-8.65,-4.3,.05,4.4,8.75,13.1]],y,roof+.5,2.2)
    for x in [-16.07,16.07]:
        b.box((x,1,roof+1.67),(.08,18,2.2),"glass")
        for zz,hh in [(roof+.52,.40),(roof+2.91,.55)]:b.box((x,1,zz),(.28,18,hh))
        for y in range(-7,11,3):b.box((x,y,roof+1.5),(.15,.08,2.0),"dark")
    b.box((0,1,roof+3.3),(33,19,.28))
    for y in [-8.45,10.45]:b.box((0,y,roof+3.62),(33,.18,.55))
    for x in [-16.45,16.45]:b.box((x,1,roof+3.62),(.18,19,.55))
    # Main roof rails and equipment, individually supported.
    for y in [-11.7,11.0]:
        b.beam((-17.8,y,roof+.23),(17.9,y,roof+.23),.027,"silver")
        for x in range(-17,19,3):b.beam((x,y,roof+.2),(x,y,roof+1.0),.023,"silver")
        b.beam((-17.8,y,roof+1),(17.9,y,roof+1),.025,"silver")
    top=roof+3.46
    for x in [-11,-6,-1,4,9]:
        for y in [-4.8,6.5]:
            b.box((x,y,top+.14),(3.8,1.9,.24),"silver")
            b.box((x,y,top+.3),(3.68,1.80,.065),"solar")
            for xx in [-1.3,0,1.3]:b.box((x+xx,y,top+.34),(.018,1.8,.015),"silver")
            for yy in [-.3,.3]:b.box((x,y+yy,top+.34),(3.68,.018,.015),"silver")
    for x in [-9,1,9]:
        b.box((x,1,top+.52),(3.1,2.0,.98),"cabinet")
        for dx in [-.8,.8]:
            b.cyl((x+dx,1,top+1.035),.60,.06,"dark",32)
            for j in range(12):
                a=j*math.pi/6;b.beam((x+dx,1,top+1.08),(x+dx+math.cos(a)*.53,1+math.sin(a)*.53,top+1.08),.014,"silver")
        b.box((x,3.2,top+.45),(1.4,2.6,.75),"silver")
    b.box((13,2,top+1.0),(3.1,3.2,2.0))
    b.box((13,2,top+2.04),(3.3,3.4,.14))
    # Entrance, canopy supported by slender columns, lobby glazing.
    b.box((9,-11.16,1.7),(3.0,.10,2.75),"glass")
    b.box((9,-12.0,3.15),(5.1,3.1,.22),"silver")
    for x in [6.6,11.4]:b.box((x,-13.4,1.65),(.13,.13,3.05),"silver")
    for x in [7.9,10.1]:b.box((x,-11.3,1.4),(.05,.05,.80),"silver")
    return b.finish(origin,bevel=.012)

def plantbed(b,loc,size):
    x,y,z=loc;w,d=size
    b.box((x,y,z+.13),(w,d,.26),"stone")
    b.box((x,y,z+.28),(w-.28,d-.28,.09),"soil")
    b.box((x,y,z+.48),(w-.44,d-.44,.45),"grass")

def tree_prototype(index=0):
    rnd=random.Random(183+index);b=Batch("tree_proto"+str(index))
    b.cyl((0,0,2),.16,4,"bark",10,r2=.065)
    for j in range(17):
        a=j*2.399;zz=rnd.uniform(3.3,6.2);rr=rnd.uniform(.8,2.2)
        tip=Vector((math.cos(a)*rr,math.sin(a)*rr,zz))
        start=Vector((0,0,zz*.56))
        b.beam(start,tip,.047,"bark",6)
        for k in range(7):
            q=tip+Vector((rnd.uniform(-.78,.78),rnd.uniform(-.78,.78),rnd.uniform(-.50,.8)))
            b.beam(tip,q,.014,"bark",5)
            for l in range(22):
                c=q+Vector((rnd.uniform(-.52,.52),rnd.uniform(-.52,.52),rnd.uniform(-.42,.42)))
                phi=rnd.random()*math.tau
                u=Vector((math.cos(phi),math.sin(phi),rnd.uniform(-.4,.4)))*rnd.uniform(.07,.15)
                v=Vector((-math.sin(phi),math.cos(phi),rnd.uniform(-.4,.4)))*rnd.uniform(.055,.1)
                b.add("leaf"+str(rnd.randrange(5)),[tuple(c+u),tuple(c+v),tuple(c-u),tuple(c-v)],[(0,1,2,3)])
    # Interior crown foliage gives depth; these are individual leaves, not green blobs.
    for j in range(3600):
        a=rnd.random()*math.tau;zz=rnd.uniform(-1,1);rr=(1-zz*zz)**.5*rnd.random()**.25
        c=Vector((math.cos(a)*rr*2.35,math.sin(a)*rr*2.15,4.65+zz*1.88))
        phi=rnd.random()*math.tau
        u=Vector((math.cos(phi),math.sin(phi),rnd.uniform(-.8,.8)))*rnd.uniform(.12,.20)
        v=Vector((-math.sin(phi),math.cos(phi),rnd.uniform(-.8,.8)))*rnd.uniform(.07,.13)
        b.add("leaf"+str(rnd.randrange(5)),[tuple(c+u),tuple(c+v),tuple(c-u),tuple(c-v)],[(0,1,2,3)])
    ob=b.finish();ob.hide_render=True
    for ch in ob.children:ch.hide_render=True
    return ob

TREE=[]
def tree(name,x,y,s=1):
    proto=TREE[int(abs(x+y))%len(TREE)]
    root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root);root.location=(x,y,.04);root.scale=(s,s,s);root.rotation_euler.z=(x+y)*.713
    for ch in proto.children:
        copy=bpy.data.objects.new(name+"."+ch.name,ch.data);bpy.context.collection.objects.link(copy);copy.parent=root
    return root

def car(b,x,y,angle=0,color="white"):
    def box(u,v,z,size,mat):
        xx=x+u*math.cos(angle)-v*math.sin(angle); yy=y+u*math.sin(angle)+v*math.cos(angle)
        b.box((xx,yy,z),size,mat,angle)
    paint="paint" if color=="white" else color
    def loft(profiles,mat):
        vv=[]
        for yy,ww,top in profiles:
            for xx,zz in [(-ww*.85,.32),(-ww,top-.17),(-ww*.89,top),(ww*.89,top),(ww,top-.17),(ww*.85,.32)]:
                vv.append((x+xx*math.cos(angle)-yy*math.sin(angle),y+xx*math.sin(angle)+yy*math.cos(angle),zz))
        n=6
        faces=[tuple(range(n-1,-1,-1)),tuple(range((len(profiles)-1)*n,len(profiles)*n))]
        faces +=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profiles)-1) for i in range(n)]
        b.add(mat,vv,faces)
    loft([(-2.0,.72,.59),(-1.73,.86,.72),(-.95,.87,.81),(.95,.86,.83),(1.67,.82,.75),(1.96,.69,.61)],paint)
    loft([(-1.06,.74,.79),(-.45,.69,1.30),(.78,.67,1.31),(1.43,.72,.78)],"glass")
    box(0,.19,1.33,(1.34,1.19,.048),paint)
    for u in [-.72,.72]:
        box(u,.18,1.03,(.047,.075,.55),paint)
        box(u,-.38,.82,(.21,.045,.07),"silver")
    for u in [-.86,.86]:
        for v in [-1.25,1.25]:
            c=(x+u*math.cos(angle)-v*math.sin(angle),y+u*math.sin(angle)+v*math.cos(angle),.38)
            dx,dy=.18*math.cos(angle),.18*math.sin(angle)
            b.beam((c[0]-dx,c[1]-dy,c[2]),(c[0]+dx,c[1]+dy,c[2]),.33,"dark",16)
            b.beam((c[0]+dx*.8,c[1]+dy*.8,c[2]),(c[0]+dx*1.02,c[1]+dy*1.02,c[2]),.20,"silver",16)
    for u in [-.57,.57]:
        box(u,-2.035,.56,(.40,.035,.13),"light")
        box(u,2.035,.6,(.36,.035,.10),"red")

def apartment_site(origin=(0,0,0),local=True):
    ox,oy,oz=origin;b=Batch("apartment_parcel")
    b.box((0,0,-.16),(100,90,.32),"grass")
    b.box((0,0,.01),(48,33,.09),"paving")
    # Real curb depth around the plot.
    for x in [-24,24]:b.box((x,-1,.13),(.2,33,.18),"white")
    b.box((0,-17,.13),(48,.20,.18),"white")
    for x in [-13,-5,2]:plantbed(b,(x,-14.8,.03),(5.0,1.45))
    plantbed(b,(22,1,.02),(2.0,21))
    if local:
        for y in [-27,31]:
            b.box((0,y,.025),(150,12,.06),"road")
            b.box((0,y-6.2,.065),(150,.24,.16),"concrete")
            b.box((0,y+6.2,.065),(150,.24,.16),"concrete")
            for x in range(-70,76,8):b.box((x,y,.065),(3.5,.10,.008),"line")
        for x in [-39,42]:
            b.box((x,0,.026),(10,100,.06),"road")
            for y in range(-46,51,8):b.box((x,y,.067),(.1,3.5,.008),"line")
        for y in [-31,-29.8,-28.6,-27.4,-26.2,-25,-23.8]:b.box((-31,y,.07),(6,.45,.01),"line")
        for x in range(-29,-19,2):b.box((x,-32,.071),(.7,6,.01),"line")
    else:
        b.box((0,-27,.031),(64,12,.062),"road")
        b.box((26,-40,.032),(12,20,.064),"road")
        for x in range(-26,29,8):b.box((x,-27,.068),(3.5,.1,.008),"line")
    for i,x in enumerate([-11,-7,-3,1,5]):
        b.box((x,-20,.05),(3.2,6.0,.05),"paving")
        for side in [-1,1]:b.box((x+side*1.57,-20,.08),(.07,6,.01),"line")
        car(b,x,-20,.12,color="white" if i!=2 else "silver")
        b.box((x,-16.8,.9),(.47,.37,1.78),"silver")
        b.box((x,-17.0,1.18),(.35,.045,.65),"dark")
        b.box((x,-17.031,1.35),(.25,.02,.21),"screen")
        b.beam((x+.28,-16.97,1.26),(x+.40,-16.98,.49),.035,"dark")
    if local:
        car(b,32,-27,math.pi/2)
        car(b,-3,31,math.pi/2,"silver")
        car(b,42,16,0)
    root=b.finish(origin)
    for i,(x,y) in enumerate([(-25,-12),(-26,6),(-22,19),(-9,20),(5,20),(24,16),(29,4),(27,-14),(-21,-23)]):
        tree("apt_tree"+str(i),ox+x,oy+y,random.uniform(.85,1.25))
    return root

def cabinet(b,x,y,z=0,w=.83,h=2.3,style=0):
    d=.77
    b.box((x,y,z+.065),(w+.055,d+.04,.13),"dark")
    b.box((x,y+d/2-.028,z+h/2), (w,.06,h),"cabinet_dark")
    for xx in [x-w/2+.035,x+w/2-.035]:b.box((xx,y,z+h/2),(.07,d,h),"cabinet")
    for zz in [z+.16,z+h-.05]:b.box((x,y,zz),(w,d,.075),"cabinet")
    front=y-d/2-.01
    b.box((x,front+.08,z+h/2),(w-.13,.03,h-.20),"cabinet_dark")
    if style==0:
        # Modular withdrawable compartments, each with seam and actuator.
        heights=[.30,.32,.34,.48,.59]
        zz=z+.20
        for i,hh in enumerate(heights):
            cz=zz+hh/2
            b.box((x,front,cz),(w-.13,.045,hh-.018),"cabinet")
            if i<3:
                for k in [-1,0,1]:
                    b.box((x+k*.135,front-.033,cz+.026),(.091,.03,.093),"dark")
                    b.box((x+k*.135,front-.052,cz+.026),(.026,.022,.060),"silver")
                b.box((x+.23,front-.041,cz-.066),(.076,.031,.038),"green")
                b.box((x-.23,front-.041,cz-.066),(.12,.02,.028),"line")
            else:
                b.box((x,front-.037,cz),(.27,.04,hh*.65),"dark")
                b.box((x,front-.066,cz),(.135,.03,hh*.42),"cabinet_dark")
                b.box((x+.065,front-.087,cz),(.032,.04,hh*.33),"silver")
            for xx in [-.27,.27]:b.box((x+xx,front-.03,cz+hh*.3),(.013,.018,.013),"silver")
            zz+=hh
    elif style==1:
        b.box((x,front,z+1.14),(w-.13,.045,2.10),"cabinet")
        b.box((x,front-.035,z+1.50),(.43,.05,.52),"dark")
        b.box((x,front-.065,z+1.55),(.31,.02,.23),"cabinet_dark")
        b.box((x,front-.09,z+1.34),(.11,.06,.11),"dark")
        for i in range(13):b.box((x,front-.03,z+.32+i*.027),(w-.28,.045,.010),"dark")
    else:
        b.box((x,front,z+1.15),(w-.13,.055,2.08),"cabinet")
        b.box((x-.10,front-.041,z+1.57),(.29,.04,.28),"dark")
        b.box((x-.10,front-.068,z+1.60),(.20,.013,.14),"screen")
        for i in range(3):b.box((x-.22+i*.125,front-.04,z+1.24),(.06,.035,.06),"green" if i!=2 else "red")
        for i in range(20):b.box((x,front-.03,z+.25+i*.024),(w-.28,.03,.008),"dark")
    # Full-height door frame, hinges, handle and asset marker.
    for xx in [x-w/2+.064,x+w/2-.064]:b.box((xx,front-.035,z+1.16),(.048,.065,2.15),"silver")
    for zz in [z+.18,z+2.20]:b.box((x,front-.035,zz),(w-.1,.065,.048),"silver")
    for zz in [z+.35,z+1.12,z+1.94]:b.box((x-w/2+.065,front-.067,zz),(.06,.035,.072),"cabinet_dark")
    b.box((x+w/2-.11,front-.091,z+1.15),(.033,.035,.15),"dark")
    b.box((x,front-.025,z+2.265),(w-.13,.025,.052),"red")
    b.box((x-.18,front-.036,z+2.13),(.20,.013,.048),"line")
    b.box((x+.22,front-.036,z+.76),(.082,.015,.081),"yellow")

def room():
    b=Batch("electrical_room_shell")
    b.box((0,0,-.13),(12,9,.26),"epoxy")
    for x in [-6,6]:b.box((x,0,1.95),(.28,9,4.1),"white")
    for y in [-4.5,4.5]:b.box((0,y,1.95),(12.3,.28,4.1),"white")
    b.box((0,0,4.05),(12.3,9.2,.22),"white")
    # Expansion joints in floor and perimeter skirting.
    for x in range(-6,7,2):b.box((x,0,.006),(.009,9,.008),"cabinet_dark")
    for y in [-4,-2,0,2,4]:b.box((0,y,.006),(12,.009,.008),"cabinet_dark")
    for x in [-5.84,5.84]:b.box((x,0,.09),(.025,9,.18),"cabinet_dark")
    for y in [-4.34,4.34]:b.box((0,y,.09),(12,.025,.18),"cabinet_dark")
    for x in [-5.0,-1.3,2.4,5.5]:
        b.box((x,4.15,1.91),(.35,.35,3.8))
        b.box((x,-4.16,1.91),(.35,.33,3.8))
    for y in [-3.7,3.7]:
        b.box((0,y,3.5),(11.8,.42,.13),"silver")
        for yy in [y-.20,y+.20]:b.box((0,yy,3.65),(11.8,.055,.24),"silver")
        for xx in range(-5,6):
            b.box((xx,y,3.73),(.03,.44,.022),"silver")
            b.box((xx,y,3.88),(.028,.028,.26),"silver")
        for dy in [-.1,0,.1]:b.box((0,y+dy,3.61),(11.7,.048,.048),"dark")
    # Rear service door, signage, outlets and full ceiling complete the panorama.
    b.box((-2.8,-4.32,1.16),(1.17,.07,2.31),"cabinet")
    for x in [-3.43,-2.17]:b.box((x,-4.29,1.23),(.10,.12,2.46),"silver")
    b.box((-2.8,-4.29,2.48),(1.36,.12,.10),"silver")
    b.box((-2.32,-4.24,1.1),(.035,.03,.2),"dark")
    b.box((-2.8,-4.2,2.69),(.62,.035,.17),"green")
    for x in [-4.5,-.2,4.6]:
        b.box((x,4.27,1.30),(.21,.08,.24),"cabinet")
        b.box((x,4.3,2.43),(.025,.04,1.95),"silver")
    for y in [-2.4,.5,3.0]:
        for x in [-3,2.8]:
            b.box((x,y,3.93),(1.5,.24,.08),"cabinet")
            b.box((x,y,3.88),(1.38,.19,.02),"light")
    b.finish(bevel=.008)
    cabinets=Batch("mns_bank")
    for i in range(9):cabinet(cabinets,-1.65+i*.835,3.75,style=0 if i<6 else 1)
    cabinets.finish(bevel=.005)
    left=Batch("mv_switchgear")
    for i in range(3):cabinet(left,-5.0+i*.97,3.75,w=.95,style=1)
    left.finish(bevel=.008)
    for i in range(2):
        s=Batch("ups_"+str(i));cabinet(s,-4.8+i*.88,-2.9,style=2);s.finish(bevel=.006)
    # Metering wall and fire extinguisher; no branded logo is fabricated.
    c=Batch("room_utilities")
    c.box((5.6,.4,1.65),(.25,1.0,.75),"cabinet")
    c.box((5.46,.4,1.7),(.045,.6,.38),"dark")
    c.cyl((4.6,-4.05,.78),.13,.65,"red",24)
    c.box((4.6,-4.05,1.16),(.12,.12,.13),"dark")
    c.beam((4.62,-4.0,1.15),(4.80,-4.0,.70),.025,"dark")
    c.finish(bevel=.005)
    for i in range(9):
        text("LV  /  "+str(i+1).zfill(2),(-1.97+i*.835,3.33,2.16),.047,rotation=(math.pi/2,0,0))
    # Rectangular soft emitters near ceiling plus controlled ambient fill.
    for x in [-3.8,0,3.8]:
        area("room_ceiling_"+str(x),(x,0,3.75),(x,0,0),180,4)

def product():
    b=Batch("mns_product")
    for i in range(5):cabinet(b,(i-2)*.835,0,style=0 if i<4 else 1)
    b.finish(bevel=.006)
    base=Batch("studio_floor");base.box((0,0,-.10),(200,200,.20),"white");base.finish()
    area("key",(-3,-4,6),(0,0,1),950,5)
    area("rim",(3,2,4),(0,0,1.2),700,4)

def tower(name,x,y,w,d,h,style="rect"):
    b=Batch(name)
    b.box((0,0,1.0),(w+8,d+8,2),"white")
    b.box((0,0,3),(w+3,d+3,4),"glass")
    floors=int(h/3.3)
    if style in ["round","oval"]:
        n=40
        for f in range(floors):
            zz=5+f*3.3;r=w/2*(1-.08*f/floors)
            # Elliptical ring with genuine slab thickness, front glass and mullions.
            for i in range(n):
                a=i*math.tau/n;aa=(i+1)*math.tau/n
                corners=[(r*math.cos(a),r*d/w*math.sin(a),zz),(r*math.cos(aa),r*d/w*math.sin(aa),zz),(r*math.cos(aa),r*d/w*math.sin(aa),zz+3.3),(r*math.cos(a),r*d/w*math.sin(a),zz+3.3)]
                b.quad(corners,"glass")
                b.beam(corners[0],corners[3],.06,"silver",5)
                b.beam(corners[0],corners[1],.12,"white",5)
        # The cap follows the actual last storey, not the unrounded requested h.
        actual_top=5+floors*3.3
        last_radius=w/2*(1-.08*(floors-1)/floors)
        # Elliptical cap matches the facade, including oval towers.
        verts=[(last_radius*1.025*math.cos(i*math.tau/n),last_radius*d/w*1.025*math.sin(i*math.tau/n),zz) for zz in [actual_top-.04,actual_top+.55] for i in range(n)]
        b.add("white",verts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    else:
        for f in range(floors):
            zz=5+f*3.3;t=f/max(floors-1,1)
            ww=w*(1-.28*t) if style=="taper" else w
            dd=d*(1-.12*t) if style=="taper" else d
            shift=(t*t*9 if style=="sweep" else 0)
            b.box((shift,0,zz+1.61),(ww,dd,3.22),"glass")
            b.box((shift,0,zz+.075),(ww+.25,dd+.25,.15),"white")
            for side in [-1,1]:
                for xx in range(1,int(ww/1.8)):
                    b.box((shift-ww/2+xx*ww/int(ww/1.8),side*(dd/2+.04),zz+1.6),(.055,.08,3.22),"silver")
                for yy in range(1,int(dd/2)):
                    b.box((shift+side*(ww/2+.04),-dd/2+yy*dd/int(dd/2),zz+1.6),(.08,.055,3.22),"silver")
            if style=="white":
                for xx in [-ww/2,ww/2]:b.box((xx,0,zz+1.6),(.8,dd+.4,3.3),"white")
                b.box((shift,-dd/2-.10,zz+1.5),(ww,.20,.40),"white")
        top=5+floors*3.3
        b.box((shift,0,top),(ww+.5,dd+.5,.7),"white")
        if style!="sweep":b.box((shift,0,top+1),(ww*.62,dd*.62,1.5),"cabinet")
        if style=="taper":
            b.beam((-w/2,-d/2-.16,5),(ww/2,-dd/2-.16,top),.6,"white")
            b.beam((w/2,-d/2-.16,5),(-ww/2,-dd/2-.16,top),.6,"white")
    root=b.finish((x,y,0))
    if style=="sweep":
        # Closed wedge plant enclosure transfers the sloping roof into the top slab.
        crown=Batch(name+"_roof_enclosure")
        xl,xr=shift-ww/2,shift+ww/2; yf,yb=-dd/2,dd/2
        bottom=top+.30; low,high=top+1.2,top+12.6
        def prism(x0,x1,y0,y1,z0,zf,zb,mat):
            crown.add(mat,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,zf),(x1,y0,zf),(x1,y1,zb),(x0,y1,zb)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
        prism(xl,xr,yf,yb,bottom,low,high,"glass")
        # Separate watertight 0.45m roof plate with a bounded 0.6m eave.
        slope=(high-low)/dd
        x0,x1,y0,y1=xl-.6,xr+.6,yf-.6,yb+.6
        zf,zb=low-.6*slope,high+.6*slope
        vv=[(x0,y0,zf),(x1,y0,zf),(x1,y1,zb),(x0,y1,zb)]
        crown.add("white",vv+[(a,b,c+.45) for a,b,c in vv],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
        for xx in [xl,xr]:
            crown.beam((xx,yf,bottom),(xx,yf,low),.16,"white")
            crown.beam((xx,yb,bottom),(xx,yb,high),.16,"white")
            crown.beam((xx,yf,low),(xx,yb,high),.16,"white")
            for j in range(1,7):
                yy=yf+dd*j/7;zz=low+slope*(yy-yf)
                crown.beam((xx,yy,bottom),(xx,yy,zz),.065,"silver")
        for j in range(1,10):
            xx=xl+ww*j/10;crown.beam((xx,yb,bottom),(xx,yb,high),.075,"silver")
        for j in range(1,12):crown.box((shift,yb+.035,bottom+j*.95),(ww,.07,.10),"silver")
        enclosure=crown.finish(bevel=.035);enclosure.parent=root
    return root

def low_building(name,x,y,w,d,floors,style="office"):
    b=Batch(name);fh=3.7
    b.box((0,0,.2),(w+2,d+2,.4),"paving")
    for f in range(floors):
        b.box((0,0,f*fh+fh/2+.4),(w,d,fh),"glass")
        b.box((0,0,f*fh+.5),(w+.3,d+.3,.3),"white")
        for xx in range(-int(w/2),int(w/2)+1,3):
            for yy in [-d/2,d/2]:b.box((xx,yy,f*fh+2),(.24,.30,fh),"white")
        for yy in range(-int(d/2),int(d/2)+1,3):
            for xx in [-w/2,w/2]:b.box((xx,yy,f*fh+2),(.30,.24,fh),"white")
    b.box((0,0,floors*fh+.55),(w+1,d+1,.45),"white")
    for xx in [-w*.22,w*.22]:
        b.box((xx,0,floors*fh+1.25),(w*.22,d*.40,1.0),"cabinet")
        b.box((xx,0,floors*fh+1.78),(w*.23,d*.41,.08),"solar")
    b.box((0,-d/2-2,3.2),(6,4.2,.28),"white")
    for xx in [-2.8,2.8]:b.box((xx,-d/2-3.7,1.6),(.25,.25,3.2),"silver")
    return b.finish((x,y,0))

def ribbon(b,pts,width,z,mat):
    vv=[]
    for i,p0 in enumerate(pts):
        prev=Vector(pts[max(i-1,0)]);nxt=Vector(pts[min(i+1,len(pts)-1)]);t=(nxt-prev).normalized();norm=Vector((-t.y,t.x))
        for side in [-1,1]:vv.append((p0[0]+side*norm.x*width/2,p0[1]+side*norm.y*width/2,z))
    b.add(mat,vv,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)])

def city():
    ground=Batch("city_ground");ground.box((0,60,-.35),(6000,6000,.7),"grass");ground.finish()
    # Coherent orthogonal streets, partitioned into disjoint top tiles.
    r=Batch("street_network")
    roadx=[-236,-108,85,218];roady=[-132,-52,116,225]
    xs=sorted(set([-290,290]+[x+s for x in roadx for s in [-5.5,5.5]]));ys=sorted(set([-250,290]+[y+s for y in roady for s in [-5.5,5.5]]))
    for a,bb in zip(xs,xs[1:]):
        for c,d in zip(ys,ys[1:]):
            x=(a+bb)/2;y=(c+d)/2
            if any(abs(x-xx)<5.6 for xx in roadx) or any(abs(y-yy)<5.6 for yy in roady):
                r.box((x,y,.03),(bb-a,d-c,.06),"road")
    for y in roady:
        for x in range(-280,280,9):
            if all(abs(x-xx)>9 for xx in roadx):r.box((x,y,.067),(4,.14,.01),"line")
    for x in roadx:
        for y in range(-240,285,9):
            if all(abs(y-yy)>9 for yy in roady):r.box((x,y,.067),(.14,4,.01),"line")
    r.finish()
    river=Batch("river");pts=[(-210+i*1.6,95-i*2.65+math.sin(i*.07)*19) for i in range(115)]
    ribbon(river,pts,17,.011,"stone");ribbon(river,pts,14,.022,"water");river.finish()
    # Parcels: skyline in centre, the hero apartment in the front-left district.
    placements=[
      ("spire_centre",6,50,27,25,212,"round"),
      ("blade_west",-35,21,26,26,151,"taper"),
      ("white_spine",8,-9,28,24,169,"white"),
      ("split_crown",46,67,27,23,192,"sweep"),
      ("glass_edge",47,17,24,28,136,"taper"),
      ("terraced_office",-27,75,22,23,121,"rect"),
      ("hotel_tower",127,62,27,25,107,"round"),
      ("narrow_south",49,-21,17,19,82,"rect"),
    ]
    for row in placements:tower(*row)
    for x,y in [(-34,-22),(7,96),(53,103)]:low_building("podium_"+str(x),x,y,29,19,3)
    apartment((-78,-85,0));apartment_site((-78,-85,0),False)
    low_building("office_east",147,3,52,28,4)
    low_building("factory", -180,157,75,45,2)
    for i in range(5):low_building("residential_"+str(i),-188+(i%3)*25,-52+(i//3)*38,16,20,4+i%2)
    # Curved hospital wings, separate footprint and forecourt.
    for i in range(4):tower("hospital_"+str(i),-164+(i%2)*33,20+(i//2)*42,24,20,27+i*4,"round")
    # Campus with concentric slab bands and a low domed roof.
    c=Batch("campus")
    c.cyl((0,0,.13),32,.26,"stone",64)
    for f in range(4):
        c.cyl((0,0,f*3.4+2),31,3.3,"glass",64)
        c.cyl((0,0,f*3.4+.42),32,.32,"white",64)
    for i in range(64):
        a=i*math.tau/64;c.beam((31*math.cos(a),31*math.sin(a),.5),(31*math.cos(a),31*math.sin(a),13),.11,"white")
    for i in range(15):c.cyl((0,0,13+i*.37),32-i*1.7,.4,"white",64)
    c.finish((141,-87,0))
    for x,y in [(111,-37),(162,-35)]:low_building("campus_annex"+str(x),x,y,20,18,3)
    low_building("airport_terminal",-187,-170,75,22,2)
    low_building("airport_finger",-155,-203,16,33,1)
    ap=Batch("airport_apron");ap.box((-185,-203,.01),(93,46,.05),"paving")
    for xx in range(-225,-140,14):
        ap.box((xx,-204,.046),(.2,34,.01),"yellow")
        ap.box((xx,-216,.047),(8,.2,.01),"yellow")
    ap.finish()
    planes=Batch("aircraft")
    for px,py in [(-202,-208),(-169,-212)]:
        planes.beam((px,py-10,2.8),(px,py+9,2.8),1.0,"white",24)
        planes.beam((px,py-10,2.8),(px,py-12,2.8),.5,"white",16)
        for side in [-1,1]:
            planes.quad([(px,py-3,2.7),(px+side*12,py+3,2.7),(px+side*12,py+5,2.7),(px,py+3,2.7)],"white")
            planes.box((px+side*5,py+1,2.1),(1.2,3.5,1.2),"silver")
            planes.quad([(px,py+6,3),(px+side*4,py+9,3),(px+side*4,py+10,3),(px,py+9,3)],"white")
        planes.quad([(px,py+5,3),(px,py+8,6),(px,py+10,6),(px,py+10,3)],"white")
        for dx in [-1,1]:planes.beam((px+dx,py+2,.5),(px+dx,py+2,2.3),.17,"dark",8)
    planes.finish()
    t=Batch("airport_control")
    t.cyl((0,0,16),2.4,32,"white",16,r2=1.8)
    t.cyl((0,0,31.6),5,3.4,"glass",12,r2=5.6)
    t.cyl((0,0,33.5),5.8,.42,"white",12);t.finish((-241,-157,0))
    # Renewable-energy fields.
    e=Batch("renewables")
    for x in [118,145,172,199]:
        for y in [167,199]:
            e.cyl((x,y,20),.8,40,"white",14,r2=.43)
            e.box((x,y,40.4),(3.8,1.7,1.6),"white")
            hub=Vector((x,y-1.0,40.3))
            for j in range(3):
                a=j*math.tau/3+.18
                end=hub+Vector((math.sin(a)*15,0,math.cos(a)*15))
                mid=hub+Vector((math.sin(a)*7,0,math.cos(a)*7))
                off=Vector((math.cos(a)*.75,0,-math.sin(a)*.75))
                e.add("white",[tuple(hub),tuple(mid+off),tuple(end),tuple(mid-off)],[(0,1,2,3)])
    for x in range(117,211,9):
        for y in range(129,154,7):
            e.box((x,y,1.0),(7,3.5,.11),"solar")
            for xx in [-2.5,0,2.5]:e.box((x+xx,y,1.075),(.045,3.5,.018),"silver")
            for dx in [-2,2]:e.box((x+dx,y,.5),(.12,.12,1),"silver")
    e.finish()
    # Lanes include sparse cars and traversable parcel approaches.
    details=Batch("city_transport")
    for i in range(40):
        y=random.choice(roady);x=random.uniform(-220,210);car(details,x,y+2.0,math.pi/2,"white" if i%3 else "silver")
    details.finish()
    # Woodland perimeter and parks, excluding developed footprints/road envelopes.
    avoid=[(-55,70,-35,110),(-106,-50,-110,-65),(90,201,-123,94),(-227,-131,-225,-149),(-222,-130,122,191),(-197,-131,0,87),(-215,-137,-72,-4),(103,211,122,222)]
    count=0
    for i in range(1900):
        x=random.uniform(-295,300);y=random.uniform(-235,345)
        if any(a<x<b and c<y<d for a,b,c,d in avoid):continue
        if min(abs(x-a) for a in roadx)<9 or min(abs(y-a) for a in roady)<9:continue
        if any((x-a)**2+(y-b)**2<160 for a,b in pts):continue
        tree("city_tree_"+str(count),x,y,random.uniform(1.0,2.1));count+=1
    # Inferred distant undulating landscape, away from all built parcels.
    hills=Batch("distant_landscape")
    nx,ny=55,18;vv=[]
    for j in range(ny):
        y=310+j*22
        for i in range(nx):
            x=-660+i*25
            fade=min(j/5,1);fade=fade*fade*(3-2*fade)
            zz=.06+fade*(38*math.exp(-((x+290)/250)**2-((y-550)/250)**2)+29*math.exp(-((x-310)/300)**2-((y-670)/260)**2))
            vv.append((x,y,zz))
    hills.add("grass",vv,[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i) for j in range(ny-1) for i in range(nx-1)]);root=hills.finish()
    for ob in root.children:
        for polygon in ob.data.polygons:polygon.use_smooth=True

def camera(loc,target,lens=47,name="Camera"):
    cu=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler();cu.lens=lens;cu.clip_end=3000;cu.clip_start=.08
    bpy.context.scene.camera=ob
    return ob

def area(name,loc,target,power,size):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.shape="DISK";d.size=size
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()

def configure():
    scene=bpy.context.scene
    scene.render.engine=args.engine
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGB"
    scene.render.resolution_percentage=100
    scene.render.resolution_x=1280 if args.quality!="final" else 3840
    scene.render.resolution_y=720 if args.quality!="final" else 2160
    scene.render.film_transparent=False
    scene.view_settings.view_transform="AgX"
    scene.view_settings.look="AgX - Medium High Contrast"
    if scene.world is None:scene.world=bpy.data.worlds.new("Scene environment")
    scene.world.use_nodes=True;wn=scene.world.node_tree.nodes
    wn["Background"].inputs[0].default_value=(.70,.79,1,1)
    wn["Background"].inputs[1].default_value=.35 if args.scene in ["room","product"] else .24
    if args.scene not in ["room","product"]:
        sky=wn.new("ShaderNodeTexSky");sky.sky_type="MULTIPLE_SCATTERING";sky.sun_elevation=.73;sky.sun_rotation=2.1;sky.sun_disc=False;sky.air_density=1.15;sky.aerosol_density=.65
        scene.world.node_tree.links.new(sky.outputs[0],wn["Background"].inputs[0])
        light=bpy.data.lights.new("afternoon_sun","SUN");light.energy=2.6;light.angle=.10
        sun=bpy.data.objects.new("afternoon_sun",light);bpy.context.collection.objects.link(sun);sun.rotation_euler=(math.radians(24),math.radians(-31),math.radians(-38))
    if args.engine=="CYCLES":
        scene.cycles.samples=12 if args.quality=="gray" else (32 if args.quality=="preview" else 64)
        scene.cycles.use_denoising=True;scene.cycles.max_bounces=5
        scene.cycles.transparent_max_bounces=4
        prefs=bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type="METAL";prefs.get_devices()
            for d in prefs.devices:d.use=d.type=="METAL"
            if any(d.type=="METAL" for d in prefs.devices):scene.cycles.device="GPU"
            print("COMPUTE",[(d.name,d.type,d.use) for d in prefs.devices],flush=True)
        except Exception as exc:print("CPU fallback:",str(exc),flush=True)
        if args.cpu:scene.cycles.device="CPU"
    else:
        scene.render.engine="BLENDER_EEVEE"
    if args.quality=="gray":
        material("gray_override",(.55,.55,.55),.82)
        scene.view_layers[0].material_override=M["gray_override"]
    return scene

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials()
    if args.scene in ["apartment","city"]:
        TREE.extend([tree_prototype(0),tree_prototype(1)])
    if args.scene=="apartment":
        ground=Batch("site_ground");ground.box((0,0,-.35),(1000,1000,.7),"grass");ground.finish()
        apartment();apartment_site()
        low_building("neighbour",70,38,28,21,4)
        if args.view=="main":
            cam=camera((-69,-89.7,80),(0,0,12),51);cam.data.shift_x=-.04
        elif args.view=="top":cam=camera((0,0,110),(0,0,0),40)
        else:
            a=float(args.view)*math.pi/4;cam=camera((math.sin(a)*80,-math.cos(a)*80,42),(0,0,12),48)
    elif args.scene=="city":
        city()
        if args.view=="apartment":
            cam=camera((-147,-174.7,80),(-78,-85,12),51);cam.data.shift_x=-.04
        else:cam=camera((325,-520,396),(0,12,57),35)
    elif args.scene=="room":
        room();cam=camera(ROOM_VIEW['eye'],ROOM_VIEW['target'],ROOM_VIEW['lensMm'])
        if args.view=="panorama":
            cam.data.type="PANO";cam.data.panorama_type="EQUIRECTANGULAR"
    else:
        product();cam=camera((5.1,-8.9,3.8),(0,0,1.15),55)
    scene=configure()
    if args.scene=="room" and args.view=="panorama":
        scene.render.resolution_x=2048 if args.quality!="final" else 8192
        scene.render.resolution_y=scene.render.resolution_x//2
        scene.cycles.samples=24 if args.quality!="final" else 48
    if args.scene=="product":
        scene.render.resolution_x=1600 if args.quality=="final" else 960
        scene.render.resolution_y=1200 if args.quality=="final" else 720
    tag=args.scene+("-"+args.view if args.view!="main" else "")
    folder=ROOT/(".local/evidence/gray" if args.quality=="gray" else ".local/renders")
    folder.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(folder/(tag+("-preview" if args.quality=="preview" else "")+".png"))
    blend=ROOT/"models"/(tag+".blend")
    blend.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    # Coordinates derive from actual camera projection, not manually placed UI.
    markers=({"electrical-room":(-65,-83,27.3)} if args.view=="apartment" else {"apartment":(-78,-90,18)}) if args.scene=="city" else ({"electrical-room":(13,2,27.3)} if args.scene=="apartment" else {"mns":ROOM_VIEW['hotspot']})
    coords={}
    for key,xyz in markers.items():
        pt=world_to_camera_view(scene,cam,Vector(xyz));coords[key]={"world":xyz,"x":pt.x,"y":1-pt.y}
    meta={"scene":args.scene,"view":args.view,"quality":args.quality,"camera":{"position":list(cam.location),"rotation":list(cam.rotation_euler),"lens":cam.data.lens},"markers":coords,"resolution":[scene.render.resolution_x,scene.render.resolution_y],"objects":len(bpy.data.objects),"blender":bpy.app.version_string,"source":"independently authored; hidden geometry and metre scale inferred"}
    (folder/(tag+"-metadata.json")).write_text(json.dumps(meta,indent=2))
    print("SCENE_READY",json.dumps(meta),flush=True)
    if not args.save_only:
        bpy.ops.render.render(write_still=True)
        print("RENDER_COMPLETE",scene.render.filepath,flush=True)

if __name__=="__main__":main()
