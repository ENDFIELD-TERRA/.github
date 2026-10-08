"""Selected D: contour ground, cropped/faded glyph companions and a glyph wall.

The user's reference supplies composition, not bitmap material. All artwork is
generated as vector geometry and real font outlines, with a GIF projection.
"""
from pathlib import Path
import json
import math
import hashlib
import numpy as np
import contourpy
from PIL import Image, ImageDraw, ImageChops, PngImagePlugin
from drawing import Art, BLACK, YELLOW, WHITE, glyph_path
from geometry import projection, style

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'
OUT.mkdir(parents=True,exist_ok=True)
W,H=1440,970
PAPER='#ddddda'
ANIMATION_FRAMES=280
FRAME_DURATION_MS=90
GIF_FRAME_STEP=5

def contour_ground(a):
    x=np.linspace(0,514,160);y=np.linspace(0,H,240)
    u,v=np.meshgrid((x-257)/225,(y-485)/255)
    z=(1.15*np.exp(-((u-.3)**2/.45+(v+.85)**2/.6))
       +.83*np.exp(-((u+.75)**2/.65+(v-1.1)**2/.48))
       -.65*np.exp(-((u-1.0)**2/.6+(v-.4)**2/.5))
       +.12*np.sin(u*2.4+v*1.4)+.08*v)
    contours=contourpy.contour_generator(x=x,y=y,z=z,name='serial')
    count=0
    for i,level in enumerate(np.linspace(float(z.min())+.04,float(z.max())-.04,11)):
        for points in contours.lines(float(level)):
            a.line([(float(px),float(py)) for px,py in points],'#f5f5f2',2 if i%4==0 else 1)
            count+=1
    return count

def clipped_glyph_companion(a,text,x,y,width=120,height=702):
    # The actual glyph bounding box, rather than its em square, defines 100%.
    em=110
    advance=sum(glyph_path('sarkaz',ch)[1]/glyph_path('sarkaz',ch)[2]*em+3 for ch in text)
    source=Art(math.ceil(advance)+20,190,None)
    source.text(8,144,text,em,BLACK,'sarkaz',3)
    x0,y0,x1,y1=source.image.getbbox()
    strip=source.image.crop((x0,y0,x1,y1)).transpose(Image.Transpose.ROTATE_270)
    strip=strip.resize((width,height),Image.Resampling.LANCZOS)
    mask=Image.new('L',(width,height));alpha=np.zeros((height,width),dtype=np.uint8)
    for column in range(width):
        t=column/width
        opacity=.78 if t<=.25 else max(0,.78*(.5-t)/.25)
        alpha[:,column]=round(opacity*255) if t<.5 else 0
    mask=Image.fromarray(alpha)
    combined=ImageChops.multiply(strip.getchannel('A'),mask)
    a.image.paste(strip,(x,y),combined);a.draw=ImageDraw.Draw(a.image)
    ident='slogan-'+str(x)
    a.parts.append(
        f'<defs><linearGradient id="{ident}-fade"><stop offset="0" stop-color="white" stop-opacity="0.78"/>'
        '<stop offset="0.25" stop-color="white" stop-opacity="0.78"/>'
        '<stop offset="0.5" stop-color="white" stop-opacity="0"/>'
        '<stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient>'
        f'<mask id="{ident}-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}">'
        f'<rect width="{width}" height="{height}" fill="url(#{ident}-fade)"/></mask>'
        f'<clipPath id="{ident}-clip"><rect width="{width/2}" height="{height}"/></clipPath></defs>'
        f'<g transform="translate({x} {y})" clip-path="url(#{ident}-clip)" mask="url(#{ident}-mask)">'
        f'<g transform="scale({width/(y1-y0):.8f} {height/(x1-x0):.8f}) matrix(0 1 -1 0 {y1} {-x0})">'
        +''.join(source.parts)+'</g></g>')

