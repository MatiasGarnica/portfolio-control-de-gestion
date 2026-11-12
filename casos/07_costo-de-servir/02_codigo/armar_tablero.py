"""Arma 03_tableros/costo_de_servir.html: mete los resultados de costo_servir.py (JSON) en la plantilla.

Uso:
  python armar_tablero.py                (usa salida/resultados.json; si no existe, corre costo_servir.py)
  python armar_tablero.py --recalcular   (vuelve a correr costo_servir.py antes de armar)

El HTML queda autocontenido: sin librerías externas, se abre con doble clic o desde GitHub Pages.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RESULTADOS = AQUI / "salida" / "resultados.json"
PLANTILLA = AQUI / "tablero_plantilla.html"
DESTINO = AQUI.parent / "03_tableros" / "costo_de_servir.html"


def main(datos=None, recalcular=False):
    if recalcular or not RESULTADOS.exists():
        sys.path.insert(0, str(AQUI))
        import costo_servir
        costo_servir.main(datos)
    res = json.loads(RESULTADOS.read_text(encoding="utf-8"))
    js = json.dumps(res, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = PLANTILLA.read_text(encoding="utf-8")
    html = html.replace("/*__DATOS__*/null", js).replace("/*__GENERADO__*/", date.today().strftime("%d/%m/%Y"))
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(html, encoding="utf-8")
    print(f"OK {DESTINO} ({DESTINO.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datos", help="carpeta con los CSV")
    ap.add_argument("--recalcular", action="store_true", help="volver a correr costo_servir.py")
    a = ap.parse_args()
    main(a.datos, a.recalcular)
