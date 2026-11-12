"""Genera los datos ficticios del Caso 07 (Mayorista Ruta Sur): clientes, pedidos, cobranzas y costos.

Uso:
  python generar_datos.py              (escribe los CSV en ../01_datos)
  python generar_datos.py --destino RUTA

Seis meses (mayo a octubre de 2026), 80 clientes, montos en miles de pesos de octubre de 2026
(moneda constante). Semilla fija: siempre da lo mismo. Empresa y datos inventados.
"""
import argparse
import csv
import math
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MESES = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]

# tipo: cantidad, ventas/mes (min, max, $ miles), margen bruto, pedidos/mes, bultos por pedido,
#       días de cobro posibles, devoluciones (% de ventas), urgentes/mes, peso por zona (C, N, S, O)
TIPOS = {
    "Súper chico":  dict(n=8,  v=(8000, 20000), mb=(.155, .185), ped=(4, 6),  bxp=(110, 190), dias=[30, 45, 60], dev=(.008, .02), urg=(0, 0.3), zona=(3, 2, 2, 1)),
    "Autoservicio": dict(n=12, v=(3000, 8000),  mb=(.175, .215), ped=(4, 8),  bxp=(40, 85),   dias=[15, 30, 45, 60, 60], dev=(.01, .06), urg=(0, 0.5), zona=(2, 3, 3, 2)),
    "Almacén":      dict(n=25, v=(1000, 3500),   mb=(.235, .275), ped=(4, 12), bxp=(6, 22),    dias=[0, 0, 7, 15], dev=(.008, .03), urg=(0, 0.3), zona=(4, 3, 3, 2)),
    "Kiosco":       dict(n=20, v=(600, 1800),   mb=(.275, .315), ped=(4, 11), bxp=(2, 7),     dias=[0, 0, 0, 7], dev=(.005, .02), urg=(0, 0.2), zona=(6, 2, 2, 1)),
    "Gastronomía":  dict(n=15, v=(1500, 5000),  mb=(.215, .255), ped=(6, 14), bxp=(8, 26),    dias=[15, 30, 30, 45], dev=(.02, .05), urg=(0.5, 3), zona=(4, 3, 2, 1)),
}
ZONAS = {"Centro": (3, 8), "Norte": (8, 18), "Sur": (10, 24), "Oeste": (20, 38)}  # km de desvío por visita

NOMBRES = {
    "Súper chico": ["Súper Los Andes", "Súper Belgrano", "Súper La Ribera", "Mercado San Roque", "Súper Don Tito", "Súper El Molino", "Mercado Las Heras", "Súper Plaza Sur"],
    "Autoservicio": ["Autoservicio Norte", "Autoservicio Mitre", "Autoservicio La Paz", "Autoservicio Sarmiento", "Autoservicio El Ceibo", "Autoservicio Dorrego",
                     "Autoservicio San Martín", "Autoservicio Las Rosas", "Autoservicio Güemes", "Autoservicio Lavalle", "Autoservicio Rivadavia", "Autoservicio Colón"],
    "Almacén": [f"Almacén {x}" for x in ["La Esquina", "Don Pepe", "Lo de Marta", "El Tano", "San Cayetano", "La Unión", "El Progreso", "Las Flores", "Doña Rosa", "Los Pinos",
                                          "El Faro", "La Estrella", "Santa Rita", "El Puente", "Del Barrio", "La Familia", "El Sol", "Don Luis", "La Paloma", "El Trébol",
                                          "Avenida", "El Ombú", "La Amistad", "Los Hermanos", "Central"]],
    "Kiosco": [f"Kiosco {x}" for x in ["Central", "La Parada", "El Rápido", "Estación", "24 Horas", "Del Club", "La Escuela", "El Vasco", "Plaza", "La Terminal",
                                        "Las Palmeras", "El Viajero", "La Esquinita", "Del Hospital", "San José", "Avenida", "El Paso", "La Placita", "Norte", "El Turco"]],
    "Gastronomía": ["Restaurante El Puerto", "Bodegón Don Carlos", "Parrilla La Tranquera", "Pizzería Napoli", "Café del Centro", "Rotisería La Abuela", "Bar El Ancla",
                    "Resto La Huella", "Hotel Del Valle", "Comedor Escolar 14", "Pizzería La Farola", "Confitería Ideal", "Parrilla El Fogón", "Bar Los Amigos", "Cantina Italia"],
}

