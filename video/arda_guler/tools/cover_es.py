import sys,os,shutil
S=sys.argv[1]
def make(name,W,H,panelH,fs,bannerTop,gbox):
    d=f'{S}/covers_es/{name}'; os.makedirs(d+'/assets/fonts',exist_ok=True)
    for f in ['hyperframes.json','package.json','meta.json']: shutil.copy(f'{S}/guler/{f}',d)
    shutil.copy(f'{S}/guler/assets/gsap.min.js',d+'/assets/')
    for f in ['poppins-800.woff2']: shutil.copy(f'{S}/guler/assets/fonts/'+f,d+'/assets/fonts/')
    shutil.copy(f'{S}/proj/frames/B/0476.jpg',d+'/assets/geste.jpg'); shutil.copy(f'{S}/proj/frames/B/0262.jpg',d+'/assets/visage.jpg')
    lw=int(W*0.56); rw=W-lw
    # crop geste: src box (x0,y0,x1,y1) mapped to panel lw x panelH (cover)
    def place(box,pw,ph):
        x0,y0,x1,y1=box; s=max(pw/(x1-x0),ph/(y1-y0)); cx,cy=(x0+x1)/2,(y0+y1)/2
        return f'width:{1920*s:.0f}px;height:{1080*s:.0f}px;left:{pw/2-cx*s:.0f}px;top:{ph/2-cy*s:.0f}px'
    g=place(gbox,lw,panelH); v=place((1325,70,1475,330),rw,panelH)
    html=f'''<!doctype html><html lang="es"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<script src="assets/gsap.min.js"></script><style>
@font-face{{font-family:"Poppins";font-weight:800;src:url(assets/fonts/poppins-800.woff2) format("woff2")}}
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#000;font-family:"Poppins"}}
.panel{{position:absolute;top:0;height:{panelH}px;overflow:hidden}}
.panel img{{position:absolute}}
#p1{{left:0;width:{lw}px}} #p2{{left:{lw}px;width:{rw}px;border-left:8px solid #e10600}}
#grad{{position:absolute;left:0;right:0;top:{int(panelH*0.45)}px;height:{H-int(panelH*0.45)}px;background:linear-gradient(to bottom,rgba(0,0,0,0) 0%,rgba(0,0,0,.85) 40%,#000 62%)}}
#banner{{position:absolute;left:50%;transform:translateX(-50%) rotate(-2deg);top:{bannerTop}px;background:#e10600;color:#fff;font-weight:800;font-size:{int(fs*0.42)}px;padding:10px 34px;border-radius:10px;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.6);letter-spacing:.02em}}
#title{{position:absolute;left:0;right:0;top:{bannerTop+int(fs*0.95)}px;text-align:center;color:#fff;font-weight:800;font-size:{fs}px;line-height:.95;text-shadow:0 6px 20px rgba(0,0,0,.8);letter-spacing:-.01em}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">
<div class="panel clip" id="p1" data-start="0" data-duration="1"><img src="assets/geste.jpg" style="{g}" alt="" /></div>
<div class="panel clip" id="p2" data-start="0" data-duration="1"><img src="assets/visage.jpg" style="{v}" alt="" /></div>
<div id="grad" class="clip" data-start="0" data-duration="1"></div>
<div id="banner" class="clip" data-start="0" data-duration="1">TURQUÍA 1-0 BÉLGICA</div>
<div id="title" class="clip" data-start="0" data-duration="1">¡QUÉ<br/>TIRO LIBRE!</div>
</div><script>const tl=gsap.timeline({{paused:true}});window.__timelines=window.__timelines||{{}};window.__timelines["main"]=tl;tl.seek(0);</script></body></html>'''
    open(d+'/index.html','w').write(html)
make('cover_9x16',1080,1920,1350,140,1300,(1000,280,1480,1000))
make('cover_1x1',1080,1080,700,120,630,(960,280,1400,920))
