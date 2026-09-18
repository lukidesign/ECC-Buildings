import test from 'node:test';
import assert from 'node:assert/strict';
import view from '../components/landscape/room-view.json' with {type:'json'};

test('camera is in the rear aisle and clear of the shell and UPS bank',()=>{
  assert.ok(view.eye[0]>-2.5 && view.eye[0]<5.5);
  assert.ok(view.eye[1]>-4.3 && view.eye[1]<-2.5);
  assert.ok(view.eye[2]>1.5 && view.eye[2]<2);
  assert.equal(view.target[0],view.eye[0]);
  assert.equal(view.target[2],view.eye[2]);
});
for(const [w,h] of [[1920,1080],[1366,768],[1280,720],[2180,1000],[960,768]]) {
  test(`whole cabinet row remains inside the default view at ${w}×${h}`,()=>{
    const verticalTangent=view.sensorWidthMm/(2*view.lensMm)/(w/h);
    const depth=3.26-view.eye[1];
    for(const x of [-5.5,5.5]) for(const z of [0,2.3]) {
      const u=.5+(x-view.eye[0])/(2*depth*verticalTangent*(w/h));
      const v=.5-(z-view.eye[2])/(2*depth*verticalTangent);
      assert.ok(u>.04 && u<.96,`horizontal edge ${u}`);
      assert.ok(v>.12 && v<.87,`vertical edge ${v}`);
    }
  });
}
test('LV switchgear hotspot is attached to its bank and lies in the initial view',()=>{
  assert.ok(view.hotspot[0]>-2.065 && view.hotspot[0]<5.445);
  assert.ok(view.hotspot[2]>0 && view.hotspot[2]<2.3);
  assert.ok(view.hotspot[1]>3.2 && view.hotspot[1]<3.4);
});
