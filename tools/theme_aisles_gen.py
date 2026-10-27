# Generates the storefront aisle sections from ecom/categories.json (re-run whenever the aisles change)
import json, re, unicodedata, os
T='/home/claude/marche-decarie-store/'
c=json.load(open('/home/claude/barcode-scanner/ecom/categories.json'))
def norm(s):
    s=unicodedata.normalize('NFD',(s or '').upper()); return ''.join(ch for ch in s if unicodedata.category(ch)!='Mn')
def slug(s): return re.sub(r'[^a-z0-9]+','-',norm(s).lower().replace('œ','oe')).strip('-')
zone_of={a:z['id'] for z in c['zones'] for a in z['aisles']}
A={a['id']:a for a in c['aisles']}
order=c.get('order') or [a for z in c['zones'] for a in z['aisles']]
for a in c['aisles']:
    for s in a['subs']+a['subsEn']+[a['fr'],a['en']]: assert not re.search(r"[|~^;']",s),s
AISLES_DEF=';'.join(f"{i}|{A[i]['fr']}|{A[i]['en']}|{zone_of[i]}|"+'^'.join(f"{slug(s)}~{s}~{e}" for s,e in zip(A[i]['subs'],A[i]['subsEn'])) for i in order)
ZONES_DEF=';'.join(f"{z['id']}|{z['fr']}|{z['en']}|{','.join(z['aisles'])}" for z in c['zones'])
PAIRS_DEF=';'.join(f"{a}|"+'^'.join(f"{p[0]}~{slug(p[1]) if p[1] else ''}" for p in v) for a,v in c['pairings'].items() if v)
DEFS=f"""{{%- comment -%}} GENERATED from ecom/categories.json by theme_gen.py -- do not edit by hand {{%- endcomment -%}}
{{%- liquid
  assign en = false
  if request.locale.iso_code == 'en'
    assign en = true
  endif
  assign aisles_def = '{AISLES_DEF}' | split: ';'
  assign zones_def = '{ZONES_DEF}' | split: ';'
  assign pairs_def = '{PAIRS_DEF}' | split: ';'
-%}}"""
open('/tmp/claude-0/aisles/defs.liquid','w').write(DEFS)

ZONE_COLORS={'frais':('#E7F3EA','#1F6B3E'),'cuisine':('#FCEFE1','#9A4F0E'),'garde-manger':('#ECEFF8','#33437F'),'sucre':('#FBE8EF','#9A2C52')}
zone_css=''.join(f".dplan__zone--{k}{{--zbg:{v[0]};--zfg:{v[1]}}}" for k,v in ZONE_COLORS.items())
ZONE_CSS_PLACE=zone_css

# ---------------- shelf card snippet ----------------
CARD="""{%- comment -%} Compact product card for the aisle shelves (home, "goes with"). {%- endcomment -%}
{%- liquid
  assign price = product.price
  assign per_kg = false
  if product.variants.size > 1
    assign kg_variant = product.variants | where: 'option1', '1 kg' | first
    if kg_variant
      assign price = kg_variant.price
      assign per_kg = true
    endif
  endif
  assign pop = 5
  for tag in product.tags
    assign t4 = tag | slice: 0, 4
    if t4 == 'pop-'
      assign pop = tag | remove: 'pop-' | plus: 0
    endif
  endfor
-%}
<a class="dshelf__card{% unless product.available %} is-out{% endunless %}" href="{{ product.url }}" data-pop="{{ pop }}" draggable="false">
  <span class="dshelf__media">
    {%- if product.featured_image -%}
      {{ product.featured_image | image_url: width: 360 | image_tag: loading: 'lazy', alt: product.title, sizes: '(min-width: 750px) 180px, 40vw', draggable: 'false' }}
    {%- endif -%}
    <span class="dshelf__new" hidden>{% if en %}Discover{% else %}À découvrir{% endif %}</span>
  </span>
  <span class="dshelf__name">{{ product.title }}</span>
  <span class="dshelf__price">
    {%- if product.compare_at_price > product.price -%}<s>{{ product.compare_at_price | money }}</s> {% endif -%}
    {{ price | money }}{% if per_kg %}<small> / kg</small>{% endif %}
  </span>
  {%- unless product.available -%}<span class="dshelf__sold">{% if en %}Sold out{% else %}Épuisé{% endif %}</span>{%- endunless -%}
</a>"""
open(T+'snippets/decarie-shelf-card.liquid','w').write(CARD)

