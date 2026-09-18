import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { zh, LANGUAGE_STORAGE_KEY, LEGACY_LANGUAGE_STORAGE_KEY, readSavedLocale } from '../components/landscape/translations.ts';

const read = path => fs.readFileSync(new URL(path, import.meta.url), 'utf8');
const theme = read('../app/globals.css');
const css = read('../app/explorer.css');
const app = read('../components/landscape/landscape.tsx');
const colors = Object.fromEntries([...theme.matchAll(/--(brand(?:-[a-z-]+)?):\s*(#[a-f0-9]{6});/g)].map(m => [m[1],m[2]]));
function luminance(hex) {
  const values = hex.slice(1).match(/../g).map(v => parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return values[0]*.2126+values[1]*.7152+values[2]*.0722;
}
function contrast(a,b) { const x=luminance(a),y=luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); }

test('ECC palette matches the approved colors',()=>{
  assert.deepEqual(colors, {'brand':'#2563eb','brand-hover':'#1d4ed8','brand-strong':'#1e40af','brand-soft':'#eff6ff','brand-soft-hover':'#dbeafe'});
  assert.match(theme,/--primary:\s*var\(--brand\)/);
  assert.match(theme,/--ring:\s*var\(--brand\)/);
  assert.doesNotMatch(theme,/prefers-color-scheme:\s*dark/);
});
for(const [fg,bg] of [['brand','#ffffff'],['brand-hover','brand-soft'],['brand-strong','brand-soft-hover']]) {
  test(`ECC text contrast ${fg} on ${bg}`,()=>{
    const ratio=contrast(colors[fg],colors[bg]??bg);
    assert.ok(ratio>=4.5, `contrast ${ratio.toFixed(2)}`);
  });
}
test('interactive CSS has no old red or pink theme values',()=>{
  assert.doesNotMatch(css,/--red|red-rule|#(?:e73335|d62d32|ec393b|fbe1e2|fbe3e3|f7d4d5|e94548|ed4c4e|cf262a|d72b2e|9c1518|c92329|b91c22|f8eded)/i);
  for(const selector of ['.beacon','.language-switch button[aria-pressed="true"]','.destination.active','.brand-rule']) assert.ok(css.includes(selector));
});
test('bilingual display content is neutral and has no previous brands',()=>{
  assert.doesNotMatch(JSON.stringify(zh),/ABB|MNS|RunDo/i);
  assert.ok(zh['ECC Spatial Explorer']);
  assert.ok(zh['APPLICATION GUIDE']);
  // The existing, non-visible metadata marker ID stays stable for picking.
  assert.doesNotMatch(app.replace('room: "mns"','room: "legacy-marker"'),/ABB|MNS|RunDo|<sup>®/i);
});
test('no external product links or empty resource tab remain',()=>{
  assert.doesNotMatch(app,/https?:\/\/|ExternalLink|value="links"/);
  assert.match(app,/TabsTrigger value="guide"/);
  assert.match(app,/TabsContent value="guide"/);
});
test('favicon and document metadata use ECC blue identity',()=>{
  const icon=read('../public/favicon.svg');
  assert.match(icon,/#2563eb/);
  assert.match(read('../app/layout.tsx'),/Buildings \| ECC/);
});
test('new language key retains a legacy migration path',()=>{
  assert.equal(LANGUAGE_STORAGE_KEY,'ecc-language');
  assert.equal(LEGACY_LANGUAGE_STORAGE_KEY,'abb01-language');
  assert.match(read('../components/landscape/language.tsx'),/readSavedLocale\(localStorage\)/);
});

function storage(values, failWrite=false) {
  return {getItem:key=>values[key]??null,setItem:(key,value)=>{if(failWrite)throw Error('blocked');values[key]=value;}};
}
test('current ECC language wins over legacy language',()=>assert.equal(readSavedLocale(storage({'ecc-language':'en','abb01-language':'zh'})),'en'));
test('legacy language migrates without deleting the old preference',()=>{
  const values={'abb01-language':'zh'};
  assert.equal(readSavedLocale(storage(values)),'zh');
  assert.deepEqual(values,{'abb01-language':'zh','ecc-language':'zh'});
});
test('invalid new language falls back to valid legacy language',()=>assert.equal(readSavedLocale(storage({'ecc-language':'fr','abb01-language':'en'})),'en'));
test('read-only storage preserves the legacy preference in memory',()=>assert.equal(readSavedLocale(storage({'abb01-language':'zh'},true)),'zh'));
test('unavailable or invalid storage falls back safely',()=>{
  assert.equal(readSavedLocale({getItem:()=>{throw Error('blocked');},setItem:()=>{}}),null);
  assert.equal(readSavedLocale(storage({'ecc-language':'fr','abb01-language':'de'})),null);
});
