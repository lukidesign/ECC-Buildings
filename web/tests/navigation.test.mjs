import test from 'node:test';
import assert from 'node:assert/strict';
import { appPath, assetPath, pagesBase, parseLocation, paths } from '../components/landscape/navigation.ts';
for (const [scene,path] of Object.entries(paths)) {
  test(`direct route: ${scene}`,()=>assert.deepEqual(parseLocation(path),{scene,product:false}));
  test(`trailing slash: ${scene}`,()=>assert.deepEqual(parseLocation(path+'/'),{scene,product:false}));
}
test('legacy product deep link',()=>assert.deepEqual(parseLocation(paths.room,'?mc=low_voltage_mns_switchgear'),{scene:'room',product:true}));
test('product query never opens on another scene',()=>assert.equal(parseLocation(paths.city,'?mc=low_voltage_mns_switchgear').product,false));
test('unknown product stays on room',()=>assert.equal(parseLocation(paths.room,'?mc=unknown').product,false));
test('unknown route has a recoverable overview',()=>assert.deepEqual(parseLocation('/unknown'),{scene:'city',product:false}));
test('root opens overview',()=>assert.deepEqual(parseLocation('/'),{scene:'city',product:false}));

test('generic product deep link',()=>assert.deepEqual(parseLocation(paths.room,'?mc=low_voltage_switchgear'),{scene:'room',product:true}));
test('generic query never opens on another scene',()=>assert.equal(parseLocation(paths.city,'?mc=low_voltage_switchgear').product,false));
for (const [scene,path] of Object.entries(paths)) {
  test(`GitHub Pages deep link: ${scene}`,()=>assert.deepEqual(parseLocation(pagesBase+path+'/'),{scene,product:false}));
  test(`GitHub Pages navigation: ${scene}`,()=>assert.equal(appPath(path,pagesBase+'/buildings'),pagesBase+path));
}
test('GitHub Pages root opens overview',()=>assert.deepEqual(parseLocation(pagesBase+'/'),{scene:'city',product:false}));
test('GitHub Pages product query opens on deep link',()=>assert.deepEqual(parseLocation(pagesBase+paths.room,'?mc=low_voltage_switchgear'),{scene:'room',product:true}));
test('GitHub Pages assets use the repository prefix',()=>assert.equal(assetPath('room.webp',pagesBase+'/buildings'),pagesBase+'/assets/room.webp'));
test('local assets remain root-relative',()=>assert.equal(assetPath('room.webp','/buildings'),'/assets/room.webp'));