SHELF_CSS="""
  .dshelf { padding: 1.4rem 0 .6rem; }
  .dshelf__head { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin-bottom: .8rem; }
  .dshelf__title { margin: 0; font-size: clamp(1.9rem, 4.6vw, 2.5rem); font-weight: 800; letter-spacing: -.01em; }
  .dshelf__zone { display: block; font-size: 1.05rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--zfg, #DC241C); margin-bottom: .2rem; }
  .dshelf__all { flex: 0 0 auto; font-size: 1.35rem; font-weight: 700; color: #DC241C; text-decoration: none; white-space: nowrap; }
  .dshelf__track { display: flex; gap: 1.1rem; overflow-x: auto; scroll-snap-type: x proximity; scrollbar-width: none; -webkit-overflow-scrolling: touch;
    padding: .2rem 1.5rem 1.2rem; margin: 0 -1.5rem; scroll-padding-left: 1.5rem; }
  .dshelf__track::-webkit-scrollbar { display: none; }
  .dshelf__card { flex: 0 0 38%; max-width: 17rem; scroll-snap-align: start; display: flex; flex-direction: column; gap: .35rem; color: inherit; text-decoration: none; }
  .dshelf__card.is-out { opacity: .55; }
  .dshelf__media { position: relative; display: block; aspect-ratio: 1; border-radius: 1.4rem; background: #fff; border: 1px solid rgba(0,0,0,.07); overflow: hidden;
    transition: transform .18s ease, box-shadow .18s ease; }
  .dshelf__card:hover .dshelf__media { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(0,0,0,.08); }
  .dshelf__media img { position: absolute; inset: 0; width: 100%; height: 100%; max-width: none; object-fit: contain; display: block; }
  .dshelf__new { position: absolute; left: .6rem; top: .6rem; padding: .3rem .6rem; border-radius: .6rem; background: #FFD23F; color: #1a1a1a;
    font-size: 1rem; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; transform: rotate(-3deg); }
  .dshelf__ua { position: absolute; right: .6rem; top: .5rem; font-size: 1.5rem; line-height: 1; }
  .dshelf__name { font-size: 1.3rem; line-height: 1.25; font-weight: 500; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; min-height: 2.5em; text-transform: lowercase; }
  .dshelf__name::first-letter { text-transform: uppercase; }
  .dshelf__price { font-size: 1.5rem; font-weight: 800; }
  .dshelf__price s { font-weight: 500; color: #777; font-size: 1.2rem; margin-right: .2rem; }
  .dshelf__price small { font-size: 1.15rem; font-weight: 600; }
  .dshelf__sold { font-size: 1.1rem; color: #b00; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
  @media screen and (min-width: 750px) { .dshelf__card { flex-basis: 17rem; } .dshelf__track { margin: 0; padding-left: 0; padding-right: 0; } }
"""
SHUFFLE_JS="""
<script>
  (function () {
    if (window.__dShelfMix) return; window.__dShelfMix = true;
    // Daily shuffle: same order all day, new order tomorrow. Best sellers (pop-1) come up more often,
    // and 2 lesser-known items get the "Discover" sticker so the shelf never looks the same twice.
    function seeded(seed) { var h = 2166136261; for (var i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
      return function () { h += 0x6D2B79F5; var t = h; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    var W = { 1: 6, 2: 4, 3: 3, 4: 2, 5: 1.4 };
    window.dShelfMix = function (track, keep, key) {
      var d = new Date(); var day = d.getFullYear() + '-' + d.getMonth() + '-' + d.getDate();
      var rnd = seeded(day + '|' + key);
      var cards = Array.prototype.slice.call(track.children);
      var scored = cards.map(function (el) { var p = +el.getAttribute('data-pop') || 5; return { el: el, p: p, k: Math.pow(rnd(), 1 / (W[p] || 1)) }; });
      scored.sort(function (a, b) { return b.k - a.k; });
      var top = scored.slice(0, keep);
      var lesser = scored.slice(keep).filter(function (s) { return s.p >= 4; }).slice(0, 2);
      if (lesser.length) { top.splice(3, 0, lesser[0]); if (lesser[1]) top.splice(7, 0, lesser[1]); top = top.slice(0, keep); }
      track.innerHTML = '';
      top.forEach(function (s) { if (s.p >= 4) { var b = s.el.querySelector('.dshelf__new'); if (b) b.hidden = false; } track.appendChild(s.el); });
    };
    document.querySelectorAll('[data-dshelf-mix]').forEach(function (t) { window.dShelfMix(t, +t.getAttribute('data-dshelf-mix') || 12, t.getAttribute('data-key') || ''); });
  })();
</script>"""

