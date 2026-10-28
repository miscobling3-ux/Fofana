// Moteur de motion design déterministe : window.seek(t) dessine l'image à l'instant t (secondes).
const DUR = 84.5;
const A = 'assets/';
const EMO = c => `url(${A}emoji/${c}.webp)`;

// ---------------------------------------------------------------- outils
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, p) => a + (b - a) * p;
const E = {
  lin: x => x,
  out: x => 1 - Math.pow(1 - x, 3),
  out5: x => 1 - Math.pow(1 - x, 5),
  in: x => x * x * x,
  io: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  back: x => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  elastic: x => (x === 0 || x === 1 ? x : Math.pow(2, -10 * x) * Math.sin((x * 10 - .75) * (2 * Math.PI) / 3) + 1),
};
const P = (t, t0, d, e = 'out') => E[e](clamp((t - t0) / d));
// interpolation par clés : [[t, v, ease], ...]
function K(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i];
    if (t <= t1) { const [t0, v0] = keys[i - 1]; return lerp(v0, v1, E[e || 'io']((t - t0) / (t1 - t0))); }
  }
  return keys[keys.length - 1][1];
}
// bruit doux pour les tremblements
const noise = (t, s = 1) => Math.sin(t * 13.1 * s) * .5 + Math.sin(t * 23.7 * s + 1.3) * .3 + Math.sin(t * 41.3 * s + 2.1) * .2;
function shake(t, t0, amp = 30, d = .45) {
  const k = t < t0 ? 0 : Math.max(0, 1 - (t - t0) / d);
  return [noise(t, 2.3) * amp * k * k, noise(t + 9, 2.1) * amp * k * k];
}
// petit « punch » de zoom (0 → pic → 0)
const punch = (t, t0, amt = .06, d = .5) => (t < t0 ? 0 : amt * Math.exp(-(t - t0) * 7 / d) * Math.sin(Math.min(Math.PI / 2, (t - t0) * 25)));
// apparition « pop » : renvoie [échelle, opacité]
function pop(t, t0, d = .38) {
  const p = clamp((t - t0) / d);
  return [p <= 0 ? .001 : E.back(p), clamp((t - t0) / (d * .4))];
}

function h(tag, cls, style, html, parent) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (style) e.style.cssText = style;
  if (html != null) e.innerHTML = html;
  if (parent) parent.appendChild(e);
  return e;
}
// positionne un élément par son centre
function set(el, o) {
  const x = o.x ?? 0, y = o.y ?? 0, s = o.s ?? 1, r = o.r ?? 0, sx = o.sx ?? 1, sy = o.sy ?? 1;
  el.style.transform = `translate(${x}px,${y}px) translate(-50%,-50%) rotate(${r}deg) scale(${s * sx},${s * sy})`;
  if (o.o != null) el.style.opacity = o.o;
  el.style.filter = o.b ? `blur(${o.b}px)` : (o.f || '');
}
function node(parent, cls, style, html) {
  return h('div', 'abs ' + (cls || ''), 'left:0;top:0;' + (style || ''), html, parent);
}
function emoji(parent, code, size = 200) {
  return node(parent, 'emoji', `width:${size}px;height:${size}px;background-image:${EMO(code)}`);
}

// ---------------------------------------------------------------- personnages (style silhouette, tête noire)
function character(o) {
  const shirt = o.shirt || '#f2f2f5', pants = o.pants || '#1b1d2e', id = o.id;
  let torso = '';
  if (o.kind === 'mao') {
    torso = `<path d="M70 215 Q150 190 230 215 L242 410 Q150 425 58 410 Z" fill="${shirt}"/>
      <path d="M118 200 L150 236 L182 200 L182 214 L150 250 L118 214Z" fill="#555a49"/>
      ${[255, 290, 325, 360, 395].map(y => `<circle cx="150" cy="${y}" r="6" fill="#3c4033"/>`).join('')}
      <rect x="88" y="262" width="44" height="30" rx="4" fill="none" stroke="#4a4e3f" stroke-width="4"/>
      <rect x="168" y="262" width="44" height="30" rx="4" fill="none" stroke="#4a4e3f" stroke-width="4"/>
      <rect x="86" y="340" width="48" height="40" rx="4" fill="none" stroke="#4a4e3f" stroke-width="4"/>
      <rect x="166" y="340" width="48" height="40" rx="4" fill="none" stroke="#4a4e3f" stroke-width="4"/>`;
  } else if (o.kind === 'suit') {
    torso = `<path d="M70 215 Q150 190 230 215 L242 410 Q150 425 58 410 Z" fill="${shirt}"/>
      <path d="M125 205 L150 300 L175 205Z" fill="#f4f4f8"/>
      <path d="M142 222 L158 222 L162 300 L150 320 L138 300Z" fill="#b3122e"/>
      <path d="M118 205 L150 330 L100 260Z" fill="#0d1226"/><path d="M182 205 L150 330 L200 260Z" fill="#0d1226"/>`;
  } else {
    torso = `<path d="M70 215 Q150 190 230 215 L242 410 Q150 425 58 410 Z" fill="${shirt}"/>
      <path d="M120 206 L150 250 L180 206" fill="none" stroke="#1f2a5c" stroke-width="10" stroke-linejoin="round"/>
      <path d="M70 215 L60 300" stroke="#c9a54a" stroke-width="6"/><path d="M230 215 L240 300" stroke="#c9a54a" stroke-width="6"/>
      <circle cx="195" cy="262" r="15" fill="none" stroke="#c9a54a" stroke-width="5"/>`;
  }
  const faces = `
    <g class="f-laugh" style="display:none"><path d="M100 112 q14 -16 28 0" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M172 112 q14 -16 28 0" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M115 145 q35 40 70 0 z" fill="#fff"/></g>
    <g class="f-shock" style="display:none"><circle cx="120" cy="110" r="20" fill="#fff"/><circle cx="182" cy="110" r="20" fill="#fff"/><circle cx="123" cy="112" r="8" fill="#0b0b10"/><circle cx="179" cy="112" r="8" fill="#0b0b10"/><ellipse cx="152" cy="160" rx="10" ry="13" fill="#fff"/></g>
    <g class="f-worry" style="display:none"><circle cx="120" cy="115" r="16" fill="#fff"/><circle cx="182" cy="115" r="16" fill="#fff"/><circle cx="122" cy="118" r="7" fill="#0b0b10"/><circle cx="180" cy="118" r="7" fill="#0b0b10"/><path d="M100 88 l38 10 M202 88 l-38 10" stroke="#fff" stroke-width="6" stroke-linecap="round"/><path d="M128 162 q24 -14 48 0" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/></g>
    <g class="f-glasses" style="display:${o.glasses ? 'block' : 'none'}"><rect x="96" y="96" width="46" height="30" rx="10" fill="none" stroke="#9fb4ff" stroke-width="5"/><rect x="160" y="96" width="46" height="30" rx="10" fill="none" stroke="#9fb4ff" stroke-width="5"/><path d="M142 108 h18" stroke="#9fb4ff" stroke-width="5"/></g>`;
  const hair = o.kind === 'mao'
    ? `<path d="M70 95 Q80 25 150 28 Q225 28 232 100 Q215 60 150 62 Q90 62 70 95Z" fill="#1d1d26"/>`
    : o.kind === 'player' ? `<path d="M78 80 Q100 30 150 32 Q205 32 224 80 Q190 52 150 54 Q110 54 78 80Z" fill="#14141c"/>` : '';
  return `<svg viewBox="0 0 300 620" width="${o.w || 300}" height="${(o.w || 300) * 620 / 300}" style="overflow:visible">
    <defs><radialGradient id="hd${id}" cx="35%" cy="30%" r="80%"><stop offset="0" stop-color="#2a2933"/><stop offset=".55" stop-color="#0d0c13"/><stop offset="1" stop-color="#050509"/></radialGradient></defs>
    <ellipse cx="150" cy="606" rx="120" ry="14" fill="rgba(0,0,0,.45)"/>
    <rect x="88" y="395" width="56" height="205" rx="24" fill="${pants}"/><rect x="156" y="395" width="56" height="205" rx="24" fill="${pants}"/>
    <rect x="40" y="225" width="44" height="190" rx="22" fill="${shirt}" transform="rotate(8 62 225)"/>
    <rect x="216" y="225" width="44" height="190" rx="22" fill="${shirt}" transform="rotate(-8 238 225)"/>
    <circle cx="44" cy="420" r="22" fill="#0d0c13"/><circle cx="256" cy="420" r="22" fill="#0d0c13"/>
    ${torso}
    <rect x="132" y="178" width="36" height="34" fill="#0d0c13"/>
    <circle cx="150" cy="118" r="88" fill="url(#hd${id})"/>
    <path d="M90 60 Q150 25 212 62" stroke="rgba(255,255,255,.18)" stroke-width="6" fill="none" stroke-linecap="round"/>
    ${hair}${faces}
  </svg>`;
}
function setFace(el, f) {
  ['laugh', 'shock', 'worry'].forEach(k => { const g = el.querySelector('.f-' + k); if (g) g.style.display = k === f ? 'block' : 'none'; });
}

function namecard(parent, name, sub, color) {
  return node(parent, 'namecard', '', `<i style="background:${color || 'var(--red)'}"></i><b>${name}</b><span>${sub}</span>`);
}

// ---------------------------------------------------------------- mise en place
const world = document.getElementById('world');
const city = h('div', 'abs', 'left:-200px;bottom:0;width:1480px;height:900px;z-index:1;opacity:.55', null, document.getElementById('stage'));
(function () {
  let r = 11; const rn = () => (r = (r * 16807) % 2147483647) / 2147483647;
  let svg = '<svg width="1480" height="900"><defs><linearGradient id="bld" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e1846"/><stop offset="1" stop-color="#07061a"/></linearGradient></defs>';
  for (let layer = 0; layer < 2; layer++) {
    let x = 0;
    while (x < 1480) {
      const w = 70 + rn() * 110, hh = (layer ? 260 : 420) + rn() * (layer ? 260 : 380);
      svg += `<rect x="${x}" y="${900 - hh}" width="${w}" height="${hh}" fill="${layer ? 'url(#bld)' : '#130f30'}"/>`;
      for (let wy = 900 - hh + 24; wy < 880; wy += 34) for (let wx = x + 12; wx < x + w - 16; wx += 26)
        if (rn() < (layer ? .22 : .1)) svg += `<rect x="${wx}" y="${wy}" width="12" height="16" fill="${rn() < .7 ? '#ffb35c' : '#a98bff'}" opacity="${.4 + rn() * .6}"/>`;
      x += w + 6;
    }
  }
  city.innerHTML = svg + '</svg>';
})();
const scenes = [];
function scene(t0, t1, build, update, cam) {
  const el = h('div', 'scene', '', null, world);
  const s = { t0, t1, el, update, build, cam: cam || 'zoom' };
  scenes.push(s);
  return s;
}

