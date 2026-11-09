"""Genera datos FICTICIOS del Caso 02: 12 semanas de reportes de primera linea
y ventas semanales por ruta. Semilla fija: siempre da lo mismo.

Dos historias plantadas:
  1) Ruta 5 (Oeste): muchos reportes de "Competencia" desde la semana 6 y sus
     ventas caen de a poco (efecto LOCAL).
  2) Las 8 rutas: "Situación económica del cliente" sube desde la semana 9 y
     las ventas bajan un poco en las semanas 10 a 12 (efecto MERCADO).

Uso:  python generar_datos.py
"""
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SEMILLA = 2026
LUNES_SEMANA_1 = date(2026, 8, 17)   # la semana 12 arranca el 2026-11-02
SEMANAS = 12

RUTAS = {
    "Ruta 1 - Centro": 3600, "Ruta 2 - Norte": 3100, "Ruta 3 - Sur": 2800,
    "Ruta 4 - Este": 3300, "Ruta 5 - Oeste": 3000, "Ruta 6 - Costanera": 2500,
    "Ruta 7 - Barrio Parque": 2200, "Ruta 8 - Zona Industrial": 2700,
}
RUTA_COMPETENCIA = "Ruta 5 - Oeste"

# Categorias fijas del formulario y su peso "normal" (reportes por semana y ruta = 9 en total)
CATEGORIAS = {
    "Precio (contra la competencia)": 0.20,
    "Calidad del producto": 0.06,
    "Atención o servicio": 0.12,
    "Falta de stock o entrega fallida": 0.14,
    "Situación económica del cliente": 0.12,
    "Clima o estacionalidad": 0.15,
    "Competencia nueva en la zona": 0.07,
    "Otro": 0.14,
}
ROLES = {"Repartidor": 0.62, "Atención al cliente": 0.23, "Encargado": 0.15}
TEXTOS = {
    "Competencia nueva en la zona": ["Abrió un dispensador nuevo a la vuelta",
                                     "Reparten a $200 menos", "Un cliente se pasó al otro proveedor", ""],
    "Situación económica del cliente": ["Piden menos bidones por semana", "Dicen que están ajustando gastos",
                                        "Pasaron de 3 a 2 bidones", ""],
    "Falta de stock o entrega fallida": ["No llegó el camión a horario", "Faltaron bidones de 20 L", ""],
    "Precio (contra la competencia)": ["Comparan con otra marca", ""],
}
MULT_ECON = {9: 1.8, 10: 2.6, 11: 3.4, 12: 4.2}          # efecto mercado en reportes
CAIDA_MERCADO = {10: 0.03, 11: 0.06, 12: 0.09}           # efecto mercado en ventas
PRECIO_BIDON_S1 = 2800.0                                  # ficticio, sube 0,6 % por semana


def main():
    rng = np.random.default_rng(SEMILLA)
    cats, pesos = list(CATEGORIAS), np.array(list(CATEGORIAS.values()))
    filas = []
    ventas = []
    for s in range(1, SEMANAS + 1):
        lunes = LUNES_SEMANA_1 + timedelta(weeks=s - 1)
        precio = PRECIO_BIDON_S1 * (1.006 ** (s - 1))
        for ruta, base in RUTAS.items():
            # ---- reportes ----
            esperado = 9 * pesos.copy()
            if s in MULT_ECON:
                esperado[cats.index("Situación económica del cliente")] *= MULT_ECON[s]
            if ruta == RUTA_COMPETENCIA and s >= 6:
                esperado[cats.index("Competencia nueva en la zona")] += 4.0 + 0.7 * (s - 6)
            for cat, lam in zip(cats, esperado):
                for _ in range(rng.poisson(lam)):
                    dia = int(rng.integers(0, 6))                 # lunes a sabado
                    hora = int(rng.integers(16, 21)); minu = int(rng.integers(0, 60))
                    marca = datetime.combine(lunes + timedelta(days=dia), datetime.min.time()).replace(hour=hora, minute=minu)
                    rol = rng.choice(list(ROLES), p=list(ROLES.values()))
                    detalle = rng.choice(TEXTOS.get(cat, [""])) if rng.random() < 0.35 else ""
                    filas.append({"Marca temporal": marca.strftime("%Y-%m-%d %H:%M:%S"), "Rol": rol,
                                  "Ruta": ruta, "Motivo": cat, "Detalle": detalle})
            # ---- ventas ----
            f = 1 + rng.normal(0, 0.008)                           # sin tendencia, solo ruido
            if ruta == RUTA_COMPETENCIA and s >= 6:
                f -= min(0.025 * (s - 5), 0.15)                    # la ruta pierde clientes de a poco
            f -= CAIDA_MERCADO.get(s, 0)
            bidones = int(round(base * f))
            ventas.append({"semana": s, "lunes": lunes.isoformat(), "ruta": ruta,
                           "bidones": bidones, "ventas_ars": int(round(bidones * precio))})

    resp = pd.DataFrame(filas).sort_values("Marca temporal")
    (BASE / "01_datos").mkdir(exist_ok=True)
    resp.to_csv(BASE / "01_datos" / "respuestas.csv", index=False, encoding="utf-8")
    pd.DataFrame(ventas).to_csv(BASE / "01_datos" / "ventas_semanales.csv", index=False, encoding="utf-8")
    print(f"respuestas.csv: {len(resp)} filas | ventas_semanales.csv: {len(ventas)} filas")


if __name__ == "__main__":
    main()