# ---------------- home: store plan ----------------
PLAN=DEFS+"""
{%- style -%}
  .dplan { padding: 2.4rem 0 1.2rem; }
  .dplan__head { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; margin-bottom: 1.4rem; }
  .dplan__title { margin: 0; font-size: clamp(2.4rem, 6vw, 3.6rem); font-weight: 900; letter-spacing: -.02em; line-height: 1; }
  .dplan__sub { margin: .5rem 0 0; font-size: 1.4rem; color: rgba(var(--color-foreground), .7); }
  .dplan__dice { flex: 0 0 auto; border: 0; border-radius: 99px; background: #1a1a1a; color: #fff; padding: .9rem 1.4rem; font-size: 1.35rem; font-weight: 700; cursor: pointer; }
  .dplan__dice:hover { background: #DC241C; }
  .dplan__zones { display: grid; grid-template-columns: 1fr; gap: 1rem; }
  .dplan__zone { background: var(--zbg); border-radius: 1.8rem; padding: 1.2rem 1.2rem 1.3rem; }
  .dplan__zname { margin: 0 0 .9rem .2rem; font-size: 1.15rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--zfg); }
  .dplan__aisles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .7rem; list-style: none; margin: 0; padding: 0; }
  .dplan__aisle { display: flex; flex-direction: column; align-items: center; gap: .3rem; padding: .7rem .4rem .8rem; border-radius: 1.2rem; background: #fff;
    color: #1a1a1a; text-decoration: none; text-align: center; height: 100%; box-sizing: border-box; transition: transform .15s ease, box-shadow .15s ease; }
  .dplan__aisle:hover { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(0,0,0,.08); }
  .dplan__pic { position: relative; display: block; width: 100%; aspect-ratio: 1; overflow: hidden; }
  .dplan__pic img { position: absolute; inset: 6%; width: 88%; height: 88%; max-width: none; object-fit: contain; }
  .dplan__aname { font-size: 1.2rem; font-weight: 700; line-height: 1.2; }
  .dplan__n { font-size: 1.05rem; color: #777; }
  @media screen and (min-width: 750px) {
    .dplan__zones { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.4rem; }
    .dplan__aisles { grid-template-columns: repeat(auto-fill, minmax(10.5rem, 1fr)); }
  }
  ZONECSS
{%- endstyle -%}
<section class="dplan" id="plan">
  <div class="page-width">
    <div class="dplan__head">
      <div>
        <h2 class="dplan__title">{% if en %}Store map{% else %}Le plan du magasin{% endif %}</h2>
        <p class="dplan__sub">{% if en %}Walk the aisles like you would in the store.{% else %}Faites le tour des allées comme en magasin.{% endif %}</p>
      </div>
      <button type="button" class="dplan__dice" data-dsurprise>🎲 {% if en %}Surprise me{% else %}Surprends-moi{% endif %}</button>
    </div>
    <div class="dplan__zones">
      {%- for zd in zones_def -%}
        {%- assign z = zd | split: '|' -%}
        {%- assign zaisles = z[3] | split: ',' -%}
        <div class="dplan__zone dplan__zone--{{ z[0] }}">
          <h3 class="dplan__zname">{% if en %}{{ z[2] }}{% else %}{{ z[1] }}{% endif %}</h3>
          <ul class="dplan__aisles" role="list">
            {%- for aid in zaisles -%}
              {%- assign h = 'allee-' | append: aid -%}
              {%- assign col = collections[h] -%}
              {%- if col != blank and col.products_count > 0 -%}
                {%- for ad in aisles_def -%}{%- assign ap = ad | split: '|' -%}{%- if ap[0] == aid -%}{%- assign a = ap -%}{%- endif -%}{%- endfor -%}
                {%- assign pic = nil -%}
                {%- for p in col.products limit: 40 -%}
                  {%- if pic == nil and p.featured_image and p.tags contains 'pop-1' -%}{%- assign pic = p.featured_image -%}{%- endif -%}
                {%- endfor -%}
                {%- if pic == nil -%}{%- for p in col.products limit: 20 -%}{%- if pic == nil and p.featured_image -%}{%- assign pic = p.featured_image -%}{%- endif -%}{%- endfor -%}{%- endif -%}
                <li>
                  <a class="dplan__aisle" href="{{ col.url }}">
                    <span class="dplan__pic">{%- if pic -%}{{ pic | image_url: width: 240 | image_tag: loading: 'lazy', alt: '' }}{%- endif -%}</span>
                    <span class="dplan__aname">{% if en %}{{ a[2] }}{% else %}{{ a[1] }}{% endif %}</span>
                    <span class="dplan__n">{{ col.products_count }}</span>
                  </a>
                </li>
              {%- endif -%}
            {%- endfor -%}
          </ul>
        </div>
      {%- endfor -%}
    </div>
  </div>
</section>
{% schema %}
{ "name": "Store map (aisles)", "settings": [], "presets": [{ "name": "Store map (aisles)" }] }
{% endschema %}
""".replace('ZONECSS',zone_css)
# store map removed from the home page (Oct 25)

