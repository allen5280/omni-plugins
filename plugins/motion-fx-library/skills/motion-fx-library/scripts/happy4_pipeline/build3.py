import json, subprocess, math, os, sys, numpy as np, wave
P=json.load(open('plan.json')); FPS=24; S=P['segs']; J=os.environ.get('JOB_DIR',os.getcwd()); VD=P['voice_dur']; T=P['total_frames']
for i,m in enumerate(S): m['out_e']=S[i+1]['out_s'] if i+1<len(S) else VD
def src(t):
    for m in S:
        if m['out_s']-1e-9<=t<m['out_e']: return m['src_s']+(t-m['out_s'])
    return S[-1]['src_e']
bounds=sorted({math.ceil(m['out_s']*FPS-1e-6) for m in S[1:]})
os.makedirs('pieces3',exist_ok=True); lst=[]; jobs=[]
for sh in P['shots']:
    if sh['t']=='b': lst.append(f"{J}/clips3/{sh['id']}.mp4"); continue
    cuts=[sh['f0']]+[b for b in bounds if sh['f0']<b<sh['f1']]+[sh['f1']]
    for k in range(len(cuts)-1):
        a,b=cuts[k],cuts[k+1]; n=b-a; out=f"{J}/pieces3/{sh['id']}_{k}.mp4"; z=sh.get('z',1.0); ss=src(a/FPS+1e-4); cw,chh=int(2160/z)//2*2,int(3840/z)//2*2
        if sh.get('push') and len(cuts)==2: vf=f"fps={FPS},scale=w='trunc(2160*(1+0.07*n/{n})/2)*2':h=-2:eval=frame:flags=bicubic,crop=2160:3840:(iw-2160)/2:(ih-3840)*0.30"
        else: vf=f"fps={FPS},crop={cw}:{chh}:(iw-{cw})/2:(ih-{chh})*0.30,scale=2160:3840:flags=lanczos"
        vf+=",vignette=PI/4.6,format=yuv420p"
        jobs.append((['ffmpeg','-y','-loglevel','error','-ss',f"{ss:.4f}",'-i','in/talk.mp4','-vf',vf,'-frames:v',str(n),'-an','-c:v','libx264','-preset','veryfast','-crf','10','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-r',str(FPS),out],out,n)); lst.append(out)
open('concat3.txt','w').write(''.join(f"file '{p}'\n" for p in lst))
if 'pieces' in sys.argv:
    from concurrent.futures import ThreadPoolExecutor
    def run(j): r=subprocess.run(j[0],capture_output=True,text=True); return os.path.basename(j[1]),j[2],r.returncode
    with ThreadPoolExecutor(2) as ex:
        for o in ex.map(run,jobs): print(*o,flush=True)

T=P['total_frames']
fc=f"[0:v]format=yuv420p[v0];[2:v]format=rgba[b];[v0][b]overlay=0:2580:format=auto[vo];[1:a]apad=whole_dur={T/FPS:.3f}[a1];[a1][3:a][4:a]amix=inputs=3:normalize=0,alimiter=limit=0.89:level=false[ao]"
cmd=['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i','concat3.txt','-i','voice.wav','-framerate','24','-i','band/%05d.png','-i','music_pad.wav','-i','sfx.wav','-filter_complex',fc,'-map','[vo]','-map','[ao]','-c:v','libx264','-preset','medium','-crf','12','-pix_fmt','yuv420p','-profile:v','high','-r','24','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-ar','48000','-t',f'{T/FPS:.4f}','-movflags','+faststart','v3_master_h264.mp4']
json.dump(cmd,open('final3_cmd.json','w')); print('ok',len(lst))
