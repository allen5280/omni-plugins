import cv2, numpy as np, sys
path,out,start,end,step,cols=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6])
Y0,Y1,X0,X1=900,1700,0,1078
CW,CH=262,194
c=cv2.VideoCapture(path); tiles=[]; i=0
while True:
    ok,f=c.read()
    if not ok: break
    if start<=i<end and (i-start)%step==0:
        if f.shape[1]==1080: f=f[:,1:1079]
        t=cv2.resize(f[Y0:Y1,X0:X1],(CW,CH))
        cv2.putText(t,str(i),(4,16),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
        tiles.append(t)
    i+=1
c.release()
while len(tiles)%cols: tiles.append(np.zeros((CH,CW,3),np.uint8))
rows=[np.hstack(tiles[r*cols:(r+1)*cols]) for r in range(len(tiles)//cols)]
cv2.imwrite(out,np.vstack(rows)); print(out,len(tiles))
