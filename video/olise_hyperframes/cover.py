import os,shutil
S='/tmp/claude-0/-home-user-Fofana/adbce7f5-53e3-54dc-bd95-fa9317b2d1f9/scratchpad'
def panel(src, x0, y0, rh, pw, ph, left):
    s = ph / rh
    return f'''<div class="pan" style="left:{left}px;width:{pw}px;height:{ph}px"><img src="{src}" style="width:{1920*s:.1f}px;height:{1080*s:.1f}px;left:{-x0*s:.1f}px;top:{-y0*s:.1f}px"></div>'''
def make(name, W, H, ph, g, f, big, band_top, big_top, fs):
    d=f'{S}/{name}'; os.makedirs(d+'/assets',exist_ok=True)
    for a,b in [('olise/assets/A/0640.jpg','g.jpg'),('olise/assets/B/0670.jpg','f.jpg'),('olise/assets/fonts/poppins-800.woff2','p800.woff2')]:
        shutil.copy(f'{S}/{a}',f'{d}/assets/{b}')
    html=f'''<!doctype html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<style>@font-face{{font-family:'Poppins';font-weight:800;src:url(assets/p800.woff2) format('woff2');}}
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#000;font-family:'Poppins';font-weight:800}}
.pan{{position:absolute;top:0;overflow:hidden}} .pan img{{position:absolute}}
.sep{{position:absolute;top:0;left:{W//2-3}px;width:6px;height:{ph}px;background:#e3121b}}
.grad{{position:absolute;left:0;right:0;top:{int(ph*0.55)}px;bottom:0;background:linear-gradient(to bottom,rgba(0,0,0,0),#000 45%)}}
.band{{position:absolute;left:0;right:0;top:{band_top}px;text-align:center}} .band span{{display:inline-block;background:#e3121b;color:#fff;font-size:{int(fs*0.42)}px;padding:10px 34px;letter-spacing:1px}}
.big{{position:absolute;left:0;right:0;top:{big_top}px;text-align:center;color:#fff;font-size:{fs}px;line-height:1.0;text-shadow:0 6px 18px rgba(0,0,0,.7)}}
</style></head><body>
<div id="root" data-composition-id="cover" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">
{panel('assets/g.jpg',*g,W//2,ph,0)}
{panel('assets/f.jpg',*f,W//2,ph,W//2)}
<div class="sep"></div><div class="grad"></div>
<div class="band"><span>ITALIA 0-1 FRANCIA</span></div>
<div class="big">{big}</div>
</div></body></html>'''
    open(d+'/index.html','w').write(html)
    open(d+'/hyperframes.json','w').write(open(f'{S}/olise/hyperframes.json').read())
    open(d+'/meta.json','w').write('{"id":"%s","name":"%s"}'%(name,name))
make('cover916',1080,1920,1250,(748,220,650),(850,120,894),'¡PURA<br>CLASE!',1330,1450,170)
make('cover11',1080,1080,760,(690,260,600),(830,120,648),'¡PURA CLASE!',800,890,120)
