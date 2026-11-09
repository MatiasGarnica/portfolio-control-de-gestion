"""
armar_tableros.py
=================
Rediseño de los 11 tableros del portfolio con DATOS FICTICIOS.

Lee los CSV sintéticos de ../../data/csv (los genera data/generate_synthetic_data.py),
calcula los indicadores de cada tablero, escribe un HTML por tablero en ./html/
y saca una captura PNG de cada uno en ../screenshots_v2/ (Playwright + Chromium).

Uso:
    python powerbi/redisenio/armar_tableros.py            # HTML + PNG
    python powerbi/redisenio/armar_tableros.py --solo-html

Requiere: pandas, numpy y (para los PNG) playwright con Chromium instalado.
Todo el dibujo es SVG/HTML escrito a mano, sin librerías de gráficos.
"""
import html
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
CSV = RAIZ / 'data' / 'csv'
OUT_HTML = AQUI / 'html'
OUT_PNG = RAIZ / 'powerbi' / 'screenshots_v2'

MARCA = 'AquaNorte Distribuidora (ficticia)'
PIE = 'Datos ficticios · Rediseño de portfolio'

# ---------------------------------------------------------------- paleta
INK, MUTE, GRID = '#1c2733', '#6b7686', '#e3e8ef'
BLUE, RED = '#1b6ca8', '#d64545'          # a favor / en contra
PET, LBLUE, GREY = '#0f4c5c', '#a9cce3', '#8b96a8'
MESES3 = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
MESES = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']