# ---------------- home: aisle shelves ----------------
SHELVES=DEFS+"""
{%- style -%}""" + SHELF_CSS + ZONE_CSS_PLACE + """
  .dua { margin: 1.6rem 0 1rem; }
  .dua__link { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 2rem 2rem; border-radius: 1.8rem; text-decoration: none; color: #fff;
    background: linear-gradient(180deg, #0057B7 0 52%, #FFD500 52% 100%); min-height: 13rem; box-sizing: border-box; }
  .dua__t { font-size: clamp(2.2rem, 6vw, 3.2rem); font-weight: 900; line-height: 1.05; text-shadow: 0 2px 10px rgba(0,0,0,.25); }
  .dua__s { display: block; font-size: 1.4rem; font-weight: 600; margin-top: .5rem; }
  .dua__go { align-self: flex-end; background: #1a1a1a; color: #fff; border-radius: 99px; padding: .8rem 1.3rem; font-weight: 800; font-size: 1.35rem; white-space: nowrap; }
{%- endstyle -%}
<div class="page-width dshelves">
  {%- assign n_done = 0 -%}
  {%- for ad in aisles_def -%}
    {%- assign a = ad | split: '|' -%}
    {%- assign h = 'allee-' | append: a[0] -%}
    {%- assign col = collections[h] -%}
    {%- if col != blank and col.products_count > 0 -%}
      {%- assign n_done = n_done | plus: 1 -%}
      {%- assign zclass = 'dplan__zone--' | append: a[3] -%}
      <section class="dshelf {{ zclass }}" aria-label="{{ a[1] | escape }}">
        <div class="dshelf__head">
          <h2 class="dshelf__title"><a href="{{ col.url }}" style="color:inherit;text-decoration:none">{% if en %}{{ a[2] }}{% else %}{{ a[1] }}{% endif %}</a></h2>
          <a class="dshelf__all" href="{{ col.url }}">{% if en %}Whole aisle{% else %}Toute l'allée{% endif %} ({{ col.products_count }}) →</a>
        </div>
        <div class="dshelf__track" data-dshelf-mix="12" data-key="{{ a[0] }}">
          {%- assign shown = 0 -%}
          {%- for pl in (1..5) -%}
            {%- assign ptag = 'pop-' | append: pl -%}
            {%- for product in col.products limit: 50 -%}
              {%- if shown < 20 and product.featured_image and product.tags contains ptag -%}
                {%- render 'decarie-shelf-card', product: product, en: en -%}
                {%- assign shown = shown | plus: 1 -%}
              {%- endif -%}
            {%- endfor -%}
          {%- endfor -%}
        </div>
      </section>
      {%- if n_done == 2 -%}
        {%- assign ua = collections['saveurs-ukraine'] -%}
        {%- if ua != blank and ua.products_count > 0 -%}
          <div class="dua"><a class="dua__link" href="{{ ua.url }}">
            <span><span class="dua__t">{% if en %}Taste of Ukraine{% else %}Saveurs d'Ukraine{% endif %}</span>
            <span class="dua__s">{% if en %}{{ ua.products_count }} products made in Ukraine{% else %}{{ ua.products_count }} produits fabriqués en Ukraine{% endif %}</span></span>
            <span class="dua__go">{% if en %}Explore{% else %}Découvrir{% endif %} →</span>
          </a></div>
        {%- endif -%}
      {%- endif -%}
    {%- endif -%}
  {%- endfor -%}
</div>
""" + SHUFFLE_JS + """
{% schema %}
{ "name": "Aisle shelves", "settings": [], "presets": [{ "name": "Aisle shelves" }] }
{% endschema %}
"""
open(T+'sections/decarie-aisle-shelves.liquid','w').write(SHELVES)

