# Couvertures HyperFrames : geste (talonnade) + visage du buteur, dégradé noir, bandeau rouge, 2-3 mots énormes
def panel(img, x0, y0, h, pw, ph, left):
    s = ph / h
    return (f'<div class="p" style="left:{left}px;width:{pw}px;height:{ph}px">'
            f'<img src="assets/{img}" style="left:{-x0*s:.1f}px;top:{-y0*s:.1f}px;width:{1920*s:.1f}px;height:{1080*s:.1f}px" alt=""></div>')
def page(W, H, ph, big, band_top, title_top):
    pw = W // 2
    # geste : talon + ballon (b0818) ; visage : Bellingham (b1150). Cadre au-dessus du filigrane (y <= 898), hors bandeau LIVE.
    hg = 788; wg = hg * pw / ph
    hv = 560; wv = hv * pw / ph
    g = panel('b0818.jpg', min(1565 - wg, 1700 - wg / 2), 110, hg, pw, ph, 0) if False else panel('b0818.jpg', 1420 if W < H else 1690 - wg * 0.62, 110, hg, pw, ph, 0)
    v = panel('b1150.jpg', 790 - wv / 2, 330, hv, pw, ph, pw)
    return f'''<!doctype html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<style>
@font-face {{ font-family: Poppins; font-weight: 800; src: url(assets/fonts/poppins-latin-800-normal.woff2) format('woff2'); }}
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#000;font-family:Poppins;font-weight:800}}
.p{{position:absolute;top:0;overflow:hidden}} .p img{{position:absolute;max-width:none}}
#sep{{position:absolute;left:{pw-3}px;top:0;width:6px;height:{ph}px;background:#fff}}
#grad{{position:absolute;left:0;right:0;top:{ph-int(H*0.22)}px;height:{int(H*0.22)+2}px;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.7) 55%,#000 100%)}}
#band{{position:absolute;left:0;right:0;top:{band_top}px;display:flex;justify-content:center}}
#band div{{background:#e3171e;color:#fff;font-size:{int(big*0.36)}px;padding:10px 34px;border-radius:12px;letter-spacing:1px}}
#title{{position:absolute;left:0;right:0;top:{title_top}px;text-align:center;color:#fff;font-size:{big}px;line-height:.98;letter-spacing:-2px;text-shadow:0 6px 18px rgba(0,0,0,.6)}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">
<div id="art" class="clip" data-start="0" data-duration="1">{g}{v}<div id="sep"></div><div id="grad"></div>
<div id="band"><div>AEK 1-1 REAL MADRID</div></div>
<div id="title">¡QUÉ<br>TACONAZO!</div></div>
</div>
<script src="assets/gsap.min.js"></script><script>const tl=gsap.timeline({{paused:true}});tl.set("#art",{{opacity:1}},0);window.__timelines=window.__timelines||{{}};window.__timelines["main"]=tl;</script>
</body></html>'''
open('cover916/index.html','w').write(page(1080,1920,1350,150,1290,1400))
open('cover11/index.html','w').write(page(1080,1080,760,112,700,790))
