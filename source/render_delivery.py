"""Render both exterior endpoints and a continuous camera move from one scene."""
import bpy, math, json, sys, argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--motion',action='store_true');p.add_argument('--gray',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/city-apartment.blend'))
s=bpy.context.scene;c=s.camera
s.render.use_persistent_data=True
bpy.data.objects['split_crown'].location.x=46
if not any(ch.name.startswith('campus.stone') for ch in bpy.data.objects['campus'].children):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=32,depth=.26,location=(0,0,.13))
    foundation=bpy.context.object;foundation.name='campus.foundation';foundation.parent=bpy.data.objects['campus'];foundation.data.materials.append(bpy.data.materials['stone'])
# Keep the inferred distant terrain clear of the base surface: no coplanar patches.
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.parent and ob.parent.name=='distant_landscape':
        for v in ob.data.vertices:
            x,y=v.co.x,v.co.y;fade=max(0,min((y-310)/110,1));fade=fade*fade*(3-2*fade)
            v.co.z=.06+fade*(38*math.exp(-((x+290)/250)**2-((y-550)/250)**2)+29*math.exp(-((x-310)/300)**2-((y-670)/260)**2))
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG'
def pose(t):
    start=Vector((325,-520,396));end=Vector((-147,-174.7,80))
    aim0=Vector((0,12,57));aim1=Vector((-78,-85,12))
    v=t*t*(3-2*t);c.location=start.lerp(end,v)
    target=aim0.lerp(aim1,v);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
    c.data.lens=35+16*v;c.data.shift_x=-.04*v
def render(path):
    s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
if a.motion:
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.cycles.samples=16
    folder=ROOT/'work/transition';folder.mkdir(parents=True,exist_ok=True)
    for i in range(73):
        pose(i/72);render(folder/f'{i:04d}.png');print('FRAME',i,flush=True)
elif a.gray:
    s.render.resolution_x=800;s.render.resolution_y=450;s.cycles.samples=12
    mat=bpy.data.materials.new('review_gray');mat.diffuse_color=(.5,.5,.5,1);s.view_layers[0].material_override=mat
    folder=ROOT/'evidence/gray';folder.mkdir(parents=True,exist_ok=True)
    for i in range(8):
        theta=i*math.pi/4;c.location=(-78+math.sin(theta)*86,-85-math.cos(theta)*86,48)
        c.rotation_euler=(Vector((-78,-85,12))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=45;c.data.shift_x=0
        render(folder/f'apartment-orbit-{i}.png')
    c.location=(-78,-85,125);c.rotation_euler=(Vector((-78,-85,0))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=42
    render(folder/'apartment-top.png')
else:
    s.render.resolution_x=3840;s.render.resolution_y=2160;s.cycles.samples=64
    for name,t,markers in [('city',0,{'apartment':(-78,-90,18)}),('apartment',1,{'electrical-room':(-65,-83,27.3)})]:
        pose(t);render(ROOT/'assets'/f'{name}.png')
        points={}
        for key,xyz in markers.items():
            point=world_to_camera_view(s,c,Vector(xyz));points[key]={'world':xyz,'x':point.x,'y':1-point.y}
        meta={'scene':name,'resolution':[3840,2160],'markers':points,'camera':{'position':list(c.location),'rotation':list(c.rotation_euler),'lens':c.data.lens,'shift_x':c.data.shift_x},'source':'Shared independent city scene; same apartment geometry at both endpoints'}
        (ROOT/'assets'/f'{name}-metadata.json').write_text(json.dumps(meta,indent=2))
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source'/f'{name}-final.blend'))
