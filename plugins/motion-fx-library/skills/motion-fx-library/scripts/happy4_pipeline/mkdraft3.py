import json, os, uuid, sys
sys.path.insert(0,os.environ.get('PYLIB','pylib'))
from copy import deepcopy
import pyJianYingDraft as draft
from pyJianYingDraft import Timerange, ClipSettings, TextStyle, TextBorder, DraftFolder, TrackType
NAME="happy4_v3"; FPS=24; PH="##RUNDIR##"; R1=os.environ.get('JOB_DIR',os.getcwd())+'/pack/happy4_1110'; R=os.environ.get('JOB_DIR',os.getcwd())+'/pack2/happy4_1110'; SPLIT=1087; END=2197
P=json.load(open(os.environ.get('JOB_DIR',os.getcwd())+'/plan.json')); EN=json.load(open(os.environ.get('JOB_DIR',os.getcwd())+'/en.json')); fu=lambda f:int(round(f*1e6/FPS)); us=lambda s:int(round(s*1e6))
root=os.environ.get('JOB_DIR',os.getcwd())+'/_jy3'; os.system('rm -rf '+root); os.makedirs(root)
sc=DraftFolder(root).create_draft(NAME,2160,3840,FPS,allow_replace=False)
sc.add_track(TrackType.video,"A-roll"); sc.add_track(TrackType.video,"B-roll FX",mute=True,relative_index=1)
sc.add_track(TrackType.text,"Subtitles ZH"); sc.add_track(TrackType.text,"Subtitles EN",relative_index=1); sc.add_track(TrackType.audio,"Music pad"); sc.add_track(TrackType.audio,"SFX",relative_index=1)
A=draft.VideoMaterial(R1+'/aroll_A.mp4'); A.path=PH+'/aroll_A.mp4'; B=draft.VideoMaterial(R1+'/aroll_B.mp4'); B.path=PH+'/aroll_B.mp4'; na=nb=0
for s in P['shots']:
    f0,f1=s['f0'],min(s['f1'],END)
    if f1>f0:
        m,off=(A,0) if f1<=SPLIT else (B,SPLIT); st=fu(f0); d=fu(f1)-st; ss=fu(f0-off); d=min(d,m.duration-ss); z=s.get('z',1)
        cs=ClipSettings(scale_x=z,scale_y=z,transform_y=-0.4*(z-1)) if (s['t']=='real' and z!=1) else ClipSettings()
        sc.add_segment(draft.VideoSegment(m,Timerange(st,d),source_timerange=Timerange(ss,d),volume=1.0,clip_settings=cs),"A-roll"); na+=1
    if s['t']=='b':
        m=draft.VideoMaterial(f"{R}/clips_v2/{s['id']}.mp4"); m.path=f"{PH}/clips_v2/{s['id']}.mp4"; st=fu(s['f0']); d=min(fu(s['f1'])-st,m.duration)
        sc.add_segment(draft.VideoSegment(m,Timerange(st,d),source_timerange=Timerange(0,d),volume=0.0),"B-roll FX"); nb+=1
ns=0
zh=TextStyle(size=12,bold=True,color=(0.91,0.9,0.91),align=1,auto_wrapping=True,max_line_width=0.9); en=TextStyle(size=6.5,bold=False,color=(0.84,0.82,0.82),align=1,auto_wrapping=True,max_line_width=0.9)
GOLD={0:('快樂','不用等好事發生'),2:('化學反應',''),15:('不用下單','燒錢'),28:('曬太陽','就有了'),44:('你隨時能開始',''),61:('感到','幸福快樂'),74:('這四個開關','都不用錢'),76:('把幸福快樂','傳出去')}
gz=TextStyle(size=17,bold=True,color=(0.945,0.85,0.64),align=1,auto_wrapping=True,max_line_width=0.9); ge=TextStyle(size=6.8,bold=False,color=(0.93,0.91,0.9),align=1,auto_wrapping=True,max_line_width=0.9)
for i,(l,t) in enumerate(zip(P['lines'],EN)):
    tr=Timerange(us(l['s']),us(l['e'])-us(l['s']))
    if i in GOLD:
        a1,a2=GOLD[i]; two=bool(a2)
        sc.add_segment(draft.TextSegment(a1+('\n'+a2 if two else ''),tr,style=deepcopy(gz),clip_settings=ClipSettings(transform_y=0.658 if two else 0.704),border=TextBorder(width=24)),"Subtitles ZH")
        sc.add_segment(draft.TextSegment(t,tr,style=deepcopy(ge),clip_settings=ClipSettings(transform_y=0.502 if two else 0.606),border=TextBorder(width=14)),"Subtitles EN")
        continue
    sc.add_segment(draft.TextSegment(l['text'],tr,style=deepcopy(zh),clip_settings=ClipSettings(transform_y=-0.48),border=TextBorder(width=20)),"Subtitles ZH")
    sc.add_segment(draft.TextSegment(t,tr,style=deepcopy(en),clip_settings=ClipSettings(transform_y=-0.552),border=TextBorder(width=14)),"Subtitles EN")
for nm,tk in (('music_pad','Music pad'),('sfx','SFX')):
    m=draft.AudioMaterial(f"{R}/audio/{nm}.m4a"); m.path=f"{PH}/audio/{nm}.m4a"; d=min(m.duration,fu(P['total_frames']))
    sc.add_segment(draft.AudioSegment(m,Timerange(0,d),volume=1.0),tk)
sc.save(); d=os.path.dirname(sc.save_path); mp=d+"/draft_meta_info.json"; meta=json.load(open(mp,encoding='utf-8'))
meta["draft_id"]=str(uuid.uuid4()).upper(); meta["draft_name"]=NAME; meta["tm_duration"]=sc.duration; json.dump(meta,open(mp,'w',encoding='utf-8'),ensure_ascii=False,indent=4)
R3=os.environ.get('JOB_DIR',os.getcwd())+'/pack3'; os.system('rm -rf '+R3); os.makedirs(R3+'/jianying_draft',exist_ok=True); os.system(f'cp -r {d} {R3}/jianying_draft/{NAME}')
txt=open(f'{R3}/jianying_draft/{NAME}/draft_content.json',encoding='utf-8').read()
print('dur',sc.duration/1e6,'aroll',na,'broll',nb,'strip',ns,'subs',len(EN)*2,'placeholders',txt.count(PH),'sandbox_paths',txt.count('/home/user'))