def glyph_wall(a):
    wall=Art(W,H,None)
    rows=[
        (1022,128,'FRONTIER',102,'#2e2e2a',9),
        (1135,884,'TERRA',128,'#2b2b28',12),
    ]
    for x,y,text,size,color,tracking in rows:wall.text(x,y,text,size,color,'sarkaz',tracking)
    clip=Image.new('L',(W,H));ImageDraw.Draw(clip).rectangle((530,0,W,H),fill=255)
    mask=ImageChops.multiply(wall.image.getchannel('A'),clip)
    a.image.paste(wall.image,(0,0),mask);a.draw=ImageDraw.Draw(a.image)
    a.parts.append('<defs><clipPath id="right-wall"><rect x="530" y="0" width="910" height="970"/></clipPath></defs><g clip-path="url(#right-wall)">'+''.join(wall.parts)+'</g>')

def composition():
    a=Art(W,H,PAPER)
    count=contour_ground(a)
    a.rect(530,0,910,H,BLACK);a.rect(514,0,16,H,YELLOW)
    # Full-width companion = 120px. Only 60px is exposed, ending in opacity zero.
    clipped_glyph_companion(a,'OVER THE FRONTIER',203,136)
    clipped_glyph_companion(a,'INTO THE FRONT',446,216,height=702)
    for i,ch in enumerate('跨越边境'):a.text(35,268+i*171,ch,164,BLACK,'zh')
    for i,ch in enumerate('直至前线'):a.text(278,347+i*171,ch,164,BLACK,'zh')
    glyph_wall(a)
    return a,count

def palette():
    values=[255,250,0,221,221,218,25,25,25,245,245,240]
    for i in range(252):
        n=round(i*255/251);values.extend([n,n,n])
    p=Image.new('P',(1,1));p.putpalette(values);return p

def main():
    base,contours=composition();frames=[];dots=[];pal=palette()
    front=Art(W,H,None)
    front.text(575,137,'TERRA',106,YELLOW,'sarkaz',9)
    front.text(575,953,'WELCOME HOME',45,YELLOW,'sarkaz',7)
    for frame in range(ANIMATION_FRAMES):
        img=base.image.copy();draw=ImageDraw.Draw(img)
        for x,y,z in projection('gyroid',frame*math.tau/ANIMATION_FRAMES,(988,526,378),(.72,0,-.22)):
            if x<548 or x>1435:continue
            radius,color=style('gyroid',z)
            draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
            if frame==0:dots.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="{color}"/>')
        img.paste(front.image,(0,0),front.image)
        if frame==0:
            info=PngImagePlugin.PngInfo();info.add_text('Source','Selected D, procedural contours and 3D point geometry; real font outlines. See ATTRIBUTION.md.')
            img.save(OUT/'hero-static.png',pnginfo=info)
        frames.append(img.quantize(palette=pal,dither=Image.Dither.NONE))
    # Five times as many projected poses preserve the original display cadence.
    frames[0].save(OUT/'hero.webp',save_all=True,append_images=frames[1:],duration=FRAME_DURATION_MS,loop=0,lossless=True,quality=70,method=4)
    fallback=frames[::GIF_FRAME_STEP]
    fallback[0].save(OUT/'hero.gif',save_all=True,append_images=fallback[1:],duration=FRAME_DURATION_MS*GIF_FRAME_STEP,loop=0,optimize=False,disposal=1,comment=b'ENDFIELD-TERRA selected D. 25.2 second cycle. Font attribution: ATTRIBUTION.md')
    base.save_svg(OUT/'hero.svg',''.join(dots)+''.join(front.parts))
    result={'size':[W,H],'contour_paths':contours,'right_silhouette_rows':2,'point_scale':378,'companion_full_width':120,'companion_visible_width':60,'frames':ANIMATION_FRAMES,'frame_duration_ms':FRAME_DURATION_MS,'duration_ms':ANIMATION_FRAMES*FRAME_DURATION_MS,'gif_fallback_frames':len(fallback),'gif_frame_duration_ms':FRAME_DURATION_MS*GIF_FRAME_STEP,'files':{name:{'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name in ['hero.svg','hero.webp','hero.gif','hero-static.png']}}
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
