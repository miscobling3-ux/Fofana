import sys
def col(img, rx, ry, rw, rh, cw, ch, left):
    s = cw / rw
    s2 = ch / rh
    s = max(s, s2)
    return (f'<div class="col" style="left:{left}px;width:{cw}px;height:{ch}px;'
            f'background-image:url(assets/img/{img});background-size:{1920*s:.1f}px {1080*s:.1f}px;'
            f'background-position:{-rx*s:.1f}px {-ry*s:.1f}px"></div>')
def page(W, H, cols, title_size, band_size, band_top, title_top):
    return f'''<!doctype html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<script src="lib/gsap.min.js"></script>
<style>
@font-face {{ font-family: "PoppinsHF"; font-weight: 800; src: url("assets/fonts/Poppins-800.woff2") format("woff2"); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#000; font-family:"PoppinsHF",sans-serif; }}
.col {{ position:absolute; top:0; background-repeat:no-repeat; }}
.split {{ position:absolute; top:0; left:{W//2-3}px; width:6px; height:{H}px; background:#ff1f1f; box-shadow:0 0 18px rgba(0,0,0,.6); }}
.grad {{ position:absolute; left:0; bottom:0; width:{W}px; height:{int(H*0.55)}px; background:linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,.78) 45%, #000 100%); }}
.band {{ position:absolute; left:0; top:{band_top}px; width:{W}px; text-align:center; }}
.band span {{ display:inline-block; background:#ff1f1f; color:#fff; font-weight:800; font-size:{band_size}px; padding:10px 34px 12px; border-radius:10px; letter-spacing:1px; box-shadow:0 6px 18px rgba(0,0,0,.6); }}
.title {{ position:absolute; left:0; top:{title_top}px; width:{W}px; text-align:center; color:#fff; font-weight:800; font-size:{title_size}px; line-height:.98; text-shadow:0 6px 18px rgba(0,0,0,.8); letter-spacing:-1px; }}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{W}" data-height="{H}">
<div id="art" class="clip" data-start="0" data-duration="1" style="position:absolute;inset:0">
{cols}
<div class="split"></div>
<div class="grad"></div>
<div class="band"><span>VALENCIA 0-2 REAL MADRID</span></div>
<div class="title">¡QUÉ<br>DEFINICIÓN!</div>
</div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }}); tl.to("#art", {{ opacity: 1, duration: 1 }}, 0);
window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = tl;
</script></body></html>'''
v_cols = col('gesto.jpg', 130, 300, 200, 711, 540, 1920, 0) + col('cara.jpg', 760, 40, 330, 1170*0+840, 540, 1920, 540)
open('cover_v/index.html','w').write(page(1080, 1920, v_cols, 150, 52, 1300, 1420))
s_cols = col('gesto.jpg', 120, 250, 400, 800, 540, 1080, 0) + col('cara.jpg', 700, 0, 440, 880, 540, 1080, 540)
open('cover_s/index.html','w').write(page(1080, 1080, s_cols, 118, 44, 640, 740))