# ---------------- aisle (collection) page ----------------
AISLE=DEFS+"""
{%- style -%}
  .daisle { padding: 1.8rem 0 .4rem; }
  .daisle__crumb { font-size: 1.15rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--zfg); margin: 0 0 .4rem; }
  .daisle__crumb a { color: inherit; text-decoration: none; }
  .daisle__title { margin: 0; font-size: clamp(2.8rem, 7vw, 4.4rem); font-weight: 900; letter-spacing: -.02em; line-height: 1; }
  .daisle__count { margin: .6rem 0 0; color: rgba(var(--color-foreground), .65); font-size: 1.4rem; }
  .daisle__next { display: flex; gap: .6rem; overflow-x: auto; scrollbar-width: none; margin: 1.2rem 0 0; padding: 0; list-style: none; }
  .daisle__next::-webkit-scrollbar { display: none; }
  .daisle__next a { display: inline-block; padding: .7rem 1.2rem; border-radius: 99px; background: var(--zbg); color: var(--zfg); font-weight: 700; font-size: 1.3rem; text-decoration: none; white-space: nowrap; }
  ZONECSS
{%- endstyle -%}
{%- liquid
  assign aid = collection.handle | remove_first: 'allee-'
  assign a = nil
  for ad in aisles_def
    assign ap = ad | split: '|'
    if ap[0] == aid
      assign a = ap
    endif
  endfor
  assign zone = ''
  assign aname = collection.title
  if a
    assign zone = a[3]
    if en
      assign aname = a[2]
    else
      assign aname = a[1]
    endif
  endif
  assign zrec = nil
  for zd in zones_def
    assign zp = zd | split: '|'
    if zp[0] == zone
      assign zrec = zp
    endif
  endfor
-%}
<div class="daisle dplan__zone--{{ zone }}">
  <div class="page-width">
    {%- if zrec -%}<p class="daisle__crumb"><a href="{{ routes.root_url }}">{% if en %}{{ zrec[2] }}{% else %}{{ zrec[1] }}{% endif %}</a></p>{%- endif -%}
    <h1 class="daisle__title">{{ aname }}</h1>
    <p class="daisle__count">{{ collection.products_count }} {% if en %}products{% else %}produits{% endif %}</p>
  </div>
</div>
{% schema %}
{ "name": "Aisle header", "settings": [] }
{% endschema %}
""".replace('ZONECSS',zone_css)
open(T+'sections/decarie-aisle-page.liquid','w').write(AISLE)
open(T+'templates/collection.allee.json','w').write(json.dumps({'sections':{'aisle':{'type':'decarie-aisle-page','settings':{}},'combo':{'type':'decarie-combo','settings':{'show_on':'allee-pret-a-manger','demo_meat':'candy-0021010800000-cmuyx97c9','demo_salad':'candy-0021010700000-cmuyx813r'}},'product-grid':{'type':'main-collection-product-grid','settings':{'products_per_page': 48, 'columns_desktop': 5, 'color_scheme': 'scheme-1', 'image_ratio': 'square', 'image_shape': 'default', 'show_secondary_image': False, 'show_vendor': False, 'show_rating': False, 'quick_add': 'standard', 'enable_filtering': False, 'filter_type': 'horizontal', 'enable_sorting': True, 'columns_mobile': '2', 'padding_top': 16, 'padding_bottom': 36}}},'order':['aisle','combo','product-grid']},indent=2))

