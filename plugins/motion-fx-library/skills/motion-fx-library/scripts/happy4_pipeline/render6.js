const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const J=(process.env.JOB_DIR||require('path').resolve(__dirname,'..')),plan=JSON.parse(fs.readFileSync(J+'/plan.json')),EN=JSON.parse(fs.readFileSync(J+'/en.json'));const L=plan.lines,T=plan.total_frames,SH=plan.shots;
const GOLD={0:['快樂','不用等好事發生','不用等'],2:['化學反應','','化學反應'],15:['不用下單','燒錢','燒錢'],28:['曬太陽','就有了','曬太陽'],44:['你隨時能開始','','隨時'],61:['感到','幸福快樂','幸福快樂'],74:['這四個開關','都不用錢','不用錢'],76:['把幸福快樂','傳出去','傳出去']},HIDE=new Set([6,20,45,62,56]);
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:2});await pg.goto('file://'+J+'/fx/fx3.html');
const all=L.map(l=>l.text).join('');
await pg.evaluate(a=>Promise.all(a.map(([f,t])=>document.fonts.load(f,t))),[['700 63px "Noto Sans TC"',all],['900 84px "Noto Serif TC"',all],['900 102px "Noto Serif TC"',all],['500 39px "Noto Sans TC"',EN.join('')+'Aa'],['400 40px "Playfair Display"',EN.join('')+'No. 1 — Earn it, and save your first pot of gold.']]);
const es=await pg.evaluate(()=>{const c=document.createElement('canvas').getContext('2d');c.font='400 100px "Playfair Display"';return 864/c.measureText('No. 1 — Earn it, and save your first pot of gold.').width*100});console.log('EN title size',es.toFixed(2));
const mk=d=>{fs.rmSync(d,{recursive:true,force:true});fs.mkdirSync(d)};const bd=J+'/band',td=J+'/tband';mk(bd);mk(td);const cache={};
const shot=async(dir,key,fx,p,t,clip)=>{const k=dir+key;if(!cache[k]){await pg.evaluate(([fx,p,t])=>window.renderFrame(fx,p,t,1),[fx,p,t]);const fn=`${dir}/k_${key}.png`;fs.writeFileSync(fn,await pg.screenshot({type:'png',omitBackground:true,clip}));cache[k]=fn}return cache[k]};
const R=L.map(l=>[Math.round(l.s*24),Math.round(l.e*24)]);const CB={x:0,y:1290,width:1080,height:250},CT={x:0,y:0,width:1080,height:720};
const gi=Object.keys(GOLD).map(Number).sort((a,b)=>a-b);const TR={};
gi.forEach((i,k)=>{const s=R[i][0],e=R[i][1],sh=SH.find(x=>x.f0<=e-1&&e-1<x.f1);let end=Math.max(e,Math.min(s+46,sh.f1));if(k+1<gi.length)end=Math.min(end,R[gi[k+1]][0]);end=Math.min(end,T);TR[i]=[s,end];console.log('title',i,GOLD[i][0]+'/'+GOLD[i][1],s,e,end)});
let n=0;for(let f=0;f<T;f++){let i=-1;for(let k=0;k<L.length;k++)if(f>=R[k][0]&&f<R[k][1]){i=k;break}
 let fn;if(i<0||HIDE.has(i)||GOLD[i]!==undefined)fn=await shot(bd,'blank','sub',{zh:''},0,CB);else fn=await shot(bd,`s${i}`,'sub',{zh:L[i].text,en:EN[i]},9,CB);
 fs.linkSync(fn,`${bd}/${String(f).padStart(5,'0')}.png`);
 let ti=-1;for(const j of gi)if(f>=TR[j][0]&&f<TR[j][1]){ti=j;break}
 let tn;if(ti<0)tn=await shot(td,'blank','title',{l1:''},0,CT);else{const G=GOLD[ti],k=f-TR[ti][0],rem=TR[ti][1]-f,ld=(R[ti][1]-R[ti][0])/24,nn=(G[0]+G[1]).length,kmax=Math.ceil((.45+Math.min(.075,.5*ld/nn)*nn)*24),kk=Math.min(k,kmax),o=rem<=5?rem/6:1;
  tn=await shot(td,`t${ti}_${kk}_${o.toFixed(2)}`,'title',{l1:G[0],l2:G[1],em:G[2],en:EN[ti],es,ld,out:o},kk/24,CT)}
 fs.linkSync(tn,`${td}/${String(f).padStart(5,'0')}.png`);n++}
console.log('frames',n,'unique',Object.keys(cache).length);await b.close()})().catch(e=>{console.error('ERR',e.message.split('\n')[0]);process.exit(1)});
