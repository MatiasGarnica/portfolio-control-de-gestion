"""Arma 03_tableros/demo_login.html: el mismo tablero, pero los datos NO van dentro de la página.

La página pide login (Supabase Auth) y trae los datos de la base. La base aplica seguridad por fila (RLS):
cada usuario recibe solo las filas de su alcance. La clave que va en la página es la "publicable"
(pensada para estar en el navegador); la clave secreta nunca sale del servidor.

Uso:  python armar_demo.py
"""
from pathlib import Path

URL = "https://wlbwelatewecujnvjzpa.supabase.co"
CLAVE_PUBLICABLE = "sb_publishable_W9iqyayREslltIOKLw_IrQ_8ROe7cJq"
BASE = Path(__file__).resolve().parent.parent
html = (Path(__file__).parent / "tablero_plantilla.html").read_text(encoding="utf-8")


def cambiar(viejo, nuevo):
    global html
    assert html.count(viejo) == 1, f"no encontré una sola vez: {viejo[:60]}"
    html = html.replace(viejo, nuevo)


# 1. El código del tablero queda "dormido" hasta que llegan los datos de la base
cambiar("<script>\nconst DATA = /*__DATOS__*/null;", '<script type="text/plain" id="app">\nconst DATA = window.__DATOS;')
cambiar("<title>Tablero de Dirección</title>", "<title>Demo con login</title>")
# 2. Textos que dependen del alcance de cada usuario
cambiar("la contribución de la red está", "${window.__ALCANCE} está")
cambiar("<h3>Contribución de la red por mes</h3>", "<h3>Contribución por mes (tu alcance)</h3>")
cambiar("<p><b>Seguridad:</b> esta página lleva todos los datos adentro, algo aceptable solo porque son ficticios. En una empresa, cada gerente vería su local o región porque el filtro se aplica en la base de datos, no en la página.</p>",
        "<p><b>Seguridad:</b> esta página no lleva datos adentro. Los pide a la base con tu sesión, y la base (seguridad por fila) devuelve solo lo que tu rol puede ver. "
        "Probá entrar con otro usuario: cambia lo que ves, no porque la página lo oculte, sino porque la base no lo manda.</p>")

cambiar("selL.innerHTML = L.map((l, i) => `<option value=\"${i}\">${l.id} ${l.nombre}</option>`).join('');",
        "selL.innerHTML = L.map((l, i) => RES[i].some(x => x) ? `<option value=\"${i}\">${l.id} ${l.nombre}</option>` : '').join('');")
cambiar('<h2 id="t-n1">Dirección: ¿cómo está la red y dónde está el desvío?</h2>', '<h2 id="t-n1">Tu alcance: ¿cómo está y dónde está el desvío?</h2>')