# ---------------- product page: goes with ----------------
GOES=DEFS+"""
{%- style -%}""" + SHELF_CSS + """{%- endstyle -%}
{%- liquid
  assign main = ''
  for tag in product.tags
    assign t7 = tag | slice: 0, 7
    if t7 == 'allee1-'
      assign main = tag | remove_first: 'allee1-'
    endif
  endfor
  assign pairs = ''
  for pd in pairs_def
    assign pp = pd | split: '|'
    if pp[0] == main
      assign pairs = pp[1] | split: '^'
    endif
  endfor
-%}
{%- if pairs != '' -%}
  {%- capture cards -%}
    {%- for pr in pairs -%}
      {%- assign pq = pr | split: '~' -%}
      {%- assign h = 'allee-' | append: pq[0] -%}
      {%- assign stag = 'rayon-' | append: pq[1] -%}
      {%- assign got = 0 -%}
      {%- for pl in (1..3) -%}
        {%- assign ptag = 'pop-' | append: pl -%}
        {%- for p in collections[h].products limit: 50 -%}
          {%- if got < 6 and p.featured_image and p.available and p.tags contains ptag and p.id != product.id -%}
            {%- if pq[1] == blank or p.tags contains stag -%}
              {%- render 'decarie-shelf-card', product: p, en: en -%}
              {%- assign got = got | plus: 1 -%}
            {%- endif -%}
          {%- endif -%}
        {%- endfor -%}
      {%- endfor -%}
    {%- endfor -%}
  {%- endcapture -%}
  {%- if cards != blank -%}
    <div class="page-width">
      <section class="dshelf">
        <div class="dshelf__head"><h2 class="dshelf__title">{% if en %}Goes well with{% else %}Ça va avec{% endif %}</h2></div>
        <div class="dshelf__track" data-dshelf-mix="10" data-key="gw-{{ product.id }}">{{ cards }}</div>
      </section>
    </div>
  {%- endif -%}
{%- endif -%}
""" + SHUFFLE_JS + """
{% schema %}
{ "name": "Goes well with", "settings": [], "presets": [{ "name": "Goes well with" }] }
{% endschema %}
"""
open(T+'sections/decarie-goes-with.liquid','w').write(GOES)

