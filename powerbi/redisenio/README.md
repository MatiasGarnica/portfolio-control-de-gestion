# Rediseño de tableros con datos ficticios

Esta carpeta contiene el rediseño de los 11 tableros del portfolio.

**Qué son estas imágenes.** Las PNG de [`../screenshots/`](../screenshots/) **no son capturas de Power BI**.
Son rediseños hechos con Python (HTML + SVG escritos a mano, sin librerías de gráficos) y calculados al 100 %
sobre el dataset **sintético** de este repositorio (`data/generate_synthetic_data.py`). La marca "AquaNorte
Distribuidora (ficticia)", las zonas y los barrios son inventados. Cada tablero mantiene el tema y la pregunta del
original, pero con jerarquía más clara y un titular que enuncia la conclusión.

| Archivo | Pregunta que responde |
|---|---|
| `01_cobranzas_kpis` | ¿Qué zona depende más del efectivo y cambia el mix digital? |
| `02_cobranzas_dias_calle` | ¿En cuántos días se cobra y qué zonas empeoran? |
| `03_cobranzas_costo_vendedor` | ¿Qué vendedores superan el umbral de costo de cobranza? |
| `04_frio_calor_sin_consumo` | ¿Qué pasó con los equipos F/C sin consumo? |
| `05_crosselling` | ¿Migramos clientes al mix premium (12 L, soda, F/C)? |
| `06_feriados_venta_recuperar` | ¿Cuánta venta hay que recuperar después de un feriado? |
| `07_altas_rto_digital` | ¿Cómo y por dónde entran los clientes nuevos? |
| `08_altas_consumo_litros` | ¿Cuántos litros consumen las altas en sus primeras semanas? |
| `09_estadisticas_repartos_litros` | ¿Qué zonas y rutas crecen o caen en litros? |
| `10_estadisticas_repartos_pesos` | ¿Qué familia de producto explica la variación en pesos? |
| `11_barrios_promo_soda` | ¿Avanza la venta cruzada de soda en barrios cerrados? |

## Qué es simulado y qué sale de los datos

Todo sale de los CSV sintéticos salvo lo siguiente, que el dataset no modela y se simula con semilla fija
(está aclarado en el pie de cada tablero):

- Canal de alta (Digital/RTO) y bonificación 2x1 (tableros 07 y 08).
- Venta del día feriado (tablero 06): venta habitual por un factor aleatorio.
- Tasas de costo por medio de pago (tablero 03) y meta de litros (tablero 09): supuestos.
- Zonas = supervisores del dataset con nombres genéricos; barrios = mapeo de los barrios sintéticos a nombres inventados.
- El mes de análisis es abril de 2026 (último mes completo; los datos llegan al 19/05/2026).

## Cómo regenerarlas

Requisitos: Python 3 con `pandas`, `numpy`, `faker` (para generar los datos) y `playwright` con Chromium
(`pip install playwright && playwright install chromium`).

```bash
python data/generate_synthetic_data.py          # genera data/csv/*.csv (tarda unos minutos)
python powerbi/redisenio/armar_tableros.py      # escribe html/*.html y screenshots/*.png
python powerbi/redisenio/armar_tableros.py --solo-html   # solo los HTML, sin PNG
```

Los HTML quedan en `powerbi/redisenio/html/` (ancho fijo de 1600 px) y las capturas en `powerbi/screenshots/`.

## Cómo usar el tema en Power BI

`tema_powerbi.json` replica la paleta y el estilo de tarjetas del rediseño.

1. En Power BI Desktop: **Vista > Temas > Examinar temas** y elegir `tema_powerbi.json`.
2. Se aplican la paleta (azul = a favor `#1b6ca8`, rojo = en contra `#d64545`, más petróleo `#0f4c5c` y dos azules suaves),
   el fondo de página `#eef1f5`, las tarjetas blancas con borde `#d6dbe3` y esquinas redondeadas, y la tipografía.
3. Para el encabezado, insertar un rectángulo con degradado `#0f4c5c` a `#1a7f8e` en la parte superior de la página y un
   cuadro de texto con el titular (la conclusión) en blanco.
4. Usar `good` / `bad` del tema en el formato condicional de las variaciones (azul sube, rojo baja).

El JSON usa el formato de temas de informe de Power BI; los ajustes finos de cada visual pueden variar según la versión de Desktop.