// ======== 1. ACCROCHE (0 – 5.17)
scene(0, 5.17, (el, s) => {
  s.flag = node(el, '', 'width:1500px;height:1000px;background:url(assets/cn.svg) center/cover;opacity:0;border-radius:20px');
  s.flagShade = node(el, '', 'width:1500px;height:1000px;background:linear-gradient(180deg,rgba(10,0,10,.2),rgba(10,0,20,.85));opacity:0');
  s.n1 = node(el, 'big', 'font-size:420px;color:#fff;text-shadow:0 20px 60px rgba(0,0,0,.6)', '1');
  s.n1l = node(el, 'big', 'font-size:84px;color:var(--gold);letter-spacing:6px', 'PHRASE');
  s.bubble = node(el, '', 'width:620px;height:250px;border-radius:60px;background:#fff;color:#111;display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:96px;box-shadow:0 30px 80px rgba(0,0,0,.5)', '« ... »');
  s.p = node(el, '', '', character({ id: 'p1', kind: 'player', w: 330 }));
  s.nc = namecard(el, 'Kylian Mbappé', 'Capitaine des Bleus · Real Madrid', '#3d6bff');
  s.chine = node(el, 'big', 'font-size:300px;color:var(--red);text-shadow:0 0 60px rgba(255,30,50,.8),0 20px 0 #000', 'CHINE');
}, (s, t) => {
  const [a, ao] = pop(t, 0.12, .4);
  set(s.n1, { x: 540, y: 620 - K(t, [[1.8, 0], [2.2, -80]]), s: a * (1 + punch(t, 1.2, .18)), o: ao * (1 - P(t, 1.85, .3)) });
  set(s.n1l, { x: 540, y: 880, s: pop(t, .3)[0], o: pop(t, .3)[1] * (1 - P(t, 1.85, .3)) });
  const [b, bo] = pop(t, 1.2, .35);
  set(s.bubble, { x: 540, y: 380, s: b * (1 - P(t, 1.85, .25, 'in')), o: bo, r: -4 });
  const pin = P(t, 2.0, .55, 'out5');
  set(s.p, { x: lerp(1300, 540, pin), y: 1010 + Math.sin(t * 5) * 6 * pin, s: 1.45 + P(t, 4.1, .9) * .3, r: lerp(18, 0, pin) });
  setFace(s.p, t > 4.15 ? 'shock' : 'none');
  const [n, no] = pop(t, 2.5, .35);
  set(s.nc, { x: 540, y: 1250, s: n, o: no * (1 - P(t, 4.0, .2)) });
  const f = P(t, 4.1, .5, 'out5');
  set(s.flag, { x: 540, y: 760, s: lerp(1.6, 1.05, f) + t * .01, o: f * .9 });
  set(s.flagShade, { x: 540, y: 760, s: lerp(1.6, 1.05, f), o: f });
  const [c, co] = pop(t, 4.12, .3);
  set(s.chine, { x: 540, y: 470, s: c * (1 + punch(t, 4.48, .12)), o: co, r: -3 });
}, 'none');

// ======== 2. L'INTERVIEW THE BRIDGE (5.17 – 10.04)
scene(5.17, 10.04, (el, s) => {
  s.sign = node(el, '', 'font-family:Anton;font-size:150px;letter-spacing:10px;color:#fff;text-shadow:0 0 18px #7d5cff,0 0 50px #7d5cff,0 0 100px #5b3cff;white-space:nowrap', 'THE BRIDGE');
  s.signSub = node(el, '', 'font-weight:800;font-size:30px;letter-spacing:12px;opacity:.7;white-space:nowrap', 'MÉDIA · INTERVIEW');
  s.light1 = node(el, '', 'width:500px;height:1200px;background:linear-gradient(180deg,rgba(160,130,255,.35),rgba(160,130,255,0));clip-path:polygon(40% 0,60% 0,100% 100%,0 100%)');
  s.p = node(el, '', '', character({ id: 'p2', kind: 'player', w: 300 }));
  s.mic = emoji(el, '1f399-fe0f', 240);
  s.vf = node(el, '', 'width:900px;height:1080px;border:0', `<svg width="900" height="1080" style="overflow:visible"><g stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round" opacity=".85"><path d="M0 90V0h90M810 0h90v90M900 990v90h-90M90 1080H0v-90"/></g></svg>`);
  s.rec = node(el, '', 'font-weight:900;font-size:40px;letter-spacing:3px;white-space:nowrap', '<span style="display:inline-block;width:26px;height:26px;border-radius:50%;background:#ff2d3d;margin-right:14px;vertical-align:-2px;box-shadow:0 0 16px #ff2d3d"></span>REC');
  s.q = node(el, 'card', 'width:760px;padding:34px 40px;font-size:46px;font-weight:800;line-height:1.2', '<span style="color:var(--gold);font-size:30px;letter-spacing:4px">QUESTION</span><br>Le mème le plus drôle sur toi ?');
  s.lol = [];
  for (let i = 0; i < 7; i++) s.lol.push(emoji(el, i % 2 ? '1f923' : '1f602', 150));
}, (s, t) => {
  const lt = t - 5.17;
  set(s.sign, { x: 540, y: 470, s: 1 + lt * .01, o: P(t, 5.2, .3) * (0.85 + .15 * Math.sin(t * 30) * (t < 6.9 && t > 6.6 ? 1 : 0)) * (1 - P(t, 7.5, .25)) });
  set(s.signSub, { x: 540, y: 575, o: P(t, 6.7, .3) * (1 - P(t, 7.5, .25)) });
  set(s.light1, { x: 540, y: 820, o: .8 });
  set(s.p, { x: 540, y: 1060, s: 1.4 + lt * .03 });
  setFace(s.p, 'none');
  set(s.mic, { x: 730, y: 1060, r: -12, s: pop(t, 5.5)[0] });
  set(s.vf, { x: 540, y: 820, s: 1.06 - P(t, 5.17, .5) * .06, o: P(t, 5.17, .3) });
  set(s.rec, { x: 200, y: 318, o: (Math.floor(t * 2) % 2 ? .35 : 1) * P(t, 5.3, .2) });
  const [q, qo] = pop(t, 7.6, .4);
  set(s.q, { x: 540, y: 500, s: q, o: qo * (1 - P(t, 9.8, .2)) });
  s.lol.forEach((e, i) => {
    const t0 = 8.44 + i * .09, p = clamp((t - t0) / 1.4);
    const ang = -90 + (i - 3) * 26;
    const d = 180 + E.out(p) * 380;
    set(e, { x: 540 + Math.cos(ang * Math.PI / 180) * d, y: 760 + Math.sin(ang * Math.PI / 180) * d * .9 + p * p * 160, s: pop(t, t0, .3)[0] * (1 - p * .3), r: (i - 3) * 14 + p * 40 * (i % 2 ? 1 : -1), o: t < t0 ? 0 : 1 - P(t, t0 + 1.1, .3) });
  });
});

// ======== 3. LE MÈME : TÊTE COLLÉE SUR UN DICTATEUR (10.04 – 15.44)
scene(10.04, 15.44, (el, s) => {
  s.p = node(el, '', '', character({ id: 'p3', kind: 'player', w: 300 }));
  s.haha = node(el, 'big', 'font-size:120px;color:var(--gold);white-space:nowrap;text-shadow:0 8px 0 #000', 'HAHA');
  s.frame = node(el, '', 'width:640px;height:820px;border-radius:26px;background:linear-gradient(180deg,#d9cfb4,#b8ab8a);box-shadow:0 40px 90px rgba(0,0,0,.6);overflow:hidden;border:16px solid #f4efe2');
  s.frame.innerHTML = `<div style="position:absolute;inset:0;background:radial-gradient(70% 60% at 50% 40%,#e8dcc0,#a8996f)"></div>
    <div style="position:absolute;left:50%;top:270px;transform:translateX(-50%)">${character({ id: 'm3', kind: 'mao', shirt: '#7b806a', pants: '#5e6252', w: 470 })}</div>
    <div style="position:absolute;left:24px;top:20px;font-weight:900;font-size:28px;color:#5a4d2c;letter-spacing:4px">MÈME</div>`;
  s.maohead = s.frame.querySelector('circle[fill^="url"]');
  s.head = node(el, '', 'width:250px;height:250px', `<svg viewBox="0 0 250 250" width="250" height="250" style="overflow:visible"><defs><radialGradient id="hh" cx="35%" cy="30%" r="80%"><stop offset="0" stop-color="#2a2933"/><stop offset=".55" stop-color="#0d0c13"/><stop offset="1" stop-color="#050509"/></radialGradient></defs><circle cx="125" cy="125" r="112" fill="url(#hh)" stroke="#fff" stroke-width="7" stroke-dasharray="16 12"/><path d="M50 82 Q75 30 125 30 Q180 30 200 82 Q165 55 125 56 Q85 56 50 82Z" fill="#14141c"/><g><path d="M78 118 q16 -18 32 0" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round"/><path d="M140 118 q16 -18 32 0" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round"/><path d="M92 155 q33 40 66 0 z" fill="#fff"/></g></svg>`);
  s.tape1 = node(el, '', 'width:160px;height:46px;background:rgba(255,240,180,.75);box-shadow:0 4px 10px rgba(0,0,0,.3)');
  s.tape2 = node(el, '', 'width:160px;height:46px;background:rgba(255,240,180,.75);box-shadow:0 4px 10px rgba(0,0,0,.3)');
  s.scis = node(el, 'big', 'font-size:70px;color:#fff;white-space:nowrap', '✂');
  s.stamp = node(el, 'stamp', 'font-size:96px', 'DICTATEUR CHINOIS');
}, (s, t) => {
  // Kylian rit puis la scène bascule sur le montage
  const out = P(t, 12.2, .45, 'in');
  set(s.p, { x: 540 - out * 900, y: 1040 + Math.abs(Math.sin(t * 14)) * -22 * (1 - out), s: 1.5, r: Math.sin(t * 14) * 3 - out * 20 });
  setFace(s.p, t > 10.6 ? 'laugh' : 'none');
  const [hh, ho] = pop(t, 10.85, .35);
  set(s.haha, { x: 720, y: 520 + Math.sin(t * 12) * 8, s: hh, r: 8, o: ho * (1 - out) });
  const fin = P(t, 12.1, .55, 'out5');
  set(s.frame, { x: lerp(1500, 540, fin), y: 800, r: lerp(15, -2, fin), s: 1 });
  // tête découpée qui vient se coller
  const hp = P(t, 12.6, .55, 'back');
  set(s.head, { x: lerp(980, 540, hp), y: lerp(250, 842, hp), r: lerp(40, -4, hp), s: lerp(1.5, 1.22, hp) * (1 + punch(t, 13.0, .1)), o: P(t, 12.5, .1) });
  const tp = P(t, 13.05, .2);
  set(s.tape1, { x: 430, y: 720, r: -32, o: tp, s: lerp(1.5, 1, tp) });
  set(s.tape2, { x: 655, y: 720, r: 30, o: P(t, 13.2, .2), s: lerp(1.5, 1, P(t, 13.2, .2)) });
  set(s.scis, { x: lerp(1000, 760, P(t, 12.3, .5)), y: 300, r: K(t, [[12.3, 0], [12.8, -30], [13, 10]]), o: P(t, 12.3, .2) * (1 - P(t, 13.4, .2)) });
  const [st, so] = pop(t, 14.08, .3);
  set(s.stamp, { x: 540, y: 1190, s: lerp(2.2, 1, E.out(clamp((t - 14.08) / .25))) * (t < 14.08 ? 0 : 1), r: -7, o: so });
});

