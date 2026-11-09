"""Controles de los datos del Caso 05: integridad, que cada número se pueda rastrear, y que las historias plantadas aparezcan.

Uso:  python validar_datos.py
"""
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent.parent / "01_datos"
leer = lambda n: pd.read_csv(D / f"{n}.csv")
loc, rub, cal = leer("dim_local"), leer("dim_rubro"), leer("dim_calendario")
res, op, nom, inc = leer("fact_resultados"), leer("fact_operativo"), leer("fact_nomina"), leer("fact_incidentes")

errores = []
def control(ok, texto):
    print(("OK   " if ok else "FALLA"), texto)
    if not ok:
        errores.append(texto)

# 1. Integridad
control(res.local_id.isin(loc.local_id).all() and res.rubro_id.isin(rub.rubro_id).all(), "Claves de resultados existen en las dimensiones")
control(res.periodo.isin(cal.periodo).all(), "Todos los períodos están en el calendario")
control(not res.duplicated(["periodo", "local_id", "rubro_id"]).any(), "Sin filas duplicadas en resultados")
control((res[["real", "presupuesto"]].fillna(0) >= 0).all().all(), "Importes no negativos (el signo lo da dim_rubro)")
control(res.real.notna().all() and res.presupuesto.notna().all(), "Real y presupuesto completos en todas las filas")

# 2. Trazabilidad: Personal del resultado = suma de la nómina; Ventas = tickets x ticket (aprox.)
pers = res[res.rubro_id == 3].set_index(["periodo", "local_id"]).real
suma_nom = nom.groupby(["periodo", "local_id"]).costo_total.sum()
control((pers - suma_nom).abs().max() == 0, "Personal (resultado) = suma exacta de fact_nomina")
ven = res[res.rubro_id == 1].set_index(["periodo", "local_id"]).real
calc = op.set_index(["periodo", "local_id"]).eval("tickets * ticket_promedio")
control(((ven - calc).abs() / ven).max() < 0.001, "Ventas = tickets x ticket promedio (dif. < 0,1 %)")

# 3. Historias plantadas
r = res.merge(rub, on="rubro_id").merge(loc[["local_id", "region"]], on="local_id")
r["real_s"], r["ppto_s"] = r.real * r.signo, r.presupuesto * r.signo
def pct(df, rubro):
    v = df[df.rubro == "Ventas"].real.sum()
    return df[df.rubro == rubro].real.sum() / v

l07 = r[r.local_id == "L07"]
control(pct(l07[l07.periodo >= "2026-01"], "Personal") - pct(l07[(l07.periodo >= "2025-01") & (l07.periodo < "2026-01")], "Personal") > 0.02,
        "L07: el costo de personal sube más de 2 p.p. de las ventas desde ene-2026")
t03 = op[op.local_id == "L03"].set_index("periodo").tickets
control(t03["2026-03":"2026-08"].mean() < 0.85 * t03["2025-03":"2025-08"].mean(), "L03: tickets de mar-ago 2026 caen más del 15 % contra 2025")
l10 = r[(r.local_id == "L10")]
control(pct(l10[l10.periodo == "2026-06"], "Costo de mercadería") > pct(l10[l10.periodo == "2026-05"], "Costo de mercadería") + 0.04,
        "L10: el costo de mercadería salta en jun-2026 (rotura de cámara de frío)")

a26 = r[(r.periodo >= "2026-01")]
ventas_real, ventas_ppto = a26[a26.rubro == "Ventas"].real.sum(), a26[a26.rubro == "Ventas"].presupuesto.sum()
control(ventas_real > ventas_ppto, "Red 2026: ventas nominales ARRIBA del presupuesto (efecto inflación)")
c = cal.set_index("periodo")
defl = lambda df, col, idx: (df[col] / df.periodo.map(c[idx]) * 100).sum()
v26 = a26[a26.rubro == "Ventas"]
control(defl(v26, "real", "ipc_indice") < defl(v26, "presupuesto", "ipc_ppto_indice"),
        "Red 2026: en moneda constante las ventas quedan ABAJO del presupuesto (la trampa)")
tk_real = op[op.periodo >= "2026-01"].tickets.sum()
print(f"     Tickets 2026 real: {tk_real:,.0f}")

# 4. Resumen para mirar
print("\nRESUMEN 2026 (ene-oct) por local, en millones de ARS nominales")
cont = a26.groupby("local_id")[["real_s", "ppto_s"]].sum() / 1e6
vent = a26[a26.rubro == "Ventas"].groupby("local_id")[["real", "presupuesto"]].sum() / 1e6
tabla = pd.DataFrame({"ventas": vent.real, "contrib": cont.real_s, "contrib_ppto": cont.ppto_s})
tabla["margen_%"] = 100 * tabla.contrib / tabla.ventas
tabla["desvio_contrib"] = tabla.contrib - tabla.contrib_ppto
print(tabla.round(1).sort_values("desvio_contrib").to_string())
tot = tabla[["ventas", "contrib", "contrib_ppto", "desvio_contrib"]].sum()
print(f"\nRed: ventas {tot.ventas:,.0f} M · contribución {tot.contrib:,.0f} M ({100*tot.contrib/tot.ventas:.1f} %) · "
      f"desvío contra ppto {tot.desvio_contrib:+,.0f} M")
print(f"Incidentes registrados: {len(inc)}")
print("\nRESULTADO:", "TODO OK" if not errores else f"{len(errores)} controles fallaron")
