import { createRequire } from 'node:module';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const sharp=require('sharp');
import { mkdir, copyFile, writeFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const out=path.join(root,'web/public/assets');await mkdir(out,{recursive:true});
const preview=process.argv.includes('--preview');
const manifest=[];
for(const name of ['city','apartment','room','product','room-panorama']) {
  const source=preview ? ({city:'city',apartment:'city-apartment-preview',room:'room-preview',product:'product-preview','room-panorama':'room-panorama-preview'}[name]) : name;
  const input=path.join(root,'assets',source+'.png');
  try { await stat(input); } catch { continue; }
  const result=await sharp(input).webp({quality:name==='room-panorama'?94:92,effort:5}).toFile(path.join(out,name+'.webp'));
  manifest.push({name,source:`assets/${source}.png`,output:`web/public/assets/${name}.webp`,width:result.width,height:result.height,bytes:result.size,origin:'Independent Blender model and Cycles render'});
  if(['city','apartment','room'].includes(name)) {
    const meta=preview&&name==='apartment'?'city-apartment':name;
    await copyFile(path.join(root,'assets',meta+'-metadata.json'),path.join(out,name+'-metadata.json'));
  }
}
await writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2));
console.log(manifest);