// ======== 4. MAO ZEDONG (15.44 – 22.24)
scene(15.44, 22.24, (el, s) => {
  s.q = node(el, 'big', 'font-size:520px;color:#fff;text-shadow:0 0 60px rgba(255,255,255,.4)', '?');
  s.gate = node(el, '', 'width:1000px;height:600px', `<svg viewBox="0 0 1000 600" width="1000" height="600">
    <defs><linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c8202d"/><stop offset="1" stop-color="#7a0f1a"/></linearGradient>
    <linearGradient id="roof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffcf4d"/><stop offset="1" stop-color="#d48b12"/></linearGradient></defs>
    <rect x="40" y="330" width="920" height="270" fill="url(#wall)"/>
    <rect x="20" y="320" width="960" height="22" fill="#e9e3d0"/>
    ${[0, 1, 2, 3, 4].map(i => `<path d="M${200 + i * 150} 600 v-130 a50 50 0 0 1 100 0 v130z" fill="#3a0910"/>`).join('')}
    <rect x="150" y="200" width="700" height="120" fill="#b81c28"/>
    ${Array.from({ length: 13 }, (_, i) => `<rect x="${165 + i * 52}" y="215" width="16" height="105" fill="#7a0f1a"/>`).join('')}
    <path d="M60 205 Q500 150 940 205 L880 160 Q500 120 120 160Z" fill="url(#roof)"/>
    <rect x="200" y="100" width="600" height="62" fill="#b81c28"/>
    <path d="M150 110 Q500 40 850 110 L800 60 Q500 10 200 60Z" fill="url(#roof)"/>
    <rect x="445" y="360" width="110" height="140" fill="#2b2a24" stroke="#ffcf4d" stroke-width="6"/>
    <circle cx="500" cy="410" r="32" fill="#0d0c13"/><path d="M455 500 Q500 440 545 500Z" fill="#6c705b"/>
  </svg>`);
  s.mao = node(el, '', '', character({ id: 'm4', kind: 'mao', shirt: '#7b806a', pants: '#5e6252', w: 360 }));
  s.nc = namecard(el, 'Mao Zedong', 'Fondateur de la Chine communiste · 1893-1976', '#ffcf4d');
  s.flag = node(el, '', 'width:900px;height:600px;background:url(assets/cn.svg) center/cover;border-radius:16px;box-shadow:0 30px 80px rgba(0,0,0,.6)');
  s.lock = emoji(el, '1f512', 300);
  s.stamp = node(el, 'stamp', 'font-size:120px;color:var(--gold);border-color:var(--gold);text-shadow:0 0 30px rgba(255,200,60,.6);box-shadow:0 0 40px rgba(255,200,60,.35)', 'INTOUCHABLE');
  s.rays = node(el, '', 'width:1600px;height:1600px;background:repeating-conic-gradient(rgba(255,207,77,.12) 0 8deg,rgba(255,207,77,0) 8deg 18deg);border-radius:50%');
  el.prepend(s.rays);
}, (s, t) => {
  const [q, qo] = pop(t, 15.5, .35);
  set(s.q, { x: 540, y: 760, s: q * (1 + .04 * Math.sin(t * 10)), o: qo * (1 - P(t, 16.75, .15)) });
  const g = P(t, 16.85, .6, 'out5');
  set(s.gate, { x: 540, y: lerp(1000, 720, g) - P(t, 19.9, .6) * 60, s: lerp(1.25, 1, g), o: g * (1 - P(t, 18.9, .3) * .0) });
  set(s.rays, { x: 540, y: 720, r: t * 6, o: P(t, 16.85, .5) * .9 });
  const m = P(t, 16.9, .5, 'back');
  set(s.mao, { x: 540, y: lerp(1600, 1080, m), s: 1.15 + P(t, 16.85, 6) * .08 });
  set(s.nc, { x: 540, y: 1260, s: pop(t, 17.2)[0], o: pop(t, 17.2)[1] * (1 - P(t, 18.9, .2)) });
  // drapeau qui balaie sur « Chine communiste »
  const f = P(t, 18.85, .45, 'out5');
  set(s.flag, { x: lerp(-700, 540, f) - P(t, 19.95, .4, 'in') * 1400, y: 640, r: lerp(-12, 3, f), o: f });
  const [l, lo] = pop(t, 20.9, .35);
  set(s.lock, { x: 540, y: 640, s: l * (1 + punch(t, 21.2, .15)), o: lo });
  const st = clamp((t - 21.2) / .22);
  set(s.stamp, { x: 540, y: 1250, s: t < 21.2 ? 0 : lerp(2.4, 1, E.out(st)), r: -6, o: st });
});

// ======== 5. LA VIDÉO EXPLOSE EN CHINE (22.24 – 26.77)
scene(22.24, 26.77, (el, s) => {
  s.ph = node(el, 'phone', '', `<div class="notch"></div><div class="scr" style="background:#101015">
     <div style="background:linear-gradient(90deg,#ff5a2b,#ff8a20);height:170px;padding:80px 34px 0;color:#fff;font-size:38px;font-weight:900;letter-spacing:2px">热门 <span style="font-size:24px;opacity:.85;font-weight:700;margin-left:10px">RÉSEAUX CHINOIS</span></div>
     <div style="margin:26px;border-radius:26px;overflow:hidden;background:#1c1c24">
       <div style="position:relative;height:440px;background:radial-gradient(70% 60% at 50% 40%,#e8dcc0,#a8996f)">
         <div style="position:absolute;left:50%;top:40px;transform:translateX(-50%) scale(.62);transform-origin:50% 0">${character({ id: 'm5', kind: 'mao', shirt: '#7b806a', pants: '#5e6252', w: 470 })}</div>
         <div style="position:absolute;left:50%;top:76px;width:180px;height:180px;margin-left:-90px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#2a2933,#050509);border:5px dashed #fff"></div>
         <div style="position:absolute;left:50%;top:50%;width:110px;height:110px;margin:-55px 0 0 -55px;border-radius:50%;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;font-size:56px">▶</div>
       </div>
       <div style="padding:22px 24px;font-size:34px;font-weight:900;color:#fff">#姆巴佩# <span style="font-size:22px;color:#aaa;letter-spacing:2px">MBAPPÉ</span></div>
       <div class="reac" style="display:flex;gap:26px;padding:0 24px 26px;font-size:40px"></div>
     </div></div>`);
  s.rows = [];
  ['♥', '💬', '↗'].forEach(ic => s.rows.push(h('div', '', 'display:flex;align-items:center;gap:10px;color:#ff5a3c;font-weight:900', `${ic}<div class="bar" style="height:14px;width:0;border-radius:7px;background:#ff5a3c"></div>`, s.ph.querySelector('.reac'))));
  s.fires = [];
  for (let i = 0; i < 6; i++) s.fires.push(emoji(el, ['1f525', '1f621', '1f92c'][i % 3], 170));
  s.slab = node(el, 'big', 'font-size:210px;color:#fff;background:var(--red);padding:20px 50px 30px;border-radius:24px;box-shadow:0 40px 90px rgba(0,0,0,.6),0 0 80px rgba(255,40,60,.5);white-space:nowrap', 'SANCTION');
}, (s, t) => {
  const pin = P(t, 22.24, .45, 'out5');
  const out = P(t, 25.45, .3, 'in');
  set(s.ph, { x: 540, y: lerp(1500, 780, pin) + out * 200, r: lerp(10, 0, pin), s: (.92 + P(t, 22.3, 3) * .06) * (1 - out * .2), o: 1 - out * .7 });
  s.rows.forEach((r, i) => {
    r.querySelector('.bar').style.width = (E.out(clamp((t - 23.7 - i * .1) / 1.2)) * (70 - i * 12)) + 'px';
    r.style.transform = `scale(${1 + punch(t, 23.76 + i * .1, .2)})`;
  });
  s.fires.forEach((e, i) => {
    const t0 = 23.76 + i * .1, p = clamp((t - t0) / 1.6);
    const side = i % 2 ? 1 : -1;
    set(e, { x: 540 + side * (330 + (i % 3) * 40) + side * p * 60, y: 1150 - E.out(p) * (520 + i * 70), s: pop(t, t0, .3)[0] * (1 - .2 * p), r: side * 15 * p, o: t < t0 ? 0 : 1 - P(t, 25.4, .2) });
  });
  const sp = clamp((t - 25.52) / .28);
  set(s.slab, { x: 540, y: lerp(-300, 760, E.in(sp)), r: lerp(-14, -4, sp), s: 1 + punch(t, 25.8, .12) });
});

