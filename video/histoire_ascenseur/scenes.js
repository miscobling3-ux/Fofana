// ================================================================ HISTOIRE : « LE 4ᵉ ÉTAGE »
// (concaténé après outils.js par build_anim.sh -> anim.js)
window.DUR = DUR;

// ---------------------------------------------------------------- personnages (style de la référence : tête noire, sweat jaune)
function person(o) {
  const id = o.id, w = o.w || 300;
  const body = o.kind === 'voisine'
    ? `<path d="M150 300 Q150 210 150 210 L230 218 Q262 420 280 600 L20 600 Q38 420 70 218Z" fill="#3a1424"/>
       <path d="M60 110 Q50 330 40 470 L95 420 Q90 300 100 200Z" fill="#050508"/><path d="M240 110 Q250 330 260 470 L205 420 Q210 300 200 200Z" fill="#050508"/>
       <rect x="44" y="230" width="40" height="230" rx="20" fill="#2a0f1b" transform="rotate(4 64 230)"/><rect x="216" y="230" width="40" height="230" rx="20" fill="#2a0f1b" transform="rotate(-4 236 230)"/>
       <circle cx="58" cy="468" r="18" fill="#0d0c13"/><circle cx="242" cy="468" r="18" fill="#0d0c13"/>`
    : `<rect x="90" y="395" width="54" height="205" rx="24" fill="#3b3d4c"/><rect x="156" y="395" width="54" height="205" rx="24" fill="#3b3d4c"/>
       <rect x="80" y="585" width="70" height="26" rx="12" fill="#e9e9ef"/><rect x="150" y="585" width="70" height="26" rx="12" fill="#e9e9ef"/>
       <rect x="38" y="225" width="46" height="190" rx="23" fill="#f0b616" transform="rotate(8 62 225)"/>
       <rect x="216" y="225" width="46" height="190" rx="23" fill="#f0b616" transform="rotate(-8 238 225)"/>
       <circle cx="44" cy="420" r="22" fill="#0d0c13"/><circle cx="256" cy="420" r="22" fill="#0d0c13"/>
       <path d="M68 215 Q150 188 232 215 L244 412 Q150 428 56 412 Z" fill="#f5c02a"/>
       <path d="M96 330 h108 v50 q-54 16 -108 0z" fill="#e0a812"/>
       <path d="M128 215 L136 300 M172 215 L164 300" stroke="#fff4c8" stroke-width="5" stroke-linecap="round"/>
       <path d="M58 140 Q60 236 150 236 Q240 236 242 140 Q246 250 150 250 Q54 250 58 140Z" fill="#e0a812"/>`;
  const hair = o.kind === 'voisine' ? `<path d="M58 125 Q55 22 150 20 Q245 22 242 125 Q232 60 150 58 Q68 60 58 125Z" fill="#050508"/>` : '';
  const faces = `
    <g class="f-shock" style="display:none"><circle cx="120" cy="110" r="21" fill="#fff"/><circle cx="182" cy="110" r="21" fill="#fff"/><circle cx="121" cy="113" r="8" fill="#0b0b10"/><circle cx="181" cy="113" r="8" fill="#0b0b10"/><path d="M135 162 q16 -8 32 0" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/></g>
    <g class="f-worry" style="display:none"><circle cx="120" cy="115" r="16" fill="#fff"/><circle cx="182" cy="115" r="16" fill="#fff"/><circle cx="123" cy="118" r="7" fill="#0b0b10"/><circle cx="179" cy="118" r="7" fill="#0b0b10"/><path d="M100 88 l38 10 M202 88 l-38 10" stroke="#fff" stroke-width="6" stroke-linecap="round"/></g>
    <g class="f-sleepy" style="display:none"><path d="M104 112 h32 M166 112 h32" stroke="#fff" stroke-width="6" stroke-linecap="round"/><path d="M106 104 q15 -8 30 0 M166 104 q15 -8 30 0" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" opacity=".7"/></g>
    <g class="f-grin" style="display:none"><path d="M88 150 Q150 215 212 150 Q150 178 88 150Z" fill="#fff"/>${Array.from({ length: 9 }, (_, i) => `<path d="M${98 + i * 13} ${154 + Math.sin(i / 8 * Math.PI) * 18} v${10 + Math.sin(i / 8 * Math.PI) * 6}" stroke="#0b0b10" stroke-width="3"/>`).join('')}<circle cx="118" cy="106" r="6" fill="#fff"/><circle cx="182" cy="106" r="6" fill="#fff"/></g>`;
  return `<svg viewBox="0 0 300 620" width="${w}" height="${w * 620 / 300}" style="overflow:visible">
    <defs><radialGradient id="hd${id}" cx="35%" cy="30%" r="80%"><stop offset="0" stop-color="#2a2933"/><stop offset=".55" stop-color="#0d0c13"/><stop offset="1" stop-color="#050509"/></radialGradient></defs>
    <ellipse cx="150" cy="612" rx="120" ry="14" fill="rgba(0,0,0,.5)"/>
    ${body}
    <rect x="132" y="178" width="36" height="34" fill="#0d0c13"/>
    <circle cx="150" cy="118" r="88" fill="url(#hd${id})"/>
    <path d="M90 60 Q150 25 212 62" stroke="rgba(255,255,255,.16)" stroke-width="6" fill="none" stroke-linecap="round"/>
    ${hair}${faces}</svg>`;
}
function setFace(el, f) {
  ['shock', 'worry', 'sleepy', 'grin'].forEach(k => { const g = el.querySelector('.f-' + k); if (g) g.style.display = k === f ? 'block' : 'none'; });
}
// bras jaune avec main noire et index tendu (comme la référence)
function armSVG() {
  return `<svg viewBox="0 0 300 900" width="300" height="900" style="overflow:visible">
    <rect x="95" y="300" width="130" height="700" rx="60" fill="#f0b616"/><rect x="95" y="300" width="130" height="80" rx="30" fill="#d79e0e"/>
    <ellipse cx="160" cy="250" rx="80" ry="95" fill="#0d0c13"/>
    <rect x="132" y="40" width="46" height="200" rx="23" fill="#0d0c13"/>
    <ellipse cx="96" cy="240" rx="26" ry="50" fill="#0d0c13" transform="rotate(-20 96 240)"/></svg>`;
}

