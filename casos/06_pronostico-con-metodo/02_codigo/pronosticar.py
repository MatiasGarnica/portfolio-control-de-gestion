"""Caso 06 · Pronóstico con método: cuánto vamos a vender y ganar, con qué método y qué tan bueno es.

Usa los datos ficticios del Caso 05 (cadena de 12 locales, nov-2024 a oct-2026) y responde:
  1. Cierre 2026 (nov-dic) y año 2027: ventas y contribución, con intervalo.
  2. Qué método usar: backtest honesto contra ingenuo, promedio móvil, regresión y el PRESUPUESTO.
  3. Inflación: se pronostica en moneda constante y se reinfla con escenarios de IPC.
  4. Ruido o señal: bandas de control por local.

Uso:
  python pronosticar.py                     (busca los CSV del Caso 05 solo)
  python pronosticar.py --datos RUTA        (carpeta con los CSV, si están en otro lado)

Los CSV del Caso 05 no se suben al repositorio: primero hay que generarlos con
  python casos/05_cadena-multisucursal/02_codigo/generar_datos.py
Solo usa pandas y numpy. No hay nada aleatorio: siempre da lo mismo.
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
CANDIDATOS = [
    AQUI.parent.parent / "05_cadena-multisucursal" / "01_datos",        # repositorio público (casos/…)
    AQUI.parent.parent / "Caso05_Cadena-multisucursal" / "01_datos",    # carpeta de trabajo local
]
SALIDA = AQUI / "salida"
# los métodos ingenuos dividen por meses sin historia (p. ej. L05 antes de abrir): numpy avisa y el resultado se descarta
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ------------------------------------------------------------------ parámetros de criterio
MESES_RAMPA = 6                 # un local nuevo tarda 6 meses en llegar a su nivel: esos meses no entrenan el modelo
MIN_MESES_TENDENCIA = 18        # con menos de 18 meses, tendencia y estacionalidad se confunden: no se estima tendencia
ORIGENES_CORTO = range(14, 23)  # backtest corto: cortes ene-26 … sep-26, pronóstico a 1-3 meses
ORIGEN_ANUAL = 11               # backtest anual: corte oct-25, pronóstico de los 12 meses siguientes
HORIZONTE_CORTO = 3
Z80 = 1.2816                    # intervalo de 80 %: 8 de cada 10 meses deberían caer adentro
ESCENARIOS_IPC = {              # inflación mensual supuesta para nov-2026 a dic-2027
    "bajo": 1.6,    # la que supuso el presupuesto 2026 (que resultó corta)
    "base": 2.0,    # promedio de los últimos 3 meses (1,97 %), redondeado
    "alto": 2.5,    # promedio de los últimos 12 meses (2,47 %), redondeado
}
GRUPO_ESTAC = {"Calle": "urbano", "Shopping": "urbano", "Ruta": "ruta"}
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# ------------------------------------------------------------------ datos
def buscar_datos(ruta=None):
    for c in ([Path(ruta)] if ruta else CANDIDATOS):
        if (c / "fact_resultados.csv").exists():
            return c
    raise SystemExit("No encuentro los CSV del Caso 05. Corré antes "
                     "'python casos/05_cadena-multisucursal/02_codigo/generar_datos.py' o pasá --datos RUTA.")


def cargar(carpeta):
    leer = lambda n: pd.read_csv(carpeta / f"{n}.csv")
    cal, loc, rub, res = leer("dim_calendario"), leer("dim_local"), leer("dim_rubro"), leer("fact_resultados")
    res = res.merge(rub[["rubro_id", "signo"]], on="rubro_id")
    per = list(cal.periodo)
    ids = list(loc.local_id)

    def matriz(df, col):
        return df.pivot_table(index="local_id", columns="periodo", values=col, aggfunc="sum").reindex(index=ids, columns=per).to_numpy(float, copy=True)

    ventas = res[res.rubro_id == 1]
    res = res.assign(c_real=res.real * res.signo, c_ppto=res.presupuesto * res.signo)
    d = {
        "periodos": per, "locales": loc,
        "ipc": cal.ipc_indice.to_numpy(float), "ipc_ppto": cal.ipc_ppto_indice.to_numpy(float),
        "infl": cal.inflacion_mensual_pct.to_numpy(float),
        "V": matriz(ventas, "real"), "VP": matriz(ventas, "presupuesto"),
        "C": matriz(res, "c_real"), "CP": matriz(res, "c_ppto"),
    }
    # local cerrado = NaN (no cero)
    abierto = ~np.isnan(d["V"])
    for k in ("C", "CP"):
        d[k][~abierto] = np.nan
    # pasaje a moneda constante: pesos de oct-2026 (el último mes conocido).
    # Real: se deflacta con el IPC real. Presupuesto: con el IPC que supuso el propio presupuesto
    # (así su error en moneda constante es solo de volumen y precio relativo, no de inflación).
    k_real = d["ipc"][-1] / d["ipc"]
    k_ppto = d["ipc"][-1] / d["ipc_ppto"]
    d["Vc"], d["Cc"] = d["V"] * k_real, d["C"] * k_real
    d["VPc"], d["CPc"] = d["VP"] * k_ppto, d["CP"] * k_ppto
    # mes del año (1-12) e índice de apertura de cada local
    d["mes"] = np.array([int(p[5:]) for p in per])
    aper = pd.PeriodIndex(loc.apertura, freq="M")
    p0 = pd.Period(per[0], freq="M")
    d["i_aper"] = np.array([(a - p0).n for a in aper])
    d["grupo"] = np.array([GRUPO_ESTAC[f] for f in loc.formato])
    return d


# ------------------------------------------------------------------ métodos de pronóstico
# Todos reciben Y (locales x meses, moneda constante) hasta el corte `o` (inclusive) y devuelven
# una matriz locales x H con el pronóstico de los meses o+1 … o+H.

def ingenuo_estacional(Y, o, H, **_):
    """Mismo mes del año anterior, en moneda constante (o sea, ajustado por inflación)."""
    ext = Y[:, : o + 1].copy()
    for h in range(1, H + 1):
        ext = np.column_stack([ext, ext[:, o + h - 12]])
    return ext[:, o + 1:]


def ingenuo_con_crecimiento(Y, o, H, **_):
    """Mismo mes del año anterior x el crecimiento interanual de los últimos 3 meses."""
    k = min(3, o - 11)
    if k <= 0:
        g = np.ones(Y.shape[0])
    else:
        g = np.nansum(Y[:, o - k + 1: o + 1], 1) / np.nansum(Y[:, o - k - 11: o - 11], 1)
    return ingenuo_estacional(Y, o, H) * g[:, None]


def promedio_movil(Y, o, H, **_):
    """Promedio de los últimos 3 meses, plano hacia adelante."""
    return np.repeat(np.nanmean(Y[:, o - 2: o + 1], 1)[:, None], H, 1)


def regresion(Y, o, H, d, estac="grupo", min_tend=MIN_MESES_TENDENCIA, robusta=True, devolver_modelo=False, **_):
    """log(Y) = nivel del local + estacionalidad (propia / de la red / por grupo) + tendencia común.

    Se estima por mínimos cuadrados con numpy. La tendencia se incluye solo si hay al menos
    `min_tend` meses de historia: con un solo año, un mes "alto" puede ser estacionalidad o tendencia
    y la regresión no tiene forma de distinguirlos.
    """
    n_loc, T = Y.shape[0], o + 1
    con_tend = T >= min_tend
    filas, yv = [], []
    if estac == "local":
        claves_e = [(l, m) for l in range(n_loc) for m in range(2, 13)]
    elif estac == "red":
        claves_e = [("red", m) for m in range(2, 13)]
    else:
        claves_e = [(g, m) for g in ("urbano", "ruta") for m in range(2, 13)]
    pos_e = {k: i for i, k in enumerate(claves_e)}

    def clave(l, m):
        return (l, m) if estac == "local" else ("red", m) if estac == "red" else (d["grupo"][l], m)

    n_par = n_loc + len(claves_e) + (1 if con_tend else 0)

    def x(l, t):
        v = np.zeros(n_par)
        v[l] = 1
        m = d["mes"][t] if t < len(d["mes"]) else (d["mes"][t % 12])
        if m != 1:
            v[n_loc + pos_e[clave(l, m)]] = 1
        if con_tend:
            v[-1] = t / 12
        return v

    for l in range(n_loc):
        for t in range(T):
            if np.isnan(Y[l, t]) or t < d["i_aper"][l] + MESES_RAMPA:
                continue
            filas.append(x(l, t))
            yv.append(np.log(Y[l, t]))
    X, yv = np.array(filas), np.array(yv)

    def ajustar(X, yv):
        usados = X.any(0)                 # parámetros sin datos (p. ej. un local que todavía no abrió) quedan en 0
        b = np.zeros(n_par)
        b[usados] = np.linalg.lstsq(X[:, usados], yv, rcond=None)[0]
        return b

    beta = ajustar(X, yv)
    if robusta:
        # segunda pasada: los meses con un residuo mayor a 3 desvíos robustos (algo puntual, como una obra
        # que corta el acceso) no entrenan el modelo, para que no contaminen el nivel ni la tendencia
        r = yv - X @ beta
        s_rob = 1.4826 * np.median(np.abs(r - np.median(r)))
        ok = np.abs(r) <= 3 * s_rob
        beta = ajustar(X[ok], yv[ok])
    entrenado = X[:, :n_loc].any(0)       # locales con al menos un mes para estimar su nivel
    out = np.full((n_loc, H), np.nan)
    for l in range(n_loc):
        if entrenado[l]:
            for h in range(1, H + 1):
                out[l, h - 1] = np.exp(x(l, o + h) @ beta)
    if devolver_modelo:
        return out, beta, con_tend, claves_e
    return out


METODOS = {
    "ingenuo": ("Ingenuo estacional", "El mismo mes del año anterior, en moneda constante", ingenuo_estacional),
    "ingenuo_crec": ("Ingenuo + crecimiento reciente",
                     "Mismo mes del año anterior x el crecimiento interanual de los últimos 3 meses (a 12 meses queda igual al ingenuo: con un año de historia no hay crecimiento que medir)", ingenuo_con_crecimiento),
    "movil": ("Promedio móvil 3 meses", "El promedio de los últimos 3 meses, plano", promedio_movil),
    "reg_local": ("Regresión · estacionalidad propia de cada local",
                  "Tendencia + 11 coeficientes de mes por local (pocos datos para tantos)",
                  lambda Y, o, H, d: regresion(Y, o, H, d, estac="local")),
    "reg_red": ("Regresión · estacionalidad de la red",
                "Tendencia + un solo patrón de meses para toda la red, aplicado a cada local",
                lambda Y, o, H, d: regresion(Y, o, H, d, estac="red")),
    "reg_grupo": ("Regresión · estacionalidad por tipo de local",
                  "Tendencia + un patrón de meses para locales urbanos y otro para los de ruta",
                  lambda Y, o, H, d: regresion(Y, o, H, d, estac="grupo")),
}


# ------------------------------------------------------------------ backtest
def pares_backtest(T, origenes, horizonte):
    """Pares (corte, mes pronosticado) del backtest."""
    return [(o, o + h) for o in origenes for h in range(1, horizonte + 1) if o + h < T]


def correr_backtest(d, Y, YP, comparables, pares):
    """Para cada método: pronóstico de cada local en cada par (corte, mes). Devuelve dict método -> matriz pares x locales."""
    salida = {}
    for clave, (_, _, f) in METODOS.items():
        cache = {}
        filas = []
        for o, t in pares:
            if o not in cache:
                H = max(tt for oo, tt in pares if oo == o) - o
                cache[o] = f(Y, o, H, d=d)
            filas.append(cache[o][:, t - o - 1])
        salida[clave] = np.array(filas)[:, comparables]
    salida["ppto"] = np.array([YP[comparables, t] for _, t in pares])
    real = np.array([Y[comparables, t] for _, t in pares])
    return salida, real


def metricas(pron, real, pares):
    """WAPE y sesgo a nivel red (suma de locales) y a nivel local. Error = pronóstico − real."""
    e_loc = pron - real
    red_p, red_r = pron.sum(1), real.sum(1)
    e_red = red_p - red_r
    hs = np.array([t - o for o, t in pares])
    return {
        "wape_red": float(np.abs(e_red).sum() / red_r.sum()),
        "sesgo_red": float(e_red.sum() / red_r.sum()),
        "wape_local": float(np.abs(e_loc).sum() / real.sum()),
        "mape_local": float(np.mean(np.abs(e_loc) / real)),
        "e_rel_red": (e_red / red_r).tolist(),
        "h": hs.tolist(),
    }


def incertidumbre(e_rel, hs):
    """Cuánto se equivocó el método en el backtest, para armar el intervalo del pronóstico.

    - Mes a mes: raíz del error cuadrático medio (RMSE) relativo, a 1-3 meses y a 4-12 meses. En este backtest
      el error casi no crece con el horizonte; si creciera, la banda larga lo toma.
    - Para un total de varios meses (nov-dic, año 2027): una parte del error se repite todos los meses (el sesgo)
      y otra se compensa (el ruido). sigma_total = raiz(sesgo² + ruido² / n_meses).
    """
    e, h = np.asarray(e_rel), np.asarray(hs)
    corto = float(np.sqrt(np.mean(e[h <= 3] ** 2)))
    largo = max(corto, float(np.sqrt(np.mean(e[h >= 4] ** 2)))) if (h >= 4).any() else corto
    return {"corto": corto, "largo": largo, "sesgo": float(e.mean()), "ruido": float(e.std(ddof=1))}


def sigma_mes(inc, hs):
    return np.where(np.asarray(hs) <= 3, inc["corto"], inc["largo"])


def sigma_total(inc, n):
    return float(np.sqrt(inc["sesgo"] ** 2 + inc["ruido"] ** 2 / n))


# ------------------------------------------------------------------ contribución
def pronostico_contribucion(Vf, Cc, Vc, o, d, modo="palanca"):
    """Contribución pronosticada a partir de las ventas pronosticadas.

    'palanca': por local, Contribución = margen variable x Ventas − costos fijos, estimado con los
               últimos 12 meses (regresión simple). Captura que en los meses fuertes el margen sube.
    'margen':  margen de contribución promedio de los últimos 12 meses x ventas pronosticadas.
    """
    n_loc = Cc.shape[0]
    out = np.full_like(Vf, np.nan)
    for l in range(n_loc):
        ini = max(0, o - 11, d["i_aper"][l] + MESES_RAMPA)
        v, c = Vc[l, ini: o + 1], Cc[l, ini: o + 1]
        ok = ~np.isnan(v) & ~np.isnan(c)
        v, c = v[ok], c[ok]
        if len(v) < 3:
            continue
        if modo == "palanca" and len(v) >= 6:
            b, a = np.polyfit(v, c, 1)
            r = c - (a + b * v)               # mes raro (p. ej. una rotura con merma y reparación): no entrena
            s_rob = 1.4826 * np.median(np.abs(r - np.median(r)))
            ok = np.abs(r) <= 3 * s_rob if s_rob > 0 else np.ones(len(r), bool)
            b, a = np.polyfit(v[ok], c[ok], 1)
            out[l] = a + b * Vf[l]
        else:
            out[l] = c.sum() / v.sum() * Vf[l]
    return out


# ------------------------------------------------------------------ bandas de control
def bandas_control(d, comparables):
    """Ruido o señal, por local, para los 12 meses nov-25 … oct-26.

    Indicadores (los dos limpian estacionalidad, inflación y lo que le pasó a toda la red):
      ventas: crecimiento interanual del local en moneda constante − el de la red comparable (p.p.)
      margen: cambio interanual del margen de contribución del local − el de la red (p.p.)
    Centro y desvío robustos (mediana y MAD x 1,4826) sobre todos los locales y meses: los meses raros
    no inflan la banda. Reglas (Western Electric): un mes fuera de ±3 desvíos; 2 de 3 meses seguidos
    fuera de ±2 desvíos del mismo lado; 8 meses seguidos del mismo lado del centro.
    """
    V, C = d["Vc"], d["Cc"]
    idx = list(range(12, 24))
    comp = np.array(comparables)
    ind = {}
    # la referencia es la MEDIANA de los locales (no el total de la red): si un local se cae 25 %,
    # el total de la red baja y todos los demás parecerían "crecer más que la red" sin haber hecho nada
    ant = [i - 12 for i in idx]
    crec_loc = V[comp][:, idx] / V[comp][:, ant] - 1
    ind["ventas"] = (crec_loc - np.median(crec_loc, 0)) * 100
    m_loc = C[comp] / V[comp]
    dm = m_loc[:, idx] - m_loc[:, ant]
    ind["margen"] = (dm - np.median(dm, 0)) * 100

    out = {}
    for nombre, x in ind.items():
        centro = float(np.median(x))
        sd = float(1.4826 * np.median(np.abs(x - centro)))
        sd_clasico = float(x.std(ddof=1))
        locs = []
        for j, l in enumerate(comparables):
            z = (x[j] - centro) / sd
            señales = []
            for t in range(12):
                r = []
                if abs(z[t]) > 3:
                    r.append(1)
                ventana = z[max(0, t - 2): t + 1]
                if len(ventana) == 3 and (np.sum(ventana > 2) >= 2 or np.sum(ventana < -2) >= 2) and abs(z[t]) > 2:
                    r.append(2)
                if t >= 7 and (np.all(z[t - 7: t + 1] > 0) or np.all(z[t - 7: t + 1] < 0)):
                    r.append(3)
                señales.append(r)
            locs.append({"local": d["locales"].local_id[l], "valores": np.round(x[j], 2).tolist(),
                         "z": np.round(z, 2).tolist(), "reglas": señales,
                         "fuera_2": int(np.sum(np.abs(z) > 2)),
                         "señal": any(señales)})
        out[nombre] = {"centro": round(centro, 3), "sd": round(sd, 3), "sd_clasico": round(sd_clasico, 3),
                       "locales": locs}
    return out


def incidentes_clave(carpeta, d):
    """Incidentes con causa conocida del registro del Caso 05 (no los menores ni los que afectaron a toda la red)."""
    inc = pd.read_csv(carpeta / "fact_incidentes.csv")
    menores = {"Corte de luz", "Falla de equipo de cocina", "Faltante de insumo", "Ausentismo (falta de personal)",
               "Reclamo de cliente grave", "Corte de agua"}          # los incidentes chicos y frecuentes del registro
    inc = inc[~inc.tipo.isin(menores)]
    toda_red = inc.groupby(["fecha", "tipo"]).local_id.transform("count") >= len(d["locales"]) - 1
    inc = inc[~toda_red]
    return [{"fecha": r.fecha, "local": r.local_id, "tipo": r.tipo, "detalle": r.detalle} for r in inc.itertuples()]


def desvio_contra_ppto(d, comparables, umbral=5.0):
    """Cuántos locales 'piden explicación' con la regla clásica: desvío de ventas nominal contra presupuesto > ±5 %."""
    idx = list(range(12, 24))
    r = []
    for l in comparables:
        dv = (d["V"][l, idx] / d["VP"][l, idx] - 1) * 100
        dvc = (d["Vc"][l, idx] / d["VPc"][l, idx] - 1) * 100
        r.append({"local": d["locales"].local_id[l], "desvio_nominal": np.round(dv, 1).tolist(),
                  "desvio_constante": np.round(dvc, 1).tolist(),
                  "meses_fuera_nominal": int(np.sum(np.abs(dv) > umbral)),
                  "meses_fuera_constante": int(np.sum(np.abs(dvc) > umbral))})
    return r


# ------------------------------------------------------------------ armado
def main(ruta_datos=None):
    carpeta = buscar_datos(ruta_datos)
    d = cargar(carpeta)
    loc = d["locales"]
    T = len(d["periodos"])
    n_loc = len(loc)
    comparables = [l for l in range(n_loc) if d["i_aper"][l] <= 0]   # abiertos todo el período: sin L05
    Y, YP = d["Vc"], d["VPc"]

    # 1) backtest de ventas
    pares_c = pares_backtest(T, ORIGENES_CORTO, HORIZONTE_CORTO)
    pares_a = pares_backtest(T, [ORIGEN_ANUAL], 12)
    bt = {}
    for nombre, pares in (("corto", pares_c), ("anual", pares_a)):
        pron, real = correr_backtest(d, Y, YP, comparables, pares)
        bt[nombre] = {k: metricas(v, real, pares) for k, v in pron.items()}
        bt[nombre]["_pron"], bt[nombre]["_real"] = pron, real

    # elección: menor WAPE promedio entre los dos backtests (red), sin contar el presupuesto
    candidatos = [k for k in METODOS]
    # criterio fijado antes de mirar: promedio de los 4 WAPE (red y local, corto y anual), porque el pronóstico
    # se usa para la red (cierre, presupuesto) y para cada local (metas)
    puntaje = {k: np.mean([bt[n][k][m] for n in ("corto", "anual") for m in ("wape_red", "wape_local")]) for k in candidatos}
    elegido = min(puntaje, key=puntaje.get)

    # 2) backtest de contribución (ventas del método elegido -> contribución)
    f_eleg = METODOS[elegido][2]
    bt_c = {}
    for nombre, pares in (("corto", pares_c), ("anual", pares_a)):
        filas = {"palanca": [], "margen": [], "directo": []}
        cache = {}
        for o, t in pares:
            if o not in cache:
                H = max(tt for oo, tt in pares if oo == o) - o
                vf = f_eleg(Y, o, H, d=d)
                cache[o] = {"palanca": pronostico_contribucion(vf, d["Cc"], Y, o, d, "palanca"),
                            "margen": pronostico_contribucion(vf, d["Cc"], Y, o, d, "margen"),
                            "directo": f_eleg(np.where(d["Cc"] > 0, d["Cc"], np.nan), o, H, d=d)}
            for k in filas:
                filas[k].append(cache[o][k][:, t - o - 1])
        real = np.array([d["Cc"][comparables, t] for _, t in pares])
        res = {k: metricas(np.array(v)[:, comparables], real, pares) for k, v in filas.items()}
        res["ppto"] = metricas(np.array([d["CPc"][comparables, t] for _, t in pares]), real, pares)
        res["_pron"] = {k: np.array(v)[:, comparables] for k, v in filas.items()}
        res["_real"] = real
        bt_c[nombre] = res
    modo_c = min(("palanca", "margen"), key=lambda k: bt_c["corto"][k]["wape_red"] + bt_c["anual"][k]["wape_red"])
    e_c_abs = np.vstack([bt_c[n]["_pron"][modo_c] - bt_c[n]["_real"] for n in ("corto", "anual")])
    sc_loc_comp = np.sqrt(np.mean(e_c_abs ** 2, 0))           # RMSE de contribución de cada local, en pesos

    # 3) pronóstico final: nov-2026 a dic-2027 (14 meses), todos los locales (L05 incluido)
    H = 14
    o = T - 1
    Vf = f_eleg(Y, o, H, d=d)
    if not np.isfinite(Vf).all():   # si el método elegido no sirve para un local con poca historia (L05), regresión
        Vf = np.where(np.isfinite(Vf), Vf, regresion(Y, o, H, d, estac="grupo"))
    Cf = pronostico_contribucion(Vf, d["Cc"], Y, o, d, modo_c)
    _, beta, con_tend, claves_e = regresion(Y, o, H, d, estac="grupo", devolver_modelo=True)
    tendencia_anual = float(np.exp(beta[-1]) - 1) if con_tend else 0.0

    per_f = [str(pd.Period(d["periodos"][-1], freq="M") + h) for h in range(1, H + 1)]

    # intervalo: errores relativos del backtest (corto + anual) de la red, ver incertidumbre()
    e_v = bt["corto"][elegido]["e_rel_red"] + bt["anual"][elegido]["e_rel_red"]
    h_v = bt["corto"][elegido]["h"] + bt["anual"][elegido]["h"]
    inc_v = incertidumbre(e_v, h_v)
    e_c = bt_c["corto"][modo_c]["e_rel_red"] + bt_c["anual"][modo_c]["e_rel_red"]
    inc_c = incertidumbre(e_c, h_v)
    # por local: sigma propio del backtest (L05, sin backtest, usa la mediana de los demás)
    pron_c, real_c = bt["corto"]["_pron"][elegido], bt["corto"]["_real"]
    pron_a, real_a = bt["anual"]["_pron"][elegido], bt["anual"]["_real"]
    e_loc = np.vstack([(pron_c - real_c) / real_c, (pron_a - real_a) / real_a])
    s1_loc_comp = np.sqrt(np.mean(e_loc ** 2, 0))     # RMSE relativo de cada local
    s1_loc = np.full(n_loc, np.median(s1_loc_comp))
    s1_loc[comparables] = s1_loc_comp

    # 4) escenarios de inflación y moneda
    escen = {}
    for k, pi in ESCENARIOS_IPC.items():
        fac = (1 + pi / 100) ** np.arange(1, H + 1)
        escen[k] = {"infl_mensual": pi, "infl_anual_2027": round(((1 + pi / 100) ** 12 - 1) * 100, 1), "factor": fac.tolist()}

    # 5) presupuesto de nov-dic 2026: no está en los datos. Se completa con los supuestos del propio presupuesto:
    #    el mismo mes de 2025 del presupuesto, llevado con la relación nov/oct y dic/oct que tenía ese presupuesto
    #    (por tipo de local) y la inflación supuesta para 2026 (1,6 % mensual).
    i_oct25, i_oct26 = 11, 23
    pp_extra = {}
    for nombre, M in (("V", d["VP"]), ("C", d["CP"])):
        ext = np.zeros((n_loc, 2))
        for l in range(n_loc):
            pares_g = [j for j in comparables if d["grupo"][j] == d["grupo"][l]]
            for h, i_m25 in ((1, 12), (2, 13)):
                rel = np.nansum(M[pares_g, i_m25]) / np.nansum(M[pares_g, i_oct25])
                rel *= (1.016 / 1.018) ** h      # el ppto 2025 suponía 1,8 % mensual; el 2026, 1,6 %
                ext[l, h - 1] = M[l, i_oct26] * rel
        pp_extra[nombre] = ext

    # ---------------------------------------------------------- resumen en pesos
    idx26 = [i for i, p in enumerate(d["periodos"]) if p.startswith("2026")]
    idx25 = [i for i, p in enumerate(d["periodos"]) if p.startswith("2025")]

    def nominal(Mf, k="base"):
        return Mf * np.array(escen[k]["factor"])[None, :]

    Vn, Cn = nominal(Vf), nominal(Cf)
    real26_V, real26_C = np.nansum(d["V"][:, idx26]), np.nansum(d["C"][:, idx26])
    cierre26_V = real26_V + Vn[:, :2].sum()
    cierre26_C = real26_C + Cn[:, :2].sum()
    ppto26_V = np.nansum(d["VP"][:, idx26]) + pp_extra["V"].sum()
    ppto26_C = np.nansum(d["CP"][:, idx26]) + pp_extra["C"].sum()

    # intervalos de nov-dic y del año 2027 (supuesto conservador: los errores de los meses no se compensan)
    def intervalo(serie, inc):
        tot = float(serie.sum())
        semi = Z80 * sigma_total(inc, len(serie)) * tot
        return tot - semi, tot + semi

    red_Vn, red_Cn = Vn.sum(0), Cn.sum(0)
    hs = np.arange(1, H + 1)
    nd_V = intervalo(red_Vn[:2], inc_v)
    nd_C = intervalo(red_Cn[:2], inc_c)
    a27 = slice(2, 14)
    v27_const = Vf.sum(0)[a27].sum()
    c27_const = Cf.sum(0)[a27].sum()
    i27_Vc = intervalo(Vf.sum(0)[a27], inc_v)
    i27_Cc = intervalo(Cf.sum(0)[a27], inc_c)
    # 2026 completo en moneda constante (pesos de oct-26) para medir el crecimiento real
    v26_const = np.nansum(Y[:, idx26]) + Vf.sum(0)[:2].sum()
    c26_const = np.nansum(d["Cc"][:, idx26]) + Cf.sum(0)[:2].sum()

    escenarios = []
    for k in ("bajo", "base", "alto"):
        fac = np.array(escen[k]["factor"])
        v26n = real26_V + (Vf.sum(0)[:2] * fac[:2]).sum()
        v27n = (Vf.sum(0)[a27] * fac[a27]).sum()
        c27n = (Cf.sum(0)[a27] * fac[a27]).sum()
        crec_nom = v27n / v26n - 1
        crec_real = v27_const / v26_const - 1
        escenarios.append({"id": k, "infl_mensual": escen[k]["infl_mensual"], "infl_anual": escen[k]["infl_anual_2027"],
                           "ventas_2026": v26n, "ventas_2027": v27n, "contrib_2027": c27n,
                           "crec_nominal": crec_nom, "crec_real": crec_real,
                           "precio_pp": ((1 + crec_nom) / (1 + crec_real) - 1) * 100,
                           "efecto_precio": (1 + crec_nom) / (1 + crec_real) - 1,
                           "factor": fac.tolist(),
                           "ventas_2027_i": [i27_Vc[0] * v27n / v27_const, i27_Vc[1] * v27n / v27_const],
                           "contrib_2027_i": [i27_Cc[0] * c27n / c27_const, i27_Cc[1] * c27n / c27_const]})

    # ---------------------------------------------------------- series para el tablero (por local y red)
    sc_loc = np.full(n_loc, np.nan)
    sc_loc[comparables] = sc_loc_comp
    # L05 (sin backtest): error de contribución proporcional a sus ventas, con la relación mediana de los demás
    rel_c = np.median(sc_loc_comp / np.nanmean(Y[comparables], 1))
    for l in range(n_loc):
        if np.isnan(sc_loc[l]):
            sc_loc[l] = rel_c * np.nanmean(Vf[l])

    def m(x):
        return np.round(np.asarray(x, float) / 1e6, 2).tolist()

    def serie(filas, sig_v, sig_c_abs):
        """Historia (constante y nominal), presupuesto, pronóstico y banda 80 %, en millones."""
        S = lambda M: np.nansum(M[filas], 0) if len(filas) > 1 else M[filas[0]]
        vf, cf = Vf[filas].sum(0), Cf[filas].sum(0)
        return {
            "v_real_c": m(S(Y)), "v_ppto_c": m(S(YP)), "v_real_n": m(S(d["V"])), "v_ppto_n": m(S(d["VP"])),
            "c_real_c": m(S(d["Cc"])), "c_ppto_c": m(S(d["CPc"])), "c_real_n": m(S(d["C"])), "c_ppto_n": m(S(d["CP"])),
            "v_pron": m(vf), "v_lo": m(vf * (1 - Z80 * sig_v)), "v_hi": m(vf * (1 + Z80 * sig_v)),
            "c_pron": m(cf), "c_lo": m(cf - Z80 * sig_c_abs), "c_hi": m(cf + Z80 * sig_c_abs),
            "v25": float(np.nansum(S(Y)[idx25])) / 1e6,
            "v26": float(np.nansum(S(Y)[idx26]) + vf[:2].sum()) / 1e6, "v27": float(vf[a27].sum()) / 1e6,
            "c26": float(np.nansum(S(d["Cc"])[idx26]) + cf[:2].sum()) / 1e6, "c27": float(cf[a27].sum()) / 1e6,
            "rmse_v": float(np.mean(sig_v)),
        }

    def serie_local(l):
        return serie([l], np.full(H, s1_loc[l]), np.full(H, sc_loc[l]))

    def serie_red():
        return serie(list(range(n_loc)), sigma_mes(inc_v, hs), Cf.sum(0) * sigma_mes(inc_c, hs))

    tabla_bt = []
    for k in list(METODOS) + ["ppto"]:
        nombre, desc = (METODOS[k][0], METODOS[k][1]) if k in METODOS else (
            "Presupuesto", "Lo que se presupuestó para cada mes (en moneda constante con su propio IPC supuesto)")
        tabla_bt.append({"id": k, "nombre": nombre, "desc": desc,
                         **{f"{n}_{m}": bt[n][k][m] for n in ("corto", "anual") for m in ("wape_red", "sesgo_red", "wape_local")}})
    tabla_bt_c = []
    for k, nombre in (("palanca", "Ventas pronosticadas x margen variable − fijos"),
                      ("margen", "Ventas pronosticadas x margen promedio 12 meses"),
                      ("directo", "Mismo método aplicado directo a la contribución"),
                      ("ppto", "Presupuesto")):
        tabla_bt_c.append({"id": k, "nombre": nombre,
                           **{f"{n}_{m}": bt_c[n][k][m] for n in ("corto", "anual") for m in ("wape_red", "sesgo_red", "wape_local")}})

    # sesgo del presupuesto en nominal (lo que ve la gerencia) para los 12 meses nov-25 … oct-26
    idx_u12 = list(range(12, 24))
    bandas = bandas_control(d, comparables)
    cmp_ = np.array(comparables)   # mismos locales y mismos meses que el backtest anual
    sesgo_ppto_nom = float(np.nansum(d["VP"][cmp_][:, idx_u12]) / np.nansum(d["V"][cmp_][:, idx_u12]) - 1)
    sesgo_ppto_const = float(np.nansum(d["VPc"][cmp_][:, idx_u12]) / np.nansum(d["Vc"][cmp_][:, idx_u12]) - 1)
    sesgo_ppto_nom_c = float(np.nansum(d["CP"][cmp_][:, idx_u12]) / np.nansum(d["C"][cmp_][:, idx_u12]) - 1)

    # de dónde sale la tendencia real: tickets y ticket promedio real, últimos 12 meses contra los 12 anteriores,
    # en los locales sin señales de control (para que una obra o un problema de personal no lo tiñan)
    op = pd.read_csv(carpeta / "fact_operativo.csv")
    señal = {x["local"] for b in ("ventas", "margen") for x in bandas[b]["locales"] if x["señal"]}
    limpios = [loc.local_id[l] for l in comparables if loc.local_id[l] not in señal]
    op = op[op.local_id.isin(limpios)]
    tk = op.groupby("periodo").tickets.sum().reindex(d["periodos"]).to_numpy(float)
    vl = np.nansum(Y[[list(loc.local_id).index(x) for x in limpios]], 0)
    tickets_yoy = float(tk[12:].sum() / tk[:12].sum() - 1)
    ticket_real_yoy = float((vl[12:].sum() / tk[12:].sum()) / (vl[:12].sum() / tk[:12].sum()) - 1)

    # cuánto vale arreglar L07: margen 2025 contra margen pronosticado 2027, por las ventas 2027 (moneda constante)
    l7 = list(loc.local_id).index("L07")
    marg25_l7 = np.nansum(d["Cc"][l7, idx25]) / np.nansum(Y[l7, idx25])
    marg27_l7 = Cf[l7, a27].sum() / Vf[l7, a27].sum()
    l07_valor = float((marg25_l7 - marg27_l7) * Vf[l7, a27].sum())
    pos = {c: i for i, c in enumerate(claves_e)}
    estac_grupo = {}
    for g in ("urbano", "ruta"):
        coefs = np.array([0.0] + [beta[n_loc + pos[(g, m)]] for m in range(2, 13)])
        fac = np.exp(coefs)
        estac_grupo[g] = np.round(fac / fac.mean(), 4).tolist()

    resultados = {
        "periodos": d["periodos"], "periodos_f": per_f,
        "locales": [{"id": r.local_id, "nombre": r.local, "region": r.region, "formato": r.formato,
                     "apertura": r.apertura, "comparable": i in comparables} for i, r in loc.iterrows()],
        "ipc": d["ipc"].tolist(), "ipc_ppto": d["ipc_ppto"].tolist(), "infl": d["infl"].tolist(),
        "metodo_elegido": elegido, "metodo_elegido_nombre": METODOS[elegido][0],
        "modo_contribucion": modo_c,
        "backtest": tabla_bt, "backtest_contrib": tabla_bt_c,
        "backtest_diseno": {
            "corto": {"cortes": [d["periodos"][o] for o in ORIGENES_CORTO], "horizonte": HORIZONTE_CORTO, "pares": len(pares_c)},
            "anual": {"corte": d["periodos"][ORIGEN_ANUAL], "meses": [d["periodos"][t] for _, t in pares_a]}},
        "incertidumbre_ventas": inc_v, "incertidumbre_contrib": inc_c,
        "tendencia_anual_real": tendencia_anual, "estacionalidad": estac_grupo,
        "series": {"red": serie_red(), **{loc.local_id[l]: serie_local(l) for l in range(n_loc)}},
        "resumen": {
            "real26_V_ene_oct": real26_V, "real26_C_ene_oct": real26_C,
            "novdic_V": float(red_Vn[:2].sum()), "novdic_V_i": list(nd_V),
            "novdic_C": float(red_Cn[:2].sum()), "novdic_C_i": list(nd_C),
            "cierre26_V": cierre26_V, "cierre26_C": cierre26_C,
            "cierre26_V_i": [real26_V + nd_V[0], real26_V + nd_V[1]],
            "cierre26_C_i": [real26_C + nd_C[0], real26_C + nd_C[1]],
            "ppto26_V": ppto26_V, "ppto26_C": ppto26_C,
            "ppto_novdic_V": float(pp_extra["V"].sum()), "ppto_novdic_C": float(pp_extra["C"].sum()),
            "v26_const": v26_const, "c26_const": c26_const,
            "v27_const": v27_const, "v27_const_i": list(i27_Vc),
            "c27_const": c27_const, "c27_const_i": list(i27_Cc),
            "v25_const": float(np.nansum(Y[:, idx25])),
            "v26_const_mismos": float(np.nansum(Y[comparables][:, idx26]) + Vf[comparables, :2].sum()),
            "v27_const_mismos": float(Vf[comparables][:, a27].sum()),
            "sesgo_ppto_nominal_12m": sesgo_ppto_nom, "sesgo_ppto_constante_12m": sesgo_ppto_const,
            "infl_ultimos_12m": float(np.prod(1 + d["infl"][12:] / 100) - 1),
            "infl_supuesta_ppto_12m": float(d["ipc_ppto"][23] / d["ipc_ppto"][11] - 1),
            "sesgo_ppto_contrib_nominal_12m": sesgo_ppto_nom_c,
            "locales_sin_señal": limpios, "tickets_yoy": tickets_yoy, "ticket_real_yoy": ticket_real_yoy,
            "l07_margen_2025": float(marg25_l7), "l07_margen_2027": float(marg27_l7), "l07_valor_2027": l07_valor,
        },
        "escenarios": escenarios,
        "bandas": bandas,
        "contra_ppto": desvio_contra_ppto(d, comparables),
        "incidentes": incidentes_clave(carpeta, d),
    }
    SALIDA.mkdir(exist_ok=True)

    def limpiar(o_):
        if isinstance(o_, dict):
            return {k: limpiar(v) for k, v in o_.items() if not k.startswith("_")}
        if isinstance(o_, (list, tuple)):
            return [limpiar(v) for v in o_]
        if isinstance(o_, (np.floating, float)):
            return None if np.isnan(o_) else round(float(o_), 6)
        if isinstance(o_, np.integer):
            return int(o_)
        if isinstance(o_, np.bool_):
            return bool(o_)
        return o_

    (SALIDA / "resultados.json").write_text(json.dumps(limpiar(resultados), ensure_ascii=False, indent=1), encoding="utf-8")

    # CSV para mirar en Excel
    filas = []
    for l in range(n_loc):
        for h in range(H):
            filas.append((per_f[h], loc.local_id[l], Vf[l, h], Cf[l, h], Vn[l, h], Cn[l, h]))
    pd.DataFrame(filas, columns=["periodo", "local_id", "ventas_const_oct26", "contrib_const_oct26",
                                 "ventas_nominal_base", "contrib_nominal_base"]).round(0).to_csv(
        SALIDA / "pronostico_mensual.csv", index=False)

    # ---------------------------------------------------------- consola
    M = 1e6
    print(f"Datos: {carpeta}")
    print("\nBacktest de VENTAS (moneda constante; error = pronóstico − real)")
    print(f"{'método':52s} {'WAPE corto':>10s} {'sesgo':>7s} {'WAPE anual':>10s} {'sesgo':>7s} {'WAPE local c/a':>15s}")
    for f in tabla_bt:
        print(f"{f['nombre']:52s} {f['corto_wape_red']*100:9.1f}% {f['corto_sesgo_red']*100:+6.1f}% "
              f"{f['anual_wape_red']*100:9.1f}% {f['anual_sesgo_red']*100:+6.1f}% "
              f"{f['corto_wape_local']*100:6.1f}%/{f['anual_wape_local']*100:5.1f}%")
    print(f"Elegido: {METODOS[elegido][0]}")
    print("\nBacktest de CONTRIBUCIÓN")
    for f in tabla_bt_c:
        print(f"{f['nombre']:52s} {f['corto_wape_red']*100:9.1f}% {f['corto_sesgo_red']*100:+6.1f}% "
              f"{f['anual_wape_red']*100:9.1f}% {f['anual_sesgo_red']*100:+6.1f}%")
    print(f"Contribución: modo {modo_c}. Incertidumbre ventas {inc_v}, contribución {inc_c}")
    r = resultados["resumen"]
    print(f"\nCierre 2026 ventas  {cierre26_V/M:,.0f} M (ppto {ppto26_V/M:,.0f} M, {cierre26_V/ppto26_V*100-100:+.1f} %)")
    print(f"Cierre 2026 contrib {cierre26_C/M:,.0f} M (ppto {ppto26_C/M:,.0f} M, {cierre26_C/ppto26_C*100-100:+.1f} %)")
    print(f"2027 ventas constantes (oct-26) {v27_const/M:,.0f} M [{i27_Vc[0]/M:,.0f} – {i27_Vc[1]/M:,.0f}] vs 2026 {v26_const/M:,.0f} M ({v27_const/v26_const*100-100:+.1f} %)")
    print(f"2027 contribución constante {c27_const/M:,.0f} M [{i27_Cc[0]/M:,.0f} – {i27_Cc[1]/M:,.0f}] vs 2026 {c26_const/M:,.0f} M")
    for e in escenarios:
        print(f"  IPC {e['id']:5s} {e['infl_mensual']} %/mes: ventas 2027 {e['ventas_2027']/M:,.0f} M, nominal {e['crec_nominal']*100:+.1f} %, real {e['crec_real']*100:+.1f} %, precio {e['precio_pp']:.1f} p.p.")
    print(f"Sesgo ppto 12m: nominal {sesgo_ppto_nom*100:+.1f} %, constante {sesgo_ppto_const*100:+.1f} %; tendencia real {tendencia_anual*100:+.1f} %/año")
    for k, b in resultados["bandas"].items():
        print(f"\nBandas {k}: centro {b['centro']:.2f}, desvío robusto {b['sd']:.2f} (clásico {b['sd_clasico']:.2f})")
        for x in b["locales"]:
            if x["señal"] or x["fuera_2"]:
                reglas = sorted({rr for rs in x["reglas"] for rr in rs})
                print(f"  {x['local']}: fuera de ±2: {x['fuera_2']} meses; reglas {reglas}")
    cp = resultados["contra_ppto"]
    print("\nRegla ±5 % contra ppto (meses fuera, nominal/constante):", {x["local"]: (x["meses_fuera_nominal"], x["meses_fuera_constante"]) for x in cp})
    print(f"\nOK {SALIDA / 'resultados.json'}")
    return resultados


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datos", help="carpeta con los CSV del Caso 05")
    main(ap.parse_args().datos)