// ======== 6. DONGPENG ROMPT (26.77 – 35.8)
function canSVG() {
  return `<svg viewBox="0 0 260 520" width="260" height="520">
    <defs><linearGradient id="can" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a0d12"/><stop offset=".35" stop-color="#e3262b"/><stop offset=".55" stop-color="#ff5a4a"/><stop offset="1" stop-color="#7a0b10"/></linearGradient>
    <linearGradient id="lid" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8d8d96"/><stop offset=".5" stop-color="#f1f1f5"/><stop offset="1" stop-color="#7c7c86"/></linearGradient></defs>
    <rect x="20" y="40" width="220" height="440" rx="26" fill="url(#can)"/>
    <ellipse cx="130" cy="40" rx="110" ry="22" fill="url(#lid)"/><ellipse cx="130" cy="480" rx="110" ry="22" fill="#5b0a0e"/>
    <rect x="20" y="150" width="220" height="160" fill="#ffd23d"/>
    <text x="130" y="236" font-family="WenQuanYi Zen Hei, sans-serif" font-size="70" font-weight="900" text-anchor="middle" fill="#b10f18">东鹏</text>
    <text x="130" y="290" font-family="WenQuanYi Zen Hei, sans-serif" font-size="40" font-weight="900" text-anchor="middle" fill="#b10f18">特饮</text>
    <path d="M150 340 L110 410 L138 410 L120 460 L175 380 L146 380 L165 340Z" fill="#ffd23d"/>
    <rect x="40" y="60" width="26" height="400" rx="13" fill="rgba(255,255,255,.25)"/></svg>`;
}
function contractHTML(brand, color) {
  return `<div style="font-size:24px;letter-spacing:6px;font-weight:900;color:#888">CONTRAT DE SPONSORING</div>
    <div style="font-family:Anton;font-size:76px;color:${color};margin:16px 0 18px;letter-spacing:2px">${brand}</div>
    <div style="font-size:30px;font-weight:800;color:#333">× KYLIAN MBAPPÉ</div>
    ${[0, 1, 2, 3, 4, 5].map(i => `<div style="height:16px;border-radius:8px;background:#ddd;margin-top:20px;width:${92 - (i % 3) * 14}%"></div>`).join('')}
    <div style="margin-top:40px;font-family:'Brush Script MT',cursive;font-size:54px;color:#1d3fa8">K. Mbappé</div>`;
}
function tearable(parent, html) {
  const wrap = node(parent, '', 'width:600px;height:780px');
  const mk = clip => h('div', '', `position:absolute;inset:0;background:#fbfaf6;border-radius:18px;padding:50px 46px;color:#111;clip-path:${clip};box-shadow:0 30px 70px rgba(0,0,0,.55)`, html, wrap);
  const L = mk('polygon(0 0,52% 0,47% 14%,55% 28%,46% 42%,54% 57%,47% 71%,53% 86%,48% 100%,0 100%)');
  const R = mk('polygon(52% 0,100% 0,100% 100%,48% 100%,53% 86%,47% 71%,54% 57%,46% 42%,55% 28%,47% 14%)');
  return { wrap, L, R };
}
scene(26.77, 35.8, (el, s) => {
  s.cal = node(el, '', 'width:360px;height:380px;border-radius:36px;background:#fff;color:#111;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);text-align:center',
    '<div style="background:var(--red);color:#fff;font-weight:900;font-size:46px;padding:22px 0;letter-spacing:4px">MARDI</div><div style="font-family:Anton;font-size:190px;line-height:1.15">27</div><div style="font-weight:900;font-size:36px;letter-spacing:6px;margin-top:-14px">OCT.</div>');
  s.can = node(el, '', '', canSVG());
  s.bolt = emoji(el, '26a1', 200);
  s.nc = namecard(el, 'Dongpeng', 'Géant chinois des boissons énergisantes', '#ffd23d');
  s.ct = tearable(el, contractHTML('DONGPENG', '#c8141d'));
  s.x = node(el, 'big', 'font-size:300px;color:var(--red);text-shadow:0 0 50px rgba(255,30,50,.8)', '✕');
  s.quote = node(el, 'quote', 'width:960px;font-size:110px;color:#fff', '<span style="color:var(--red)">«</span> HEURTÉ LES<br><span style="color:var(--gold)">SENTIMENTS<br>NATIONAUX</span> <span style="color:var(--red)">»</span>');
  s.motif = node(el, 'tag', 'background:#fff;color:#111;font-size:40px', 'MOTIF OFFICIEL');
  s.zero = node(el, 'big', 'font-size:640px;color:#ff2238;text-shadow:0 0 40px #ff2238,0 0 120px rgba(255,30,50,.8)', '0');
  s.zl = node(el, 'big', 'font-size:96px;color:#fff;letter-spacing:8px;white-space:nowrap', 'TOLÉRANCE');
}, (s, t) => {
  const [c, co] = pop(t, 26.8, .35);
  const calOut = P(t, 27.25, .3, 'in');
  set(s.cal, { x: 540 + calOut * -900, y: 720, s: c, r: -5 + calOut * -20, o: co });
  const cin = P(t, 27.3, .5, 'back');
  const cOut = P(t, 29.5, .3, 'in');
  set(s.can, { x: lerp(1400, 540, cin) + cOut * 1200, y: 760 + Math.sin(t * 3) * 10, r: lerp(25, -6, cin) + Math.sin(t * 2) * 2, s: 1.05 });
  set(s.bolt, { x: 760 + cOut * 1200, y: 500, s: pop(t, 28.6)[0], r: 12, o: pop(t, 28.6)[1] });
  set(s.nc, { x: 540, y: 1230, s: pop(t, 27.6)[0], o: pop(t, 27.6)[1] * (1 - cOut) });
  // contrat déchiré
  const ci = P(t, 29.55, .35, 'out5');
  const tear = P(t, 29.95, .4, 'out');
  const ctOut = P(t, 30.8, .3, 'in');
  set(s.ct.wrap, { x: 540, y: lerp(1700, 760, ci) + ctOut * 1300, s: 1, o: ci * (1 - ctOut) });
  set(s.ct.L, { x: 300 - tear * 90, y: 390 + tear * 60, r: -tear * 14 });
  set(s.ct.R, { x: 300 + tear * 90, y: 390 + tear * 90, r: tear * 16 });
  s.ct.L.style.left = s.ct.R.style.left = '0'; s.ct.L.style.top = s.ct.R.style.top = '0';
  s.ct.L.style.width = s.ct.R.style.width = '600px'; s.ct.L.style.height = s.ct.R.style.height = '780px';
  const [x, xo] = pop(t, 29.95, .3);
  set(s.x, { x: 540, y: 760, s: x * (1 + punch(t, 30.1, .1)), o: xo * (1 - ctOut) });
  // citation
  const qa = P(t, 30.9, .3);
  const qOut = P(t, 34.25, .25, 'in');
  set(s.motif, { x: 540, y: 420, s: pop(t, 30.85)[0], o: pop(t, 30.85)[1] * (1 - qOut) });
  set(s.quote, { x: 540, y: 760 - qOut * 200, s: (lerp(.8, 1, E.back(clamp((t - 32.5) / .4))) + (t - 32.5) * .01) * (1 + punch(t, 33.16, .06)), o: clamp((t - 32.45) / .15) * (1 - qOut) });
  // zéro
  const [z, zo] = pop(t, 35.05, .35);
  set(s.zero, { x: 540, y: 820, s: z * (1 + punch(t, 35.12, .14)) + Math.max(0, t - 35.2) * .03, o: zo });
  set(s.zl, { x: 540, y: 470, s: pop(t, 34.37, .3)[0], o: pop(t, 34.37, .3)[1] });
});

