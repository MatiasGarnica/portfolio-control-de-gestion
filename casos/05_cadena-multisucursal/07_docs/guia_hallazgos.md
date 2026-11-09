# Guía de hallazgos · Caso 05 (las "respuestas")

Los datos son ficticios y tienen **historias plantadas a propósito** para que el tablero tenga algo que encontrar. Esta guía sirve para chequear que el tablero las muestre. Se dice abiertamente en el README: no se presentan como hallazgos reales.

Cifras de ene-oct 2026, en millones de ARS nominales (salen de `validar_datos.py`).

| # | Dónde | Qué pasó | Cómo se ve en los datos | Nivel del tablero donde aparece |
|---|---|---|---|---|
| 1 | Toda la red | **La trampa de la inflación.** El presupuesto 2026 supuso 1,6 % mensual y la real fue más alta | Ventas nominales **arriba** del presupuesto; en moneda constante, **abajo**. Además, se presupuestó +3 % de tickets y se vendieron casi los mismos | Nivel 1: columnas "nominal" y "moneda constante" |
| 2 | L07 Galería Centro | Renunció el encargado en enero y hubo rotación alta | Bajas de personal +3 por mes, horas extra del 3 % al 12 %, ventas por hora trabajada al nivel más bajo de los shoppings. Contribución −101 M contra el presupuesto: **el peor desvío** | Nivel 2 (Personal) → Nivel 3 (fact_nomina + incidente del 20/01) |
| 3 | L03 Parador Ruta Norte | Obra vial en el acceso de marzo a agosto | Tickets −25 % en esos meses. Con costos fijos, la contribución pasa a negativa (−9 M; ppto +82 M) | Nivel 2 (Ventas, efecto volumen) → incidente del 02/03 |
| 4 | L10 Shopping Sur | Rotura de la cámara de frío el 17/06 | En junio, costo de mercadería +6 p.p. (merma) y mantenimiento +9 M; ventas −8 % ese mes | Nivel 2 (Costo de mercadería y Mantenimiento de un solo mes) → incidente |
| 5 | Toda la red | Falla del sistema de cobro el 12/03 | Un día de ventas menos en todos los locales en marzo (~−3 %) | Nivel 3: incidente que se repite en los 12 locales (no es un problema de un local) |
| 6 | L12 Barrio Sur | **Chico pero bien gestionado** | Menos pesos de contribución que casi todos, pero el mejor food cost de la red (29,5 %, contra ~32 %) y margen 18,4 %, arriba del presupuesto | Comparación dentro del formato Calle: "rentable ≠ bien gestionado" (al revés) |
| 7 | L05 Shopping Centro | Abrió en nov-2025 | Si se lo suma al crecimiento de la red, infla las ventas contra el año anterior | Indicador "mismos locales" |
| 8 | Formato Ruta (L03, L11) | Estructuralmente débil fuera de temporada | Margen cerca de 0 % aun en el presupuesto; dependen del verano y de julio | Comparar por formato, no contra el promedio de la red |

**Ranking por desvío de contribución contra el presupuesto (2026):** L07 −101 · L03 −91 · L10 −39 · L11 −24 · … · L05 +13 · L02 +25. Red: −224 M.

Para la presentación a Dirección: "La red está 224 M abajo del presupuesto en contribución. Tres locales y tres causas concretas explican todo el desvío (−231 M): rotación de personal en L07, una obra vial en L03 y una rotura de cámara en L10. Los otros nueve, en conjunto, están en línea (+7 M). Además, el presupuesto subestimó la inflación: en pesos vendimos más, pero en moneda constante, menos."
