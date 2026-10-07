from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
ROOT=Path(__file__).resolve().parents[1]
FONTS=ROOT/'assets/fonts'
BLACK,YELLOW,WHITE='#191919','#fffa00','#f5f5f0'
font_paths={'display':FONTS/'Rajdhani-Bold.ttf','mono':FONTS/'IBMPlexMono-Regular.ttf','sarkaz':FONTS/'EndfieldByButan.ttf','zh':FONTS/'NotoSansSC-Display.ttf'}
tt={key:TTFont(path) for key,path in font_paths.items()}
glyphs={key:font.getGlyphSet() for key,font in tt.items()}
@lru_cache(maxsize=256)
def pillow_font(kind, size):
    return ImageFont.truetype(str(font_paths[kind]), size)

@lru_cache(maxsize=1024)
def glyph_path(kind, char):
    font = tt[kind]
    name = font.getBestCmap().get(ord(char))
    if name is None:
        raise ValueError(f'Missing glyph: {kind} {char!r}')
    pen = SVGPathPen(glyphs[kind])
    glyphs[kind][name].draw(pen)
    return pen.getCommands(), font['hmtx'][name][0], font['head'].unitsPerEm

class Art:
    def __init__(self, width, height, background):
        self.w, self.h = width, height
        self.image = Image.new('RGBA' if background is None else 'RGB', (width, height), background or (0,0,0,0))
        self.draw = ImageDraw.Draw(self.image)
        self.parts = [] if background is None else [f'<rect width="{width}" height="{height}" fill="{background}"/>']

    def rect(self, x, y, w, h, fill):
        self.draw.rectangle((x, y, x+w, y+h), fill=fill)
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')

    def line(self, points, fill, width=1):
        self.draw.line(points, fill=fill, width=width)
        coords = ' '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<polyline points="{coords}" fill="none" stroke="{fill}" stroke-width="{width}"/>')

    def polygon(self, points, fill):
        self.draw.polygon(points, fill=fill)
        coords = ' '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<polygon points="{coords}" fill="{fill}"/>')

    def text(self, x, baseline, value, size, fill=BLACK, kind='display', tracking=0):
        # Per-glyph advances keep the raster and outline layouts identical.
        for ch in value:
            path, advance, upm = glyph_path(kind, ch)
            scale = size/upm
            self.draw.text((x, baseline), ch, fill=fill, font=pillow_font(kind,size), anchor='ls')
            if path:
                self.parts.append(f'<path d="{path}" transform="translate({x:.3f} {baseline}) scale({scale:.6f} {-scale:.6f})" fill="{fill}"/>')
            x += advance*scale+tracking
        return x

    def circle(self, x, y, radius, fill):
        self.draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=fill)
        self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="{fill}"/>')

    def save_svg(self, path, extra=''):
        source=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img"><title>ENDFIELD-TERRA — geometric study</title><desc>Original point geometry. Sarkaz lettering outlined from EndfieldByButan by 罗醭坦, CC BY-NC 4.0.</desc>'+''.join(self.parts)+extra+'</svg>'
        path.write_text(source,encoding='utf-8')