// ======== 7. MENGNIU (35.8 – 41.68)
function milkSVG() {
  return `<svg viewBox="0 0 300 520" width="300" height="520">
    <defs><linearGradient id="mk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d9dde6"/><stop offset=".4" stop-color="#ffffff"/><stop offset="1" stop-color="#b9bfcc"/></linearGradient></defs>
    <path d="M40 140 L150 40 L260 140 Z" fill="#e6e9f0"/><rect x="120" y="10" width="60" height="40" fill="#e6e9f0"/>
    <rect x="40" y="140" width="220" height="360" fill="url(#mk)"/>
    <path d="M40 330 Q90 290 150 330 T260 320 V500 H40Z" fill="#17a34a"/>
    <text x="150" y="240" font-family="WenQuanYi Zen Hei, sans-serif" font-size="78" font-weight="900" text-anchor="middle" fill="#127c39">蒙牛</text>
    <text x="150" y="300" font-family="InterV, sans-serif" font-size="34" font-weight="900" text-anchor="middle" fill="#127c39" letter-spacing="4">MENGNIU</text>
    <rect x="58" y="150" width="20" height="340" rx="10" fill="rgba(255,255,255,.5)"/></svg>`;
}
scene(35.8, 41.68, (el, s) => {
  s.milk = node(el, '', '', milkSVG());
  s.drop = emoji(el, '1f95b', 220);
  s.nc = namecard(el, 'Mengniu', 'Mastodonte chinois du lait', '#17a34a');
  s.ct = tearable(el, contractHTML('MENGNIU', '#127c39'));
  s.copy = node(el, 'stamp', 'font-size:110px', 'IDEM');
  s.cards = [];
  [['DONGPENG', '#c8141d'], ['MENGNIU', '#127c39'], ['???', '#666']].forEach(([n, c], i) => {
    s.cards.push(node(el, '', `width:290px;height:380px;border-radius:26px;background:${i === 2 ? '#1b1834' : '#fbfaf6'};border:${i === 2 ? '4px dashed rgba(255,255,255,.5)' : '0'};box-shadow:0 26px 60px rgba(0,0,0,.55);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center`,
      `<div style="font-family:Anton;font-size:${i === 2 ? 120 : 52}px;color:${i === 2 ? '#fff' : c}">${n}</div><div style="margin-top:14px;font-weight:900;font-size:24px;letter-spacing:4px;color:${i === 2 ? '#aaa' : '#888'}">${i === 2 ? 'SPONSOR N°3' : 'SPONSOR'}</div>`));
  });
  s.crosses = s.cards.map(() => node(el, 'big', 'font-size:260px;color:var(--red);text-shadow:0 0 40px rgba(255,30,50,.8)', '✕'));
}, (s, t) => {
  const m = P(t, 36.4, .45, 'back');
  const mOut = P(t, 38.35, .3, 'in');
  set(s.milk, { x: lerp(-400, 540, m) - mOut * 1200, y: 760 + Math.sin(t * 3) * 10, r: lerp(-25, 4, m) });
  set(s.drop, { x: 330 - mOut * 1200, y: 520, s: pop(t, 37.9)[0], o: pop(t, 37.9)[1] });
  set(s.nc, { x: 540, y: 1230, s: pop(t, 36.7)[0], o: pop(t, 36.7)[1] * (1 - mOut) });
  const ci = P(t, 38.35, .3, 'out5');
  const tear = P(t, 38.9, .35);
  const ctOut = P(t, 39.85, .25, 'in');
  set(s.ct.wrap, { x: 540, y: lerp(1700, 760, ci) + ctOut * 1300, o: ci * (1 - ctOut) });
  [s.ct.L, s.ct.R].forEach((e, i) => { e.style.left = '0'; e.style.top = '0'; e.style.width = '600px'; e.style.height = '780px'; });
  set(s.ct.L, { x: 300 - tear * 90, y: 390 + tear * 60, r: -tear * 14 });
  set(s.ct.R, { x: 300 + tear * 90, y: 390 + tear * 90, r: tear * 16 });
  const cs = clamp((t - 39.2) / .22);
  set(s.copy, { x: 540, y: 1210, s: t < 39.2 ? 0 : lerp(2.2, 1, E.out(cs)), r: -8, o: cs * (1 - ctOut) });
  // les 3 sponsors alignés
  s.cards.forEach((c, i) => {
    const t0 = 39.9 + i * .12, [a, o] = pop(t, t0, .35);
    set(c, { x: 200 + i * 340, y: 760 + (i === 1 ? -30 : 0), s: a * (i === 2 ? 1 + .03 * Math.sin(t * 8) : 1), r: (i - 1) * 6, o });
    const xt = i < 2 ? 40.2 + i * .15 : 40.95;
    const [xs, xo] = pop(t, xt, .25);
    set(s.crosses[i], { x: 200 + i * 340, y: 760, s: xs * (i === 2 ? .8 : 1), o: xo * (i === 2 ? .55 : 1) });
  });
});

// ======== 8. PÉKIN S'EN MÊLE : CARTE + PORTE-PAROLE (41.68 – 50.84)
scene(41.68, 50.84, (el, s) => {
  // carte (projection équirectangulaire simple)
  const topo = window.TOPO;
  const fc = topojson.feature(topo, topo.objects.countries);
  const k = 14, X = lon => (lon + 20) * k, Y = lat => (75 - lat) * k * 1.12;
  const path = g => {
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
    return polys.map(p => p.map(r => 'M' + r.map(([a, b]) => `${X(a).toFixed(1)},${Y(b).toFixed(1)}`).join('L') + 'Z').join('')).join('');
  };
  let paths = '';
  fc.features.forEach(f => {
    const id = f.id;
    const fill = id === '156' ? '#e02435' : id === '724' ? '#ffc83d' : id === '250' ? '#4b6bff' : '#2b2552';
    const stroke = id === '156' ? '#ff7d88' : '#3b3470';
    paths += `<path d="${path(f.geometry)}" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`;
  });
  const mx = X(-3.7), my = Y(40.4), bx = X(116.4), by = Y(39.9);
  s.mapW = X(160); s.mapH = Y(-10);
  s.pts = { mx, my, bx, by };
  s.map = node(el, '', `width:${s.mapW}px;height:${s.mapH}px`, `<svg width="${s.mapW}" height="${s.mapH}" style="overflow:visible">
    <g opacity=".95">${paths}</g>
    <path id="arc" d="M${mx},${my} Q${(mx + bx) / 2},${my - 900} ${bx},${by}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-dasharray="30 22"/>
    <g id="pinM"><circle cx="${mx}" cy="${my}" r="22" fill="#ffc83d" stroke="#fff" stroke-width="6"/></g>
    <g id="pinB"><circle cx="${bx}" cy="${by}" r="40" fill="none" stroke="#fff" stroke-width="6" class="ring"/><circle cx="${bx}" cy="${by}" r="24" fill="#fff"/></g>
    <text x="${mx}" y="${my + 80}" font-family="Anton" font-size="64" fill="#ffc83d" text-anchor="middle">MADRID</text>
    <text x="${bx}" y="${by - 70}" font-family="Anton" font-size="96" fill="#fff" text-anchor="middle" id="pkLab">PÉKIN</text>
  </svg>`);
  s.arc = s.map.querySelector('#arc');
  s.arcLen = s.arc.getTotalLength();
  s.ring = s.map.querySelector('.ring');
  s.pk = s.map.querySelector('#pkLab');
  // porte-parole au pupitre
  s.back = node(el, '', 'width:1080px;height:1100px;background:linear-gradient(180deg,#123a7a,#0b2050);border-top:6px solid #2d5fb3', `<div style="position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(255,255,255,.04) 0 2px,transparent 2px 120px)"></div>`);
  s.guo = node(el, '', '', character({ id: 'g8', kind: 'suit', shirt: '#151b33', pants: '#101425', glasses: true, w: 340 }));
  s.desk = node(el, '', 'width:520px;height:420px', `<svg viewBox="0 0 520 420" width="520" height="420"><path d="M40 60 H480 L440 420 H80Z" fill="#6b3b1f"/><path d="M40 60 H480 L470 100 H50Z" fill="#8a4f2a"/><circle cx="260" cy="210" r="70" fill="#d8b04a"/><circle cx="260" cy="210" r="56" fill="#b81c28"/><path d="M260 170 l12 36 h38 l-30 22 l12 36 l-32 -22 l-32 22 l12 -36 l-30 -22 h38z" fill="#ffd23d"/><path d="M200 60 L170 -60 M320 60 L350 -60" stroke="#222" stroke-width="10"/><rect x="150" y="-90" width="40" height="50" rx="16" fill="#333"/><rect x="330" y="-90" width="40" height="50" rx="16" fill="#333"/></svg>`);
  s.nc = namecard(el, 'Guo Jiakun', 'Porte-parole · Ministère chinois des Affaires étrangères', '#e02435');
  s.quote = node(el, 'card', 'width:900px;padding:44px 50px;text-align:left', `<div style="font-weight:900;font-size:28px;letter-spacing:6px;color:var(--red)">PÉKIN PRÉVIENT</div><div style="font-family:Anton;font-size:84px;line-height:1.05;margin-top:16px;text-transform:uppercase">« Ces propos se heurtent au <span style="color:var(--red)">rejet</span> de toute la société chinoise »</div>`);
}, (s, t) => {
  // caméra sur la carte : de Madrid vers Pékin
  const pm = clamp((t - 41.68) / 2.3);
  const cx = lerp(s.pts.mx, s.pts.bx, E.io(clamp((t - 42.1) / 1.0)));
  const cy = lerp(s.pts.my, s.pts.by, E.io(clamp((t - 42.1) / 1.0))) - 80;
  const z = lerp(.55, 1.0, E.io(clamp((t - 42.1) / 1.1))) * (1 + punch(t, 42.9, .08));
  const mapOut = P(t, 43.75, .35, 'in');
  s.map.style.transformOrigin = '0 0';
  s.map.style.transform = `translate(${540 - cx * z}px,${760 - cy * z}px) scale(${z})`;
  s.map.style.opacity = 1 - mapOut;
  s.map.style.filter = mapOut > 0 ? `blur(${mapOut * 20}px)` : '';
  s.arc.style.strokeDashoffset = 0;
  s.arc.setAttribute('stroke-dasharray', `${s.arcLen * clamp((t - 41.8) / 1.2)} ${s.arcLen}`);
  s.ring.setAttribute('r', 40 + ((t * 60) % 60));
  s.ring.setAttribute('opacity', 1 - ((t * 60) % 60) / 60);
  s.pk.setAttribute('opacity', clamp((t - 42.85) / .15));
  const bi = P(t, 43.8, .45, 'out5');
  set(s.back, { x: 540, y: lerp(1900, 900, bi), o: bi });
  set(s.guo, { x: 540, y: lerp(2100, 960, P(t, 43.85, .5, 'back')), s: 1.25 + (t - 44) * .01, o: t > 43.8 ? 1 : 0 });
  set(s.desk, { x: 540, y: lerp(2300, 1250, P(t, 43.95, .5, 'out5')), s: 1.15 });
  const qOut = P(t, 47.4, .3);
  set(s.nc, { x: 540, y: 470, s: pop(t, 44.05)[0], o: pop(t, 44.05)[1] * (1 - qOut) });
  const [q, qo] = pop(t, 47.55, .4);
  set(s.quote, { x: 540, y: 620, s: q * (1 + punch(t, 48.72, .05)), o: qo });
});