# ---------------- header: aisle bar + store-map overlay + surprise ----------------
NAV=DEFS+"""
{%- style -%}
  .dnav { position: relative; z-index: 4; background: rgb(var(--color-background)); border-bottom: 1px solid rgba(var(--color-foreground), .08); }
  .dnav__row { display: flex; align-items: center; gap: .6rem; overflow-x: auto; scrollbar-width: none; padding: .7rem 1.5rem; }
  .dnav__row::-webkit-scrollbar { display: none; }
  .dnav__btn, .dnav__a { flex: 0 0 auto; border: 0; border-radius: 99px; padding: .65rem 1.1rem; font-size: 1.3rem; font-weight: 700; white-space: nowrap; text-decoration: none; cursor: pointer; font-family: inherit; }
  .dnav__btn { background: #1a1a1a; color: #fff; }
  .dnav__btn--red { background: #DC241C; }
  .dnav__a { background: rgba(var(--color-foreground), .06); color: rgb(var(--color-foreground)); }
  .dnav__a.is-here { background: #1a1a1a; color: #fff; }
  .dmap { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.45); display: flex; align-items: flex-start; justify-content: center; padding: env(safe-area-inset-top, 0) 0 0; }
  .dmap[hidden] { display: none; }
  .dmap__panel { background: rgb(var(--color-background)); width: 100%; max-width: 92rem; max-height: 100%; overflow-y: auto; border-radius: 0 0 2rem 2rem; padding: 1.6rem 1.5rem 2.2rem; box-sizing: border-box; }
  .dmap__top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem; }
  .dmap__top h2 { margin: 0; font-size: 2.4rem; font-weight: 900; }
  .dmap__x { border: 0; background: rgba(0,0,0,.07); width: 4rem; height: 4rem; border-radius: 50%; font-size: 2rem; cursor: pointer; }
  .dmap__zones { display: grid; gap: 1rem; }
  .dmap__zone { background: var(--zbg); border-radius: 1.6rem; padding: 1.1rem 1.2rem 1.2rem; }
  .dmap__zone h3 { margin: 0 0 .7rem; font-size: 1.1rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--zfg); }
  .dmap__zone ul { display: flex; flex-wrap: wrap; gap: .5rem; list-style: none; margin: 0; padding: 0; }
  .dmap__zone a { display: inline-block; padding: .75rem 1.15rem; border-radius: 99px; background: #fff; color: #1a1a1a; text-decoration: none; font-weight: 700; font-size: 1.35rem; }
  .dmap__zone a small { color: #888; font-weight: 600; margin-left: .3rem; }
  @media screen and (min-width: 750px) { .dmap__zones { grid-template-columns: 1fr 1fr; } .dnav__row { justify-content: center; flex-wrap: wrap; } }
  ZONECSS
{%- endstyle -%}
{%- assign here = '' -%}
{%- if template.name == 'collection' -%}{%- assign here = collection.handle -%}{%- endif -%}
<div class="dnav" data-dnav>
  <div class="dnav__row">
    <button type="button" class="dnav__btn" data-dmap-open>🧭 {% if en %}Aisles{% else %}Allées{% endif %}</button>
    {%- assign sp = collections['specials'] -%}
    {%- if sp != blank and sp.products_count > 0 -%}<a class="dnav__a{% if here == 'specials' %} is-here{% endif %}" href="{{ sp.url }}" style="background:#FFD23F;color:#1a1a1a">🔥 {% if en %}Specials{% else %}Spéciaux{% endif %}</a>{%- endif -%}
    {%- for ad in aisles_def -%}
      {%- assign a = ad | split: '|' -%}
      {%- assign h = 'allee-' | append: a[0] -%}
      {%- if collections[h].products_count > 0 -%}
        <a class="dnav__a{% if here == h %} is-here{% endif %}" href="{{ collections[h].url }}">{% if en %}{{ a[2] }}{% else %}{{ a[1] }}{% endif %}</a>
      {%- endif -%}
    {%- endfor -%}
    <button type="button" class="dnav__btn dnav__btn--red" data-dsurprise>🎲</button>
  </div>
</div>
<div class="dmap" data-dmap hidden>
  <div class="dmap__panel" role="dialog" aria-modal="true" aria-label="{% if en %}Store map{% else %}Plan du magasin{% endif %}">
    <div class="dmap__top"><h2>🧭 {% if en %}Store map{% else %}Plan du magasin{% endif %}</h2><button type="button" class="dmap__x" data-dmap-close aria-label="Close">×</button></div>
    <div class="dmap__zones">
      {%- for zd in zones_def -%}
        {%- assign z = zd | split: '|' -%}
        {%- assign zaisles = z[3] | split: ',' -%}
        <div class="dmap__zone dplan__zone--{{ z[0] }}">
          <h3>{% if en %}{{ z[2] }}{% else %}{{ z[1] }}{% endif %}</h3>
          <ul role="list">
            {%- for ad in aisles_def -%}
              {%- assign a = ad | split: '|' -%}
              {%- assign h = 'allee-' | append: a[0] -%}
              {%- if zaisles contains a[0] and collections[h].products_count > 0 -%}
                <li><a href="{{ collections[h].url }}">{% if en %}{{ a[2] }}{% else %}{{ a[1] }}{% endif %}<small>{{ collections[h].products_count }}</small></a></li>
              {%- endif -%}
            {%- endfor -%}
          </ul>
        </div>
      {%- endfor -%}
    </div>
  </div>
</div>
<script>
  (function () {
    var nav = document.querySelector('[data-dnav]'), map = document.querySelector('[data-dmap]');
    var here = nav && nav.querySelector('.is-here'); if (here) here.scrollIntoView({ block: 'nearest', inline: 'center' });
    document.addEventListener('click', function (e) {
      if (e.target.closest('[data-dmap-open]')) { map.hidden = false; document.documentElement.style.overflow = 'hidden'; }
      else if (e.target.closest('[data-dmap-close]') || e.target === map) { map.hidden = true; document.documentElement.style.overflow = ''; }
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !map.hidden) { map.hidden = true; document.documentElement.style.overflow = ''; } });
    // 🎲 Surprise me: a random product that is in stock and has a photo
    document.addEventListener('click', function (e) {
      var b = e.target.closest('[data-dsurprise]'); if (!b) return;
      e.preventDefault(); b.disabled = true;
      var root = (window.Shopify && Shopify.routes && Shopify.routes.root) || '/';
      var page = 1 + Math.floor(Math.random() * 4);
      fetch(root + 'products.json?limit=250&page=' + page).then(function (r) { return r.json(); }).then(function (d) {
        var list = (d.products || []).filter(function (p) { return p.images && p.images.length && p.variants.some(function (v) { return v.available; }); });
        if (!list.length) return fetch(root + 'products.json?limit=250&page=1').then(function (r) { return r.json(); }).then(function (d2) { return d2.products || []; });
        return list;
      }).then(function (list) {
        var p = list[Math.floor(Math.random() * list.length)];
        if (p) location.href = root + 'products/' + p.handle; else b.disabled = false;
      }).catch(function () { b.disabled = false; location.href = root + 'collections/all'; });
    });
  })();
</script>
{% schema %}
{ "name": "Aisle bar", "settings": [] }
{% endschema %}
""".replace('ZONECSS',zone_css)
open(T+'sections/decarie-aisle-nav.liquid','w').write(NAV)

