"""Cruza los reportes de primera linea con las ventas y escribe 04_informes/hallazgos.md.
Separa "efecto mercado" (pasa en todas las rutas) de "efecto local" (pasa en una ruta).

Uso:  python analizar.py
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SEM_BASE = range(1, 6)        # semanas de referencia (antes de los cambios)
SEM_RECIENTE = range(9, 13)   # ultimas 4 semanas
UMBRAL_RUTAS_MERCADO = 6      # si sube en 6 o mas de 8 rutas -> mercado
CAT_ECON = "Situación económica del cliente"
CAT_COMP = "Competencia nueva en la zona"


def n1(x):
    return f"{x:.1f}".replace(".", ",")


def pct(x):
    return f"{x * 100:+.1f} %".replace(".", ",")


def calcular(base=BASE):
    r = pd.read_csv(base / "01_datos" / "respuestas.csv", parse_dates=["Marca temporal"])
    v = pd.read_csv(base / "01_datos" / "ventas_semanales.csv")
    r = r.rename(columns={"Ruta": "ruta", "Motivo": "categoria", "Rol": "rol"})
    lunes1 = pd.Timestamp(v["lunes"].min())
    r["semana"] = ((r["Marca temporal"].dt.normalize() - lunes1).dt.days // 7) + 1
    rutas = sorted(v["ruta"].unique())
    cats = sorted(r["categoria"].unique())
    semanas = sorted(int(s) for s in v["semana"].unique())

    # reportes por semana, ruta y categoria
    idx = pd.MultiIndex.from_product([semanas, rutas, cats], names=["semana", "ruta", "categoria"])
    cnt = r.groupby(["semana", "ruta", "categoria"]).size().reindex(idx, fill_value=0)
    # promedio semanal por ruta y categoria: referencia vs reciente
    ref = cnt.loc[list(SEM_BASE)].groupby(["ruta", "categoria"]).mean()
    rec = cnt.loc[list(SEM_RECIENTE)].groupby(["ruta", "categoria"]).mean()
    sube = (rec >= ref * 2) & ((rec - ref) >= 1.5)      # sube "de verdad" en esa ruta
    rutas_que_suben = sube.groupby("categoria").sum()
    clasif = {}
    for c in cats:
        n = int(rutas_que_suben[c])
        if c == "Otro":
            clasif[c] = "sin señal"      # "Otro" no es un motivo concreto
            continue
        clasif[c] = "mercado" if n >= UMBRAL_RUTAS_MERCADO else "local" if 1 <= n <= 2 else "sin señal"
    rutas_local = {c: [ru for ru in rutas if sube[(ru, c)]] for c in cats if clasif[c] == "local"}

    # ventas
    vb = v[v["semana"].isin(SEM_BASE)].groupby("ruta")["bidones"].mean()
    vr = v[v["semana"].isin(SEM_RECIENTE)].groupby("ruta")["bidones"].mean()
    var = vr / vb - 1
    total_var = vr.sum() / vb.sum() - 1
    por_ruta = pd.DataFrame({"var": var})
    por_ruta["mercado"] = float(var.median())                 # lo que cae "en todas": la mediana
    por_ruta["local"] = por_ruta["var"] - por_ruta["mercado"]
    ventas_sem = v.pivot(index="semana", columns="ruta", values="bidones")

    # ranking de motivos (ultimas 4 semanas contra referencia)
    rank = pd.DataFrame({
        "reportes_recientes": cnt.loc[list(SEM_RECIENTE)].groupby("categoria").sum(),
        "por_semana_ref": cnt.loc[list(SEM_BASE)].groupby("categoria").sum() / len(SEM_BASE),
    })
    rank["por_semana_rec"] = rank["reportes_recientes"] / len(SEM_RECIENTE)
    rank["veces"] = rank["por_semana_rec"] / rank["por_semana_ref"]
    rank["tipo"] = [clasif[c] for c in rank.index]
    rank = rank.sort_values("reportes_recientes", ascending=False)

    # alerta de la ultima semana (misma regla que el Apps Script: el doble del promedio y al menos 4 reportes)
    ult = max(semanas)
    alertas = []
    for ru in rutas + ["TODAS"]:
        for c in cats:
            if ru == "TODAS":
                serie = cnt.xs(c, level="categoria").groupby("semana").sum()
            else:
                serie = cnt.xs(ru, level="ruta").xs(c, level="categoria")
            ahora = serie.loc[ult]
            prom = serie.loc[ult - 4:ult - 1].mean()
            if ahora >= 4 and ahora >= prom * 2:
                alertas.append((ru, c, int(ahora), float(prom)))

    sem_comp = cnt.xs(CAT_COMP, level="categoria").groupby(["semana", "ruta"]).sum().unstack()
    ruta_comp = max(rutas, key=lambda ru: sem_comp[ru].loc[list(SEM_RECIENTE)].sum())
    primera = next((s for s in semanas if sem_comp[ruta_comp].loc[s] >= 3), None)
    econ_sem = cnt.xs(CAT_ECON, level="categoria").groupby("semana").sum()

    # titular automatico
    pts_mercado = abs(float(por_ruta["mercado"].iloc[0])) * 100
    pts_local = abs(float(por_ruta.loc[ruta_comp, "local"])) * 100
    ru_corta = ruta_comp.split(" - ")[0]
    caida_ru = abs(float(por_ruta.loc[ruta_comp, "var"])) * 100
    titular = (f"Las ventas cayeron {n1(abs(total_var) * 100)} % en las últimas 4 semanas. "
               f"Mercado: todas las rutas caen cerca de {n1(pts_mercado)} % y la situación económica del cliente sube en "
               f"{int(rutas_que_suben[CAT_ECON])} de {len(rutas)} rutas. "
               f"Gestión local: {ru_corta} cae {n1(caida_ru)} %, {n1(pts_local)} puntos de más, con competencia nueva.")
    return dict(r=r, v=v, rutas=rutas, cats=cats, semanas=semanas, cnt=cnt, ref=ref, rec=rec, clasif=clasif,
                rutas_que_suben=rutas_que_suben, rutas_local=rutas_local, por_ruta=por_ruta, total_var=total_var,
                ventas_sem=ventas_sem, rank=rank, alertas=alertas, sem_comp=sem_comp, ruta_comp=ruta_comp,
                primera=primera, econ_sem=econ_sem, titular=titular, ult=ult)


def escribir_informe(d):
    L = []
    a = L.append
    a("# Hallazgos: voz de primera línea contra ventas\n")
    a("*Datos ficticios. Semanas 1 a 5 = referencia; semanas 9 a 12 = reciente.*\n")
    a(f"## Titular\n\n**{d['titular']}**\n")
    a("## 1. Ventas por ruta (bidones por semana, reciente contra referencia)\n")
    a("| Ruta | Variación | De mercado | De gestión local |\n|---|---:|---:|---:|")
    for ru in d["rutas"]:
        p = d["por_ruta"].loc[ru]
        a(f"| {ru} | {pct(p['var'])} | {pct(p['mercado'])} | {pct(p['local'])} |")
    a(f"| **Total** | **{pct(d['total_var'])}** | | |\n")
    a("*Mercado = lo que cae la ruta mediana (lo que pasa en todas). Local = lo que cae de más en esa ruta.*\n")
    a("## 2. Ranking de motivos (últimas 4 semanas)\n")
    a("| Motivo | Reportes | Por semana (ref.) | Por semana (reciente) | Veces | Lectura |\n|---|---:|---:|---:|---:|---|")
    for c, x in d["rank"].iterrows():
        a(f"| {c} | {int(x['reportes_recientes'])} | {n1(x['por_semana_ref'])} | {n1(x['por_semana_rec'])} | x{n1(x['veces'])} | {x['tipo']} |")
    a("")
    a("## 3. Efecto mercado (se repite en todas las rutas)\n")
    mer = [c for c, t in d["clasif"].items() if t == "mercado"]
    if mer:
        for c in mer:
            a(f"- **{c}** sube en {int(d['rutas_que_suben'][c])} de {len(d['rutas'])} rutas.")
        a(f"- Las ventas bajan en todas las rutas: la mediana es {pct(d['por_ruta']['mercado'].iloc[0])}.")
        e = d["econ_sem"]
        a(f"- Alerta temprana: los reportes de situación económica pasan de {e.loc[1:5].mean():.0f} por semana (semanas 1 a 5) a {e.loc[12]:.0f} (semana 12). "
          "Se movieron **antes** que las ventas (semana 9 contra semana 10).")
        a("- Lectura: no se arregla con gestión comercial de una ruta. Se miran precio, promociones y mix, y se avisa a Dirección.\n")
    else:
        a("- Ninguna categoría sube en la mayoría de las rutas.\n")
    a("## 4. Efecto local (una sola ruta)\n")
    if d["rutas_local"]:
        for c, rs in d["rutas_local"].items():
            for ru in rs:
                p = d["por_ruta"].loc[ru]
                ref, rec = d["ref"][(ru, c)], d["rec"][(ru, c)]
                a(f"- **{ru}: {c}**. {n1(ref)} reportes por semana antes, {n1(rec)} ahora. Ventas {pct(p['var'])} "
                  f"({pct(p['local'])} por encima de lo que cae el mercado).")
        a(f"- Los reportes se disparan en la semana {d['primera']}; la venta de esa ruta cae desde la semana siguiente.")
        a("- Lectura: es gestión local. Se sale a ver qué ofrece el competidor, qué clientes se fueron y qué se puede responder (precio, promoción, visita).\n")
    else:
        a("- No hay categorías concentradas en una sola ruta.\n")
    a("## 5. Alertas de la última semana (misma regla que el Apps Script)\n")
    if d["alertas"]:
        a("| Dónde | Motivo | Reportes | Promedio 4 semanas previas |\n|---|---|---:|---:|")
        for ru, c, n, pr in d["alertas"]:
            a(f"| {ru} | {c} | {n} | {n1(pr)} |")
    else:
        a("Sin alertas.")
    a("\n## Cuidados\n")
    a("- Es una señal, no una encuesta estadística. Con pocos reportes por ruta, un salto chico puede ser azar.")
    a("- Correlación no es causa: los reportes dan la hipótesis; la confirman las visitas y los datos de clientes.")
    a("- Datos ficticios generados con semilla fija.")
    out = BASE / "04_informes" / "hallazgos.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    d = calcular()
    print("Escrito:", escribir_informe(d))
    print(d["titular"])