// ======== 9. LA TÉLÉ D'ÉTAT COUPE LA LIGA (50.84 – 55.25)
scene(50.84, 55.25, (el, s) => {
  s.tv = node(el, '', 'width:900px;height:720px;border-radius:60px;background:linear-gradient(180deg,#3a3550,#1c1930);padding:44px;box-shadow:0 40px 100px rgba(0,0,0,.7),inset 0 2px 0 rgba(255,255,255,.15)',
    `<div class="scr" style="position:relative;width:100%;height:100%;border-radius:30px;overflow:hidden;background:#1f7a3a">
      <div class="pitch" style="position:absolute;inset:0;background:repeating-linear-gradient(90deg,#238a42 0 80px,#1f7a3a 80px 160px)"></div>
      <svg style="position:absolute;inset:0" width="812" height="632"><g stroke="rgba(255,255,255,.75)" stroke-width="5" fill="none"><rect x="30" y="30" width="752" height="572"/><path d="M406 30V602"/><circle cx="406" cy="316" r="90"/><rect x="30" y="196" width="110" height="240"/><rect x="672" y="196" width="110" height="240"/></g></svg>
      <div style="position:absolute;left:24px;top:24px;background:rgba(0,0,0,.75);border-radius:12px;padding:10px 20px;font-weight:900;font-size:30px;letter-spacing:2px">LALIGA <span style="color:var(--gold)">EN DIRECT</span></div>
      <div class="ball emoji" style="width:70px;height:70px;background-image:${EMO('26bd')}"></div>
      <canvas class="static" width="203" height="158" style="position:absolute;inset:0;width:100%;height:100%;opacity:0;image-rendering:pixelated"></canvas>
      <div class="ban" style="position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);background:var(--red);text-align:center;font-family:Anton;font-size:88px;padding:16px 0;opacity:0;letter-spacing:3px">SIGNAL SUSPENDU</div>
    </div>`);
  s.ball = s.tv.querySelector('.ball');
  s.cv = s.tv.querySelector('.static');
  s.ban = s.tv.querySelector('.ban');
  s.ant = node(el, '', 'width:400px;height:200px', `<svg width="400" height="200"><path d="M200 200 L80 20 M200 200 L320 20" stroke="#8d88a8" stroke-width="10" stroke-linecap="round"/><circle cx="80" cy="20" r="14" fill="#8d88a8"/><circle cx="320" cy="20" r="14" fill="#8d88a8"/></svg>`);
  s.lab = node(el, 'tag', 'background:#e02435;color:#fff;font-size:40px', 'TÉLÉ D\'ÉTAT CHINOISE');
}, (s, t) => {
  const ti = P(t, 50.84, .5, 'back');
  const [sx, sy] = shake(t, 54.08, 26, .6);
  set(s.tv, { x: 540 + sx, y: 800 + sy, s: lerp(.6, 1, ti) * (1 + punch(t, 51.56, .05)), o: clamp((t - 50.84) / .15) });
  set(s.ant, { x: 540 + sx, y: 360 + sy + lerp(400, 0, ti), o: ti });
  set(s.lab, { x: 540, y: 1250, s: pop(t, 51.0)[0], o: pop(t, 51.0)[1] });
  const bp = (t * .55) % 1;
  set(s.ball, { x: 120 + bp * 560, y: 420 - Math.abs(Math.sin(bp * Math.PI * 3)) * 220, r: t * 400 });
  const st = t > 54.0;
  s.cv.style.opacity = st ? .92 : 0;
  if (st) {
    const c = s.cv.getContext('2d'), im = c.createImageData(203, 158);
    let seed = Math.floor(t * 30) * 9973;
    for (let i = 0; i < im.data.length; i += 4) { seed = (seed * 1103515245 + 12345) & 0x7fffffff; const v = seed % 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    c.putImageData(im, 0, 0);
  }
  const b = clamp((t - 54.1) / .2);
  s.ban.style.opacity = b;
  s.ban.style.transform = `translateY(-50%) scaleY(${b})`;
});

// ======== 10. EXCUSES DE LA LIGA + LE REAL TREMBLE (55.25 – 61.6)
scene(55.25, 61.6, (el, s) => {
  s.doc = node(el, 'card', 'width:860px;padding:50px 54px;background:#fbfaf6;color:#111;border:0',
    `<div style="display:flex;justify-content:space-between;align-items:center"><div style="font-family:Anton;font-size:64px;letter-spacing:2px;color:#ff4b44">LALIGA</div><div style="font-weight:900;font-size:24px;letter-spacing:4px;color:#999">COMMUNIQUÉ</div></div>
     <div style="height:4px;background:#eee;margin:26px 0"></div>
     <div style="font-family:Anton;font-size:76px;line-height:1.05;text-transform:uppercase">Nos excuses<br>aux fans <span style="color:#e02435">chinois</span></div>
     ${[0, 1, 2].map(i => `<div style="height:16px;border-radius:8px;background:#e4e4e4;margin-top:22px;width:${90 - i * 18}%"></div>`).join('')}`);
  s.pray = emoji(el, '1f64f', 230);
  s.stad = node(el, '', 'width:1000px;height:520px', `<svg viewBox="0 0 1000 520" width="1000" height="520"><defs><linearGradient id="st" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8ecf5"/><stop offset="1" stop-color="#9aa3bb"/></linearGradient></defs>
    <path d="M40 520 V200 Q500 80 960 200 V520Z" fill="url(#st)"/>
    ${Array.from({ length: 16 }, (_, i) => `<rect x="${70 + i * 56}" y="${190 - Math.sin(i / 15 * Math.PI) * 70}" width="18" height="${330 + Math.sin(i / 15 * Math.PI) * 70}" fill="#c3c9d8"/>`).join('')}
    <path d="M40 200 Q500 80 960 200" stroke="#fff" stroke-width="14" fill="none"/>
    <rect x="40" y="430" width="920" height="90" fill="#6c7591"/>
    <text x="500" y="495" font-family="Anton" font-size="60" text-anchor="middle" fill="#fff" letter-spacing="6">REAL MADRID</text></svg>`);
  s.chart = node(el, 'card', 'width:640px;height:400px;padding:30px', `<div style="font-weight:900;font-size:28px;letter-spacing:4px;color:#aaa">MARCHÉ CHINOIS</div><svg width="580" height="300" style="overflow:visible"><path class="cl" d="M20 60 L120 90 L200 70 L300 150 L380 130 L470 230 L560 280" stroke="#ff3344" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
  s.cl = s.chart.querySelector('.cl'); s.clLen = 700;
  s.coins = [];
  for (let i = 0; i < 9; i++) s.coins.push(emoji(el, i % 3 ? '1f4b0' : '1f4b8', 140));
  s.jt = node(el, 'big', 'font-size:150px;color:var(--gold);text-shadow:0 0 40px rgba(255,200,60,.7);white-space:nowrap', '€€€');
}, (s, t) => {
  const d = P(t, 55.3, .45, 'back');
  const dOut = P(t, 58.3, .3, 'in');
  set(s.doc, { x: 540 - dOut * 1200, y: lerp(1500, 720, d), r: lerp(12, -2, d) });
  set(s.pray, { x: 860 - dOut * 1200, y: 420, s: pop(t, 56.95)[0], r: 10, o: pop(t, 56.95)[1] });
  const si = P(t, 58.4, .5, 'out5');
  const [sx, sy] = [noise(t, 3) * 16 * P(t, 59.2, .2), noise(t + 5, 3.3) * 10 * P(t, 59.2, .2)];
  set(s.stad, { x: 540 + sx + lerp(1200, 0, si), y: 1010 + sy, s: 1 });
  const ch = P(t, 59.2, .4, 'back');
  set(s.chart, { x: 540, y: 560, s: ch, o: clamp((t - 59.2) / .1) });
  s.cl.setAttribute('stroke-dasharray', `${s.clLen * clamp((t - 59.4) / 1.1)} ${s.clLen}`);
  s.coins.forEach((c, i) => {
    const t0 = 60.6 + i * .08, p = clamp((t - t0) / 1.0);
    set(c, { x: 140 + i * 100, y: lerp(-150, 1500, E.in(p)), r: (i % 2 ? 1 : -1) * p * 200, o: t < t0 ? 0 : 1 });
  });
  const [j, jo] = pop(t, 60.8, .3);
  set(s.jt, { x: 540, y: 690, s: j, o: jo * .0 });
});

// ======== 11. MBAPPÉ S'EXCUSE (61.6 – 71.98)
scene(61.6, 71.98, (el, s) => {
  s.p = node(el, '', '', character({ id: 'p11', kind: 'player', w: 300 }));
  s.ph = node(el, 'phone', '', `<div class="notch"></div><div class="scr" style="background:#0f0f14;padding:110px 36px 0">
     <div style="display:flex;align-items:center;gap:20px"><div style="width:96px;height:96px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#2a2933,#050509);border:4px solid #3d6bff"></div><div><div style="font-weight:900;font-size:36px">Kylian Mbappé <span style="color:#3d9bff">✔</span></div><div style="font-size:24px;opacity:.6;font-weight:700">Communiqué officiel</div></div></div>
     <div class="tabs" style="display:flex;gap:10px;margin:36px 0 28px"></div>
     <div class="txt" style="font-size:34px;line-height:1.45;font-weight:600;color:#ddd"></div></div>`);
  s.tabs = [];
  ['FRANÇAIS', 'ENGLISH', '中文'].forEach(l => s.tabs.push(h('div', '', 'padding:10px 18px;border-radius:40px;font-weight:900;font-size:24px;border:3px solid #444;color:#777;white-space:nowrap', l, s.ph.querySelector('.tabs'))));
  s.txt = s.ph.querySelector('.txt');
  s.lines = [
    ['Des propos ', '<b style="color:#fff;background:#e02435;padding:0 8px;border-radius:6px">maladroits</b>', '.'],
    ['Un ', '<b style="color:#fff;background:#3d6bff;padding:0 8px;border-radius:6px">profond respect</b>', ' pour le peuple chinois.'],
    ['', '<b style="color:#111;background:#ffc83d;padding:0 8px;border-radius:6px">Je suis sincèrement désolé.</b>', ''],
  ].map(l => h('div', '', 'margin-bottom:26px;opacity:0', l.join(''), s.txt));
  s.flags = [['fr', 63.76], ['gb', 64.56], ['cn', 65.52]].map(([f, t0]) => {
    const e = node(el, '', `width:240px;height:180px;border-radius:20px;box-shadow:0 20px 50px rgba(0,0,0,.5);background:${f === 'gb' ? 'linear-gradient(#012169,#012169)' : `url(assets/${f}.svg) center/cover`};overflow:hidden`,
      f === 'gb' ? `<svg viewBox="0 0 60 30" width="240" height="180" preserveAspectRatio="none"><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#C8102E" stroke-width="2"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/></svg>` : '');
    return { e, t0 };
  });
  s.sorry = node(el, 'big', 'font-size:150px;color:#fff;text-align:center;white-space:nowrap;text-shadow:0 0 40px rgba(255,200,60,.5)', 'SINCÈREMENT<br><span style="color:var(--gold)">DÉSOLÉ</span>');
}, (s, t) => {
  // il recule
  const back = P(t, 62.2, .6, 'out');
  const pOut = P(t, 62.95, .3, 'in');
  set(s.p, { x: 540, y: 1040 - back * 40, s: (1.55 - back * .35) * (1 - pOut), r: Math.sin(t * 9) * 2, o: 1 - pOut });
  setFace(s.p, 'worry');
  const pin = P(t, 62.95, .5, 'out5');
  const phOut = P(t, 70.95, .3, 'in');
  set(s.ph, { x: 540, y: lerp(1700, 790, pin) + phOut * 300, s: .95 * (1 - phOut * .3), o: 1 - phOut });
  const lang = t > 65.52 ? 2 : t > 64.56 ? 1 : t > 63.76 ? 0 : -1;
  s.tabs.forEach((e, i) => {
    const on = i === lang;
    e.style.background = on ? '#fff' : 'transparent'; e.style.color = on ? '#111' : '#777'; e.style.borderColor = on ? '#fff' : '#444';
    e.style.transform = `scale(${on ? 1 + punch(t, [63.76, 64.56, 65.52][i], .25) : 1})`;
  });
  s.flags.forEach(({ e, t0 }, i) => {
    const [a, o] = pop(t, t0, .3);
    const pos = [[200, 360], [880, 520], [200, 1180]][i];
    set(e, { x: pos[0], y: pos[1] + Math.sin(t * 2 + i) * 8, s: a * (i === 2 ? 1 + punch(t, 65.52, .15) : 1), r: (i - 1) * 8, o: o * (1 - P(t, 66.2, .3)) });
  });
  [67.1, 68.3, 70.2].forEach((t0, i) => {
    const l = s.lines[i]; const p = clamp((t - t0) / .3);
    l.style.opacity = p; l.style.transform = `translateY(${(1 - E.out(p)) * 30}px)`;
  });
  const sd = clamp((t - 71.15) / .25);
  set(s.sorry, { x: 540, y: 760, s: t < 71.15 ? 0 : lerp(1.8, 1, E.out(sd)), o: sd });
});

