"""Calcula el costo de servir de cada cliente (Caso 07) y deja salida/resultados.json para el tablero.

Uso:
  python costo_servir.py              (lee ../01_datos; si no hay CSV, corre generar_datos.py)
  python costo_servir.py --datos RUTA

Método (detalle en 07_docs/metodo_y_criterios.md):
  1. Cada cuenta de costo va a una actividad: preparación, reparto o estructura.
  2. Cada actividad se reparte con su driver: pedidos, bultos, visitas, km.
     Tasa = costo de la actividad ÷ cantidad total del driver.
  3. Se suman el costo financiero (saldo × tasa mensual) y el de las devoluciones.
  4. Margen bruto − costo de servir = contribución del cliente. La estructura no se asigna.
Montos en miles de pesos de octubre de 2026; promedios mensuales del semestre mayo-octubre.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida" / "resultados.json"

# Criterios (se discuten en el documento de método)
PREP_POR_PEDIDO = 0.55     # relevamiento de tiempos: 55 % del tiempo del depósito es fijo por pedido
REPARTO_EN_PARADA = 0.50   # choferes y camiones: mitad del tiempo en la parada, mitad manejando
KM_URGENTE = 3.0           # un urgente es un viaje dedicado: unas 3 veces el km de desvío
TASA_FIN = 0.03            # costo del dinero, mensual (descubierto bancario ficticio)
COSTO_DEV = 0.30           # costo de una devolución: 20 % merma + 10 % manipuleo y re-entrega


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def costear(c, t, ped=None, dias=None, urg=None, bultos=None):
    ped = c["pedidos"] if ped is None else ped
    dias = c["dias_cobro"] if dias is None else dias
    urg = c["urgentes"] if urg is None else urg
    bultos = c["bultos"] if bultos is None else bultos
    visitas = ped + urg
    km = ped * c["km_desvio"] + urg * c["km_desvio"] * KM_URGENTE
    r = dict(
        prep=ped * t["pedido"] + bultos * t["bulto"],
        entrega=visitas * t["visita"] + km * t["km"],
        fin=c["ventas"] * dias / 30 * TASA_FIN,
        dev=c["devoluciones"] * COSTO_DEV,
    )
    r["cts"] = sum(r.values())
    r["contrib"] = c["mb"] - r["cts"]
    return r


def main(datos=None):
    d = Path(datos) if datos else AQUI.parent / "01_datos"
    if not (d / "clientes.csv").exists():
        sys.path.insert(0, str(AQUI))
        import generar_datos
        generar_datos.main(d)
    cli = {r["cliente_id"]: r for r in leer(d / "clientes.csv")}
    mov = leer(d / "movimientos_mensuales.csv")
    cos = leer(d / "costos_operativos.csv")
    meses = sorted({r["mes"] for r in mov})
    nm = len(meses)

    # 1. Agregados por cliente (promedio mensual)
    acc = defaultdict(lambda: defaultdict(float))
    for r in mov:
        a = acc[r["cliente_id"]]
        for k in ("ventas", "costo_mercaderia", "pedidos", "bultos", "urgentes", "devoluciones"):
            a[k] += float(r[k]) / nm
    clientes = []
    for cid, a in acc.items():
        c = cli[cid]
        clientes.append(dict(id=cid, n=c["cliente"], tipo=c["tipo"], zona=c["zona"], km_desvio=float(c["km_desvio"]),
                             dias_cobro=int(c["dias_cobro"]), ventas=a["ventas"], mb=a["ventas"] - a["costo_mercaderia"],
                             pedidos=a["pedidos"], bultos=a["bultos"], urgentes=a["urgentes"], devoluciones=a["devoluciones"]))

    # 2. Costos por actividad (promedio mensual) y tasas por driver
    pool = defaultdict(float)
    cuentas = defaultdict(float)
    for r in cos:
        pool[r["actividad"]] += float(r["monto"]) / nm
        cuentas[(r["cuenta"], r["actividad"])] += float(r["monto"]) / nm
    tot = dict(pedidos=sum(c["pedidos"] for c in clientes), bultos=sum(c["bultos"] for c in clientes),
               visitas=sum(c["pedidos"] + c["urgentes"] for c in clientes),
               km=sum(c["pedidos"] * c["km_desvio"] + c["urgentes"] * c["km_desvio"] * KM_URGENTE for c in clientes),
               ventas=sum(c["ventas"] for c in clientes), mb=sum(c["mb"] for c in clientes))
    prep, rep, rep_km, estr = pool["Preparación"], pool["Reparto"], pool["Reparto · km"], pool["Estructura"]
    t = dict(pedido=prep * PREP_POR_PEDIDO / tot["pedidos"], bulto=prep * (1 - PREP_POR_PEDIDO) / tot["bultos"],
             visita=rep * REPARTO_EN_PARADA / tot["visitas"], km=(rep * (1 - REPARTO_EN_PARADA) + rep_km) / tot["km"])
    tasas = [
        dict(act="Preparación", driver="pedido", base=f"{PREP_POR_PEDIDO:.0%} del depósito", costo=prep * PREP_POR_PEDIDO, cant=tot["pedidos"], tasa=t["pedido"], unidad="por pedido"),
        dict(act="Preparación", driver="bulto", base=f"{1 - PREP_POR_PEDIDO:.0%} del depósito", costo=prep * (1 - PREP_POR_PEDIDO), cant=tot["bultos"], tasa=t["bulto"], unidad="por bulto"),
        dict(act="Reparto", driver="visita", base=f"{REPARTO_EN_PARADA:.0%} de choferes y camiones", costo=rep * REPARTO_EN_PARADA, cant=tot["visitas"], tasa=t["visita"], unidad="por visita"),
        dict(act="Reparto", driver="km", base=f"{1 - REPARTO_EN_PARADA:.0%} de choferes y camiones + combustible y mantenimiento", costo=rep * (1 - REPARTO_EN_PARADA) + rep_km, cant=tot["km"], tasa=t["km"], unidad="por km"),
    ]

    # 3. Costo de servir por cliente
    for c in clientes:
        c.update(costear(c, t))
        c["pct"] = c["contrib"] / c["ventas"]
        c["mb_pct"] = c["mb"] / c["ventas"]
        c["bxp"] = c["bultos"] / c["pedidos"]
    clientes.sort(key=lambda c: -c["contrib"])
    for i, c in enumerate(clientes, 1):
        c["rk"] = i
    for i, c in enumerate(sorted(clientes, key=lambda c: -c["mb"]), 1):
        c["rk_mb"] = i

    # 4. Prorrateo por ventas (lo habitual) contra el costeo por actividad
    cts_total = sum(c["cts"] for c in clientes)
    for c in clientes:
        c["cts_prorr"] = cts_total * c["ventas"] / tot["ventas"]
        c["contrib_prorr"] = c["mb"] - c["cts_prorr"]
    ocultos = [c for c in clientes if c["contrib"] < 0 <= c["contrib_prorr"]]

    # 5. Curva de ballena: contribución acumulada con los clientes ordenados de mejor a peor
    contrib_total = sum(c["contrib"] for c in clientes)
    acum, curva = 0.0, [dict(x=0, y=0)]
    for i, c in enumerate(clientes, 1):
        acum += c["contrib"]
        curva.append(dict(x=i / len(clientes), y=acum / contrib_total, id=c["id"]))
    pico = max(curva, key=lambda p: p["y"])

    def agrupar(campo):
        g = defaultdict(lambda: defaultdict(float))
        for c in clientes:
            x = g[c[campo]]
            x["n"] += 1
            x["neg"] += c["contrib"] < 0
            for k in ("ventas", "mb", "prep", "entrega", "fin", "dev", "cts", "contrib", "pedidos", "bultos"):
                x[k] += c[k]
        return [dict(nombre=k, **v) for k, v in sorted(g.items(), key=lambda kv: -kv[1]["contrib"])]

    negativos = [c for c in clientes if c["contrib"] < 0]
    res = dict(
        meta=dict(empresa="Mayorista Ruta Sur", periodo=f"{meses[0]} a {meses[-1]}", meses=nm, clientes=len(clientes),
                  criterios=dict(prep_por_pedido=PREP_POR_PEDIDO, reparto_en_parada=REPARTO_EN_PARADA, km_urgente=KM_URGENTE,
                                 tasa_fin=TASA_FIN, costo_dev=COSTO_DEV)),
        totales=dict(ventas=tot["ventas"], mb=tot["mb"], prep=sum(c["prep"] for c in clientes), entrega=sum(c["entrega"] for c in clientes),
                     fin=sum(c["fin"] for c in clientes), dev=sum(c["dev"] for c in clientes), cts=cts_total, contrib=contrib_total,
                     estructura=estr, resultado=contrib_total - estr, pedidos=tot["pedidos"], bultos=tot["bultos"], visitas=tot["visitas"], km=tot["km"],
                     negativos=len(negativos), perdida_negativos=sum(c["contrib"] for c in negativos),
                     ventas_negativos=sum(c["ventas"] for c in negativos), pico=pico, ocultos=len(ocultos)),
        pools=dict(prep=prep, rep=rep, rep_km=rep_km, estr=estr, camiones=5),
        tasas=tasas,
        cuentas=[dict(cuenta=k[0], actividad=k[1], monto=v) for k, v in cuentas.items()],
        tipos=agrupar("tipo"), zonas=agrupar("zona"),
        curva=curva, clientes=clientes,
    )
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    T = res["totales"]
    print(f"Ventas {T['ventas']:,.0f} · MB {T['mb']:,.0f} ({T['mb']/T['ventas']:.1%}) · costo de servir {T['cts']:,.0f} ({T['cts']/T['ventas']:.1%})")
    print(f"Contribución {T['contrib']:,.0f} ({T['contrib']/T['ventas']:.1%}) · estructura {T['estructura']:,.0f} · resultado {T['resultado']:,.0f}")
    print(f"Clientes con contribución negativa: {T['negativos']} (pierden {T['perdida_negativos']:,.0f}/mes) · ocultos por el prorrateo: {T['ocultos']}")
    print(f"Pico de la curva: {pico['y']:.0%} con el {pico['x']:.0%} de los clientes")
    print("Tasas:", {k: round(v, 3) for k, v in t.items()})
    for g in res["tipos"]:
        print(f"  {g['nombre']:<13} n={g['n']:.0f} neg={g['neg']:.0f} contrib={g['contrib']:,.0f} ({g['contrib']/g['ventas']:.1%}) MB {g['mb']/g['ventas']:.1%}")
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datos")
    main(ap.parse_args().datos)