# ---------------------------------------------------------------- formato
def fnum(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


def fpct(x, d=1):
    return fnum(x, d) + ' %'


def fmon(x):
    a = abs(x)
    if a >= 1e9:
        return '$ ' + fnum(x / 1e9, 2) + ' mil M'
    if a >= 1e6:
        return '$ ' + fnum(x / 1e6, 1) + ' M'
    if a >= 1e3:
        return '$ ' + fnum(x / 1e3, 0) + ' mil'
    return '$ ' + fnum(x)


def lab(p):
    return f'{MESES3[p.month]}-{str(p.year)[2:]}'


def esc(s):
    return html.escape(str(s))


def delta(cur, prev, mode='pct', hib=True, txt='vs mes ant.'):
    """Devuelve (texto, clase). hib: True si subir es favorable, False si es desfavorable, None neutro."""
    if prev in (0, None) or pd.isna(prev) or pd.isna(cur):
        return ('s/d', 'neu')
    x = (cur / prev - 1) * 100 if mode == 'pct' else cur - prev
    unit = '%' if mode == 'pct' else 'pp'
    if abs(x) < 0.05:
        return (f'= {txt}', 'neu')
    arrow = '▲' if x > 0 else '▼'
    cls = 'neu' if hib is None else ('good' if (x > 0) == hib else 'bad')
    return (f'{arrow} {fnum(abs(x), 1)} {unit} <span>{txt}</span>', cls)


# ---------------------------------------------------------------- componentes HTML
def kpi(label, value, deltas=(), sub=''):
    d = ''.join(f'<div class="kd {c}">{t}</div>' for t, c in deltas)
    s = f'<div class="ks">{sub}</div>' if sub else ''
    return f'<div class="card kpi"><div class="kl">{label}</div><div class="kv">{value}</div>{d}{s}</div>'


def card(title, inner, sub='', style=''):
    t = f'<h3>{title}</h3>' if title else ''
    s = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="card" style="{style}">{t}{s}{inner}</div>'


def row(cols, *cards):
    return f'<div class="row" style="grid-template-columns:{cols}">' + ''.join(cards) + '</div>'


def legend(items):
    return '<div class="leg">' + ''.join(
        f'<span><i style="background:{c}"></i>{esc(n)}</span>' for n, c in items) + '</div>'


def table(headers, rows, aligns=None, cls=''):
    aligns = aligns or ['l'] + ['r'] * (len(headers) - 1)
    th = ''.join(f'<th class="{a}">{h}</th>' for h, a in zip(headers, aligns))
    body = ''
    for r in rows:
        body += '<tr>' + ''.join(f'<td class="{a}">{c}</td>' for c, a in zip(r, aligns)) + '</tr>'
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def heat(txt, v, vmin, vmax, color='27,108,168'):
    a = 0 if vmax == vmin else max(0, min(1, (v - vmin) / (vmax - vmin)))
    fg = '#fff' if a > .62 else INK
    return f'<span class="heat" style="background:rgba({color},{0.08 + a * .8:.2f});color:{fg}">{txt}</span>'


# ---------------------------------------------------------------- componentes SVG
def svg(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="system-ui,Segoe UI,Roboto,Arial,sans-serif">{inner}</svg>')


def T(x, y, s, size=13, fill=INK, anchor='start', weight='400', halo=False):
    h = ' stroke="#fff" stroke-width="3.5" paint-order="stroke"' if halo else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{h}>{esc(s)}</text>')


def hbars(rows, w, label_w=150, bar_h=20, gap=9, vmax=None, vfmt=fnum, ref=None, ref_txt='', val_w=90):
    """rows: dict(l, v, c, t) -> barras horizontales."""
    vmax = vmax or max(r['v'] for r in rows) or 1
    top = 20 if ref is not None else 2
    h = top + len(rows) * (bar_h + gap)
    pw = w - label_w - val_w
    o = []
    for i, r in enumerate(rows):
        y = top + i * (bar_h + gap)
        bw = max(1, pw * r['v'] / vmax)
        o.append(T(label_w - 10, y + bar_h / 2 + 4.5, r['l'], anchor='end'))
        o.append(f'<rect x="{label_w}" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="3" fill="{r.get("c", BLUE)}"/>')
        o.append(T(label_w + bw + 7, y + bar_h / 2 + 4.5, r.get('t', vfmt(r['v'])), 12.5, INK, weight='600', halo=True))
    if ref is not None:
        x = label_w + pw * ref / vmax
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="14" y2="{h}" stroke="{INK}" stroke-dasharray="4 3" stroke-width="1.2"/>')
        o.append(T(x, 10, ref_txt, 11.5, MUTE, 'middle'))
    return svg(w, h, ''.join(o))


def divbars(rows, w, label_w=150, bar_h=18, gap=8, vmax=None, vfmt=lambda v: fnum(v, 1) + ' %', val_w=0):
    """Barras divergentes (negativo rojo / positivo azul)."""
    vmax = vmax or max(abs(r['v']) for r in rows) or 1
    h = len(rows) * (bar_h + gap) + 2
    half = (w - label_w - 150) / 2
    mid = label_w + 75 + half
    o = [f'<line x1="{mid:.1f}" x2="{mid:.1f}" y1="0" y2="{h}" stroke="{GREY}" stroke-width="1"/>']
    for i, r in enumerate(rows):
        y = 2 + i * (bar_h + gap)
        v = r['v']
        bw = max(1, half * abs(v) / vmax)
        col = BLUE if v >= 0 else RED
        o.append(T(label_w - 8, y + bar_h / 2 + 4.5, r['l'], 12.5, anchor='end'))
        if v >= 0:
            o.append(f'<rect x="{mid:.1f}" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="3" fill="{col}"/>')
            o.append(T(mid + bw + 6, y + bar_h / 2 + 4.5, vfmt(v), 12, INK, weight='600'))
        else:
            o.append(f'<rect x="{mid - bw:.1f}" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="3" fill="{col}"/>')
            o.append(T(mid - bw - 6, y + bar_h / 2 + 4.5, vfmt(v), 12, INK, 'end', '600'))
    return svg(w, h, ''.join(o))


def lines(series, xl, w, h, ymin=0, ymax=None, vfmt=fnum, ml=46, mr=140, mt=14, mb=28, ticks=4):
    """series: dict(n, v, c, w, lab)."""
    vals = [v for s in series for v in s['v'] if v is not None and not pd.isna(v)]
    ymax = ymax if ymax is not None else max(vals) * 1.12
    ymin = ymin if ymin is not None else min(vals) * .9
    n = len(xl)
    X = lambda i: ml + (w - ml - mr) * i / max(1, n - 1)
    Y = lambda v: mt + (h - mt - mb) * (1 - (v - ymin) / ((ymax - ymin) or 1))
    o = []
    for k in range(ticks + 1):
        v = ymin + (ymax - ymin) * k / ticks
        o.append(f'<line x1="{ml}" x2="{w - mr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        o.append(T(ml - 8, Y(v) + 4, vfmt(v), 11.5, MUTE, 'end'))
    for i, x in enumerate(xl):
        o.append(T(X(i), h - 8, x, 11.5, MUTE, 'middle'))
    ends = []
    for s in sorted(series, key=lambda s: 1 if s.get('lab') else 0):
        pts = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(s['v']) if v is not None and not pd.isna(v))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{s["c"]}" stroke-width="{s.get("w", 2)}" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
        last = [(i, v) for i, v in enumerate(s['v']) if v is not None and not pd.isna(v)][-1]
        if s.get('lab'):
            o.append(f'<circle cx="{X(last[0]):.1f}" cy="{Y(last[1]):.1f}" r="3.5" fill="{s["c"]}"/>')
            ends.append([Y(last[1]), s])
    ends.sort(key=lambda e: e[0])
    for j in range(1, len(ends)):
        if ends[j][0] - ends[j - 1][0] < 15:
            ends[j][0] = ends[j - 1][0] + 15
    for y, s in ends:
        lastv = [v for v in s['v'] if v is not None and not pd.isna(v)][-1]
        o.append(T(w - mr + 10, y + 4, f'{s["n"]} {vfmt(lastv)}', 12, s['c'], weight='600'))
    return svg(w, h, ''.join(o))


def stack_v(cats, series, w, h, ml=40, mt=10, mb=26, minlab=7):
    """Columnas apiladas al 100 %. series: (nombre, color, [valores %])."""
    n = len(cats)
    bw = (w - ml) / n * .62
    ph = h - mt - mb
    o = []
    for k in range(5):
        y = mt + ph * (1 - k / 4)
        o.append(f'<line x1="{ml}" x2="{w}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(T(ml - 6, y + 4, f'{k * 25}%', 11, MUTE, 'end'))
    for i, c in enumerate(cats):
        x = ml + (w - ml) / n * (i + .5) - bw / 2
        acc = 0
        for nm, col, vals in series:
            v = vals[i]
            hh = ph * v / 100
            y = mt + ph - ph * (acc + v) / 100
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(hh, 0):.1f}" fill="{col}"/>')
            if v >= minlab:
                fg = '#fff' if col in (BLUE, PET, GREY, RED) else INK
                o.append(T(x + bw / 2, y + hh / 2 + 4, f'{v:.0f}', 11.5, fg, 'middle', '600'))
            acc += v
        o.append(T(x + bw / 2, h - 8, c, 11.5, MUTE, 'middle'))
    return svg(w, h, ''.join(o))


def stack_h(rows, colors, w, label_w=110, bar_h=24, gap=10, extra_w=110, minlab=6):
    """rows: dict(l, v=[% por serie], e=texto a la derecha)."""
    h = len(rows) * (bar_h + gap) + 2
    pw = w - label_w - extra_w
    o = []
    for i, r in enumerate(rows):
        y = 2 + i * (bar_h + gap)
        o.append(T(label_w - 10, y + bar_h / 2 + 4.5, r['l'], anchor='end'))
        x = label_w
        for v, col in zip(r['v'], colors):
            bw = pw * v / 100
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{bar_h}" fill="{col}"/>')
            if v >= minlab:
                fg = '#fff' if col in (BLUE, PET, GREY) else INK
                o.append(T(x + bw / 2, y + bar_h / 2 + 4.5, f'{v:.0f}', 12, fg, 'middle', '600'))
            x += bw
        o.append(T(label_w + pw + 10, y + bar_h / 2 + 4.5, r.get('e', ''), 12.5, INK, weight='600'))
    return svg(w, h, ''.join(o))


def vbars(cats, vals, w, h, colors=None, vfmt=fnum, ml=10, mt=22, mb=30, ymax=None):
    n = len(cats)
    ymax = ymax or max(vals) * 1.15 or 1
    bw = (w - ml) / n * .6
    ph = h - mt - mb
    o = [f'<line x1="{ml}" x2="{w}" y1="{mt + ph}" y2="{mt + ph}" stroke="{GREY}"/>']
    for i, (c, v) in enumerate(zip(cats, vals)):
        x = ml + (w - ml) / n * (i + .5) - bw / 2
        hh = ph * v / ymax
        col = (colors or [BLUE] * n)[i]
        o.append(f'<rect x="{x:.1f}" y="{mt + ph - hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="3" fill="{col}"/>')
        o.append(T(x + bw / 2, mt + ph - hh - 6, vfmt(v), 12, INK, 'middle', '600'))
        o.append(T(x + bw / 2, h - 10, c, 11.5, MUTE, 'middle'))
    return svg(w, h, ''.join(o))


# ---------------------------------------------------------------- página
CSS = """
*{box-sizing:border-box}
body{margin:0;width:1600px;background:#eef1f5;font-family:system-ui,"Segoe UI",Roboto,Arial,sans-serif;color:#1c2733;font-size:14px}
.hdr{background:linear-gradient(90deg,#0f4c5c,#1a7f8e);color:#fff;padding:20px 28px 22px;display:flex;justify-content:space-between;align-items:flex-end;gap:24px}
.brand{font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.88;margin-bottom:8px;display:flex;align-items:center;gap:9px}
h1{margin:0;font-size:30px;font-weight:700;letter-spacing:-.01em}
.head{font-size:17px;opacity:.96;margin-top:7px;max-width:1120px;line-height:1.35}
.chips{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:400px}
.chip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.38);padding:5px 12px;border-radius:999px;font-size:13px;white-space:nowrap}
.main{padding:20px 28px 6px;display:flex;flex-direction:column;gap:16px}
.row{display:grid;gap:16px}
.card{background:#fff;border:1px solid #d6dbe3;border-radius:10px;box-shadow:0 1px 3px rgba(20,40,70,.08);padding:16px 20px;min-width:0}
.card h3{margin:0 0 2px;font-size:15px;font-weight:650}
.sub{color:#6b7686;font-size:12.5px;margin-bottom:10px;line-height:1.35}
.kpi{padding:14px 18px}
.kl{color:#6b7686;font-size:12.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.kv{font-size:34px;font-weight:700;margin:4px 0 2px;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kd{font-size:13px;font-weight:650;margin-top:1px}.kd span{color:#6b7686;font-weight:400}
.good{color:#1b6ca8}.bad{color:#d64545}.neu{color:#6b7686}
.ks{color:#6b7686;font-size:12.5px;margin-top:3px}
.leg{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:#44505f;margin:2px 0 8px}
.leg i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:#6b7686;font-weight:650;padding:6px 8px;border-bottom:1.5px solid #d6dbe3}
td{padding:6px 8px;border-bottom:1px solid #edf0f4;font-size:13.5px}
.l{text-align:left}.r{text-align:right}.c{text-align:center}
.heat{display:inline-block;min-width:54px;padding:3px 8px;border-radius:5px;text-align:center;font-weight:600}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.pill.bad{background:#fbe4e4}.pill.good{background:#dcebf6}.pill.neu{background:#eaedf2}
.note{font-size:12.5px;color:#44505f;line-height:1.45}
.foot{padding:14px 28px 22px;color:#6b7686;font-size:12.5px;display:flex;justify-content:space-between;gap:30px}
"""

DROP = ('<svg width="22" height="22" viewBox="0 0 24 24"><path d="M12 2C12 2 5 10.2 5 15a7 7 0 0 0 14 0C19 10.2 12 2 12 2z" '
        'fill="#fff" opacity=".95"/></svg>')


def pagina(titulo, titular, chips, cuerpo, nota=''):
    ch = ''.join(f'<span class="chip">{esc(c)}</span>' for c in chips)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=1600">
<title>{esc(titulo)} · {esc(MARCA)}</title><style>{CSS}</style></head><body>
<div class="hdr"><div><div class="brand">{DROP}<span>{esc(MARCA)} · Control de gestión</span></div>
<h1>{esc(titulo)}</h1><div class="head">{titular}</div></div><div class="chips">{ch}</div></div>
<div class="main">{cuerpo}</div>
<div class="foot"><span>{esc(nota)}</span><span>{PIE}</span></div></body></html>"""


# ================================================================= DATOS
def cargar():
    rd = lambda n, **k: pd.read_csv(CSV / f'{n}.csv', keep_default_na=False, na_values=[''], **k)
    D = {}
    D['ped'] = rd('Pedidos', usecols=['idPedido', 'idVendedor', 'Fecha_Pedido', 'idCliente'], parse_dates=['Fecha_Pedido'])
    D['pp'] = rd('Pedidos_Productos', usecols=['idPedido', 'idProducto', 'Cantidad', 'Precio'])
    D['prod'] = rd('Productos', usecols=['idProducto', 'Litros'])
    cli = rd('Clientes', usecols=['NroCta', 'Direcc', 'TipCli', 'CndPag', 'FecAlt'], parse_dates=['FecAlt'])
    cli['estado'] = 'Activo'
    baja = rd('ClientesBaja', usecols=['NroCta', 'Direcc', 'TipCli', 'CndPag', 'FecAlt'], parse_dates=['FecAlt'])
    baja['estado'] = 'Baja'
    cli = pd.concat([cli, baja], ignore_index=True)
    rutas = rd('Rutas', usecols=['Codigo', 'Vnddor'])
    rep = rd('repartos', usecols=['Codigo', 'CodSup'])
    cr = rd('ClientesRutas', usecols=['CdRuta', 'Cliente_Ruteo']).drop_duplicates('Cliente_Ruteo')
    ZONA = {201: 'Norte', 202: 'Sur', 203: 'Este', 204: 'Oeste', 205: 'Gastronomía', 206: 'Empresas', 208: 'Ribera'}
    rz = rutas.merge(rep.rename(columns={'Codigo': 'Vnddor'}), on='Vnddor')
    rz['zona'] = rz.CodSup.map(ZONA)
    cli = cli.merge(cr.rename(columns={'Cliente_Ruteo': 'NroCta', 'CdRuta': 'ruta'}), on='NroCta', how='left')
    cli = cli.merge(rz[['Codigo', 'Vnddor', 'zona']].rename(columns={'Codigo': 'ruta'}), on='ruta', how='left')
    D['cli'] = cli
    act = cli[cli.estado == 'Activo']
    L = D['pp'].merge(D['ped'][['idPedido', 'Fecha_Pedido', 'idCliente', 'idVendedor']], on='idPedido')
    L = L.merge(D['prod'], on='idProducto')
    L['pesos'] = L.Cantidad * L.Precio
    L['litros'] = L.Cantidad * L.Litros
    L = L.merge(act[['NroCta', 'TipCli', 'zona', 'ruta']], left_on='idCliente', right_on='NroCta', how='left')
    L['mes'] = L.Fecha_Pedido.dt.to_period('M')
    L['soda'] = L.idProducto.isin(['m', 'SX'])
    L['fam'] = np.where(L.soda, 'Sodas', L.TipCli.map({'HOG': 'Botellones', 'GAS': 'Gastro'}).fillna('Resto'))
    D['L'] = L
    mt = rd('MovTes', usecols=['FchMov', 'NroCta', 'CodCpt', 'Import'], parse_dates=['FchMov'])
    mt['NroCta'] = pd.to_numeric(mt.NroCta)
    mt = mt.merge(act[['NroCta', 'zona', 'ruta', 'Vnddor']], on='NroCta', how='left')
    mt['mes'] = mt.FchMov.dt.to_period('M')
    D['mt'] = mt
    cc = rd('CtaCteVT', usecols=['CodMov', 'NroMov', 'FchMov', 'NroCta', 'NroApl', 'Import'], parse_dates=['FchMov'])
    cc['NroCta'] = pd.to_numeric(cc.NroCta)
    D['cc'] = cc
    D['cs'] = rd('ClientesServicios', usecols=['IdCliente', 'Fecha_Desde', 'Fecha_Baja'],
                 parse_dates=['Fecha_Desde', 'Fecha_Baja'])
    D['me'] = rd('Movimientos_Equipos', usecols=['Fecha', 'IdCliente', 'Tipo_Movimiento'], parse_dates=['Fecha'])
    return D


# ================================================================= TABLEROS
CUR = pd.Period('2026-04', 'M')      # último mes completo del dataset (datos hasta 19/05/2026)
PREV = CUR - 1
YAGO = CUR - 12
METODOS = [('EFE', 'Efectivo', PET), ('DIG', 'Digital', BLUE), ('TRF', 'Transferencia', '#6fa8d0'),
           ('TRJ', 'Tarjeta', LBLUE), ('CHQ', 'Cheque', GREY)]


def mix_por(df):
    t = df.groupby('CodCpt').Import.sum()
    tot = t.sum()
    return {k: t.get(k, 0) / tot * 100 for k, _, _ in METODOS}, tot


# ---- 01
def b01(D):
    mt = D['mt']
    meses = [CUR - i for i in range(5, -1, -1)]
    mixm = {m: mix_por(mt[mt.mes == m]) for m in meses}
    (mc, tc), (mp, tp) = mixm[CUR], mixm[PREV]
    kp = row('repeat(5,1fr)',
             kpi('Total cobrado', fmon(tc), [delta(tc, tp)]),
             kpi('% Efectivo', fpct(mc['EFE']), [delta(mc['EFE'], mp['EFE'], 'pp', False)], 'menos efectivo = menos riesgo de traslado'),
             kpi('% Digital', fpct(mc['DIG']), [delta(mc['DIG'], mp['DIG'], 'pp', True)],
                 f'en 6 meses: {"+" if mc["DIG"] >= mixm[meses[0]][0]["DIG"] else "-"}{fnum(abs(mc["DIG"] - mixm[meses[0]][0]["DIG"]), 1)} pp (vs {lab(meses[0])})'),
             kpi('% Transferencias', fpct(mc['TRF']), [delta(mc['TRF'], mp['TRF'], 'pp', True)]),
             kpi('% Cheques', fpct(mc['CHQ']), [delta(mc['CHQ'], mp['CHQ'], 'pp', False)]))
    zs = []
    for z, g in mt[mt.mes == CUR].groupby('zona'):
        m, t = mix_por(g)
        zs.append((z, m, t))
    zs.sort(key=lambda x: -x[1]['EFE'])
    rows = [dict(l=z, v=[m[k] for k, _, _ in METODOS], e=fmon(t)) for z, m, t in zs]
    c1 = card('Mix de cobranza por zona · ' + lab(CUR),
              legend([(n, c) for _, n, c in METODOS]) +
              stack_h(rows, [c for _, _, c in METODOS], 860, label_w=110, extra_w=110, bar_h=34, gap=18),
              'Ordenado de mayor a menor dependencia del efectivo. Números en % del total cobrado.')
    ser = [(n, c, [mixm[m][0][k] for m in meses]) for k, n, c in METODOS]
    c2 = card('Evolución del mix (6 meses)', legend([(n, c) for _, n, c in METODOS]) +
              stack_v([lab(m) for m in meses], ser, 588, 370), '% del total cobrado por medio de pago.')
    top = zs[0]
    d = mc['DIG'] - mixm[meses[0]][0]['DIG']
    tit = (f'El efectivo sigue siendo {mc["EFE"]:.0f} % de lo cobrado (más alto en {top[0]}: {top[1]["EFE"]:.0f} %) '
           f'y lo digital {"ganó" if d >= 0 else "perdió"} {fnum(abs(d), 1)} pp en 6 meses (vs {lab(meses[0])}; contra el mes anterior: {fnum(mc["DIG"] - mp["DIG"], 1)} pp)')
    return dict(titulo='Cobranzas por zona · mix de medios de pago', titular=tit,
                chips=['Mes: ' + lab(CUR), 'Todas las zonas', 'Comparación: mes anterior'],
                cuerpo=kp + row('900px 628px', c1, c2),
                nota='Digital = billeteras y pagos electrónicos. Zonas inventadas a partir de la jerarquía de supervisores del dataset.')


# ---- 02
def b02(D):
    cc, cli = D['cc'], D['cli']
    fac = cc[cc.CodMov == 'FACA'][['NroMov', 'FchMov', 'NroCta', 'Import']].merge(
        cli[['NroCta', 'zona', 'TipCli']], on='NroCta', how='left')
    fac['grande'] = fac.TipCli.isin(['EMP', 'INS', 'GCT'])
    app = cc[cc.CodMov.isin(['RECA', 'NCA'])][['NroApl', 'FchMov', 'Import']].rename(
        columns={'FchMov': 'FchApl', 'Import': 'ImpApl'})
    app = app.merge(fac[['NroMov', 'FchMov', 'zona', 'grande']], left_on='NroApl', right_on='NroMov')
    meses = [CUR - i for i in range(5, -1, -1)]

    def dso(c, key):
        f = fac[(fac.FchMov > c - pd.Timedelta(days=90)) & (fac.FchMov <= c)]
        a = app[(app.FchMov > c - pd.Timedelta(days=90)) & (app.FchMov <= c) & (app.FchApl <= c)]
        fi = f.groupby(key).Import.sum() if key else pd.Series({'T': f.Import.sum()})
        ai = a.groupby(key).ImpApl.sum() if key else pd.Series({'T': a.ImpApl.sum()})
        return ((fi + ai.reindex(fi.index).fillna(0)) / (fi / 90))

    zon = {m: dso(m.end_time.normalize(), 'zona') for m in meses}
    gra = {m: dso(m.end_time.normalize(), 'grande') for m in meses}
    tot = {m: dso(m.end_time.normalize(), None)['T'] for m in meses}
    zonas = sorted(zon[CUR].index, key=lambda z: -zon[CUR][z])
    kp = row('repeat(4,1fr)',
             kpi('Días calle · total', fnum(tot[CUR], 1) + ' d', [delta(tot[CUR], tot[PREV], 'pct', False)],
                 'saldo abierto ÷ venta diaria (90 d)'),
             kpi('Zona más alta', f'{zonas[0]}', [(fnum(zon[CUR][zonas[0]], 1) + ' d', 'bad')]),
             kpi('Zona más baja', f'{zonas[-1]}', [(fnum(zon[CUR][zonas[-1]], 1) + ' d', 'good')]),
             kpi('Cuentas grandes', fnum(gra[CUR][True], 1) + ' d',
                 [delta(gra[CUR][True], gra[CUR][False], 'pct', False, 'vs resto de cuentas')]))
    # tabla zona x mes
    allv = [zon[m][z] for m in meses for z in zonas]
    rows = []
    for z in zonas:
        first, last = zon[meses[0]][z], zon[CUR][z]
        dd = last - first
        pill = f'<span class="pill {"bad" if dd > 1 else "good" if dd < -1 else "neu"}">{"+" if dd > 0 else ""}{fnum(dd, 1)}</span>'
        rows.append([z] + [heat(fnum(zon[m][z], 1), zon[m][z], min(allv), max(allv), '214,69,69') for m in meses] + [pill])
    c1 = card('Días calle por zona y mes', table(['Zona'] + [lab(m) for m in meses] + ['Δ 6 m'], rows,
              ['l'] + ['c'] * 6 + ['c']), 'Más oscuro = más días para cobrar. Δ 6 m: cambio entre el primer y el último mes.')
    peor = sorted(zonas, key=lambda z: -(zon[CUR][z] - zon[meses[0]][z]))[:2]
    mejor = sorted(zonas, key=lambda z: (zon[CUR][z] - zon[meses[0]][z]))[0]
    cols = {peor[0]: RED, peor[1]: '#e8935a', mejor: BLUE}
    ser = [dict(n=z, v=[zon[m][z] for m in meses], c=cols.get(z, '#c3cad6'), w=3 if z in cols else 1.6, lab=z in cols)
           for z in zonas]
    ser.append(dict(n='Total', v=[tot[m] for m in meses], c=INK, w=2.2, lab=True))
    c2 = card('Evolución: las zonas que más empeoran, en rojo/naranja',
              lines(ser, [lab(m) for m in meses], 628, 262, ymin=0), 'Gris: resto de las zonas. Azul: la que más mejora.')
    c3 = card('Cuentas grandes vs resto',
              legend([('Cuentas grandes', PET), ('Resto', LBLUE)]) +
              lines([dict(n='Grandes', v=[gra[m][True] for m in meses], c=PET, w=3, lab=True),
                     dict(n='Resto', v=[gra[m][False] for m in meses], c=LBLUE, w=3, lab=True)],
                    [lab(m) for m in meses], 1460, 200, ymin=0, mr=160), 'Cuenta grande = empresa, institución o gran cuenta.')
    tit = (f'{peor[0]} es la zona que más empeora en 6 meses (+{fnum(zon[CUR][peor[0]] - zon[meses[0]][peor[0]], 1)} d vs {lab(meses[0])}) '
           f'y {mejor} la que más mejora; el total está en {fnum(tot[CUR], 1)} días y la zona más alta hoy es {zonas[0]} ({fnum(zon[CUR][zonas[0]], 1)} d)')
    return dict(titulo='Días calle por zona', titular=tit,
                chips=['Cierre: ' + lab(CUR), 'Ventana: 6 meses'],
                cuerpo=kp + row('860px 668px', c1, c2) + c3,
                nota='Días calle = saldo pendiente de facturas de los últimos 90 días ÷ (venta de 90 días / 90).')


# ---- 03
TASAS = {'EFE': 1.2, 'CHQ': 0.6, 'TRF': 0.4, 'DIG': 3.2, 'TRJ': 4.5}   # % de costo estimado (supuestos ficticios)
NOMB = {k: n for k, n, _ in METODOS}
UMBRAL = 2.0


def b03(D):
    mt = D['mt']
    x = mt[(mt.mes == CUR) & mt.Vnddor.notna()].copy()
    x['costo'] = x.Import * x.CodCpt.map(TASAS) / 100
    g = x.groupby('Vnddor').agg(cob=('Import', 'sum'), costo=('costo', 'sum'))
    g['pct'] = g.costo / g.cob * 100
    dom = x.groupby(['Vnddor', 'CodCpt']).Import.sum().unstack(fill_value=0)
    g['dom'] = dom.idxmax(axis=1).map(NOMB)
    g['domp'] = dom.max(axis=1) / dom.sum(axis=1) * 100
    g['zona'] = x.groupby('Vnddor').zona.first()
    g = g.sort_values('pct', ascending=False)
    tc, tcost = g.cob.sum(), g.costo.sum()
    sobre = int((g.pct > UMBRAL).sum())
    xp = mt[(mt.mes == PREV) & mt.Vnddor.notna()]
    pc_prev = (xp.Import * xp.CodCpt.map(TASAS) / 100).sum() / xp.Import.sum() * 100
    kp = row('repeat(5,1fr)',
             kpi('Total cobrado', fmon(tc)),
             kpi('Costo estimado', fmon(tcost)),
             kpi('% costo', fpct(tcost / tc * 100, 2), [delta(tcost / tc * 100, pc_prev, 'pp', False)]),
             kpi('Vendedores', fnum(len(g))),
             kpi(f'Vendedores > {UMBRAL:.0f} %', fnum(sobre), [(f'{sobre / len(g) * 100:.0f} % del total', 'bad' if sobre else 'good')]))
    top = g.head(14)
    rows = [dict(l=f'V-{int(v):04d} · {r.zona}', v=r.pct, c=RED if r.pct > UMBRAL else BLUE,
                 t=f'{fnum(r.pct, 2)} % · {r.dom} {r.domp:.0f} %') for v, r in top.iterrows()]
    c1 = card('Vendedores con mayor costo de cobranza', hbars(rows, 880, label_w=190, val_w=230, bar_h=24, gap=10,
              vmax=max(top.pct.max(), UMBRAL) * 1.02, vfmt=lambda v: fnum(v, 2) + ' %', ref=UMBRAL, ref_txt=f'umbral {UMBRAL:.0f} %'),
              'En rojo, por encima del umbral. A la derecha: % de costo y medio de pago dominante del vendedor.')
    mm = x.groupby('CodCpt').Import.sum()
    tr = []
    for k, n, c in sorted(METODOS, key=lambda m: -mm.get(m[0], 0)):
        mix = mm.get(k, 0) / tc * 100
        tr.append([n, f'<div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">'
                      f'<div style="width:{mix * 1.5:.0f}px;height:10px;background:{c};border-radius:2px"></div>{fnum(mix, 1)} %</div>',
                   fpct(TASAS[k], 1), fmon(mm.get(k, 0) * TASAS[k] / 100)])
    tr.append(['<b>Total</b>', '<b>100 %</b>', f'<b>{fnum(tcost / tc * 100, 2)} %</b>', f'<b>{fmon(tcost)}</b>'])
    c2 = card('Resumen por medio de pago', table(['Medio', '% mix', 'Tasa', 'Costo'], tr), 'La tasa es un supuesto ficticio por medio.')
    bins = [(0, 1, '< 1 %'), (1, 1.5, '1–1,5'), (1.5, 2, '1,5–2'), (2, 99, '> 2 %')]
    cnt = [int(((g.pct >= a) & (g.pct < b)).sum()) for a, b, _ in bins]
    c3 = card('Cuántos vendedores en cada tramo de costo', vbars([b[2] for b in bins], cnt, 560, 190,
              colors=[BLUE, BLUE, BLUE, RED], vfmt=lambda v: fnum(v)), 'Cantidad de vendedores por % de costo.')
    tit = (f'{sobre} de {len(g)} vendedores superan el {UMBRAL:.0f} % de costo de cobranza; '
           f'el medio digital explica la mayor parte del costo ({fmon(mm.get("DIG", 0) * TASAS["DIG"] / 100)})')
    return dict(titulo='Costo de cobranza por vendedor', titular=tit,
                chips=['Mes: ' + lab(CUR), f'Umbral: {UMBRAL:.0f} %'],
                cuerpo=kp + row('928px 600px', c1, f'<div style="display:flex;flex-direction:column;gap:16px">{c2}{c3}</div>'),
                nota='Costos estimados con tasas supuestas (efectivo 1,2 %: manejo, traslado, arqueo y faltantes; cheque 0,6 %, transferencia 0,4 %, digital 3,2 %, tarjeta 4,5 %).')


# ---- 04
def b04(D):
    cs, ped, me = D['cs'], D['ped'], D['me']
    C, E = pd.Timestamp('2026-03-31'), pd.Timestamp('2026-04-30')
    a = cs[(cs.Fecha_Desde <= C) & (cs.Fecha_Baja.isna() | (cs.Fecha_Baja > C))].copy()
    last = ped[ped.Fecha_Pedido <= C].groupby('idCliente').Fecha_Pedido.max()
    a['ult'] = a.IdCliente.map(last)
    a['dias'] = (C - a.ult.fillna(a.Fecha_Desde)).dt.days
    a = a[a.dias >= 60].copy()
    po = ped[(ped.Fecha_Pedido > C) & (ped.Fecha_Pedido <= E)]
    fug = set(po[po.idVendedor == 146].idCliente)
    cor = set(po[po.idVendedor == 147].idCliente)
    vol = set(po.idCliente)
    # simulación: el dataset no registra retiros de equipos de esta cohorte; ~6 % de los que seguirían sin consumo, semilla fija
    cand = sorted(set(a.IdCliente) - fug - cor - vol)
    ret = set(np.random.default_rng(42).choice(cand, size=max(1, round(len(a) * .06)), replace=False)) if cand else set()

    def ev(c):
        if c in fug:
            return 'Fugado'
        if c in cor:
            return 'Corrección interna'
        if c in vol:
            return 'Volvió a comprar'
        if c in ret:
            return 'Retiro de equipo'
        return 'Sigue sin consumo'
    a['ev'] = a.IdCliente.map(ev)
    n = len(a)
    cnt = a.ev.value_counts()
    orden = [('Sigue sin consumo', RED), ('Volvió a comprar', BLUE), ('Retiro de equipo', GREY),
             ('Corrección interna', LBLUE), ('Fugado', PET)]
    pc = lambda k: cnt.get(k, 0) / n * 100
    kp = row('repeat(5,1fr)',
             kpi('Cohorte sin consumo', fnum(n), sub='equipos F/C activos, 60+ días sin pedir al 31/03'),
             kpi('Sigue sin consumo', fpct(pc('Sigue sin consumo')), [(f'{fnum(cnt.get("Sigue sin consumo", 0))} cuentas', 'bad')]),
             kpi('Volvió a comprar', fpct(pc('Volvió a comprar')), [(f'{fnum(cnt.get("Volvió a comprar", 0))} cuentas', 'good')]),
             kpi('Retiro de equipo', fpct(pc('Retiro de equipo')), [(f'{fnum(cnt.get("Retiro de equipo", 0))} equipos (simulado)', 'neu')]),
             kpi('Fugados + correcciones', fpct(pc('Fugado') + pc('Corrección interna')),
                 [(f'{cnt.get("Fugado", 0) + cnt.get("Corrección interna", 0)} cuentas', 'neu')]))
    rows = [dict(l=k, v=cnt.get(k, 0), c=c, t=f'{fnum(cnt.get(k, 0))} · {fnum(pc(k), 1)} %') for k, c in orden]
    c1 = card('¿Qué pasó en abril con la cohorte?', hbars(rows, 700, label_w=150, val_w=130, bar_h=32, gap=16, vmax=max(r['v'] for r in rows) * 1.0),
              'Evento único por cuenta, observado hasta el 30/04/2026.')
    bins = [(60, 90, '60–90'), (90, 120, '90–120'), (120, 180, '120–180'), (180, 99999, '> 180')]
    ser = []
    for lo, hi, nm in bins:
        s = a[(a.dias >= lo) & (a.dias < hi)]
        ser.append((nm, len(s), (s.ev == 'Sigue sin consumo').sum()))
    maxv = max(s[1] for s in ser) * 1.15
    o = ['<line x1="10" x2="600" y1="190" y2="190" stroke="%s"/>' % GREY]
    bw = 590 / len(ser) * .6
    for i, (nm, tot, sig) in enumerate(ser):
        x = 10 + 590 / len(ser) * (i + .5) - bw / 2
        h1, h2 = 160 * sig / maxv, 160 * (tot - sig) / maxv
        o.append(f'<rect x="{x:.1f}" y="{190 - h1:.1f}" width="{bw:.1f}" height="{h1:.1f}" fill="{RED}"/>')
        o.append(f'<rect x="{x:.1f}" y="{190 - h1 - h2:.1f}" width="{bw:.1f}" height="{h2:.1f}" fill="{BLUE}"/>')
        o.append(T(x + bw / 2, 190 - h1 - h2 - 6, fnum(tot), 12, INK, 'middle', '600'))
        o.append(T(x + bw / 2, 208, nm + ' d', 11.5, MUTE, 'middle'))
    c2 = card('Antigüedad de la inactividad (días sin pedir)', legend([('Sigue sin consumo', RED), ('Reaccionó', BLUE)]) +
              svg(610, 220, ''.join(o)), 'A más días sin consumo, más difícil la recuperación.')
    pri = a[a.ev == 'Sigue sin consumo'].sort_values('dias', ascending=False).head(10)
    zmap = D['cli'].set_index('NroCta').zona
    tr = [[f'CTA {int(r.IdCliente)}', zmap.get(r.IdCliente, '-'), fnum(r.dias), r.Fecha_Desde.strftime('%d/%m/%Y'),
           '<span class="pill bad">Retiro / llamado</span>'] for r in pri.itertuples()]
    c3 = card('Cuentas a priorizar (más días sin consumo)', table(['Cuenta', 'Zona', 'Días sin consumo', 'Equipo desde', 'Acción'], tr,
              ['l', 'l', 'r', 'r', 'c']), 'Las 10 cuentas con mayor inactividad que siguen sin volver.')
    tit = (f'Al 30/04, un mes después del corte, {fpct(pc("Volvió a comprar"), 0)} de los equipos F/C inactivos volvió a comprar '
           f'y {fpct(pc("Sigue sin consumo"), 0)} sigue sin consumo ({fnum(cnt.get("Sigue sin consumo", 0))} cuentas a gestionar)')
    return dict(titulo='Frío/Calor sin consumo · cohorte marzo', titular=tit,
                chips=['Corte: 31/03/2026', 'Seguimiento: abril', 'Umbral: 60 días'],
                cuerpo=kp + row('730px 1fr', c1, c2) + c3,
                nota='Cohorte: equipos instalados y activos al 31/03 con 60 o más días sin pedidos. Cuentas con numeración sintética. Valor simulado: el dataset no modela retiros de equipos de la cohorte (semilla fija, ~6 %).')


# ---- 05
def b05(D):
    L, cs = D['L'], D['cs']
    meses = [CUR - i for i in range(13, -1, -1)]
    bot = ['E', 'EM', 'F', 'FM', 'EMSC']
    res = {}
    for m in meses:
        x = L[L.mes == m]
        act = x.idCliente.nunique()
        b = x[x.idProducto.isin(bot)]
        fc = cs[(cs.Fecha_Desde <= m.end_time) & (cs.Fecha_Baja.isna() | (cs.Fecha_Baja > m.start_time))].IdCliente
        res[m] = dict(
            p20=b[b.idProducto == 'E'].Cantidad.sum() / b.Cantidad.sum() * 100,
            p12=b[b.idProducto.isin(['EM', 'EMSC'])].Cantidad.sum() / b.Cantidad.sum() * 100,
            soda=x[x.soda].idCliente.nunique() / act * 100,
            fc=x[x.idCliente.isin(set(fc))].idCliente.nunique() / act * 100,
            lsoda=x[x.soda].litros.sum() / x.litros.sum() * 100)
    defs = [('p20', '% Bidón 20 L', 'de las unidades de bidón'), ('p12', '% Bidón 12 L', 'de las unidades de bidón'),
            ('soda', '% Clientes con soda', 'de los clientes activos'), ('fc', '% Clientes con F/C', 'de los clientes activos'),
            ('lsoda', '% Litros de soda', 'del volumen total')]
    cards = []
    for k, nm, sb in defs:
        v = [res[m][k] for m in meses]
        sp = lines([dict(n='', v=v, c=BLUE, w=2.4)], [lab(m) if i in (0, 6, 13) else '' for i, m in enumerate(meses)],
                   262, 120, ymin=min(v) * .96, ymax=max(v) * 1.04, vfmt=lambda x: fnum(x, 1), ml=34, mr=26, mt=8, mb=30, ticks=2)
        d1, d2 = delta(v[-1], v[-2], 'pp', True, 'vs mes ant.'), delta(v[-1], v[-13], 'pp', True, 'vs año ant.')
        cards.append(
            f'<div class="card kpi"><div class="kl">{nm}</div><div class="kv">{fpct(v[-1], 2)}</div>'
                     f'<div class="kd {d1[1]}">{d1[0]}</div><div class="kd {d2[1]}">{d2[0]}</div>'
                     f'<div class="ks" style="margin-bottom:6px">{sb}</div>{sp}</div>')
    kp = row('repeat(5,1fr)', *cards)
    x = L[L.mes == CUR]
    zs = []
    for z, g in x.groupby('zona'):
        zs.append((z, g[g.soda].idCliente.nunique() / g.idCliente.nunique() * 100,
                   g[g.idProducto.isin(['EM', 'EMSC'])].Cantidad.sum() / g[g.idProducto.isin(bot)].Cantidad.sum() * 100))
    avg_s, avg_12 = res[CUR]['soda'], res[CUR]['p12']
    zs_s = sorted(zs, key=lambda t: -t[1])
    r1 = [dict(l=z, v=s, c=BLUE if s >= avg_s else RED, t=fpct(s, 1)) for z, s, _ in zs_s]
    c1 = card('Penetración de soda por zona', hbars(r1, 700, label_w=110, val_w=70, vmax=max(t[1] for t in zs) * 1.1,
              ref=avg_s, ref_txt=f'promedio {fnum(avg_s, 1)} %'), 'Rojo: zonas por debajo del promedio de la compañía.')
    zs_t = sorted(zs, key=lambda t: -t[2])
    r2 = [dict(l=z, v=s, c=BLUE if s >= avg_12 else RED, t=fpct(s, 1)) for z, _, s in zs_t]
    c2 = card('Adopción del bidón de 12 L por zona', hbars(r2, 700, label_w=110, val_w=70, vmax=max(t[2] for t in zs) * 1.1,
              ref=avg_12, ref_txt=f'promedio {fnum(avg_12, 1)} %'), 'Rojo: zonas por debajo del promedio de la compañía.')
    bajos = [z for z, s, _ in zs_s if s < avg_s]
    d = res[CUR]['soda'] - res[CUR - 12]['soda']
    tit = (f'La soda llega al {fnum(res[CUR]["soda"], 1)} % de los clientes ({"+" if d >= 0 else ""}{fnum(d, 1)} pp vs año anterior); '
           f'{len(bajos)} zonas están por debajo del promedio')
    return dict(titulo='Cross-selling · migración al mix premium', titular=tit,
                chips=['Período de análisis: ' + str(CUR), 'Serie: 14 meses'],
                cuerpo=kp + row('1fr 1fr', c1, c2),
                nota='% 20 L y % 12 L sobre unidades de bidón; soda y F/C sobre clientes con pedido en el mes. Línea de cada tarjeta: 14 meses.')


# ---- 06
FERIADOS = [('2026-01-01', 'Año Nuevo', .12), ('2026-02-16', 'Carnaval (lun)', .38), ('2026-02-17', 'Carnaval (mar)', .34),
            ('2026-03-23', 'Feriado puente', .40), ('2026-03-24', 'Día de la Memoria', .30),
            ('2026-04-02', 'Día de Malvinas', .33), ('2026-04-03', 'Viernes Santo', .22), ('2026-05-01', 'Día del Trabajador', .28)]
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def b06(D):
    L = D['L']
    ds = L.groupby(['ruta', L.Fecha_Pedido.dt.normalize()]).pesos.sum().unstack(fill_value=0)
    fer = {pd.Timestamp(f[0]) for f in FERIADOS}
    zr = D['cli'].drop_duplicates('ruta').set_index('ruta').zona
    rng = np.random.default_rng(7)
    res = []
    for f, nm, base in FERIADOS:
        h = pd.Timestamp(f)
        prev = [h - pd.Timedelta(days=7 * k) for k in range(1, 9)]
        prev = [d for d in prev if d not in fer][:4]
        prom = ds.reindex(columns=prev, fill_value=0).mean(axis=1)
        fac = np.clip(base + rng.normal(0, .10, len(prom)), .03, .9)   # simulación: caída de venta en feriado
        df = pd.DataFrame({'prom': prom, 'vta': prom * fac})
        df['rec'] = df.prom - df.vta
        df['zona'] = zr.reindex(df.index)
        res.append((h, nm, df))
    h, nm, df = res[-1]
    P, V, R = df.prom.sum(), df.vta.sum(), df.rec.sum()
    kp = row('repeat(4,1fr)',
             kpi('Venta habitual del día', fmon(P), sub=f'promedio de 4 {DIAS[h.weekday()]}{"" if DIAS[h.weekday()].endswith("s") else "s"} previos'),
             kpi('Venta en el feriado', fmon(V), [(f'{fnum(V / P * 100, 0)} % de lo habitual', 'bad')]),
             kpi('A recuperar', fmon(R), [(f'{fnum(R / P * 100, 0)} % de la venta habitual', 'bad')]),
             kpi('Rutas con más del 80 % a recuperar', fnum(int(((df.rec / df.prom) > .8).sum())),
                 sub=f'de {len(df)} rutas'))
    r1 = [dict(l=f'{x[0].strftime("%d/%m")} · {x[1]}', v=x[2].rec.sum() / x[2].prom.sum() * 100,
               c=RED if x[0] == h else BLUE, t=fpct(x[2].rec.sum() / x[2].prom.sum() * 100, 0)) for x in res]
    c1 = card('% de venta a recuperar por feriado', hbars(r1, 550, label_w=200, val_w=60, vmax=100, bar_h=22, gap=10),
              'Rojo: el feriado seleccionado.')
    z = df.groupby('zona').agg(prom=('prom', 'sum'), rec=('rec', 'sum'))
    z['p'] = z.rec / z.prom * 100
    z = z.sort_values('rec', ascending=False)
    r2 = [dict(l=i, v=r.rec, c=BLUE, t=f'{fmon(r.rec)} · {r.p:.0f} %') for i, r in z.iterrows()]
    c2 = card(f'A recuperar por zona · {h.strftime("%d/%m/%Y")}', hbars(r2, 550, label_w=100, val_w=140, bar_h=22, gap=10),
              'Monto a recuperar y % sobre la venta habitual de la zona.')
    top = df.sort_values('rec', ascending=False).head(16)
    tr = [[i, r.zona, fmon(r.prom), fmon(r.vta), fmon(r.rec), heat(f'{r.rec / r.prom * 100:.0f} %', r.rec / r.prom, .2, 1, '214,69,69')]
          for i, r in top.iterrows()]
    c3 = card('Rutas con mayor monto a recuperar', table(['Ruta', 'Zona', 'Habitual', 'Feriado', 'A recuperar', '%'], tr,
              ['l', 'l', 'r', 'r', 'r', 'c']), 'Priorizar capacidad de reparto en estas rutas el día siguiente.')
    sig = (h + pd.Timedelta(days=1))
    tit = (f'El feriado del {h.strftime("%d/%m")} dejó {fmon(R)} por recuperar ({fnum(R / P * 100, 0)} % de la venta habitual): '
           f'el {DIAS[sig.weekday()]} {sig.strftime("%d/%m")} conviene reforzar las rutas de arriba')
    return dict(titulo='Venta a recuperar tras feriados', titular=tit,
                chips=[f'Feriado: {h.strftime("%d/%m/%Y")} ({DIAS[h.weekday()]})', 'Base: 4 semanas previas'],
                cuerpo=kp + row('590px 934px', f'<div style="display:flex;flex-direction:column;gap:16px">{c1}{c2}</div>', c3),
                nota='La venta del día feriado es una simulación (el dataset no modela cierres): venta habitual × factor aleatorio fijo por feriado y ruta.')


# ---- altas (7 y 8)
def altas(D):
    cli, ped, pp = D['cli'], D['ped'], D['pp']
    a = cli[(cli.FecAlt >= '2025-12-01')].copy()
    a['mes'] = a.FecAlt.dt.to_period('M')
    rng = np.random.default_rng(11)
    idx = (a.mes - pd.Period('2025-01', 'M')).apply(lambda x: x.n)
    a['canal'] = np.where(rng.random(len(a)) < 0.28 + 0.012 * idx, 'Digital', 'RTO')
    pr = ped.sort_values('Fecha_Pedido').drop_duplicates('idCliente')[['idCliente', 'idPedido']]
    sc = pp[pp.Precio == 0].idPedido.unique()
    pr['sc'] = pr.idPedido.isin(sc)
    a = a.merge(pr, left_on='NroCta', right_on='idCliente', how='left')
    r = rng.random(len(a))
    a['tipo'] = np.where(a.idPedido.isna(), 'Sin compra', np.where(a.sc, 'Sin cargo', np.where(r < .12, '2x1 / bonif.', 'Normal')))
    a['sem'] = ((a.FecAlt.dt.day - 1) // 7 + 1).clip(upper=5)
    return a


def b07(D):
    a = altas(D)
    M = pd.Period('2026-03', 'M')
    cur, prv = a[a.mes == M], a[a.mes == M - 1]
    dg = lambda x: (x.canal == 'Digital').mean() * 100
    sc = lambda x: (x.tipo == 'Sin compra').mean() * 100
    bj = lambda x: (x.estado == 'Baja').mean() * 100
    kp = row('repeat(5,1fr)',
             kpi('Altas del mes', fnum(len(cur)), [delta(len(cur), len(prv))]),
             kpi('% Digital', fpct(dg(cur)), [delta(dg(cur), dg(prv), 'pp', True)]),
             kpi('% Sin compra', fpct(sc(cur)), [delta(sc(cur), sc(prv), 'pp', False)], 'altas que aún no pidieron'),
             kpi('% Dadas de baja', fpct(bj(cur)), [delta(bj(cur), bj(prv), 'pp', False)]),
             kpi('% Con promo', fpct(((cur.tipo == 'Sin cargo') | (cur.tipo == '2x1 / bonif.')).mean() * 100),
                 [delta(((cur.tipo == 'Sin cargo') | (cur.tipo == '2x1 / bonif.')).mean() * 100,
                        ((prv.tipo == 'Sin cargo') | (prv.tipo == '2x1 / bonif.')).mean() * 100, 'pp', None)], 'sin cargo + 2x1'))
    w = cur.groupby(['sem', 'canal']).size().unstack(fill_value=0).reindex(range(1, 6), fill_value=0)
    cats = ['Sem 1 (1–7)', 'Sem 2 (8–14)', 'Sem 3 (15–21)', 'Sem 4 (22–28)', 'Sem 5 (29–31)']
    tot = (w.get('Digital', 0) + w.get('RTO', 0)).tolist()
    mx = max(tot) * 1.12
    o = [f'<line x1="10" x2="740" y1="210" y2="210" stroke="{GREY}"/>']
    bw = 730 / 5 * .55
    for i in range(5):
        x = 10 + 730 / 5 * (i + .5) - bw / 2
        d, r_ = w.get('Digital', pd.Series([0] * 5)).iloc[i], w.get('RTO', pd.Series([0] * 5)).iloc[i]
        h1, h2 = 180 * d / mx, 180 * r_ / mx
        o.append(f'<rect x="{x:.1f}" y="{210 - h1:.1f}" width="{bw:.1f}" height="{h1:.1f}" fill="{BLUE}"/>')
        o.append(f'<rect x="{x:.1f}" y="{210 - h1 - h2:.1f}" width="{bw:.1f}" height="{h2:.1f}" fill="{LBLUE}"/>')
        o.append(T(x + bw / 2, 210 - h1 / 2 + 4, str(int(d)), 12, '#fff', 'middle', '600'))
        o.append(T(x + bw / 2, 210 - h1 - h2 / 2 + 4, str(int(r_)), 12, INK, 'middle', '600'))
        o.append(T(x + bw / 2, 210 - h1 - h2 - 6, str(int(d + r_)), 12.5, INK, 'middle', '700'))
        o.append(T(x + bw / 2, 230, cats[i], 11.5, MUTE, 'middle'))
    c1 = card('Altas por semana y canal', legend([('Digital', BLUE), ('RTO (reparto)', LBLUE)]) + svg(750, 240, ''.join(o)),
              'Semana del mes en que se dio de alta la cuenta.')
    tp = cur.tipo.value_counts()
    r2 = [dict(l=k, v=tp.get(k, 0), c=RED if k == 'Sin compra' else BLUE, t=f'{tp.get(k, 0)} · {tp.get(k, 0) / len(cur) * 100:.0f} %')
          for k in ['Normal', 'Sin cargo', '2x1 / bonif.', 'Sin compra']]
    c2 = card('Tipo de alta', hbars(r2, 698, label_w=120, val_w=110, bar_h=40, gap=26), 'Según la primera compra del cliente.')
    zz = cur.groupby('zona').size().sort_values(ascending=False)
    zs = cur.groupby(['zona', 'sem']).size().unstack(fill_value=0).reindex(columns=range(1, 6), fill_value=0)
    mxh = zs.values.max()
    tr = []
    for z in zz.index:
        dgp = (cur[cur.zona == z].canal == 'Digital').mean() * 100
        tr.append([z] + [heat(str(int(zs.loc[z, s])), zs.loc[z, s], 0, mxh) for s in range(1, 6)] +
                  [f'<b>{zz[z]}</b>', fpct(dgp, 0)])
    c3 = card('Altas por zona y semana', table(['Zona', 'S1', 'S2', 'S3', 'S4', 'S5', 'Total', '% Digital'], tr,
              ['l'] + ['c'] * 5 + ['r', 'r']), 'Más oscuro = más altas.')
    tit = (f'{len(cur)} altas en {MESES[M.month]} ({"+" if len(cur) >= len(prv) else ""}{fnum((len(cur) / len(prv) - 1) * 100, 0)} % vs {MESES[M.month - 1]}): '
           f'el canal digital pesa {fnum(dg(cur), 0)} % y {fnum(sc(cur), 0)} % aún no compró')
    return dict(titulo='Altas de clientes · RTO vs Digital', titular=tit,
                chips=['Mes de alta: ' + lab(M), 'Canal: Digital + RTO', 'Estado: Activo + Baja'],
                cuerpo=kp + row('790px 738px', c1, c2) + c3,
                nota='Canal de alta (Digital/RTO) y bonificación 2x1 son simulados con semilla fija; el resto sale de los CSV sintéticos.')


def b08(D):
    a = altas(D)
    L = D['L']
    a = a[(a.mes <= pd.Period('2026-03', 'M')) & (a.estado == 'Activo')]
    j = L[['idCliente', 'Fecha_Pedido', 'litros']].merge(a[['NroCta', 'FecAlt', 'mes', 'canal', 'tipo']], left_on='idCliente', right_on='NroCta')
    j['w'] = (j.Fecha_Pedido - j.FecAlt).dt.days // 7
    j = j[(j.w >= 0) & (j.w < 6)]
    meses = sorted(a.mes.unique())
    wk = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6']

    def curva(sub_a, sub_j):
        n = max(1, len(sub_a))
        s = sub_j.groupby('w').litros.sum().reindex(range(6), fill_value=0) / n
        return s.cumsum().tolist()
    cols = [GREY, '#6fa8d0', BLUE, PET]
    ser = []
    for m, c in zip(meses, cols):
        sa = a[a.mes == m]
        ser.append(dict(n=lab(m), v=curva(sa, j[j.mes == m]), c=c, w=3, lab=True))
    c1 = card('Litros acumulados por cliente según semanas desde el alta', lines(ser, wk, 720, 426, ymin=0, vfmt=lambda x: fnum(x, 0)),
              'Cada línea es una cohorte de altas. Cuanto más arriba, mejor consumo.')
    cn = {c: (a[a.canal == c], j[j.canal == c]) for c in ['Digital', 'RTO']}
    lit = {c: curva(*cn[c])[-1] for c in cn}
    buy = lambda s: s[s.tipo != 'Sin compra']
    comp = {c: j[j.canal == c].idCliente.nunique() / max(1, len(cn[c][0])) * 100 for c in cn}
    kp = row('repeat(5,1fr)',
             kpi('Altas analizadas', fnum(len(a)), sub=f'cohortes {lab(meses[0])} a {lab(meses[-1])}'),
             kpi('Litros por alta (6 sem)', fnum(curva(a, j)[-1], 1) + ' L'),
             kpi('Compraron al menos 1 vez', fpct(j.idCliente.nunique() / len(a) * 100, 0), [(f'{fnum(100 - j.idCliente.nunique() / len(a) * 100, 0)} % sin consumo', 'bad')]),
             kpi('Digital · L por alta', fnum(lit['Digital'], 1) + ' L', [delta(lit['Digital'], lit['RTO'], 'pct', True, 'vs RTO')]),
             kpi('RTO · L por alta', fnum(lit['RTO'], 1) + ' L'))
    rr = []
    for m in meses:
        sa = a[a.mes == m]
        sj = j[j.mes == m]
        s = sj.groupby('w').litros.sum().reindex(range(6), fill_value=0) / max(1, len(sa))
        v = s.tolist()
        mxx = max(max(v), .01)
        rr.append([lab(m), fnum(len(sa))] + [heat(fnum(x, 1), x, 0, mxx) for x in v] +
                  [f'<b>{fnum(sum(v), 1)}</b>', fpct(sj.idCliente.nunique() / max(1, len(sa)) * 100, 0)])
    c2 = card('Litros por cliente y semana (cohorte × semana)', table(['Cohorte', 'Altas'] + wk + ['Total', '% compró'], rr,
              ['l', 'r'] + ['c'] * 6 + ['r', 'r']), 'Litros semanales por cliente dado de alta.')
    tp = []
    for t in ['Normal', 'Sin cargo', '2x1 / bonif.']:
        sa = a[a.tipo == t]
        if len(sa):
            tp.append(dict(l=t, v=curva(sa, j[j.tipo == t])[-1], c=RED if t == 'Sin compra' else BLUE))
    c3 = card('Litros por alta en 6 semanas, según tipo de alta', hbars(tp, 720, label_w=120, val_w=90, bar_h=24, gap=12,
              vfmt=lambda v: fnum(v, 1) + ' L'), 'Las altas sin compra consumen 0 L por definición y no se grafican.')
    d = (lit['Digital'] / lit['RTO'] - 1) * 100
    tit = (f'En 6 semanas cada alta consume {fnum(curva(a, j)[-1], 0)} L en promedio; el canal Digital consume '
           f'{fnum(abs(d), 0)} % {"más" if d >= 0 else "menos"} que RTO y {fnum(100 - j.idCliente.nunique() / len(a) * 100, 0)} % de las altas no compró')
    return dict(titulo='Consumo de litros por cohorte de altas', titular=tit,
                chips=['Cohortes: ' + lab(meses[0]) + ' a ' + lab(meses[-1]), 'Ventana: 6 semanas', 'Estado: Activo'],
                cuerpo=kp + row('760px 768px', c1, f'<div style="display:flex;flex-direction:column;gap:16px">{c2}{c3}</div>'),
                nota='Semana 1 = primeros 7 días desde el alta. Canal y tipo de alta simulados con semilla fija.')


# ---- 09 / 10
def var(a, b):
    return (a / b - 1) * 100 if b else np.nan


def b09(D):
    L = D['L']
    x = {k: L[L.mes == m] for k, m in [('c', CUR), ('p', PREV), ('y', YAGO)]}
    tl = {k: v.litros.sum() for k, v in x.items()}
    cc = x['c'][x['c'].Precio > 0].litros.sum()
    prom3 = np.mean([L[L.mes == CUR - i].litros.sum() for i in (1, 2, 3)])
    meta = prom3 * 1.03
    kp = row('repeat(5,1fr)',
             kpi('Litros totales', fnum(tl['c'] / 1000, 0) + ' mil L'),
             kpi('Litros con cargo', fnum(cc / 1000, 0) + ' mil L', sub=f'{fnum(cc / tl["c"] * 100, 1)} % del total'),
             kpi('Vs mes anterior', fpct(var(tl['c'], tl['p']), 1), [delta(tl['c'], tl['p'], 'pct', True)]),
             kpi('Vs año anterior', fpct(var(tl['c'], tl['y']), 1), [delta(tl['c'], tl['y'], 'pct', True, 'vs ' + lab(YAGO))]),
             kpi('Vs meta del mes', fpct(var(tl['c'], meta), 1), [delta(tl['c'], meta, 'pct', True, 'meta = prom. 3 m × 1,03')]))
    # zona
    zt = {k: v.groupby('zona').litros.sum() for k, v in x.items()}
    zs = sorted(zt['c'].index, key=lambda z: -zt['c'][z])
    rows = []
    for z in zs:
        cell = lambda a, b: (lambda v: f'<span class="{"good" if v >= 0 else "bad"}" style="font-weight:650">{"+" if v >= 0 else ""}{fnum(v, 1)} %</span>')(var(a, b))
        rows.append([z, fnum(zt['c'][z]), cell(zt['c'][z], zt['p'].get(z)), cell(zt['c'][z], zt['y'].get(z)),
                     cell(zt['c'][z], prom_z(L, z) * 1.03)])
    c1 = card('Litros por zona', table(['Zona', 'Litros ' + lab(CUR), 'Vs mes ant.', 'Vs año ant.', 'Vs meta'], rows),
              'Azul = a favor, rojo = en contra.')
    # familias
    fam = ['Botellones', 'Gastro', 'Resto', 'Sodas']
    fr = [dict(l=f, v=var(x['c'][x['c'].fam == f].litros.sum(), x['p'][x['p'].fam == f].litros.sum())) for f in fam]
    fy = [dict(l=f, v=var(x['c'][x['c'].fam == f].litros.sum(), x['y'][x['y'].fam == f].litros.sum())) for f in fam]
    c2 = card('Variación por familia · vs mes anterior', divbars(fr, 560, label_w=110, vmax=max(abs(r['v']) for r in fr + fy) * 1.0), '')
    c3 = card('Variación por familia · vs año anterior', divbars(fy, 560, label_w=110, vmax=max(abs(r['v']) for r in fr + fy) * 1.0), '')
    # rutas
    rt = {k: v.groupby('ruta').litros.sum() for k, v in x.items()}
    rv = pd.DataFrame({'c': rt['c'], 'p': rt['p']}).dropna()
    rv = rv[rv.c > rv.c.quantile(.2)]
    rv['v'] = (rv.c / rv.p - 1) * 100
    rv = rv.sort_values('v')
    sel = pd.concat([rv.head(6), rv.tail(6)])
    c4 = card('Rutas: las que más caen y las que más crecen (vs mes ant.)',
              divbars([dict(l=i, v=r.v) for i, r in sel.iterrows()], 1500, label_w=70, bar_h=15, gap=6, vmax=rv.v.abs().max()), '')
    tit = (f'Se despacharon {fnum(tl["c"] / 1000, 0)} mil litros en {MESES[CUR.month]}: '
           f'{fnum(var(tl["c"], tl["p"]), 1)} % vs mes anterior y {"+" if var(tl["c"], tl["y"]) >= 0 else ""}{fnum(var(tl["c"], tl["y"]), 1)} % vs año anterior')
    return dict(titulo='Estadísticas de repartos · litros', titular=tit,
                chips=[f'Mes actual: {lab(CUR)}', f'Mes ant.: {lab(PREV)}', f'Año ant.: {lab(YAGO)}', 'Familia: todas'],
                cuerpo=kp + row('820px 708px', c1, f'<div style="display:flex;flex-direction:column;gap:16px">{c2}{c3}</div>') + row('1fr', c4),
                nota='Meta ficticia = promedio de los 3 meses previos × 1,03. Familias: Botellones (hogar), Gastro, Resto (empresas e instituciones), Sodas.')


def prom_z(L, z):
    return np.mean([L[(L.mes == CUR - i) & (L.zona == z)].litros.sum() for i in (1, 2, 3)])


def b10(D):
    L = D['L']
    fam = [('Botellones', PET), ('Gastro', BLUE), ('Resto', GREY), ('Sodas', LBLUE)]
    pf = lambda m, f: L[(L.mes == m) & (L.fam == f)].pesos.sum()
    tot = lambda m: L[L.mes == m].pesos.sum()
    kp = row('repeat(4,1fr)',
             kpi('Venta total', fmon(tot(CUR)), [delta(tot(CUR), tot(PREV)), delta(tot(CUR), tot(YAGO), 'pct', True, 'vs año ant.')]),
             *[kpi(f, fmon(pf(CUR, f)), [delta(pf(CUR, f), pf(PREV, f)), delta(pf(CUR, f), pf(YAGO, f), 'pct', True, 'vs año ant.')],
                   f'{fnum(pf(CUR, f) / tot(CUR) * 100, 1)} % del total') for f, _ in fam[:3]])
    # barras comparativas por familia
    w, h = 880, 300
    o = [f'<line x1="10" x2="{w}" y1="{h - 40}" y2="{h - 40}" stroke="{GREY}"/>']
    mx = max(pf(m, f) for m in (YAGO, PREV, CUR) for f, _ in fam) * 1.15
    gw = (w - 10) / 4
    bw = gw * .22
    for i, (f, c) in enumerate(fam):
        for k, (m, col) in enumerate([(YAGO, '#c3cad6'), (PREV, LBLUE), (CUR, BLUE)]):
            v = pf(m, f)
            hh = (h - 70) * v / mx
            x = 10 + gw * i + gw * .5 - bw * 1.6 + k * bw * 1.1
            o.append(f'<rect x="{x:.1f}" y="{h - 40 - hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="2" fill="{col}"/>')
            o.append(T(x + bw / 2, h - 46 - hh, fnum(v / 1e6, 0) + ' M' if v >= 1e6 else fnum(v / 1e3, 0) + ' mil', 11, INK, 'middle', '600'))
        o.append(T(10 + gw * i + gw / 2, h - 16, f, 13, INK, 'middle', '600'))
    c1 = card('Venta por familia: año anterior, mes anterior y mes actual',
              legend([(lab(YAGO), '#c3cad6'), (lab(PREV), LBLUE), (lab(CUR), BLUE)]) + svg(w, h, ''.join(o)),
              'Pesos a precios constantes del dataset.')
    meses = [CUR - i for i in range(12, -1, -1)]
    ser = [dict(n=f, v=[pf(m, f) / 1e6 for m in meses], c=c, w=2.8, lab=True) for f, c in fam]
    c2 = card('Evolución mensual (millones de $)', lines(ser, [lab(m) if i % 3 == 0 else '' for i, m in enumerate(meses)], 560, 332,
              ymin=0, vfmt=lambda v: fnum(v, 0), mr=120), 'Últimos 13 meses.')
    # contribución a la variación
    dv = [dict(l=f, v=pf(CUR, f) - pf(PREV, f)) for f, _ in fam]
    dy = [dict(l=f, v=pf(CUR, f) - pf(YAGO, f)) for f, _ in fam]
    mm = max(abs(r['v']) for r in dv + dy)
    fm = lambda v: ('+' if v >= 0 else '-') + fmon(abs(v))
    c3 = card('Qué familia explica la variación vs mes anterior', divbars(dv, 720, label_w=110, vmax=mm, vfmt=fm), '')
    c4 = card('Qué familia explica la variación vs año anterior', divbars(dy, 720, label_w=110, vmax=mm, vfmt=fm), '')
    top = max(dv, key=lambda r: abs(r['v']))
    tit = (f'Venta de {fmon(tot(CUR))} en {MESES[CUR.month]}: {fnum(var(tot(CUR), tot(YAGO)), 1)} % más que hace un año; '
           f'{top["l"]} explica la mayor parte del movimiento mensual ({fm(top["v"])})')
    return dict(titulo='Estadísticas de repartos · pesos por familia', titular=tit,
                chips=[f'Mes actual: {lab(CUR)}', f'Mes ant.: {lab(PREV)}', f'Año ant.: {lab(YAGO)}'],
                cuerpo=kp + row('928px 600px', c1, c2) + row('1fr 1fr', c3, c4),
                nota='Importes en pesos ficticios a precios constantes; sin ajuste por inflación. Familias definidas por tipo de cliente y producto.')


# ---- 11
BARRIOS_FIC = {'NORDELTA': 'Lomas del Sauce', 'BAHIA GRANDE': 'Costa Serena', 'BAHIA SAN MARCO': 'Bahía Azul',
               'EL TRIGAL': 'Los Aromos', 'LOS LAGOS': 'Lagos del Sur', 'PILAR DEL ESTE': 'Altos del Río',
               'CAMPOS DE ECHEVERRIA': 'Campos Verdes', 'SAN AGUSTIN': 'El Mirador', 'SANTA CATALINA': 'Cerro Claro',
               'BARRIO ABRIL': 'Arenales', 'ALTOS DE GOLF': 'Bosques del Lago', 'LOS CARDALES': 'Alto Pinar',
               'AYRES DEL PILAR': 'Vista Dorada'}


def b11(D):
    cli, L = D['cli'], D['L']
    b = cli[(cli.estado == 'Activo')].copy()
    b['barrio'] = b.Direcc.str.rsplit(', ', n=1).str[-1].map(BARRIOS_FIC)
    b = b[b.barrio.notna()]
    meses = [CUR - i for i in range(5, -1, -1)]
    Lb = L[L.idCliente.isin(set(b.NroCta))]

    def est(m, sub=None):
        pop = b if sub is None else b[b.barrio == sub]
        pop = pop[pop.FecAlt <= m.end_time]
        x = Lb[(Lb.mes == m) & Lb.idCliente.isin(set(pop.NroCta))]
        bo = set(x[~x.soda].idCliente)
        so = set(x[x.soda].idCliente)
        n = len(pop)
        both = len(bo & so)
        return dict(n=n, bot=len(bo - so) / n * 100, soda=len(so - bo) / n * 100, both=both / n * 100,
                    none=(n - len(bo | so)) / n * 100, soda_any=len(so) / n * 100)
    E = {m: est(m) for m in meses}
    c, p = E[CUR], E[PREV]
    kp = row('repeat(4,1fr)',
             kpi('Clientes en barrios', fnum(c['n']), [delta(c['n'], p['n'])]),
             kpi('% con soda', fpct(c['soda_any']), [delta(c['soda_any'], p['soda_any'], 'pp', True)], 'compran soda y botellón: el cliente más valioso'),
             kpi('% solo botellón', fpct(c['bot']), [delta(c['bot'], p['bot'], 'pp', None)], 'oportunidad de venta cruzada'),
             kpi('% sin compras', fpct(c['none']), [delta(c['none'], p['none'], 'pp', False)]))
    cols = [('Solo botellón', LBLUE, 'bot'), ('Soda y botellón', BLUE, 'both'), ('Sin compras', RED, 'none')]
    ser = [(n.strip(), col, [E[m][k] for m in meses]) for n, col, k in cols]
    c1 = card('Composición de la base por mes', legend([(n.strip(), col) for n, col, _ in cols]) +
              stack_v([MESES[m.month].capitalize() for m in meses], ser, 640, 486, minlab=5), 'Porcentaje de clientes de barrios cerrados.')
    rows = []
    zs = {}
    for k in sorted(b.barrio.unique()):
        e = est(CUR, k)
        zs[k] = e
    for k, e in sorted(zs.items(), key=lambda t: -t[1]['soda_any']):
        rows.append([k, fnum(e['n']), heat(fpct(e['soda_any'], 0), e['soda_any'], 0, 25),
                     heat(fpct(e['none'], 0), e['none'], 40, 100, '214,69,69')])
    c2 = card('Por barrio · ' + MESES[CUR.month], table(['Barrio', 'Clientes', '% con soda', '% sin compras'], rows, ['l', 'r', 'c', 'c']),
              'Ordenado por penetración de soda.')
    tit = (f'Solo {fnum(c["soda_any"], 0)} % de los clientes de barrios cerrados compra soda; '
           f'{fnum(c["none"], 0)} % no compró nada en {MESES[CUR.month]} ({"+" if c["none"] >= p["none"] else ""}{fnum(c["none"] - p["none"], 1)} pp vs mes anterior)')
    return dict(titulo='Barrios cerrados · promoción de soda', titular=tit,
                chips=['Segmento: barrios cerrados', 'Últimos 6 meses'],
                cuerpo=kp + row('690px 838px', c1, c2),
                nota='Nombres de barrios inventados (mapeo ficticio de las direcciones sintéticas). Categorías excluyentes por cliente y mes. No se muestra "solo soda": en el dataset todo cliente que compra soda también compra botellón (0 %).')


TABLEROS = [('01_cobranzas_kpis', b01), ('02_cobranzas_dias_calle', b02), ('03_cobranzas_costo_vendedor', b03),
            ('04_frio_calor_sin_consumo', b04), ('05_crosselling', b05), ('06_feriados_venta_recuperar', b06),
            ('07_altas_rto_digital', b07), ('08_altas_consumo_litros', b08), ('09_estadisticas_repartos_litros', b09),
            ('10_estadisticas_repartos_pesos', b10), ('11_barrios_promo_soda', b11)]


def capturar(nombres):
    from playwright.sync_api import sync_playwright
    OUT_PNG.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': 1600, 'height': 400})
        for n in nombres:
            pg.goto((OUT_HTML / f'{n}.html').as_uri())
            pg.wait_for_timeout(150)
            h = pg.evaluate('Math.ceil(document.body.getBoundingClientRect().height)') + 24   # alto real + margen
            pg.set_viewport_size({'width': 1600, 'height': h})
            pg.screenshot(path=str(OUT_PNG / f'{n}.png'), clip={'x': 0, 'y': 0, 'width': 1600, 'height': h})
            print('  png', n)
        br.close()


def main():
    OUT_HTML.mkdir(parents=True, exist_ok=True)
    print('Leyendo CSV…')
    D = cargar()
    hechos = []
    for nombre, fn in TABLEROS:
        r = fn(D)
        (OUT_HTML / f'{nombre}.html').write_text(
            pagina(r['titulo'], r['titular'], r['chips'], r['cuerpo'], r.get('nota', '')), encoding='utf-8')
        print('  html', nombre, '·', r['titular'])
        hechos.append(nombre)
    if '--solo-html' not in sys.argv:
        capturar(hechos)


if __name__ == '__main__':
    main()
