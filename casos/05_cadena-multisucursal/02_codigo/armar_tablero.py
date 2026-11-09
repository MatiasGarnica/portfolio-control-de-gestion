"""Arma 03_tableros/tablero_direccion.html: toma los CSV de 01_datos y los mete en la plantilla.

Uso:  python armar_tablero.py
Nota de seguridad: este HTML lleva TODOS los datos adentro (sirve para el portfolio porque son ficticios).
En una empresa real, el filtro por usuario va en la base, no en la página (ver PLAN, "Limitaciones y seguridad").
"""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
D = BASE / "01_datos"
leer = lambda n: pd.read_csv(D / f"{n}.csv")

loc, rub, cal = leer("dim_local"), leer("dim_rubro"), leer("dim_calendario")
res, op, nom, inc = leer("fact_resultados"), leer("fact_operativo"), leer("fact_nomina"), leer("fact_incidentes")

pi = {p: i for i, p in enumerate(cal.periodo)}
li = {l: i for i, l in enumerate(loc.local_id)}
puestos = list(dict.fromkeys(nom.puesto))

data = {
    "locales": loc[["local_id", "local", "region", "formato", "m2", "apertura"]].values.tolist(),
    "rubros": rub[["rubro_id", "rubro", "signo", "grupo_puente"]].values.tolist(),
    "cal": cal[["periodo", "ipc_indice", "ipc_ppto_indice"]].values.tolist(),
    "res": [[pi[r.periodo], li[r.local_id], int(r.rubro_id), int(r.real), int(r.presupuesto)] for r in res.itertuples()],
    "op": [[pi[r.periodo], li[r.local_id], int(r.tickets), int(r.ticket_promedio), int(r.dotacion),
            int(r.horas_trabajadas), int(r.bajas_personal), int(r.tickets_ppto), int(r.ticket_promedio_ppto)]
           for r in op.itertuples()],
    "puestos": puestos,
    "nom": [[pi[r.periodo], li[r.local_id], puestos.index(r.puesto), int(r.dotacion), int(r.horas_normales),
             int(r.horas_extra), int(r.costo_total)] for r in nom.itertuples()],
    "inc": [[r.fecha, li[r.local_id], r.tipo, int(r.horas_afectadas), r.detalle] for r in inc.itertuples()],
}

plantilla = (Path(__file__).parent / "tablero_plantilla.html").read_text(encoding="utf-8")
html = plantilla.replace("/*__DATOS__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
destino = BASE / "03_tableros" / "tablero_direccion.html"
destino.write_text(html, encoding="utf-8")
print(f"OK {destino} ({destino.stat().st_size / 1024:.0f} KB)")