# ---------------- hamburger menu: zones -> aisles ----------------
DRAWER=DEFS+"""
{%- assign specials = collections['specials'] -%}
<li class="decarie-drawer__heading" role="presentation">{% if en %}Aisles{% else %}Allées{% endif %}</li>
{%- if specials != blank and specials.products_count > 0 -%}
  <li><a href="{{ specials.url }}" class="menu-drawer__menu-item list-menu__item link link--text focus-inset decarie-drawer__special">{{ 'decarie.drawer.specials' | t }}</a></li>
{%- endif -%}
{%- for zd in zones_def -%}
  {%- assign z = zd | split: '|' -%}
  {%- assign zaisles = z[3] | split: ',' -%}
  <li>
    <div class="decarie-acc">
      <a href="#" role="button" class="menu-drawer__menu-item list-menu__item link link--text focus-inset decarie-acc__summary" aria-expanded="false" data-decarie-acc>
        <span>{% if en %}{{ z[2] }}{% else %}{{ z[1] }}{% endif %}</span>
        {{- 'icon-caret.svg' | inline_asset_content -}}
      </a>
      <ul class="decarie-acc__list" role="list" hidden>
        {%- for ad in aisles_def -%}
          {%- assign a = ad | split: '|' -%}
          {%- assign h = 'allee-' | append: a[0] -%}
          {%- if zaisles contains a[0] and collections[h].products_count > 0 -%}
            <li><a href="{{ collections[h].url }}" class="menu-drawer__menu-item list-menu__item link link--text focus-inset decarie-drawer__sub">{% if en %}{{ a[2] }}{% else %}{{ a[1] }}{% endif %}</a></li>
          {%- endif -%}
        {%- endfor -%}
      </ul>
    </div>
  </li>
{%- endfor -%}
{%- assign ua = collections['saveurs-ukraine'] -%}
{%- if ua != blank and ua.products_count > 0 -%}
  <li><a href="{{ ua.url }}" class="menu-drawer__menu-item list-menu__item link link--text focus-inset">🇺🇦 {% if en %}Taste of Ukraine{% else %}Saveurs d'Ukraine{% endif %}</a></li>
{%- endif -%}
<li><a href="{{ routes.all_products_collection_url }}" class="menu-drawer__menu-item list-menu__item link link--text focus-inset">{{ 'decarie.drawer.all' | t }}</a></li>
<li class="decarie-drawer__divider" role="presentation"></li>
<script>
  (function () {
    if (window.__decarieAcc) return; window.__decarieAcc = true;
    document.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-decarie-acc]');   // a link, not a <button>: the theme's drawer script binds every <button> and <details> inside the menu
      if (!b) return;
      e.preventDefault(); e.stopPropagation();
      var open = b.getAttribute('aria-expanded') === 'true';
      b.setAttribute('aria-expanded', open ? 'false' : 'true');
      var list = b.nextElementSibling;
      if (list) list.hidden = open;
    }, true);
  })();
</script>
"""
open(T+'snippets/decarie-drawer-departments.liquid','w').write(DRAWER)
print('theme files written')
