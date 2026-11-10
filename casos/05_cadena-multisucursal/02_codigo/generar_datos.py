"""Genera los datos ficticios del Caso 05: una cadena de comida rápida con 12 locales en 3 regiones.

Todo es inventado ("Cadena Demo S.A."). Los datos tienen historias plantadas a propósito
(ver 07_docs/guia_hallazgos.md) para que el tablero tenga algo que descubrir.

Uso:  python generar_datos.py        (escribe los CSV en ../01_datos)
Mismo resultado en cada corrida: la semilla es fija.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2026
SALIDA = Path(__file__).resolve().parent.parent / "01_datos"
rng = np.random.default_rng(SEMILLA)

# ---------------------------------------------------------------- calendario e inflación
PERIODOS = pd.period_range("2024-11", "2026-10", freq="M")
# Inflación mensual FICTICIA (inspirada en un contexto argentino de inflación moderada, no es el IPC real)
INFL_REAL = [2.4, 2.7, 2.2, 2.4, 3.6, 2.8, 1.6, 1.7, 1.9, 1.9, 2.1, 2.3,
             2.5, 2.8, 2.9, 2.9, 3.4, 2.6, 2.3, 2.1, 2.0, 2.2, 2.0, 1.9]
# Inflación que se supuso al armar cada presupuesto (siempre más baja que la real: la trampa clásica)
INFL_PPTO = {2024: 2.5, 2025: 1.8, 2026: 1.6}

def indice(tasas):
    """Índice acumulado base 100 en el primer período."""
    return 100 * np.cumprod([1.0] + [1 + t / 100 for t in tasas[1:]])

ipc = indice(INFL_REAL)
ipc_ppto = indice([INFL_PPTO[p.year] for p in PERIODOS])

ESTACIONALIDAD = {1: 1.05, 2: 0.98, 3: 0.97, 4: 0.96, 5: 0.97, 6: 0.98,
                  7: 1.06, 8: 0.97, 9: 0.98, 10: 1.00, 11: 1.01, 12: 1.10}
ESTAC_RUTA = {1: 1.25, 2: 1.15, 3: 0.95, 4: 0.92, 5: 0.88, 6: 0.88,
              7: 1.12, 8: 0.90, 9: 0.90, 10: 0.94, 11: 0.98, 12: 1.10}

# ---------------------------------------------------------------- locales
LOCALES = pd.DataFrame([
    # id, nombre, región, formato, m2, factor de tamaño, apertura
    ("L01", "Plaza Norte",        "Norte",  "Calle",    180, 1.00, "2018-03"),
    ("L02", "Shopping Norte",     "Norte",  "Shopping", 220, 1.15, "2019-06"),
    ("L03", "Parador Ruta Norte", "Norte",  "Ruta",     260, 1.00, "2020-11"),
    ("L04", "Avenida Norte",      "Norte",  "Calle",    160, 0.90, "2021-04"),
    ("L05", "Shopping Centro",    "Centro", "Shopping", 240, 1.10, "2025-11"),
    ("L06", "Peatonal Centro",    "Centro", "Calle",    200, 1.20, "2017-08"),
    ("L07", "Galería Centro",     "Centro", "Shopping", 210, 1.05, "2019-02"),
    ("L08", "Terminal Centro",    "Centro", "Calle",    170, 1.05, "2020-09"),
    ("L09", "Costanera Sur",      "Sur",    "Calle",    190, 0.95, "2018-12"),
    ("L10", "Shopping Sur",       "Sur",    "Shopping", 230, 1.00, "2021-10"),
    ("L11", "Parador Ruta Sur",   "Sur",    "Ruta",     250, 0.90, "2022-01"),
    ("L12", "Barrio Sur",         "Sur",    "Calle",    110, 0.66, "2023-05"),
], columns=["local_id", "local", "region", "formato", "m2", "factor", "apertura"])

TRANS_BASE = {"Calle": 8500, "Shopping": 11000, "Ruta": 6500}   # tickets por mes, local promedio
TICKET_BASE = 9500                                               # ARS, nov-2024
DOTACION = {  # puesto: (Calle, Shopping, Ruta)
    "Encargado": (2, 2, 2), "Atención": (6, 8, 5), "Cocina": (6, 8, 5), "Limpieza": (2, 2, 2)}
SUELDO_BASE = {"Encargado": 1_450_000, "Atención": 1_050_000, "Cocina": 1_100_000, "Limpieza": 950_000}
CARGAS = 1.27            # contribuciones patronales, ART, etc. sobre el bruto
HORAS_MES = 180
ALQ_FIJO = {"Calle": 6_800_000, "Ruta": 5_000_000}   # nov-2024; shopping paga % de ventas con mínimo
ALQ_SHOP_PCT, ALQ_SHOP_MIN = 0.08, 6_000_000

RUBROS = pd.DataFrame([
    (1, "Ventas",               "Ingreso",  1,  "Ventas"),
    (2, "Costo de mercadería",  "Costo",   -1,  "Costo de mercadería"),
    (3, "Personal",             "Costo",   -1,  "Personal"),
    (4, "Alquiler",             "Costo",   -1,  "Gastos de ocupación"),
    (5, "Servicios",            "Costo",   -1,  "Gastos de ocupación"),
    (6, "Mantenimiento",        "Costo",   -1,  "Gastos operativos"),
    (7, "Marketing",            "Costo",   -1,  "Gastos operativos"),
    (8, "Impuestos",            "Costo",   -1,  "Impuestos"),
    (9, "Financiero",           "Costo",   -1,  "Financiero"),
], columns=["rubro_id", "rubro", "tipo", "signo", "grupo_puente"])

# ---------------------------------------------------------------- historias plantadas
def p(s):
    return pd.Period(s, freq="M")

OBRA_RUTA_L03 = (p("2026-03"), p("2026-08"))     # obra vial: caen los tickets 25 %
ROTACION_L07 = p("2026-01")                       # desde acá: renuncias, horas extra y menos productividad
ROTURA_FRIO_L10 = p("2026-06")                    # rotura de cámara de frío: merma y mantenimiento
FALLA_POS_RED = p("2026-03")                      # falla del sistema de cobro en toda la red, 1 día


def paritaria(periodos, tasas_idx, lag=0.95):
    """Índice salarial: aumenta cada 3 meses (ene, abr, jul, oct) por la inflación acumulada x 0.95."""
    idx, actual, ult = [], 100.0, 0
    for i, per in enumerate(periodos):
        if i > 0 and per.month in (1, 4, 7, 10):
            actual *= 1 + (tasas_idx[i] / tasas_idx[ult] - 1) * lag
            ult = i
        idx.append(actual)
    return np.array(idx)


def ajuste_semestral(periodos, tasas_idx):
    """Índice de alquiler: se actualiza en enero y julio por la inflación acumulada."""
    idx, actual, ult = [], 100.0, 0
    for i, per in enumerate(periodos):
        if i > 0 and per.month in (1, 7):
            actual *= tasas_idx[i] / tasas_idx[ult]
            ult = i
        idx.append(actual)
    return np.array(idx)


def escenario(es_ppto):
    """Arma real o presupuesto con el mismo modelo. El presupuesto no tiene ruido ni historias."""
    idx_precio = ipc_ppto if es_ppto else ipc
    # la carta se actualiza con un mes de atraso y traslada el 98 % de la inflación
    idx_carta = np.concatenate([[100.0], idx_precio[:-1] * 0.98 + 2.0])
    idx_sueldo = paritaria(PERIODOS, idx_precio)
    idx_alq = ajuste_semestral(PERIODOS, idx_precio)
    idx_tarifa = idx_precio * np.linspace(1.0, 1.06, len(PERIODOS))  # tarifas suben algo más que la inflación

    filas_res, filas_op, filas_nom = [], [], []
    for _, loc in LOCALES.iterrows():
        apertura = p(loc.apertura)
        k = ["Calle", "Shopping", "Ruta"].index(loc.formato)
        for i, per in enumerate(PERIODOS):
            if per < apertura:
                continue
            meses_abierto = (per - apertura).n
            estac = (ESTAC_RUTA if loc.formato == "Ruta" else ESTACIONALIDAD)[per.month]
            crec = 1.03 ** (i / 12) if es_ppto else 1.0 + 0.004 * i / 12   # el ppto suponía +3 % anual de tickets
            rampa = min(1.0, 0.70 + 0.05 * meses_abierto) if meses_abierto < 6 else 1.0
            trans = TRANS_BASE[loc.formato] * loc.factor * estac * crec * rampa
            ticket = TICKET_BASE * idx_carta[i] / 100
            cmv_pct, extra_pct, bajas, mant_extra, product = 0.32, 0.03, 1, 0.0, 1.0

            if not es_ppto:
                trans *= rng.normal(1.0, 0.025)
                ticket *= rng.normal(1.0, 0.012)
                cmv_pct += rng.normal(0, 0.006) + (0.004 if loc.region == "Sur" else 0)
                bajas = rng.poisson(1.0)
                if loc.local_id == "L03" and OBRA_RUTA_L03[0] <= per <= OBRA_RUTA_L03[1]:
                    trans *= 0.75
                if loc.local_id == "L07" and per >= ROTACION_L07:
                    extra_pct, bajas, product = 0.12, bajas + 3, 0.93
                    trans *= product
                if loc.local_id == "L10" and per == ROTURA_FRIO_L10:
                    cmv_pct += 0.06
                    trans *= 0.92
                    mant_extra = 9_000_000
                if per == FALLA_POS_RED:
                    trans *= 1 - 1 / 31
                if loc.local_id == "L12":
                    cmv_pct -= 0.03    # local chico, encargado muy ordenado con la merma

            trans = round(trans)
            ventas = trans * ticket
            cmv = ventas * cmv_pct

            # nómina por puesto
            personal = 0.0
            dot_total = horas_total = 0
            for puesto, dots in DOTACION.items():
                dot = dots[k]
                if loc.local_id == "L12":
                    dot = max(1, round(dot * 0.62))
                if rampa < 1:
                    dot = max(1, round(dot * 0.9))
                bruto = SUELDO_BASE[puesto] * idx_sueldo[i] / 100
                h_norm = dot * HORAS_MES
                h_extra = h_norm * extra_pct * (rng.normal(1, 0.15) if not es_ppto else 1)
                costo = round((dot * bruto + h_extra * bruto / HORAS_MES * 1.5) * CARGAS)
                personal += costo   # Personal del resultado = suma exacta de la nómina (se puede rastrear)
                dot_total += dot
                horas_total += h_norm + h_extra
                if not es_ppto:
                    filas_nom.append((str(per), loc.local_id, puesto, dot, round(h_norm), round(h_extra), round(costo)))

            if loc.formato == "Shopping":
                alquiler = max(ALQ_SHOP_PCT * ventas, ALQ_SHOP_MIN * idx_alq[i] / 100)
            else:
                alquiler = ALQ_FIJO[loc.formato] * (0.65 if loc.local_id == "L12" else 1) * idx_alq[i] / 100
            servicios = 14_000 * loc.m2 * idx_tarifa[i] / 100
            mantenimiento = (900_000 * idx_precio[i] / 100) * (rng.normal(1, 0.2) if not es_ppto else 1) + mant_extra
            marketing = 0.04 * ventas
            impuestos = 0.045 * ventas + 300_000 * idx_precio[i] / 100
            financiero = 0.021 * ventas

            for rid, val in zip(range(1, 10), [ventas, cmv, personal, alquiler, servicios,
                                               mantenimiento, marketing, impuestos, financiero]):
                filas_res.append((str(per), loc.local_id, rid, round(val)))
            filas_op.append((str(per), loc.local_id, trans, round(ticket), dot_total, round(horas_total), bajas))

    res = pd.DataFrame(filas_res, columns=["periodo", "local_id", "rubro_id", "importe"])
    op = pd.DataFrame(filas_op, columns=["periodo", "local_id", "tickets", "ticket_promedio",
                                         "dotacion", "horas_trabajadas", "bajas_personal"])
    nom = pd.DataFrame(filas_nom, columns=["periodo", "local_id", "puesto", "dotacion",
                                           "horas_normales", "horas_extra", "costo_total"])
    return res, op, nom


def incidentes(operativo):
    """Registro de incidentes: los plantados + incidentes chicos al azar."""
    tipos = [("Corte de luz", 2, 6, 0.010), ("Falla de equipo de cocina", 4, 24, 0.006),
             ("Faltante de insumo", 3, 12, 0.004), ("Ausentismo (falta de personal)", 3, 8, 0.005),
             ("Reclamo de cliente grave", 0, 0, 0.0), ("Corte de agua", 2, 8, 0.008)]
    DETALLE = {"Corte de luz": "Corte de la distribuidora; se cerró la cocina hasta que volvió",
               "Falla de equipo de cocina": "Equipo fuera de servicio; menú reducido hasta la reparación",
               "Faltante de insumo": "No llegó un insumo del proveedor; platos sin stock",
               "Ausentismo (falta de personal)": "Faltó personal del turno; demoras en la atención",
               "Reclamo de cliente grave": "Reclamo por demora o error en el pedido; se respondió y se compensó",
               "Corte de agua": "Corte del servicio; atención limitada"}
    filas = []
    for _, r in operativo.iterrows():
        for _ in range(rng.poisson(0.35)):
            tipo, hmin, hmax, impacto = tipos[rng.integers(len(tipos))]
            dia = int(rng.integers(1, 28))
            horas = int(rng.integers(hmin, hmax + 1)) if hmax else 0
            venta_dia = r.tickets * r.ticket_promedio / 30
            filas.append((f"{r.periodo}-{dia:02d}", r.local_id, tipo, horas, round(venta_dia * impacto * max(horas, 1) / 4),
                          DETALLE[tipo]))
    filas += [
        ("2026-03-12", lid, "Falla del sistema de cobro (POS)", 14, None, "Caída del proveedor de cobros en toda la red")
        for lid in LOCALES.local_id]
    filas += [("2026-03-02", "L03", "Obra vial en el acceso", 0, None, "Obra en la ruta hasta agosto: acceso reducido, -25 % de tickets"),
              ("2026-06-17", "L10", "Rotura de cámara de frío", 36, None, "Se perdió mercadería (merma) y hubo reparación urgente"),
              ("2026-01-20", "L07", "Renuncia del encargado", 0, None, "Rotación alta desde enero: horas extra y menor productividad")]
    inc = pd.DataFrame(filas, columns=["fecha", "local_id", "tipo", "horas_afectadas", "impacto_estimado_ventas", "detalle"])
    inc = inc.sort_values(["fecha", "local_id"]).reset_index(drop=True)
    inc.insert(0, "incidente_id", [f"I{n:04d}" for n in range(1, len(inc) + 1)])
    return inc


def main():
    SALIDA.mkdir(exist_ok=True)
    real, operativo, nomina = escenario(es_ppto=False)
    ppto, op_ppto, _ = escenario(es_ppto=True)
    # tickets y ticket presupuestados: permiten abrir el desvío de ventas en efecto volumen y efecto precio
    operativo = operativo.merge(
        op_ppto[["periodo", "local_id", "tickets", "ticket_promedio"]].rename(
            columns={"tickets": "tickets_ppto", "ticket_promedio": "ticket_promedio_ppto"}),
        on=["periodo", "local_id"], how="left")

    resultados = real.rename(columns={"importe": "real"}).merge(
        ppto.rename(columns={"importe": "presupuesto"}), on=["periodo", "local_id", "rubro_id"], how="outer")

    calendario = pd.DataFrame({"periodo": [str(p_) for p_ in PERIODOS],
                               "anio": [p_.year for p_ in PERIODOS], "mes": [p_.month for p_ in PERIODOS],
                               "inflacion_mensual_pct": INFL_REAL, "ipc_indice": np.round(ipc, 2),
                               "inflacion_ppto_pct": [INFL_PPTO[p_.year] for p_ in PERIODOS],
                               "ipc_ppto_indice": np.round(ipc_ppto, 2)})

    usuarios = pd.DataFrame([
        ("direccion@demo", "Dirección", None, None),
        ("regional.norte@demo", "Gerente regional", "Norte", None),
        ("regional.centro@demo", "Gerente regional", "Centro", None),
        ("regional.sur@demo", "Gerente regional", "Sur", None),
        ("local.L07@demo", "Gerente de local", "Centro", "L07"),
        ("local.L10@demo", "Gerente de local", "Sur", "L10"),
        ("supervisor.L03@demo", "Supervisor", "Norte", "L03"),
    ], columns=["usuario", "rol", "region", "local_id"])

    tablas = {"dim_local": LOCALES.drop(columns="factor"), "dim_rubro": RUBROS, "dim_calendario": calendario,
              "fact_resultados": resultados, "fact_operativo": operativo, "fact_nomina": nomina,
              "fact_incidentes": incidentes(operativo), "usuarios_demo": usuarios}
    for nombre, df in tablas.items():
        df.to_csv(SALIDA / f"{nombre}.csv", index=False, encoding="utf-8")
        print(f"{nombre:16s} {len(df):6d} filas")
    return tablas


if __name__ == "__main__":
    main()