// ======== 12. ÇA SUFFIRA ? CONTRATS ENVOLÉS (71.98 – 76.43)
scene(71.98, 76.43, (el, s) => {
  s.q = node(el, 'big', 'font-size:200px;color:#fff;text-align:center;white-space:nowrap', 'ÇA SUFFIRA<span style="color:var(--red)"> ?</span>');
  s.lol = emoji(el, '1f602', 300);
  s.items = [];
  const kinds = ['contract', '1f4b8', 'contract', '1f4b0', 'contract', '1f4b8'];
  kinds.forEach((k, i) => {
    const wrap = node(el, '', 'width:260px;height:220px');
    const body = k === 'contract'
      ? `<div style="position:absolute;left:50%;top:50%;width:150px;height:190px;margin:-95px 0 0 -75px;background:linear-gradient(180deg,#fff7d6,#ffd96b);border-radius:12px;box-shadow:0 14px 30px rgba(0,0,0,.45);padding:18px 14px;color:#7a5600;font-family:Anton;font-size:30px;text-align:center">CONTRAT<div style="height:8px;background:#e9c25a;margin-top:14px;border-radius:4px"></div><div style="height:8px;background:#e9c25a;margin-top:10px;border-radius:4px;width:70%"></div><div style="font-size:52px;color:#c99400;margin-top:8px">€</div></div>`
      : `<div class="emoji" style="left:50%;top:50%;width:150px;height:150px;margin:-75px 0 0 -75px;background-image:${EMO(k)}"></div>`;
    wrap.innerHTML = `<div class="wl emoji" style="left:-10px;top:30px;width:120px;height:120px;background-image:${EMO('1fabd')};transform:scaleX(-1)"></div><div class="wr emoji" style="right:-10px;top:30px;width:120px;height:120px;background-image:${EMO('1fabd')}"></div>${body}`;
    s.items.push(wrap);
  });
}, (s, t) => {
  const [q, qo] = pop(t, 72.0, .35);
  set(s.q, { x: 540, y: 760, s: q * (1 + .03 * Math.sin(t * 9)), o: qo * (1 - P(t, 73.4, .2)) });
  const [l, lo] = pop(t, 73.6, .35);
  set(s.lol, { x: 540, y: 760, s: l * (1 - P(t, 74.6, .25, 'in')), r: Math.sin(t * 8) * 8, o: lo });
  s.items.forEach((e, i) => {
    const t0 = 74.75 + i * .1;
    const p = clamp((t - t0) / 1.8);
    const col = i % 3, row = Math.floor(i / 3);
    const x0 = 230 + col * 310, y0 = 640 + row * 300;
    const fly = E.in(clamp((t - 75.7 - i * .06) / 1.4));
    const flap = Math.sin(t * 22 + i) * 18;
    e.querySelector('.wl').style.transform = `scaleX(-1) rotate(${flap}deg)`;
    e.querySelector('.wr').style.transform = `rotate(${flap}deg)`;
    set(e, { x: x0 + fly * (col - 1) * 260, y: y0 - fly * 1300 + Math.sin(t * 4 + i) * 12, s: pop(t, t0, .3)[0], r: Math.sin(t * 3 + i) * 8, o: t < t0 ? 0 : 1 });
  });
});

// ======== 13. À TOI DE JUGER + ABONNE-TOI (76.43 – 84.5)
scene(76.43, DUR, (el, s) => {
  s.left = node(el, '', 'width:540px;height:1920px;background:linear-gradient(180deg,#a3101f,#4d0710)');
  s.right = node(el, '', 'width:540px;height:1920px;background:linear-gradient(180deg,#1f3fb8,#0c1a52)');
  s.lt = node(el, 'big', 'font-size:92px;text-align:center;width:480px', '<span style="font-size:60px;opacity:.8">LA CHINE</span><br>EN FAIT<br><span style="color:var(--gold)">TROP</span>');
  s.rt = node(el, 'big', 'font-size:92px;text-align:center;width:480px', '<span style="font-size:60px;opacity:.8">MBAPPÉ</span><br>A VRAIMENT<br><span style="color:var(--gold)">DÉRAPÉ</span>');
  s.lf = node(el, '', 'width:260px;height:180px;border-radius:18px;background:url(assets/cn.svg) center/cover;box-shadow:0 20px 50px rgba(0,0,0,.5)');
  s.rf = node(el, '', '', character({ id: 'p13', kind: 'player', w: 180 }));
  s.vs = node(el, 'big', 'font-size:120px;width:220px;height:220px;border-radius:50%;background:#fff;color:#111;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 14px rgba(255,255,255,.15),0 20px 60px rgba(0,0,0,.6)', 'VS');
  s.masc = node(el, '', 'width:520px;height:620px;border-radius:40px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);border:8px solid #fff;background:#0e1b44 center/cover');
  s.bub = node(el, '', 'background:#fff;color:#111;border-radius:40px;padding:26px 40px;font-weight:900;font-size:48px;white-space:nowrap;box-shadow:0 20px 50px rgba(0,0,0,.5)', `<span class="emoji" style="position:relative;display:inline-block;width:80px;height:80px;vertical-align:middle;margin-right:14px;background-image:${EMO('1f4ac')}"></span>DIS-LE EN COMMENTAIRE`);
  s.follow = node(el, '', 'background:var(--red);color:#fff;border-radius:60px;padding:28px 60px;font-family:Anton;font-size:96px;letter-spacing:3px;white-space:nowrap;box-shadow:0 0 60px rgba(255,40,60,.6)', '+ ABONNE-TOI');
  s.sub = node(el, '', 'font-weight:800;font-size:38px;letter-spacing:6px;opacity:.85;white-space:nowrap', "L'ACTU FRANÇAISE EN 90 SECONDES");
}, (s, t) => {
  const sp = P(t, 76.45, .5, 'out5');
  const endP = P(t, 80.9, .5, 'io');
  set(s.left, { x: lerp(-270, 270, sp) - endP * 600, y: 960 });
  set(s.right, { x: lerp(1350, 810, sp) + endP * 600, y: 960 });
  const lpop = pop(t, 77.2, .35), rpop = pop(t, 78.3, .35);
  set(s.lt, { x: 270 - endP * 600, y: 800, s: lpop[0] * (1 + punch(t, 77.76, .1)), o: lpop[1] });
  set(s.rt, { x: 810 + endP * 600, y: 800, s: rpop[0] * (1 + punch(t, 79.32, .1)), o: rpop[1] });
  set(s.lf, { x: 270 - endP * 600, y: 480, s: pop(t, 76.9)[0], r: -6 });
  set(s.rf, { x: 810 + endP * 600, y: 520, s: pop(t, 78.1)[0] * .9 });
  setFace(s.rf, 'worry');
  const [v, vo] = pop(t, 76.6, .35);
  set(s.vs, { x: 540, y: 1120, s: v * (1 + .05 * Math.sin(t * 8)) * (1 - endP), o: vo });
  // mascotte de la chaîne (vidéo de référence) qui réagit
  const mi = P(t, 80.4, .45, 'back');
  const f = Math.min(95, Math.floor(Math.max(0, t - 80.4) * 24)) + 1;
  s.masc.style.backgroundImage = `url(assets/mascotte/m${String(f).padStart(3, '0')}.jpg)`;
  set(s.masc, { x: 540, y: lerp(1900, 700, mi), r: lerp(10, -2, mi), o: clamp((t - 80.4) / .1) });
  const [b, bo] = pop(t, 80.45, .35);
  set(s.bub, { x: 540, y: 300, s: b * (1 + .03 * Math.sin(t * 7)), o: bo });
  const [fl, fo] = pop(t, 81.6, .4);
  set(s.follow, { x: 540, y: 1150, s: fl * (1 + .04 * Math.sin(t * 6)), o: fo });
  set(s.sub, { x: 540, y: 1270, o: P(t, 81.9, .3) });
});

