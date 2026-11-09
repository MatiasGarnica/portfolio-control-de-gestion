"""Arma 03_tableros/voz_primera_linea.html leyendo los CSV (via analizar.py).
El HTML queda autocontenido: datos embebidos, sin librerias externas.

Uso:  python armar_tablero.py
"""
import json
from pathlib import Path

from analizar import BASE, CAT_COMP, CAT_ECON, SEM_RECIENTE, calcular


def datos_para_tablero(d):
    rutas = []
    for ru in d["rutas"]:
        rec = d["cnt"].loc[list(SEM_RECIENTE)].xs(ru, level="ruta").groupby("categoria").sum()
        comp, econ = int(rec.get(CAT_COMP, 0)), int(rec.get(CAT_ECON, 0))
        serie = d["ventas_sem"][ru]
        rutas.append({
            "nombre": ru, "corta": ru.split(" - ")[0], "zona": ru.split(" - ")[1],
            "var": round(float(d["por_ruta"].loc[ru, "var"]) * 100, 1),
            "local": round(float(d["por_ruta"].loc[ru, "local"]) * 100, 1),
            "comp": comp, "econ": econ, "otros": int(rec.sum()) - comp - econ,
            "ventas_idx": [round(float(x) / float(serie.iloc[:5].mean()) * 100, 1) for x in serie],
        })
    rank = [{"motivo": c, "n": int(x["reportes_recientes"]), "veces": round(float(x["veces"]), 1),
             "tipo": x["tipo"]} for c, x in d["rank"].iterrows()]
    rc = d["ruta_comp"]
    alerta = {
        "ruta": rc, "primera": d["primera"],
        "comp_sem": [int(d["sem_comp"][rc].loc[s]) for s in d["semanas"]],
        "ventas_idx": next(x["ventas_idx"] for x in rutas if x["nombre"] == rc),
        "var": next(x["var"] for x in rutas if x["nombre"] == rc),
        "local": next(x["local"] for x in rutas if x["nombre"] == rc),
        "comp_ref": round(float(d["ref"][(rc, CAT_COMP)]), 1),
        "comp_rec": round(float(d["rec"][(rc, CAT_COMP)]), 1),
    }
    return {"titular": d["titular"], "semanas": d["semanas"], "rutas": rutas, "ranking": rank,
            "alerta": alerta, "econ_sem": [int(d["econ_sem"].loc[s]) for s in d["semanas"]],
            "mercado_var": round(float(d["por_ruta"]["mercado"].iloc[0]) * 100, 1),
            "total_var": round(float(d["total_var"]) * 100, 1)}


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voz de primera línea contra ventas</title>
<style>
:root{--page:#e9eef4;--card:#fff;--ink:#14202e;--ink2:#4a5a6c;--muted:#7a8898;--line:#dde4ec;
--comp:#d03b3b;--econ:#d98a1f;--otros:#9fb3c8;--blue:#2a78d6;--good:#1f7a3d}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}
header h1{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:4px 0 10px;font-weight:600}
.card{background:var(--card);border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(20,32,46,.08)}
.card h2{font-size:16px;margin:0 0 2px}
.sub{color:var(--ink2);font-size:13px;margin:0 0 12px}
.titular{font-size:19px;line-height:1.35;font-weight:600;margin:0}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.chip{font-size:12px;padding:4px 10px;border-radius:99px;background:#eef3f8;color:var(--ink2)}
.alerta{border-left:5px solid var(--comp)}
.alerta h2{color:var(--comp)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin-bottom:8px}
.leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.row{display:grid;grid-template-columns:110px 64px 1fr;gap:10px;align-items:center;padding:7px 0;border-top:1px solid var(--line)}
.row>div,.rk>div{min-width:0}.row .n{font-size:13px;font-weight:600}.row .n small{display:block;font-weight:400;color:var(--muted);font-size:11px}
.var{font-weight:700;font-size:14px;text-align:right}
.neg{color:var(--comp)}.mid{color:var(--econ)}
.bar{display:flex;height:16px;border-radius:4px;overflow:hidden;background:#f1f4f8}
.bar span{display:block;height:100%}
.row.hot{background:#fdf1f1;margin:0 -8px;padding:7px 8px;border-radius:6px}
.rk{display:grid;grid-template-columns:1fr 46px;gap:4px 10px;align-items:center;padding:5px 0;font-size:13px}
.rk .t{height:10px;background:#f1f4f8;border-radius:3px;grid-column:1/2}
.rk .t b{display:block;height:100%;border-radius:3px}
.rk .v{text-align:right;font-weight:600}
.tag{font-size:11px;padding:1px 7px;border-radius:99px;margin-left:6px;color:#fff;vertical-align:1px}
svg{width:100%;height:auto;display:block}
svg text{fill:var(--ink2);font-size:11px}
.foot{font-size:12px;color:var(--muted);text-align:center;margin:18px 0 8px}
@media(max-width:640px){.grid2{grid-template-columns:1fr}.row{grid-template-columns:86px 56px 1fr}.titular{font-size:17px}main{padding:12px}}
</style>
</head>
<body>
<main>
<header><h1>Voz de primera línea contra ventas · semanas 1 a 12 · datos ficticios</h1></header>

<section class="card">
  <p class="titular" id="titular"></p>
  <div class="chips" id="chips"></div>
</section>

<section class="card alerta" id="alerta"></section>

<section class="card">
  <h2>Ventas por ruta contra reportes</h2>
  <p class="sub">Variación de bidones (últimas 4 semanas contra las semanas 1 a 5) y reportes de las últimas 4 semanas por motivo.</p>
  <div class="leg"><span><i style="background:var(--comp)"></i>Competencia</span><span><i style="background:var(--econ)"></i>Situación económica</span><span><i style="background:var(--otros)"></i>Otros motivos</span></div>
  <div id="rutas"></div>
</section>

<div class="grid2">
  <section class="card">
    <h2>Ranking de motivos</h2>
    <p class="sub">Reportes de las últimas 4 semanas. "x" = veces contra el ritmo de las semanas 1 a 5.</p>
    <div id="rank"></div>
  </section>
  <section class="card">
    <h2>Situación económica: efecto mercado</h2>
    <p class="sub">Reportes por semana, las 8 rutas juntas. Suben antes de que caigan las ventas.</p>
    <div id="econ"></div>
  </section>
</div>
<p class="foot">Señal de primera línea, no encuesta estadística. Se cruza con ventas para formar la hipótesis; la confirman las visitas.</p>
</main>
<script>
const D = __DATOS__;
const $ = id => document.getElementById(id);
const f1 = x => String(x).replace(".", ",");
const sg = x => (x > 0 ? "+" : "") + f1(x);
$("titular").textContent = D.titular;
$("chips").innerHTML =
  `<span class="chip">Total: ${sg(D.total_var)} %</span>` +
  `<span class="chip">Mercado (ruta mediana): ${sg(D.mercado_var)} %</span>` +
  `<span class="chip">${D.alerta.ruta}: ${sg(D.alerta.var)} %</span>`;

// ---- alerta de Competencia ----
const A = D.alerta, W = D.semanas.length;
function chartAlerta() {
  const w = 460, l = 34, r = 34, pw = w - l - r, bw = pw / W, cx = i => l + i * bw + bw / 2;
  const grid = (x1, x2, yy, lab, strong) => `<line x1="${x1}" x2="${x2}" y1="${yy}" y2="${yy}" stroke="${strong ? "var(--muted)" : "var(--line)"}" stroke-width="${strong ? 1 : .75}"${strong ? ' stroke-dasharray="3 3"' : ""}/>` +
    `<text x="${x1 - 5}" y="${yy + 4}" text-anchor="end">${lab}</text>`;
  const marca = (hh, t, b) => `<line x1="${l + (A.primera - 1) * bw}" x2="${l + (A.primera - 1) * bw}" y1="${t}" y2="${b}" stroke="var(--comp)" stroke-width="1" stroke-dasharray="2 3" opacity=".7"/>`;
  // arriba: ventas
  const h1 = 130, t1 = 10, b1 = 14, ph1 = h1 - t1 - b1, vmin = 70, vmax = 105, y = v => t1 + ph1 - (v - vmin) / (vmax - vmin) * ph1;
  let s1 = `<svg viewBox="0 0 ${w} ${h1}" role="img" aria-label="Ventas de la ruta, base 100 en las semanas 1 a 5">`;
  [70, 85].forEach(v => s1 += grid(l, w - r, y(v), v, false));
  s1 += grid(l, w - r, y(100), 100, true) + marca(h1, t1, t1 + ph1);
  const pts = A.ventas_idx.map((v, i) => `${cx(i)},${y(v)}`).join(" ");
  s1 += `<polyline points="${pts}" fill="none" stroke="var(--blue)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`;
  const last = A.ventas_idx[W - 1];
  s1 += `<circle cx="${cx(W - 1)}" cy="${y(last)}" r="3" fill="var(--blue)"/><text x="${cx(W - 1) + 7}" y="${y(last) + 4}" style="fill:var(--blue);font-weight:700">${Math.round(last)}</text>`;
  for (let i = 0; i < W; i++) s1 += `<text x="${cx(i)}" y="${h1 - 2}" text-anchor="middle" style="fill:var(--muted)">${i + 1}</text>`;
  s1 += `</svg>`;
  // abajo: reportes
  const h2 = 130, t2 = 22, b2 = 18, ph2 = h2 - t2 - b2, maxC = Math.max(...A.comp_sem, 4), top = Math.ceil(maxC / 3) * 3, yb = v => t2 + ph2 - v / top * ph2;
  let s2 = `<svg viewBox="0 0 ${w} ${h2}" role="img" aria-label="Reportes de competencia por semana">`;
  [0, top / 3, 2 * top / 3, top].forEach(v => s2 += grid(l, w - r, yb(v), v, false));
  const pk = A.comp_sem.indexOf(Math.max(...A.comp_sem));
  for (let i = 0; i < W; i++) {
    const bh = A.comp_sem[i] / top * ph2, x = l + i * bw;
    s2 += `<rect x="${x + 4}" y="${t2 + ph2 - bh}" width="${bw - 8}" height="${bh}" rx="1.5" fill="var(--comp)" opacity="${i + 1 >= A.primera ? 1 : .35}"/>`;
    if (i === pk || i === W - 1) s2 += `<text x="${cx(i)}" y="${t2 + ph2 - bh - 3}" text-anchor="middle" style="fill:var(--comp);font-weight:700">${A.comp_sem[i]}</text>`;
    s2 += `<text x="${cx(i)}" y="${h2 - 3}" text-anchor="middle" style="fill:var(--muted)">${i + 1}</text>`;
  }
  s2 += marca(h2, 12, t2 + ph2) + `<text x="${l + (A.primera - 1) * bw + 4}" y="10" style="fill:var(--comp)">semana ${A.primera}: aparece la competencia</text></svg>`;
  const tt = t => `<h3 style="font-size:13px;margin:10px 0 2px;color:var(--ink2)">${t}</h3>`;
  return `<div style="max-width:620px">` + tt("Ventas de la Ruta 5 (base 100 = semanas 1 a 5)") + s1 + tt("Reportes de competencia por semana") + s2 + `<div style="font-size:11px;color:var(--muted);text-align:center">Semana</div></div>`;
}
$("alerta").innerHTML = `
  <h2>Alerta: ${A.ruta}, competencia nueva</h2>
  <p class="sub">Los reportes de "Competencia nueva en la zona" pasaron de ${f1(A.comp_ref)} a ${f1(A.comp_rec)} por semana desde la semana ${A.primera}.
  Es la única ruta donde pasa: la venta cae ${f1(Math.abs(A.var))} %, ${f1(Math.abs(A.local))} puntos más que el mercado. Es gestión local.</p>
  ${chartAlerta()}`;

// ---- ventas por ruta contra reportes ----
const maxTot = Math.max(...D.rutas.map(r => r.comp + r.econ + r.otros));
$("rutas").innerHTML = D.rutas.map(r => {
  const t = r.comp + r.econ + r.otros, k = 100 / maxTot;
  const cls = r.local < -5 ? "neg" : (r.var < -2 ? "mid" : "");
  return `<div class="row ${r.local < -5 ? "hot" : ""}">
    <div class="n">${r.corta}<small>${r.zona}</small></div>
    <div class="var ${cls}">${sg(r.var)} %</div>
    <div><div class="bar" title="${r.comp} competencia, ${r.econ} situación económica, ${r.otros} otros">
      <span style="width:${r.comp * k}%;background:var(--comp)"></span>
      <span style="width:${r.econ * k}%;background:var(--econ)"></span>
      <span style="width:${r.otros * k}%;background:var(--otros)"></span></div>
      <small style="color:var(--muted);font-size:11px">${t} reportes: ${r.comp} compet. · ${r.econ} econ. · ${r.otros} otros</small></div>
  </div>`;
}).join("");

// ---- ranking ----
const colorTipo = {mercado: "var(--econ)", local: "var(--comp)", "sin señal": "var(--otros)"};
const maxN = Math.max(...D.ranking.map(x => x.n));
$("rank").innerHTML = D.ranking.map(x => `
  <div class="rk"><div>${x.motivo}${x.tipo !== "sin señal" ? `<span class="tag" style="background:${colorTipo[x.tipo]}">${x.tipo}</span>` : ""}</div><div class="v">${x.n}</div>
  <div class="t"><b style="width:${x.n / maxN * 100}%;background:${colorTipo[x.tipo]}"></b></div><div style="font-size:11px;color:var(--muted);text-align:right">x${f1(x.veces)}</div></div>`).join("");

// ---- economia por semana ----
(function () {
  const w = 440, h = 150, l = 24, t = 14, b = 24, pw = w - l - 6, ph = h - t - b, E = D.econ_sem, m = Math.max(...E), bw = pw / W;
  let s = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Reportes de situación económica por semana">`;
  E.forEach((v, i) => {
    const bh = v / m * ph, x = l + i * bw;
    s += `<rect x="${x + 3}" y="${t + ph - bh}" width="${bw - 6}" height="${bh}" rx="2" fill="var(--econ)" opacity="${i + 1 >= 9 ? 1 : .4}"/>
      <text x="${x + bw / 2}" y="${t + ph - bh - 3}" text-anchor="middle">${v}</text><text x="${x + bw / 2}" y="${h - 8}" text-anchor="middle">${i + 1}</text>`;
  });
  $("econ").innerHTML = s + "</svg>";
})();
</script>
</body>
</html>
"""


def main():
    d = calcular()
    datos = json.dumps(datos_para_tablero(d), ensure_ascii=False)
    html = PLANTILLA.replace("__DATOS__", datos)
    out = BASE / "03_tableros" / "voz_primera_linea.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("Tablero:", out, f"({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
