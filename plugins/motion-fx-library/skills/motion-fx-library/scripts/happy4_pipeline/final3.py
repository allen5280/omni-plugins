import json,subprocess,sys,os
P=json.load(open('plan.json'));T=P['total_frames'];H=1132
def part(a,b,out):
    fc=(f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,format=yuv420p[v0];[1:v]format=rgba[b];[2:v]format=rgba[tb];"
        "[v0][b]overlay=0:2580:format=auto[v1];[v1][tb]overlay=0:0:format=auto,format=yuv420p[vo]")
    cmd=['ffmpeg','-y','-loglevel','error','-stats','-f','concat','-safe','0','-i','concat3.txt','-framerate','24','-start_number',str(a),'-i','band/%05d.png','-framerate','24','-start_number',str(a),'-i','tband/%05d.png',
         '-filter_complex',fc,'-map','[vo]','-frames:v',str(b-a),'-c:v','libx264','-preset','medium','-crf',os.environ.get('CRF','12'),'-pix_fmt','yuv420p','-profile:v','high','-r','24','-g','48','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-an',out]
    return subprocess.run(cmd).returncode
m=sys.argv[1]
if m=='A': sys.exit(part(0,H,os.environ.get('OA','v3_A.mp4')))
if m=='B': sys.exit(part(H,T,os.environ.get('OB','v3_B.mp4')))
if m=='mux':
    fa=f"[0:a]apad=whole_dur={T/24:.3f}[a1];[a1][1:a][2:a]amix=inputs=3:normalize=0,alimiter=limit=0.89:level=false[ao]"
    r=subprocess.run(['ffmpeg','-y','-loglevel','error','-i','voice.wav','-i','music_pad.wav','-i','sfx.wav','-filter_complex',fa,'-map','[ao]','-c:a','aac','-b:a','320k','-ar','48000','-t',f'{T/24:.4f}','v3_a.m4a']).returncode
    open('v3_list.txt','w').write("file 'v3_A.mp4'\nfile 'v3_B.mp4'\n")
    r|=subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i','v3_list.txt','-i','v3_a.m4a','-map','0:v','-map','1:a','-c','copy','-movflags','+faststart','v3_master_h264.mp4']).returncode
    sys.exit(r)