# Costos del mes (miles de $ de octubre 2026), del estado de resultados de la empresa
COSTOS = [
    # cuenta, actividad, monto mensual, cómo se reparte
    ("Sueldos depósito (8 operarios + encargado)", "Preparación", 13200),
    ("Choferes y ayudantes (5 camiones)", "Reparto", 11500),
    ("Seguro, patentes y amortización de camiones", "Reparto", 3500),
    ("Combustible", "Reparto · km", 2400),
    ("Mantenimiento y neumáticos", "Reparto · km", 1050),
    ("Administración de ventas y cobranzas", "Estructura", 4200),
    ("Gerencia, alquiler y servicios", "Estructura", 7800),
]


def main(destino=None):
    rnd = random.Random(7)
    dest = Path(destino) if destino else AQUI.parent / "01_datos"
    dest.mkdir(parents=True, exist_ok=True)

    clientes, mov = [], []
    cid = 0
    for tipo, p in TIPOS.items():
        for i in range(p["n"]):
            cid += 1
            zona = rnd.choices(list(ZONAS), weights=p["zona"])[0]
            km = round(rnd.uniform(*ZONAS[zona]), 1)
            v = rnd.uniform(*p["v"])
            ped = rnd.randint(*p["ped"])
            # los chicos que piden mucho piden poco por vez: bultos por pedido bajan con la frecuencia
            bxp = rnd.uniform(*p["bxp"]) * (1.15 - 0.3 * (ped - p["ped"][0]) / max(1, p["ped"][1] - p["ped"][0]))
            cli = dict(cliente_id=f"C{cid:03d}", cliente=NOMBRES[tipo][i], tipo=tipo, zona=zona, km_desvio=km,
                       dias_cobro=rnd.choice(p["dias"]), margen_bruto=round(rnd.uniform(*p["mb"]), 4),
                       dev_pct=round(rnd.uniform(*p["dev"]), 4))
            tasa_urg = rnd.uniform(*p["urg"])  # pedidos urgentes fuera de ruta por mes
            clientes.append(cli)
            for m in MESES:
                f = rnd.uniform(.88, 1.12)
                ventas = round(v * f, 1)
                pedidos = max(2, round(ped * rnd.uniform(.85, 1.15)))
                bultos = max(pedidos, round(bxp * pedidos * f))
                urg = math.floor(tasa_urg) + (1 if rnd.random() < tasa_urg - math.floor(tasa_urg) else 0)
                mov.append(dict(mes=m, cliente_id=cli["cliente_id"], ventas=ventas,
                                costo_mercaderia=round(ventas * (1 - cli["margen_bruto"]), 1),
                                pedidos=pedidos, bultos=bultos, urgentes=urg,
                                devoluciones=round(ventas * cli["dev_pct"] * rnd.uniform(.7, 1.3), 1)))

    costos = []
    for m in MESES:
        for cuenta, act, monto in COSTOS:
            costos.append(dict(mes=m, cuenta=cuenta, actividad=act, monto=round(monto * rnd.uniform(.97, 1.03), 1)))

    def escribir(nombre, filas):
        with open(dest / nombre, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)

    for c in clientes:
        c.pop("dev_pct")
    escribir("clientes.csv", clientes)
    escribir("movimientos_mensuales.csv", mov)
    escribir("costos_operativos.csv", costos)
    print(f"OK {dest}: {len(clientes)} clientes, {len(mov)} filas de movimientos, {len(costos)} de costos")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destino")
    main(ap.parse_args().destino)
