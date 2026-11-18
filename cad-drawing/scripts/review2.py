import pymupdf, numpy as np, json, sys
from PIL import Image, ImageDraw
from scipy import ndimage as nd
def ras(path,dpi):
    p=pymupdf.open(path)[0]; pm=p.get_pixmap(dpi=dpi,colorspace=pymupdf.csGRAY)
    return np.frombuffer(pm.samples,dtype=np.uint8).reshape(pm.h,pm.w)
dpi=200; s=72/dpi
A=ras('p17.pdf',dpi); B=ras('p17-v9.pdf',dpi)
a=A<200; b=B<200
def regions(x,y,minpx):
    miss=x&~nd.binary_dilation(y,iterations=4)
    miss=nd.binary_opening(miss,iterations=1)
    lab,n=nd.label(nd.binary_dilation(miss,iterations=8))
    out=[]
    for i,sl in enumerate(nd.find_objects(lab)):
        px=int((miss[sl]&(lab[sl]==i+1)).sum())
        if px<minpx: continue
        out.append({'px':px,'sl':(sl[0].start,sl[0].stop,sl[1].start,sl[1].stop)})
    out.sort(key=lambda o:-o['px']); return out
def sheet(regs,name):
    tiles=[]
    for k,o in enumerate(regs[:30]):
        y0,y1,x0,x1=o['sl']; pad=40
        y0=max(0,y0-pad);x0=max(0,x0-pad);y1=min(A.shape[0],y1+pad);x1=min(A.shape[1],x1+pad)
        ca=Image.fromarray(A[y0:y1,x0:x1]).convert('RGB'); cb=Image.fromarray(B[y0:y1,x0:x1]).convert('RGB')
        sc=min(1,260/max(ca.width,ca.height)); sz=(max(1,int(ca.width*sc)),max(1,int(ca.height*sc)))
        ca=ca.resize(sz); cb=cb.resize(sz)
        t=Image.new('RGB',(540,290),'white'); t.paste(ca,(5,25)); t.paste(cb,(275,25))
        d=ImageDraw.Draw(t); d.text((5,5),f"#{k} px={o['px']} pt=({x0*s:.0f},{y0*s:.0f}) L=orig R=new",fill='red')
        d.line([(270,0),(270,290)],fill='blue')
        tiles.append(t)
    cols=3; rows=(len(tiles)+cols-1)//cols
    S=Image.new('RGB',(540*cols,290*max(rows,1)),'gray')
    for i,t in enumerate(tiles): S.paste(t,((i%cols)*540,(i//cols)*290))
    S.save(name)
m=regions(a,b,40); e=regions(b,a,40)
print('missing',len(m),'extra',len(e))
for tag,r in (('M',m),('E',e)):
    for k,o in enumerate(r[:30]):
        y0,y1,x0,x1=o['sl']; print(tag,k,o['px'],[round(v*s) for v in (x0,y0,x1,y1)])
sheet(m,'rev_missing.png'); sheet(e,'rev_extra.png')
