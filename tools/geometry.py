import math
import numpy as np
_gyroid=None


def sampled_gyroid():
    global _gyroid
    if _gyroid is None:
        x,y,z=np.meshgrid(np.linspace(-math.pi,math.pi,66),np.linspace(-math.pi,math.pi,66),np.linspace(-math.pi,math.pi,66))
        keep=np.abs(np.sin(x)*np.cos(y)+np.sin(y)*np.cos(z)+np.sin(z)*np.cos(x))<.065
        _gyroid=np.stack([x[keep],y[keep],z[keep]],axis=1)/math.pi*.82
    return _gyroid

def projection(kind,phase,center,rotation):
    p=sampled_gyroid().copy()
    ax,ay,az=rotation[0],phase,rotation[2]
    rx=np.array([[1,0,0],[0,math.cos(ax),-math.sin(ax)],[0,math.sin(ax),math.cos(ax)]])
    ry=np.array([[math.cos(ay),0,math.sin(ay)],[0,1,0],[-math.sin(ay),0,math.cos(ay)]])
    rz=np.array([[math.cos(az),-math.sin(az),0],[math.sin(az),math.cos(az),0],[0,0,1]])
    p=p@rx.T@ry.T@rz.T;p=p[np.argsort(p[:,2])]
    cx,cy,s=center;persp=3.8/(4.2-p[:,2]*.25)
    return np.stack([cx+p[:,0]*s*persp,cy+p[:,1]*s*persp,p[:,2]],axis=1)

def style(kind,z):
    n=min(1,max(0,(z+1.5)/3));value=int(56+196*n)
    return .95+1.4*n,f'#{value:02x}{value:02x}{int(value*.97):02x}'