LOGIN = r"""
<style>
#login { position: fixed; inset: 0; z-index: 30; background: var(--page); display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 32px 16px; }
#login .caja { max-width: 560px; width: 100%; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 22px; }
#login h1 { font-size: 21px; } #login p { color: var(--ink2); font-size: 14px; margin: 6px 0 14px; }
#login .usuarios { display: grid; gap: 8px; margin: 12px 0 16px; }
#login .usuarios button { text-align: left; padding: 10px 12px; }
#login .usuarios b { display: block; font-size: 14px; } #login .usuarios span { font-size: 12.5px; color: var(--ink2); }
#login form { display: grid; gap: 8px; border-top: 1px solid var(--border); padding-top: 14px; }
#login input { font: inherit; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--page); color: var(--ink); }
#login .msg { min-height: 20px; font-size: 13px; color: var(--bad); }
#sesion { display: none; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 10px 14px; margin-bottom: 12px; font-size: 13.5px; gap: 10px; justify-content: space-between; align-items: center; flex-wrap: wrap; }
#solo-incidentes { display: none; }
</style>
<div id="login" role="dialog" aria-labelledby="t-login">
  <div class="caja">
    <h1 id="t-login">Demo con login · Cadena Demo S.A.</h1>
    <p>Cada usuario de prueba ve solo lo que le corresponde según su rol. La página no tiene los datos adentro: los pide a la base, y la base filtra por usuario. Empresa y datos <b>ficticios</b>, de solo lectura.</p>
    <div class="usuarios" id="botones"></div>
    <form id="form">
      <label>Email <input id="email" type="email" autocomplete="username" required></label>
      <label>Contraseña <input id="pw" type="password" autocomplete="current-password" required></label>
      <button type="submit">Entrar</button>
      <div class="msg" id="msg" role="status"></div>
    </form>
    <p style="font-size:12.5px">Contraseña de todos los usuarios de prueba: <code>Caso05-Demo</code></p>
  </div>
</div>
<script type="module">
import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/+esm";
const sb = createClient("__URL__", "__CLAVE__");
const USUARIOS = [
  ["direccion@cadena-demo.test", "Dirección", "Ve los 12 locales"],
  ["regional.norte@cadena-demo.test", "Gerente regional Norte", "Ve solo los locales de su región"],
  ["regional.centro@cadena-demo.test", "Gerente regional Centro", "Ve solo los locales de su región"],
  ["local.l07@cadena-demo.test", "Gerente de local L07", "Ve solo su local"],
  ["local.l10@cadena-demo.test", "Gerente de local L10", "Ve solo su local"],
  ["supervisor.l03@cadena-demo.test", "Supervisor L03", "Ve solo los incidentes de su local, sin números económicos"],
];
const $ = id => document.getElementById(id);
$("botones").innerHTML = USUARIOS.map(([e, r, d]) => `<button type="button" data-email="${e}"><b>${r}</b><span>${d} · ${e}</span></button>`).join("");
$("botones").addEventListener("click", ev => { const b = ev.target.closest("button"); if (!b) return; $("email").value = b.dataset.email; $("pw").value = "Caso05-Demo"; entrar(); });
$("form").addEventListener("submit", ev => { ev.preventDefault(); entrar(); });

async function todo(tabla, cols, orden) {           // la API devuelve hasta 1000 filas por pedido: pido por tandas
  let filas = [], desde = 0;
  for (;;) {
    const { data, error } = await sb.from(tabla).select(cols).order(orden).range(desde, desde + 999);
    if (error) throw error;
    filas = filas.concat(data); if (data.length < 1000) return filas; desde += 1000;
  }
}
async function entrar() {
  $("msg").textContent = "Entrando…";
  const { error } = await sb.auth.signInWithPassword({ email: $("email").value.trim(), password: $("pw").value });
  if (error) { $("msg").textContent = "No se pudo entrar: " + error.message; return; }
  try { await cargar(); } catch (e) { $("msg").textContent = "Error al traer los datos: " + (e.message || e); }
}
async function cargar() {
  const [perfil] = await todo("perfiles", "email,rol,region,local_id", "email");
  const [loc, rub, cal, res, op, nom, inc] = await Promise.all([
    todo("dim_local", "*", "local_id"), todo("dim_rubro", "*", "rubro_id"), todo("dim_calendario", "*", "periodo"),
    todo("fact_resultados", "periodo,local_id,rubro_id,real,presupuesto", "periodo"),
    todo("fact_operativo", "*", "periodo"), todo("fact_nomina", "*", "periodo"), todo("fact_incidentes", "*", "fecha")]);
  const pi = Object.fromEntries(cal.map((c, i) => [c.periodo, i])), li = Object.fromEntries(loc.map((l, i) => [l.local_id, i]));
  const PUESTOS = ["Encargado", "Atención", "Cocina", "Limpieza"];
  window.__DATOS = {
    locales: loc.map(l => [l.local_id, l.local, l.region, l.formato, l.m2, l.apertura]),
    rubros: rub.map(r => [r.rubro_id, r.rubro, r.signo, r.grupo_puente]),
    cal: cal.map(c => [c.periodo, Number(c.ipc_indice), Number(c.ipc_ppto_indice)]),
    res: res.map(r => [pi[r.periodo], li[r.local_id], r.rubro_id, Number(r.real), Number(r.presupuesto)]),
    op: op.map(o => [pi[o.periodo], li[o.local_id], o.tickets, o.ticket_promedio, o.dotacion, o.horas_trabajadas, o.bajas_personal, o.tickets_ppto, o.ticket_promedio_ppto]),
    puestos: PUESTOS,
    nom: nom.map(n => [pi[n.periodo], li[n.local_id], PUESTOS.indexOf(n.puesto), n.dotacion, n.horas_normales, n.horas_extra, Number(n.costo_total)]),
    inc: inc.map(x => [x.fecha, li[x.local_id], x.tipo, x.horas_afectadas, x.detalle]),
  };
  const pf = await sb.rpc("promedio_formato");
  if (pf.error) throw pf.error;
  window.__DATOS.pf = {};
  for (const r of pf.data) if (r.rubro_id === 1) (window.__DATOS.pf[r.formato] ||= [])[pi[r.periodo]] = Number(r.monto_real);
  let coms = [], fbs = [];
  async function recargar() {
    const [c, f] = await Promise.all([
      sb.from("comentarios_desvio").select("*").order("creado"),
      sb.from("feedback_primera_linea").select("*").order("fecha")]);
    if (c.error) throw c.error; if (f.error) throw f.error;
    coms = c.data; fbs = f.data;
  }
  await recargar();
  const esc = s => String(s ?? "").replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
  const fechaAR = f => f.split("-").reverse().join("/");
  const GRUPOS = ["Ventas", "Costo de mercadería", "Personal", "Gastos de ocupación", "Gastos operativos", "Impuestos", "Financiero"];
  const CATS = ["Precio", "Calidad del producto", "Atención o servicio", "Falta de stock o entrega", "Situación económica del cliente", "Competencia", "Clima o estacionalidad", "Otro"];
  const propio = id => perfil.local_id === id;
  function htmlFeedback(localId, periodos) {
    const sel = fbs.filter(x => x.local_id === localId && (!periodos || periodos.has(x.fecha.slice(0, 7))));
    const cuenta = {}; sel.forEach(x => cuenta[x.categoria] = (cuenta[x.categoria] || 0) + 1);
    const max = Math.max(1, ...Object.values(cuenta));
    let h = `<div class="card-h"><h3>Lo que dice la primera línea · ${sel.length} reporte${sel.length === 1 ? "" : "s"} en el período</h3></div>`;
    h += sel.length
      ? Object.entries(cuenta).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<div style="display:flex;gap:8px;align-items:center;margin:5px 0"><span style="width:220px;font-size:13px">${esc(k)}</span><span style="height:12px;border-radius:0 4px 4px 0;background:var(--s1);width:${Math.round(v / max * 200)}px"></span><span style="font-size:12.5px;color:var(--ink2)">${v}</span></div>`).join("")
        + `<div class="nota">Últimos: ${sel.slice(-3).reverse().map(x => `${fechaAR(x.fecha)} · ${esc(x.categoria)}${x.detalle ? ": " + esc(x.detalle) : ""}`).join(" | ")}</div>`
      : `<div class="nota">Sin reportes en el período.</div>`;
    if (propio(localId) && ["Supervisor", "Gerente de local"].includes(perfil.rol)) h += `<form class="fform" data-tipo="fb" style="display:grid;gap:6px;margin-top:12px;max-width:520px">
      <b style="font-size:13px">Cargar un reporte (1 minuto)</b>
      <select name="categoria" aria-label="Categoría">${CATS.map(c => `<option>${c}</option>`).join("")}</select>
      <input name="detalle" maxlength="300" placeholder="Detalle breve (opcional)" aria-label="Detalle">
      <button type="submit">Guardar reporte</button><span class="nota" data-msg role="status"></span></form>`;
    return h;
  }
  function htmlComentarios(localId) {
    const sel = coms.filter(x => x.local_id === localId).slice().reverse();
    let h = `<div class="card-h"><h3>¿Qué pasó? Explicación del responsable del local</h3></div>`;
    h += sel.length
      ? `<div class="scroll"><table><thead><tr><th class="txt">Mes</th><th class="txt">Rubro</th><th class="txt">Causa</th><th class="txt">¿Controlable?</th><th class="txt">Acción y plazo</th></tr></thead><tbody>${sel.map(x => `<tr><td class="txt">${x.periodo}</td><td class="txt">${esc(x.grupo)}</td><td class="txt">${esc(x.causa)}</td><td class="txt">${x.controlable ? "Sí (gestión)" : "No (externo)"}</td><td class="txt">${esc(x.accion)}${x.fecha_compromiso ? " · hasta " + fechaAR(x.fecha_compromiso) : ""}</td></tr>`).join("")}</tbody></table></div>`
      : `<div class="nota">Todavía no hay explicaciones para este local.</div>`;
    if (propio(localId) && perfil.rol === "Gerente de local") h += `<form class="fform" data-tipo="cm" style="display:grid;gap:6px;margin-top:12px;max-width:620px">
      <b style="font-size:13px">Explicar un desvío de tu local (queda firmado con tu usuario)</b>
      <select name="grupo" aria-label="Rubro">${GRUPOS.map(g => `<option>${g}</option>`).join("")}</select>
      <textarea name="causa" required minlength="5" maxlength="400" rows="2" placeholder="Causa: qué pasó" aria-label="Causa"></textarea>
      <select name="controlable" aria-label="¿Controlable?"><option value="true">Controlable (gestión)</option><option value="false">No controlable (externo)</option></select>
      <input name="accion" required minlength="3" maxlength="300" placeholder="Acción: qué se hace" aria-label="Acción">
      <label style="font-size:13px">Fecha de compromiso <input name="fecha" type="date"></label>
      <button type="submit">Guardar explicación</button><span class="nota" data-msg role="status"></span></form>`;
    else h += `<div class="nota">Solo el gerente de este local puede escribir acá; vos lo leés. La base lo controla, no la página.</div>`;
    return h;
  }
  document.addEventListener("submit", async ev => {
    const f = ev.target.closest(".fform"); if (!f) return;
    ev.preventDefault();
    const d = Object.fromEntries(new FormData(f)), msg = f.querySelector("[data-msg]");
    msg.textContent = "Guardando…";
    const r = f.dataset.tipo === "cm"
      ? await sb.from("comentarios_desvio").insert({ local_id: perfil.local_id, periodo: window.__ULT_PERIODO, grupo: d.grupo, causa: d.causa, controlable: d.controlable === "true", accion: d.accion, fecha_compromiso: d.fecha || null })
      : await sb.from("feedback_primera_linea").insert({ local_id: perfil.local_id, categoria: d.categoria, detalle: d.detalle || null });
    if (r.error) { msg.textContent = "No se pudo guardar: " + r.error.message; return; }
    await recargar(); window.__DEMO.refrescar();
  });
  window.__DEMO = {
    _ult: null,
    resumen(id) { const c = coms.filter(x => x.local_id === id).at(-1); return c ? `<br>Explicación (${c.periodo}): ${esc(c.causa.slice(0, 90))}${c.causa.length > 90 ? "…" : ""}` : ""; },
    render(l, ms) {
      const id = window.__DATOS.locales[l][0], per = new Set(ms.map(i => window.__DATOS.cal[i][0]));
      window.__ULT_PERIODO = window.__DATOS.cal[ms[ms.length - 1]][0];
      $("cm").innerHTML = htmlComentarios(id); $("fb").innerHTML = htmlFeedback(id, per);
      $("cm").classList.remove("oculto"); $("fb").classList.remove("oculto");
      this._ult = [l, ms];
    },
    refrescar() {
      if (perfil.rol === "Supervisor") $("fb-sup").innerHTML = htmlFeedback(perfil.local_id, null);
      else if (this._ult) this.render(...this._ult);
    },
  };
  const visibles = new Set(res.map(r => r.local_id));
  const alcance = perfil.rol === "Dirección" ? "la contribución de la red"
    : perfil.rol === "Gerente regional" ? `la contribución de tu región (${perfil.region})`
    : `la contribución de tu local (${perfil.local_id})`;
  window.__ALCANCE = alcance;
  $("sesion").innerHTML = `<span><b>${perfil.rol}</b>${perfil.region ? " · " + perfil.region : ""}${perfil.local_id ? " · " + perfil.local_id : ""} — la base te mandó <b>${res.length.toLocaleString("es-AR")}</b> filas de resultados de <b>${visibles.size}</b> local${visibles.size === 1 ? "" : "es"} y <b>${inc.length}</b> incidentes (de 2.484 y 110 en total).</span><button type="button" id="salir">Cerrar sesión</button>`;
  $("sesion").style.display = "flex";
  $("salir").onclick = async () => { await sb.auth.signOut(); location.reload(); };
  $("login").style.display = "none";
  if (!res.length) {   // supervisor: no ve números económicos, solo sus incidentes
    document.querySelectorAll("#n1, #n2, #n3, .filtros").forEach(n => n.style.display = "none");
    const s = $("solo-incidentes"); s.style.display = "block";
    s.querySelector("tbody").innerHTML = inc.sort((a, b) => b.fecha.localeCompare(a.fecha)).map(x =>
      `<tr><td class="txt">${x.fecha.split("-").reverse().join("/")}</td><td class="txt">${x.local_id}</td><td class="txt">${x.tipo}</td><td>${x.horas_afectadas || "—"}</td><td class="txt">${x.detalle}</td></tr>`).join("");
    $("fb-sup").innerHTML = htmlFeedback(perfil.local_id, null);
    return;
  }
  const app = document.createElement("script"); app.textContent = $("app").textContent; document.body.appendChild(app);
}
</script>
""".replace("__URL__", URL).replace("__CLAVE__", CLAVE_PUBLICABLE)

cambiar('<div class="wrap">\n  <header class="marca">', '<div class="wrap">\n  <div id="sesion" role="status"></div>\n  <header class="marca">')
cambiar('  <section id="n1"', '''  <section id="solo-incidentes"><div class="nivel"><span class="tag">Supervisor</span><h2>Incidentes de tu local</h2></div>
    <div class="card scroll"><table><thead><tr><th class="txt">Fecha</th><th class="txt">Local</th><th class="txt">Tipo</th><th>Horas</th><th class="txt">Detalle</th></tr></thead><tbody></tbody></table>
    <div class="nota">Tu rol ve los incidentes y carga lo que dice la primera línea, pero no los resultados económicos: la base no te los manda.</div></div>
    <div class="card" id="fb-sup" style="margin-top:14px"></div></section>
  <section id="n1"''')
cambiar("</body>", LOGIN + "</body>")

destino = BASE / "03_tableros" / "demo_login.html"
destino.write_text(html, encoding="utf-8")
print(f"OK {destino} ({destino.stat().st_size / 1024:.0f} KB, sin datos adentro)")