// ---------------------------------------------------------------- décors
// rend les id SVG uniques (un dégradé référencé dans une scène masquée ne s'affiche pas ailleurs)
let UID = 0;
function uniq(svg) {
  const n = ++UID;
  return svg.replace(/id="([\w-]+)"/g, `id="$1_${n}"`).replace(/url\(#([\w-]+)\)/g, `url(#$1_${n})`);
}
function buildingSVG(o = {}) { return uniq(buildingRaw(o)); }
function buildingRaw(o = {}) {
  let win = '';
  for (let f = 0; f < 4; f++) for (let c = 0; c < 4; c++) {
    const lit = (f * 4 + c) % 5 === 1 || (f === 0 && c === 2);
    win += `<rect x="${78 + c * 120}" y="${520 - f * 150}" width="70" height="90" rx="6" fill="${lit ? '#ffb85c' : '#1a1638'}" ${lit ? 'filter="url(#wg)"' : ''}/>`;
  }
  return `<svg viewBox="0 0 560 800" width="560" height="800" style="overflow:visible">
    <defs><filter id="wg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="fac" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b2457"/><stop offset="1" stop-color="#151133"/></linearGradient></defs>
    <rect x="40" y="120" width="480" height="680" fill="url(#fac)"/><rect x="24" y="100" width="512" height="30" fill="#3a3270"/>
    ${win}
    <rect x="230" y="660" width="100" height="140" fill="#ffcf7a" filter="url(#wg)"/><rect x="236" y="666" width="88" height="134" fill="#3a2a10" opacity=".25"/>
    <rect x="210" y="640" width="140" height="18" fill="#3a3270"/>
    ${['RDC', '1', '2', '3'].map((l, i) => `<text x="525" y="${610 - i * 150}" font-family="Anton" font-size="34" fill="rgba(255,255,255,.55)" text-anchor="end">${l}</text>`).join('')}
    <g class="ghost" opacity="0"><rect x="40" y="-60" width="480" height="160" fill="none" stroke="#ff2a3d" stroke-width="6" stroke-dasharray="20 14"/>
      ${[0, 1, 2, 3].map(c => `<rect x="${78 + c * 120}" y="-30" width="70" height="90" rx="6" fill="#ff2a3d" opacity=".35"/>`).join('')}
      <text x="525" y="10" font-family="Anton" font-size="44" fill="#ff2a3d" text-anchor="end">4 ?</text></g>
  </svg>`;
}
function corridorSVG() { return uniq(corridorRaw()); }
function corridorRaw() {
  const VX0 = 395, VX1 = 685, VY0 = 560, VY1 = 930;
  const L = d => ({ x: lerp(0, VX0, d), top: lerp(0, VY0, d), bot: lerp(1920, VY1, d) });
  const R = d => ({ x: lerp(1080, VX1, d), top: lerp(0, VY0, d), bot: lerp(1920, VY1, d) });
  let doors = '';
  [[.18, .34], [.5, .62], [.72, .8]].forEach(([a, b], i) => {
    [L, R].forEach((S, side) => {
      const p = S(a), q = S(b), hp = .64;
      const pt = p.bot - (p.bot - p.top) * hp, qt = q.bot - (q.bot - q.top) * hp;
      doors += `<path class="door" d="M${p.x} ${p.bot} L${p.x} ${pt} L${q.x} ${qt} L${q.x} ${q.bot}Z" fill="#4a2e22" stroke="#2a1810" stroke-width="4"/>
        <circle cx="${lerp(p.x, q.x, side ? .2 : .8)}" cy="${lerp(p.bot, q.bot, .5) - (lerp(p.bot, q.bot, .5) - lerp(pt, qt, .5)) * .45}" r="${6 - i * 1.5}" fill="#d9b25a"/>
        <text x="${lerp(p.x, q.x, .5)}" y="${lerp(pt, qt, .5) - 14 + i * 4}" font-family="Anton" font-size="${34 - i * 9}" fill="#d9b25a" text-anchor="middle">${['4A', '4B', '4C'][i]}${side ? "'" : ''}</text>`;
    });
  });
  let neons = '';
  [.12, .38, .6, .78].forEach((d, i) => {
    const y = lerp(0, VY0, d) + 6, x0 = lerp(380, 505, d), x1 = lerp(700, 575, d), hh = 18 * (1 - d) + 4;
    neons += `<rect class="neon n${i}" x="${x0}" y="${y}" width="${x1 - x0}" height="${hh}" rx="${hh / 2}" fill="#e8f6ff" filter="url(#ng)"/>`;
  });
  let stripes = '';
  for (let i = -6; i <= 6; i++) stripes += `<path d="M${540 + i * 190} 1920 L${540 + i * 22} ${VY1}" stroke="rgba(0,0,0,.25)" stroke-width="${10 - Math.abs(i) * .5}"/>`;
  for (let d = .05; d < 1; d += .09) stripes += `<path d="M${lerp(0, VX0, d)} ${lerp(1920, VY1, d)} H${lerp(1080, VX1, d)}" stroke="rgba(0,0,0,.18)" stroke-width="${8 * (1 - d) + 2}"/>`;
  return `<svg viewBox="0 0 1080 1920" width="1080" height="1920">
    <defs><filter id="ng" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <linearGradient id="lw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4c5a3a"/><stop offset="1" stop-color="#1e2418"/></linearGradient>
      <linearGradient id="rw" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#4c5a3a"/><stop offset="1" stop-color="#1e2418"/></linearGradient>
      <linearGradient id="fl" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#6b1a22"/><stop offset="1" stop-color="#2a080d"/></linearGradient>
      <radialGradient id="dl" cx="50%" cy="100%" r="80%"><stop offset="0" stop-color="#ffd38a" stop-opacity=".9"/><stop offset="1" stop-color="#ffd38a" stop-opacity="0"/></radialGradient></defs>
    <path d="M0 0 H1080 L${VX1} ${VY0} H${VX0}Z" fill="#cfd3c4"/>
    <path d="M0 0 L${VX0} ${VY0} V${VY1} L0 1920Z" fill="url(#lw)"/>
    <path d="M1080 0 L${VX1} ${VY0} V${VY1} L1080 1920Z" fill="url(#rw)"/>
    <path d="M0 1920 H1080 L${VX1} ${VY1} H${VX0}Z" fill="url(#fl)"/>
    ${stripes}
    <path d="M0 1290 L${VX0} ${VY1 - 60} M1080 1290 L${VX1} ${VY1 - 60}" stroke="#2b3322" stroke-width="10"/>
    <rect x="${VX0}" y="${VY0}" width="${VX1 - VX0}" height="${VY1 - VY0}" fill="#39432c"/>
    <g class="enddoor"><rect x="490" y="700" width="100" height="230" fill="#ffcf7a"/>
      <path class="leaf" d="M490 700 L452 690 L452 945 L490 930Z" fill="#4a2e22"/>
      <path d="M440 1250 L490 930 H590 L700 1250Z" fill="url(#dl)" class="spill"/>
      <text x="540" y="690" font-family="Anton" font-size="30" fill="#d9b25a" text-anchor="middle">3B</text></g>
    ${doors}${neons}
  </svg>`;
}

// ---------------------------------------------------------------- mise en place
const world = document.getElementById('world');
const scenes = [];
function scene(t0, t1, build, update) {
  const el = h('div', 'scene', '', null, world);
  scenes.push({ t0, t1, el, update, build });
}

// ======== 1. DEHORS : IMAGINE, MINUIT MOINS DEUX (0 – 3.9)
scene(0, 3.9, (el, s) => {
  s.moon = node(el, '', 'width:170px;height:170px;border-radius:50%;background:radial-gradient(circle at 40% 40%,#fff,#dfe3ff);box-shadow:0 0 80px 30px rgba(220,225,255,.35)');
  s.bld = node(el, '', '', buildingSVG());
  s.street = node(el, '', 'width:1400px;height:420px;background:linear-gradient(180deg,#1b1838,#0a0918)');
  s.lamp = node(el, '', 'width:300px;height:900px', `<svg width="300" height="900"><rect x="140" y="80" width="14" height="820" fill="#2a2650"/><path d="M147 80 Q147 40 200 40 H230" stroke="#2a2650" stroke-width="12" fill="none"/><path d="M200 40 h60 l-12 22 h-36z" fill="#3a3470"/><path d="M212 62 L120 900 H380 L250 62Z" fill="rgba(255,210,130,.12)"/></svg>`);
  s.p = node(el, '', '', person({ id: 'a1', w: 300 }));
  s.img = node(el, 'big', 'font-size:150px;letter-spacing:6px;white-space:nowrap;text-shadow:0 0 40px rgba(170,140,255,.6)', 'IMAGINE');
}, (s, t) => {
  set(s.moon, { x: 820, y: 380 });
  set(s.bld, { x: 400, y: 900, s: 1.15 + t * .02 });
  set(s.street, { x: 540, y: 1520 });
  set(s.lamp, { x: 900, y: 1080 });
  const walk = clamp(t / 3.9);
  set(s.p, { x: lerp(1000, 520, walk), y: 1270 + Math.abs(Math.sin(t * 7)) * -10, s: .95 - walk * .2 });
  setFace(s.p, 'sleepy');
  const [a, ao] = pop(t, 0, .45);
  set(s.img, { x: 540, y: 560, s: a, o: ao * (1 - P(t, .9, .3)) });
});

// ======== 2. LE HALL VIDE (3.9 – 6.0)
scene(3.9, 6.0, (el, s) => {
  s.room = node(el, '', 'width:1080px;height:1920px', `<svg width="1080" height="1920"><defs><linearGradient id="hw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2d2a4f"/><stop offset="1" stop-color="#17142f"/></linearGradient></defs>
    <rect width="1080" height="1300" fill="url(#hw)"/><rect y="1300" width="1080" height="620" fill="#0f0d22"/>
    ${Array.from({ length: 12 }, (_, i) => `<path d="M${i * 100 - 40} 1920 L${440 + i * 20} 1300" stroke="rgba(255,255,255,.04)" stroke-width="4"/>`).join('')}
    <rect x="330" y="620" width="420" height="680" fill="#8d93a8"/><rect x="345" y="640" width="190" height="660" fill="#b6bccd"/><rect x="545" y="640" width="190" height="660" fill="#aab0c2"/>
    <rect x="300" y="560" width="480" height="50" rx="10" fill="#141126"/><text x="540" y="598" font-family="Anton" font-size="36" fill="#ff5a5a" text-anchor="middle">RDC</text>
    <rect x="790" y="900" width="60" height="110" rx="10" fill="#141126"/><circle cx="820" cy="935" r="14" fill="#ffcf4d"/><circle cx="820" cy="975" r="14" fill="#444"/>
    ${Array.from({ length: 12 }, (_, i) => `<rect x="${60 + (i % 3) * 70}" y="${760 + Math.floor(i / 3) * 80}" width="60" height="68" rx="6" fill="#6c5a3a" stroke="#3a2f1d" stroke-width="4"/>`).join('')}
    </svg>`);
  s.light = node(el, '', 'width:700px;height:1400px;background:linear-gradient(180deg,rgba(255,240,200,.35),rgba(255,240,200,0));clip-path:polygon(42% 0,58% 0,100% 100%,0 100%)');
  s.p = node(el, '', '', person({ id: 'a2', w: 300 }));
  s.vide = node(el, 'big', 'font-size:120px;letter-spacing:30px;opacity:.0;white-space:nowrap', 'VIDE');
}, (s, t) => {
  set(s.room, { x: 540, y: 960 });
  const fl = (Math.floor(t * 12) % 7 === 0) ? .35 : 1;
  set(s.light, { x: 540, y: 700, o: .9 * fl });
  const w = clamp((t - 3.9) / 2.1);
  set(s.p, { x: lerp(300, 540, w), y: 1500 - w * 120, s: 1.3 - w * .35 });
  setFace(s.p, 'sleepy');
  set(s.vide, { x: 540, y: 420, o: P(t, 5.3, .4) * .55, s: 1 + (t - 5.3) * .05 });
});

// ======== 3. DANS L'ASCENSEUR : LE BOUTON 3, ÇA MONTE (6.0 – 14.6)
scene(6.0, 14.6, (el, s) => {
  s.wall = node(el, '', 'width:1300px;height:2100px;background:repeating-linear-gradient(90deg,#8c92a6 0 3px,#9aa0b4 3px 7px,#868ca0 7px 12px)', '<div style="position:absolute;inset:0;background:radial-gradient(70% 50% at 50% 30%,rgba(255,255,255,.25),rgba(0,0,0,.45))"></div>');
  s.disp = node(el, '', 'width:520px;height:250px;border-radius:30px;background:#07060d;border:10px solid #2a2a36;box-shadow:inset 0 0 40px rgba(255,60,60,.15),0 20px 50px rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;gap:40px',
    '<span class="arr" style="font-size:110px;color:#ff3b3b;text-shadow:0 0 20px #ff3b3b">▲</span><span class="num bebas" style="font-size:210px;color:#ff3b3b;text-shadow:0 0 25px #ff3b3b;width:170px;text-align:center">0</span>');
  s.num = s.disp.querySelector('.num'); s.arr = s.disp.querySelector('.arr');
  s.panel = node(el, '', 'width:420px;height:820px;border-radius:40px;background:linear-gradient(180deg,#c9ced9,#a2a8b8);box-shadow:0 30px 70px rgba(0,0,0,.5),inset 0 2px 0 #fff');
  s.btns = ['3', '2', '1', 'RDC'].map((l, i) => {
    const b = h('div', 'abs', `left:${210 - 85}px;top:${70 + i * 180}px;width:170px;height:170px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#f4f5f8,#9aa0b0);box-shadow:0 8px 0 #6d7384,0 14px 20px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:${l === 'RDC' ? 54 : 84}px;color:#3a3f4f`, l, s.panel);
    return b;
  });
  s.arm = node(el, '', '', armSVG());
}, (s, t) => {
  set(s.wall, { x: 540, y: 960 + Math.sin(t * 40) * (t > 10.4 ? 2 : 0) });
  // affichage d'étage
  const fl = t > 13.68 ? '3' : t > 12.8 ? '2' : t > 11.84 ? '1' : '0';
  s.num.textContent = fl === '0' ? 'RDC'.slice(0, 1) === 'R' ? '0' : '0' : fl;
  s.num.style.transform = `scale(${1 + punch(t, [11.84, 12.8, 13.68].find(x => t >= x && t < x + .5) || -9, .25)})`;
  s.arr.style.opacity = t > 10.4 ? (Math.floor(t * 3) % 2 ? .4 : 1) : .15;
  set(s.disp, { x: 540, y: 400, s: pop(t, 6.0, .4)[0] });
  set(s.panel, { x: 540, y: 960 + (1 - P(t, 6.0, .5, 'out5')) * 600, s: .82 });
  // le doigt appuie sur 3
  const reach = P(t, 7.3, .8, 'io'), press = t > 8.1 && t < 8.5 ? 1 : 0, back = P(t, 9.4, .5, 'in');
  set(s.arm, { x: lerp(860, 588, reach) + back * 400, y: lerp(1900, 1085 + press * 14, reach) + back * 400, r: lerp(-30, -10, reach) });
  const lit = t > 8.16;
  s.btns[0].style.background = lit ? 'radial-gradient(circle at 40% 35%,#fff6c9,#ffb31a)' : 'radial-gradient(circle at 40% 35%,#f4f5f8,#9aa0b0)';
  s.btns[0].style.boxShadow = lit ? '0 8px 0 #b37a00,0 0 40px 10px rgba(255,190,40,.7)' : '0 8px 0 #6d7384,0 14px 20px rgba(0,0,0,.35)';
  s.btns[0].style.transform = `scale(${1 + punch(t, 8.16, .12)})`;
});

// ======== 4. IL NE S'ARRÊTE PAS : DING, 4ᵉ ÉTAGE (14.6 – 21.7)
scene(14.6, 21.7, (el, s) => {
  s.wall = node(el, '', 'width:1300px;height:2100px;background:repeating-linear-gradient(90deg,#8c92a6 0 3px,#9aa0b4 3px 7px,#868ca0 7px 12px)', '<div style="position:absolute;inset:0;background:radial-gradient(70% 50% at 50% 30%,rgba(255,255,255,.15),rgba(0,0,0,.6))"></div>');
  s.disp = node(el, '', 'width:720px;height:560px;border-radius:40px;background:#07060d;border:14px solid #2a2a36;box-shadow:inset 0 0 80px rgba(255,40,40,.25),0 30px 70px rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center',
    '<span class="num bebas" style="font-size:520px;color:#ff2a2a;text-shadow:0 0 40px #ff2a2a,0 0 120px rgba(255,0,0,.6)">3</span>');
  s.num = s.disp.querySelector('.num');
  s.ding = node(el, 'big', 'font-size:170px;color:#fff;letter-spacing:10px;white-space:nowrap;text-shadow:0 0 50px #fff', 'DING');
  s.bld = node(el, '', '', buildingSVG());
  s.ghost = s.bld.querySelector('.ghost');
  s.cab = node(el, '', 'width:90px;height:110px;border-radius:12px;background:#ffcf4d;box-shadow:0 0 40px #ffcf4d;border:6px solid #fff');
  s.only = node(el, 'big', 'font-size:130px;text-align:center;white-space:nowrap', 'SEULEMENT<br><span style="color:var(--red)">3 ÉTAGES</span>');
}, (s, t) => {
  set(s.wall, { x: 540, y: 960 + Math.sin(t * 40) * (t < 16 ? 3 : 0) });
  const out = P(t, 18.4, .35, 'in');
  // le chiffre « glitche » de 3 vers 4
  const g = t > 15.0 && t < 16.08;
  s.num.textContent = t >= 16.08 ? '4' : g && Math.floor(t * 18) % 3 === 0 ? '4' : '3';
  s.num.style.transform = g ? `translateX(${Math.sin(t * 90) * 12}px)` : `scale(${1 + punch(t, 16.08, .2)})`;
  set(s.disp, { x: 540, y: 820 - out * 1400, s: (1 + (t - 14.6) * .03) * (1 + punch(t, 16.08, .08)) });
  const [d, dO] = pop(t, 16.08, .3);
  set(s.ding, { x: 540, y: 330 - out * 1400, s: d, o: dO });
  // coupe de l'immeuble : la cabine dépasse le toit
  const bi = P(t, 18.4, .45, 'out5');
  set(s.bld, { x: 540, y: lerp(2400, 1150, bi), s: 1.0 });
  s.ghost.setAttribute('opacity', clamp((t - 19.6) / .3) * (Math.floor(t * 10) % 4 ? 1 : .5));
  const cy = K(t, [[18.6, 1150 + 260], [19.6, 1150 + 260 - 450], [20.2, 1150 + 260 - 640]]);
  set(s.cab, { x: 570, y: cy, o: bi });
  const [o2, oo] = pop(t, 20.3, .35);
  set(s.only, { x: 540, y: 430, s: o2 * .85, o: oo });
});

// ======== 5. LES PORTES S'OUVRENT SUR LE COULOIR (21.7 – 34.5)
scene(21.7, 34.5, (el, s) => {
  s.cor = node(el, '', 'width:1080px;height:1920px', corridorSVG());
  s.neons = [...s.cor.querySelectorAll('.neon')];
  s.doors = [...s.cor.querySelectorAll('.door')];
  s.spill = s.cor.querySelector('.spill');
  s.leaf = s.cor.querySelector('.leaf');
  s.dl = node(el, '', 'width:560px;height:1920px;background:repeating-linear-gradient(90deg,#9aa0b4 0 4px,#8c92a6 4px 10px);box-shadow:inset -20px 0 40px rgba(0,0,0,.4)');
  s.dr = node(el, '', 'width:560px;height:1920px;background:repeating-linear-gradient(90deg,#9aa0b4 0 4px,#8c92a6 4px 10px);box-shadow:inset 20px 0 40px rgba(0,0,0,.4)');
  s.ring = node(el, '', 'width:420px;height:200px;border:10px solid #ff3344;border-radius:50%;box-shadow:0 0 30px #ff3344');
  s.tagM = node(el, 'tag', 'background:#fff;color:#111', 'MÊME MOQUETTE');
  s.tagP = node(el, 'tag', 'background:#fff;color:#111', 'MÊMES PORTES');
  s.tagN = node(el, 'tag', 'background:#fff;color:#111', 'MÊME NÉON');
  s.tagD = node(el, 'tag', 'background:var(--red);color:#fff;font-size:44px', 'TA PORTE');
}, (s, t) => {
  // portes de l'ascenseur qui s'ouvrent
  const op = P(t, 21.8, 1.0, 'io');
  set(s.dl, { x: 280 - op * 560, y: 960 });
  set(s.dr, { x: 800 + op * 560, y: 960 });
  // travelling avant dans le couloir, puis zoom vers le fond
  const z = 1 + (t - 21.7) * .025 + P(t, 31.1, 1.4, 'io') * 1.4;
  s.cor.style.transformOrigin = '540px 820px';
  set(s.cor, { x: 540, y: 960, s: z });
  // néon qui grésille
  s.neons.forEach((n, i) => {
    const f = i === 1 && t > 29.5 ? (Math.floor(t * 23) % 5 < 2 ? .15 : 1) : (Math.floor(t * 7 + i * 3) % 23 === 0 ? .3 : 1);
    n.setAttribute('opacity', f);
  });
  s.leaf.setAttribute('d', `M490 700 L${lerp(490, 452, P(t, 32.6, .6))} 690 L${lerp(490, 452, P(t, 32.6, .6))} 945 L490 930Z`);
  s.spill.setAttribute('opacity', P(t, 32.6, .6));
  const hlR = t > 27.0 && t < 27.9;
  set(s.ring, { x: 540, y: 1190, s: hlR ? pop(t, 27.0, .3)[0] : 0, r: -4 });
  set(s.tagM, { x: 540, y: 1050, s: pop(t, 27.0)[0], o: pop(t, 27.0)[1] * (1 - P(t, 27.9, .2)) });
  s.doors.forEach(d => d.setAttribute('stroke', t > 28.4 && t < 29.1 ? '#ff3344' : '#2a1810'));
  s.doors.forEach(d => d.setAttribute('stroke-width', t > 28.4 && t < 29.1 ? 10 : 4));
  set(s.tagP, { x: 540, y: 1050, s: pop(t, 28.4)[0], o: pop(t, 28.4)[1] * (1 - P(t, 29.1, .2)) });
  set(s.tagN, { x: 540, y: 330, s: pop(t, 29.6)[0], o: pop(t, 29.6)[1] * (1 - P(t, 30.9, .2)) });
  set(s.tagD, { x: 540, y: 520, s: pop(t, 32.7)[0], o: pop(t, 32.7)[1] });
});

// ======== 6. LA VOISINE (34.5 – 41.3)
scene(34.5, 41.3, (el, s) => {
  s.cor = node(el, '', 'width:1080px;height:1920px', corridorSVG());
  s.cor.querySelector('.leaf').setAttribute('d', 'M490 700 L452 690 L452 945 L490 930Z');
  s.neons = [...s.cor.querySelectorAll('.neon')];
  s.v = node(el, '', '', person({ id: 'v6', kind: 'voisine', w: 300 }));
  s.bub = node(el, '', 'background:#fff;color:#111;border-radius:40px;padding:30px 44px;font-family:Anton;font-size:76px;white-space:nowrap;box-shadow:0 20px 60px rgba(0,0,0,.6)', '« VIENS VITE !<br>C\'EST CHEZ TOI ! »');
  s.name = node(el, '', 'background:#fff;color:#111;border-radius:40px;padding:26px 44px;font-family:Anton;font-size:96px;white-space:nowrap;box-shadow:0 0 60px rgba(255,40,60,.6)', '« <span class="nm" style="background:#111;color:#111;border-radius:10px;padding:0 20px">TON PRÉNOM</span> ! »');
  s.nm = s.name.querySelector('.nm');
}, (s, t) => {
  s.cor.style.transformOrigin = '540px 820px';
  const z = 2.4 + (t - 34.5) * .04 - P(t, 34.5, .01) * 0;
  set(s.cor, { x: 540, y: 960, s: z });
  s.neons.forEach((n, i) => n.setAttribute('opacity', Math.floor(t * 9 + i * 5) % 13 === 0 ? .2 : 1));
  // la voisine apparaît d'un coup devant la porte
  const app = t > 35.4 ? 1 : 0;
  const near = P(t, 39.36, 1.2, 'in');
  set(s.v, { x: 540, y: lerp(1000, 1180, near), s: (.9 + near * .9) * (1 + punch(t, 35.44, .08)), o: app * (Math.floor(t * 20) % 9 === 0 && t < 36.5 ? .4 : 1), r: Math.sin(t * 1.3) * 3 + 6 });
  setFace(s.v, t > 40.5 ? 'grin' : 'none');
  const [b, bo] = pop(t, 37.05, .3);
  set(s.bub, { x: 540, y: 380, s: b * (1 + punch(t, 37.9, .05)), o: bo * (1 - P(t, 39.2, .2)) });
  const [n, no] = pop(t, 39.4, .3);
  set(s.name, { x: 540 + (t > 40.5 ? Math.sin(t * 70) * 6 : 0), y: 400, s: n, o: no });
  s.nm.style.color = t > 40.52 ? '#ff3344' : '#111';
  s.nm.style.filter = t > 40.52 ? `blur(${Math.abs(Math.sin(t * 13)) * 3}px)` : '';
});

// ======== 7. TU NE LUI AS JAMAIS DIT (41.3 – 44.55)
scene(41.3, 44.55, (el, s) => {
  s.p = node(el, '', '', person({ id: 'a7', w: 520 }));
  s.never = node(el, 'big', 'font-size:150px;text-align:center;white-space:nowrap;text-shadow:0 10px 0 #000', 'JAMAIS<br><span style="color:var(--red)">DIT.</span>');
}, (s, t) => {
  const z = 1 + (t - 41.3) * .12;
  set(s.p, { x: 540, y: 1300, s: z, r: Math.sin(t * 30) * (t > 42.8 ? 1 : 0) });
  setFace(s.p, 'shock');
  const [a, ao] = pop(t, 42.88, .3);
  set(s.never, { x: 540, y: 420, s: a, o: ao });
});

// ======== 8. LES PORTES SE REFERMENT : 2 SECONDES (44.55 – 50.5)
scene(44.55, 50.5, (el, s) => {
  s.cor = node(el, '', 'width:1080px;height:1920px', corridorSVG());
  s.cor.querySelector('.leaf').setAttribute('d', 'M490 700 L452 690 L452 945 L490 930Z');
  s.v = node(el, '', '', person({ id: 'v8', kind: 'voisine', w: 300 }));
  s.dl = node(el, '', 'width:560px;height:1920px;background:repeating-linear-gradient(90deg,#9aa0b4 0 4px,#8c92a6 4px 10px);box-shadow:inset -20px 0 40px rgba(0,0,0,.4)');
  s.dr = node(el, '', 'width:560px;height:1920px;background:repeating-linear-gradient(90deg,#9aa0b4 0 4px,#8c92a6 4px 10px);box-shadow:inset 20px 0 40px rgba(0,0,0,.4)');
  s.timer = node(el, '', 'width:300px;height:300px', `<svg width="300" height="300"><circle cx="150" cy="150" r="130" fill="rgba(0,0,0,.7)" stroke="#333" stroke-width="16"/><circle class="arc" cx="150" cy="150" r="130" fill="none" stroke="#ff3344" stroke-width="16" stroke-linecap="round" transform="rotate(-90 150 150)" stroke-dasharray="817 817"/><text class="tn" x="150" y="200" font-family="Anton" font-size="150" fill="#fff" text-anchor="middle">2</text></svg>`);
  s.arc = s.timer.querySelector('.arc'); s.tn = s.timer.querySelector('.tn');
  s.cA = node(el, '', 'width:400px;height:520px;border-radius:40px;background:linear-gradient(180deg,#2a1a3f,#140d22);border:6px solid #fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 30px 80px rgba(0,0,0,.7)',
    `<div class="emoji" style="position:relative;width:200px;height:200px;background-image:url(assets/emoji/1f6aa.webp)"></div><div style="font-family:Anton;font-size:84px;margin-top:10px">TU SORS</div>`);
  s.cB = node(el, '', 'width:400px;height:520px;border-radius:40px;background:linear-gradient(180deg,#2a1a3f,#140d22);border:6px solid #ffcf4d;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 30px 80px rgba(0,0,0,.7),0 0 50px rgba(255,200,60,.4)',
    `<div style="width:200px;height:200px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#fff6c9,#ffb31a);box-shadow:0 10px 0 #b37a00,0 0 50px rgba(255,190,40,.7);display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:80px;color:#5a3a00">RDC</div><div style="font-family:Anton;font-size:84px;margin-top:20px">RDC</div>`);
  s.ou = node(el, 'big', 'font-size:80px;width:150px;height:150px;border-radius:50%;background:var(--red);display:flex;align-items:center;justify-content:center;box-shadow:0 0 40px rgba(255,40,60,.8)', 'OU');
}, (s, t) => {
  s.cor.style.transformOrigin = '540px 820px';
  set(s.cor, { x: 540, y: 960, s: 1.6 });
  set(s.v, { x: 540, y: 1080, s: 1.1, r: 6 });
  setFace(s.v, 'grin');
  // portes qui se referment lentement puis s'arrêtent pour le choix
  const cl = P(t, 44.7, 3.0, 'io') * .62;
  set(s.dl, { x: -280 + cl * 560, y: 960 });
  set(s.dr, { x: 1360 - cl * 560, y: 960 });
  const tt = clamp((t - 46.4) / 2.0);
  s.arc.setAttribute('stroke-dasharray', `${817 * (1 - tt)} 817`);
  s.tn.textContent = t < 47.4 ? '2' : '1';
  const [tm, to] = pop(t, 46.4, .3);
  set(s.timer, { x: 540, y: 400, s: tm * (1 + punch(t, 47.4, .15)), o: to * (1 - P(t, 47.8, .2)) });
  const [a, ao] = pop(t, 47.84, .35), [b, bo] = pop(t, 49.0, .35);
  set(s.cA, { x: 270, y: 900, s: a * (1 + punch(t, 48.2, .05)), r: -5, o: ao });
  set(s.cB, { x: 810, y: 900, s: b * (1 + .03 * Math.sin(t * 8)), r: 5, o: bo });
  set(s.ou, { x: 540, y: 900, s: pop(t, 48.6)[0], o: pop(t, 48.6)[1] });
});

// ======== 9. LA RÈGLE (50.5 – 55.4)
scene(50.5, 55.4, (el, s) => {
  s.wall = node(el, '', 'width:1300px;height:2100px;background:repeating-linear-gradient(90deg,#8c92a6 0 3px,#9aa0b4 3px 7px,#868ca0 7px 12px)', '<div style="position:absolute;inset:0;background:radial-gradient(60% 45% at 50% 40%,rgba(255,255,255,.1),rgba(0,0,0,.75))"></div>');
  s.note = node(el, '', 'width:780px;padding:60px 60px 70px;background:#f3ecd6;color:#1a1410;box-shadow:0 40px 90px rgba(0,0,0,.7);font-family:"Courier New",monospace;font-weight:700',
    `<div style="font-family:Anton;font-size:96px;color:#b3121f;letter-spacing:3px;text-align:center">RÈGLE N°1</div>
     <div style="height:4px;background:#b3121f;margin:18px 0 30px"></div>
     <div class="txt" style="font-size:52px;line-height:1.35;min-height:280px"></div>`);
  s.txt = s.note.querySelector('.txt');
  s.tape = node(el, '', 'width:220px;height:60px;background:rgba(255,240,180,.7);box-shadow:0 4px 10px rgba(0,0,0,.3)');
  s.full = "Ici, ne réponds JAMAIS à quelqu'un qui connaît ton prénom.";
}, (s, t) => {
  set(s.wall, { x: 540, y: 960 });
  const ni = P(t, 50.55, .45, 'back');
  set(s.note, { x: 540, y: lerp(1900, 820, ni), r: lerp(14, -3, ni) + Math.sin(t * 2) * .5, s: 1 + (t - 50.5) * .01 });
  set(s.tape, { x: 540, y: lerp(1900, 820, ni) - 330, r: -4 });
  const n = Math.floor(clamp((t - 52.1) / 3.0) * s.full.length);
  s.txt.innerHTML = s.full.slice(0, n).replace('JAMAIS', '<span style="color:#b3121f">JAMAIS</span>').replace('prénom', '<u>prénom</u>') + (Math.floor(t * 3) % 2 ? '▍' : '');
});

// ======== 10. COMMENTAIRE + ELLE T'ATTEND (55.4 – fin)
scene(55.4, DUR, (el, s) => {
  s.cA = node(el, '', 'width:860px;padding:36px 44px;border-radius:30px;background:rgba(20,16,36,.92);border:4px solid #fff;font-family:Anton;font-size:80px;white-space:nowrap;box-shadow:0 20px 60px rgba(0,0,0,.6)', '<span style="color:var(--gold)">A</span> · JE SORS 🚪');
  s.cB = node(el, '', 'width:860px;padding:36px 44px;border-radius:30px;background:rgba(20,16,36,.92);border:4px solid #fff;font-family:Anton;font-size:80px;white-space:nowrap;box-shadow:0 20px 60px rgba(0,0,0,.6)', '<span style="color:var(--gold)">B</span> · J\'APPUIE SUR RDC');
  s.com = node(el, '', 'background:#fff;color:#111;border-radius:40px;padding:26px 40px;font-weight:900;font-size:50px;white-space:nowrap;box-shadow:0 20px 50px rgba(0,0,0,.5)', `<span class="emoji" style="position:relative;display:inline-block;width:80px;height:80px;vertical-align:middle;margin-right:14px;background-image:url(assets/emoji/1f4ac.webp)"></span>RÉPONDS EN COMMENTAIRE`);
  s.dark = node(el, '', 'width:1080px;height:1920px;background:#000');
  s.cor = node(el, '', 'width:1080px;height:1920px', corridorSVG());
  s.cor.querySelector('.leaf').setAttribute('d', 'M490 700 L452 690 L452 945 L490 930Z');
  s.v = node(el, '', '', person({ id: 'v10', kind: 'voisine', w: 300 }));
  s.att = node(el, 'big', 'font-size:140px;text-align:center;white-space:nowrap;color:#fff;text-shadow:0 0 40px rgba(255,30,50,.9)', "ELLE<br><span style=\"color:var(--red)\">T'ATTEND.</span>");
  s.end = node(el, '', 'text-align:center;white-space:nowrap', '<div style="font-family:Anton;font-size:110px;letter-spacing:4px">À SUIVRE…</div><div style="margin-top:30px;display:inline-block;background:var(--red);border-radius:60px;padding:24px 56px;font-family:Anton;font-size:80px;letter-spacing:3px;box-shadow:0 0 50px rgba(255,40,60,.6)">+ ABONNE-TOI</div>');
}, (s, t) => {
  const [a, ao] = pop(t, 55.5, .35), [b, bo] = pop(t, 55.75, .35);
  const out = P(t, 57.3, .3, 'in');
  set(s.cA, { x: 540, y: 700 - out * 1500, s: a, o: ao });
  set(s.cB, { x: 540, y: 900 - out * 1500, s: b, o: bo });
  set(s.com, { x: 540, y: 420 - out * 1500, s: pop(t, 55.8)[0], o: pop(t, 55.8)[1] });
  const ci = t > 57.35;
  s.dark.style.display = s.cor.style.display = s.v.style.display = ci ? 'block' : 'none';
  set(s.dark, { x: 540, y: 960 });
  s.cor.style.transformOrigin = '540px 820px';
  const push = P(t, 57.35, 2.4, 'in');
  set(s.cor, { x: 540, y: 960, s: 2.2 + push * 1.6, o: t > 59.75 ? 0 : (Math.floor(t * 9) % 6 === 0 ? .55 : 1) });
  set(s.v, { x: 540, y: 1150 + push * 300, s: 1.3 + push * 2.6, r: 6, o: t > 59.75 ? 0 : 1 });
  setFace(s.v, t > 58.6 ? 'grin' : 'none');
  const [at, ato] = pop(t, 58.99, .3);
  set(s.att, { x: 540, y: 470, s: at, o: ato * (t > 59.75 ? 0 : 1) });
  set(s.end, { x: 540, y: 900, s: pop(t, 60.0, .4)[0], o: pop(t, 60.0, .4)[1] });
});

// ---------------------------------------------------------------- en-tête : lieu + horloge (comme la référence)
const LIEUX = [[0, 'NUIT 1 · RUE'], [3.9, 'NUIT 1 · HALL'], [6.0, 'NUIT 1 · ASCENSEUR'], [16.08, 'NUIT 1 · ÉTAGE 4'], [41.3, 'NUIT 1 · ÉTAGE 4'], [50.5, 'NUIT 1 · ASCENSEUR'], [57.35, 'NUIT 1 · ÉTAGE 4']];
const hlab = document.getElementById('hlab'), hval = document.getElementById('hval'), hdr = document.getElementById('hdr');
function header(t) {
  let lab = LIEUX[0][1];
  LIEUX.forEach(([a, l]) => { if (t >= a) lab = l; });
  if (hlab.textContent !== lab) hlab.textContent = lab;
  let secs = 23 * 3600 + 58 * 60 + Math.floor(t);
  let txt = [Math.floor(secs / 3600), Math.floor(secs / 60) % 60, secs % 60].map(x => String(x).padStart(2, '0')).join(':');
  // au 4ᵉ étage l'horloge se bloque et devient rouge
  if (t >= 16.08 && t < 50.5) txt = Math.floor(t * 8) % 11 === 0 ? '??:??:??' : '23:58:16';
  if (t >= 57.35) txt = '23:59:59';
  hval.innerHTML = (t >= 16.08 && t < 50.5) || t >= 57.35 ? `<em>${txt}</em>` : txt;
  hdr.style.opacity = t > 59.75 ? 0 : 1;
}

// ---------------------------------------------------------------- sous-titres mot par mot
const KEY = new Set(('IMAGINE MINUIT TARD VIDE TROIS DERNIER MONTE UN DEUX S\'ARRÊTE PAS DING QUATRIÈME ÉTAGES COULOIR TIEN MOQUETTE PORTES NÉON GRÉSILLE PORTE OUVERTE ' +
  'VOIX VOISINE VITE PRÉNOM PROBLÈME JAMAIS REFERMER SECONDES SORS REZ-DE-CHAUSSÉE RÈGLE COMMENTAIRE T\'ATTEND').split(' '));
let GROUPS = [];
function buildGroups(words) {
  const ws = words.filter(w => w.type === 'word' && /[\p{L}\p{N}]/u.test(w.text));
  let g = [];
  const flush = () => { if (g.length) GROUPS.push(g); g = []; };
  ws.forEach((w, i) => {
    const clean = w.text.replace(/[«»"]/g, '').replace(/[.,:;!?…]+$/g, '').toUpperCase();
    const len = g.reduce((a, x) => a + x.c.length + 1, 0) + clean.length;
    if (g.length && (g.length >= 3 || len > 16 || w.start - g[g.length - 1].e > .45)) flush();
    g.push({ c: clean, s: w.start, e: w.end });
    if (/[.,:;!?…»]$/.test(w.text) || (ws[i + 1] && /^[:?!»]/.test(ws[i + 1].text))) flush();
  });
  flush();
}
const capline = document.getElementById('capline');
let curG = -1, spans = [];
function captions(t) {
  let gi = -1;
  for (let i = 0; i < GROUPS.length; i++) if (t >= GROUPS[i][0].s - .05) gi = i;
  const g = GROUPS[gi];
  const end = g ? g[g.length - 1].e + .6 : 0;
  const nextS = GROUPS[gi + 1] ? GROUPS[gi + 1][0].s : 1e9;
  if (!g || t > Math.min(end, nextS) || t > 59.8) { capline.style.opacity = 0; return; }
  capline.style.opacity = 1;
  if (gi !== curG) {
    curG = gi;
    capline.innerHTML = g.map(w => `<span class="w ${KEY.has(w.c) ? 'k' : ''}">${w.c}</span>`).join(' ');
    spans = [...capline.querySelectorAll('.w')];
  }
  g.forEach((w, i) => {
    const p = clamp((t - w.s + .04) / .16);
    spans[i].style.opacity = p > 0 ? 1 : 0;
    spans[i].style.transform = `scale(${p > 0 ? lerp(1.35, 1, E.out(p)) : .5}) translateY(${(1 - E.out(p)) * 14}px)`;
  });
}

// ---------------------------------------------------------------- ambiance + caméra
const dust = document.getElementById('dust');
const DUST = [];
let rs = 7;
const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
for (let i = 0; i < 40; i++) DUST.push({ e: h('b', '', '', null, dust), x: rnd() * 1080, y: rnd() * 1920, s: .3 + rnd() * .8, v: 8 + rnd() * 30, ph: rnd() * 6 });
const grain = document.getElementById('grain'), gctx = grain.getContext('2d');
const GR = [];
for (let k = 0; k < 6; k++) {
  const im = gctx.createImageData(590, 1010);
  for (let i = 0; i < im.data.length; i += 4) { const v = rnd() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  GR.push(im);
}
const tint = document.getElementById('tint'), flash = document.getElementById('flash'), prog = document.getElementById('prog');
const g1 = document.getElementById('g1'), g2 = document.getElementById('g2');
const RED = [[16.08, 18.3], [35.44, 36.3], [40.5, 44.5], [46.4, 47.8], [58.6, 59.75]];
const IMPACT = [8.16, 16.08, 35.44, 40.52, 42.88, 59.0];
const CUTS = scenes.map(s => s.t0).filter(x => x > 0);

window.seek = function (t) {
  scenes.forEach(s => {
    const vis = t >= s.t0 && t < s.t1;
    s.el.style.display = vis ? 'block' : 'none';
    if (vis) {
      s.update(s, t);
      const lt = t - s.t0, ent = clamp(lt / .28);
      const z = 1 + lt * .01 + (1 - E.out(ent)) * .2;
      let sx = 0, sy = 0;
      IMPACT.forEach(it => { const [a, b] = shake(t, it, 24, .45); sx += a; sy += b; });
      s.el.style.transform = `translate(${sx}px,${sy + (1 - E.out(ent)) * 30}px) scale(${z})`;
      s.el.style.filter = ent < 1 ? `blur(${(1 - ent) * 12}px)` : '';
    }
  });
  let fl = 0;
  CUTS.forEach(c => { if (t >= c && t < c + .15) fl = Math.max(fl, .22 * (1 - (t - c) / .15)); });
  IMPACT.forEach(c => { if (t >= c && t < c + .12) fl = Math.max(fl, .3 * (1 - (t - c) / .12)); });
  flash.style.opacity = fl;
  flash.style.background = t > 59.7 && t < 59.9 ? '#ff0018' : '#fff';
  if (t > 59.7 && t < 59.9) flash.style.opacity = .8;
  let rt = 0;
  RED.forEach(([a, b]) => { rt = Math.max(rt, clamp((t - a) / .15) * (1 - clamp((t - b) / .3))); });
  tint.style.opacity = rt * (.7 + .3 * Math.sin(t * 9));
  g1.style.background = t > 14.6 ? '#ff2a3d' : '#ff9a4d';
  g1.style.opacity = t > 21.7 && t < 50.5 ? .25 : .5;
  g1.style.transform = `translate(${Math.sin(t * .4) * 120}px,${Math.cos(t * .3) * 80}px)`;
  g2.style.transform = `translate(${Math.cos(t * .35) * 140}px,${Math.sin(t * .25) * 160}px)`;
  DUST.forEach(d => {
    const y = ((d.y - t * d.v) % 1920 + 1920) % 1920;
    d.e.style.transform = `translate(${d.x + Math.sin(t * .6 + d.ph) * 30}px,${y}px) scale(${d.s})`;
    d.e.style.opacity = .1 + .25 * (0.5 + .5 * Math.sin(t * 1.3 + d.ph));
  });
  gctx.putImageData(GR[Math.floor(t * 30) % GR.length], 0, 0);
  grain.style.transform = 'scale(1.9)';
  prog.style.width = (clamp(t / 59.7) * 1080) + 'px';
  header(t);
  captions(t);
};

window.ready = (async () => {
  const words = await fetch(A + 'words.json').then(r => r.json());
  buildGroups(words.words);
  scenes.forEach(s => s.build(s.el, s));
  await document.fonts.ready;
  const imgs = [...new Set([...document.querySelectorAll('*')].map(e => getComputedStyle(e).backgroundImage).join(',').match(/url\("?[^")]+"?\)/g) || [])];
  await Promise.all(imgs.map(u => new Promise(r => { const i = new Image(); i.onload = i.onerror = r; i.src = u.replace(/^url\("?|"?\)$/g, ''); })));
  return true;
})();