// ---------------------------------------------------------------- en-tête (chapitres + compteur)
const CH = [
  [0, 'ALERTE · MARDI 27 OCTOBRE', 'MBAPPÉ × CHINE'],
  [5.17, 'ÉPISODE 1 · LA BLAGUE', "L'INTERVIEW"],
  [15.44, 'ÉPISODE 1 · LA BLAGUE', 'MAO ZEDONG'],
  [22.24, 'ÉPISODE 2 · LA SANCTION', 'SPONSORS PERDUS : <em>0</em>'],
  [29.68, 'ÉPISODE 2 · LA SANCTION', 'SPONSORS PERDUS : <em>1</em>'],
  [38.44, 'ÉPISODE 2 · LA SANCTION', 'SPONSORS PERDUS : <em>2</em>'],
  [40.08, 'ÉPISODE 2 · LA SANCTION', 'SPONSORS PERDUS : <em>3 ?</em>'],
  [41.68, 'ÉPISODE 3 · PÉKIN RÉPLIQUE', 'PÉKIN ENTRE EN JEU'],
  [50.84, 'ÉPISODE 3 · PÉKIN RÉPLIQUE', 'LA LIGA COUPÉE'],
  [55.25, 'ÉPISODE 3 · PÉKIN RÉPLIQUE', 'LE REAL TREMBLE'],
  [61.6, 'ÉPISODE 4 · LES EXCUSES', 'FR · EN · 中文'],
  [71.98, 'ÉPISODE 4 · LES EXCUSES', 'ET MAINTENANT ?'],
  [76.43, 'À TOI DE JUGER', 'TON AVIS ?'],
];
const hlab = document.getElementById('hlab'), hval = document.getElementById('hval'), hdr = document.getElementById('hdr');
function header(t) {
  let c = CH[0], ti = 0;
  CH.forEach((x, i) => { if (t >= x[0]) { c = x; ti = i; } });
  if (hlab.textContent !== c[1]) hlab.textContent = c[1];
  if (hval.innerHTML !== c[2]) hval.innerHTML = c[2];
  const p = punch(t, c[0], .22, .5);
  hval.style.transform = `scale(${1 + p})`;
  hdr.style.opacity = t > 80.3 ? 1 - P(t, 80.3, .3) : 1;
}

// ---------------------------------------------------------------- sous-titres mot par mot
const KEY = new Set(('CHINE PHRASE SEULE DOS BRIDGE MÈME DRÔLE AMUSÉ DICTATEUR MAO ZEDONG COMMUNISTE INTOUCHABLE EXPLOSE SANCTION TOMBE MARDI DONGPENG ' +
  'CONTRAT HEURTÉ SENTIMENTS NATIONAUX ZÉRO MENGNIU LAIT PAREIL TROISIÈME PÉKIN GUO JIAKUN REJET FORT SUSPENDUS EXCUSES REAL MADRID TREMBLE JUTEUX ' +
  'RECULE MALADROITS RESPECT DÉSOLÉ SUFFIRA BLAGUE OR ENVOLÉS TROP DÉRAPÉ COMMENTAIRE COLLÉE TÊTE').split(' '));
const GOLD = new Set(['MBAPPÉ', 'KYLIAN', 'TOI']);
let GROUPS = [];
function buildGroups(words) {
  const ws = words.filter(w => w.type === 'word' && /[\p{L}\p{N}]/u.test(w.text));
  let g = [];
  const flush = () => { if (g.length) GROUPS.push(g); g = []; };
  ws.forEach((w, i) => {
    const clean = w.text.replace(/[«»"]/g, '').replace(/[.,:;!?…]+$/g, '').toUpperCase();
    const len = g.reduce((a, x) => a + x.c.length + 1, 0) + clean.length;
    if (g.length && (g.length >= 3 || len > 17 || w.start - g[g.length - 1].e > .45)) flush();
    g.push({ c: clean, s: w.start, e: w.end });
    if (/[.,:;!?…»]$/.test(w.text) || (ws[i + 1] && /^[:?»]/.test(ws[i + 1].text))) flush();
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
  if (!g || t > Math.min(end, nextS) || t > 81.3) { capline.style.opacity = 0; return; }
  capline.style.opacity = 1;
  if (gi !== curG) {
    curG = gi;
    capline.innerHTML = g.map(w => `<span class="w ${KEY.has(w.c) ? 'k' : GOLD.has(w.c) ? 'g' : ''}">${w.c}</span>`).join(' ');
    spans = [...capline.querySelectorAll('.w')];
  }
  g.forEach((w, i) => {
    const p = clamp((t - w.s + .04) / .16);
    const sp = spans[i];
    sp.style.opacity = p > 0 ? 1 : 0;
    sp.style.transform = `scale(${p > 0 ? lerp(1.35, 1, E.out(p)) : .5}) translateY(${(1 - E.out(p)) * 14}px)`;
  });
  capline.style.transform = `scale(${1 + punch(t, g[0].s, .04, .4)})`;
}

// ---------------------------------------------------------------- ambiance : poussière, grain, lumières, caméra
const dust = document.getElementById('dust');
const DUST = [];
let rs = 7;
const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
for (let i = 0; i < 46; i++) DUST.push({ e: h('b', '', '', null, dust), x: rnd() * 1080, y: rnd() * 1920, s: .3 + rnd() * .9, v: 10 + rnd() * 40, ph: rnd() * 6 });
const grain = document.getElementById('grain'), gctx = grain.getContext('2d');
const GR = [];
for (let k = 0; k < 6; k++) {
  const im = gctx.createImageData(590, 1010);
  for (let i = 0; i < im.data.length; i += 4) { const v = rnd() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  GR.push(im);
}
const g1 = document.getElementById('g1'), g2 = document.getElementById('g2');
const tint = document.getElementById('tint'), flash = document.getElementById('flash'), prog = document.getElementById('prog');
// teinte rouge sur les moments « choc »
const RED = [[4.12, 5.1], [14.08, 15.3], [25.52, 26.7], [29.95, 30.8], [34.37, 35.8], [47.55, 50.8], [54.08, 55.2]];
const IMPACT = [4.12, 14.08, 21.2, 25.8, 29.95, 35.12, 39.2, 54.08, 59.2, 71.15];
const CUTS = scenes.map(s => s.t0).filter(x => x > 0);

window.seek = function (t) {
  // scènes visibles
  scenes.forEach(s => {
    const vis = t >= s.t0 && t < s.t1;
    s.el.style.display = vis ? 'block' : 'none';
    if (vis) {
      s.update(s, t);
      // caméra : poussée lente + entrée en « whip zoom »
      const lt = t - s.t0;
      const ent = clamp(lt / .28);
      const z = 1 + lt * .012 + (1 - E.out(ent)) * .25;
      let sx = 0, sy = 0;
      IMPACT.forEach(it => { const [a, b] = shake(t, it, 22, .4); sx += a; sy += b; });
      s.el.style.transform = `translate(${sx}px,${sy + (1 - E.out(ent)) * 40}px) scale(${z})`;
      s.el.style.filter = ent < 1 ? `blur(${(1 - ent) * 14}px)` : '';
    }
  });
  // flash bref à chaque coupe
  let fl = 0;
  CUTS.forEach(c => { if (t >= c && t < c + .18) fl = Math.max(fl, .35 * (1 - (t - c) / .18)); });
  IMPACT.forEach(c => { if (t >= c && t < c + .12) fl = Math.max(fl, .25 * (1 - (t - c) / .12)); });
  flash.style.opacity = fl;
  let rt = 0;
  RED.forEach(([a, b]) => { rt = Math.max(rt, clamp((t - a) / .15) * (1 - clamp((t - b) / .3))); });
  tint.style.opacity = rt * (.75 + .25 * Math.sin(t * 12));
  // lumières d'ambiance
  const redScene = rt > 0 || (t > 15.4 && t < 22.2) || (t > 41.6 && t < 50.8);
  g1.style.background = redScene ? '#ff2a3d' : '#ff7a3d';
  g1.style.transform = `translate(${Math.sin(t * .4) * 120}px,${Math.cos(t * .3) * 80}px)`;
  g2.style.transform = `translate(${Math.cos(t * .35) * 140}px,${Math.sin(t * .25) * 160}px)`;
  DUST.forEach(d => {
    const y = ((d.y - t * d.v) % 1920 + 1920) % 1920;
    d.e.style.transform = `translate(${d.x + Math.sin(t * .6 + d.ph) * 30}px,${y}px) scale(${d.s})`;
    d.e.style.opacity = .15 + .35 * (0.5 + .5 * Math.sin(t * 1.3 + d.ph));
  });
  city.style.transform = `translateX(${-t * 2.2}px)`;
  gctx.putImageData(GR[Math.floor(t * 30) % GR.length], 0, 0);
  grain.style.transform = `scale(1.9)`;
  prog.style.width = (clamp(t / 81.2) * 1080) + 'px';
  header(t);
  captions(t);
};

window.ready = (async () => {
  const [topo, words] = await Promise.all([fetch(A + 'countries-110m.json').then(r => r.json()), fetch(A + 'words.json').then(r => r.json())]);
  window.TOPO = topo;
  buildGroups(words.words);
  scenes.forEach(s => s.build(s.el, s));
  await document.fonts.ready;
  const imgs = [...new Set([...document.querySelectorAll('*')].map(e => getComputedStyle(e).backgroundImage).join(',').match(/url\("?[^")]+"?\)/g) || [])];
  await Promise.all(imgs.map(u => new Promise(r => { const i = new Image(); i.onload = i.onerror = r; i.src = u.replace(/^url\("?|"?\)$/g, ''); })));
  // précharge les images de la mascotte
  await Promise.all(Array.from({ length: 96 }, (_, i) => new Promise(r => { const im = new Image(); im.onload = im.onerror = r; im.src = `${A}mascotte/m${String(i + 1).padStart(3, '0')}.jpg`; })));
  return true;
})();
