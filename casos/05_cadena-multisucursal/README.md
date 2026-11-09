# Caso 05 · Control de gestión de una cadena con 12 locales

**Empresa ficticia:** Cadena Demo S.A., comida rápida con 12 locales en 3 regiones (Norte, Centro, Sur) y 3 formatos (calle, shopping, ruta).
**Período:** nov-2024 a oct-2026. **Todos los datos son inventados** y se generan con un script. Tienen historias plantadas a propósito para que el análisis tenga algo que encontrar.

## Qué muestra este caso

1. **El recorrido del desvío:**
   - **Dirección:** el desvío general y el ranking de locales.
   - **Gerente:** el desvío de un local, abierto en ventas, mercadería, personal, ocupación, impuestos y financiero.
   - **Causa:** la nómina, la operación y los incidentes del día.
2. **La misma información resuelta para tres tamaños de empresa**, con sus herramientas, licencias y costos: chica, mediana y grande.
3. **Seguridad pensada desde el diseño:** cada usuario de prueba ve solo lo suyo. El filtro está en la base, no en la página.
4. **De dónde sale cada número:** el diccionario de indicadores con sus variantes y qué implica cada una.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `01_datos\` | CSV del modelo estrella (dimensiones, hechos, usuarios de prueba) |
| `02_codigo\` | `generar_datos.py` (semilla fija: siempre da lo mismo) y `validar_datos.py` (controles de integridad, trazabilidad e historias) |
| `03_tableros\` | `tablero_direccion.html`: HTML autocontenido; filtros de período, moneda nominal o constante, y local |
| `07_docs\` | `diccionario_datos_e_indicadores.md`, `guia_hallazgos.md`, `seguridad_demo.md`, `propuesta_economica.md` |

## Cómo reproducirlo

```
cd 02_codigo
python generar_datos.py
python validar_datos.py
python armar_tablero.py
```

## Estado

- [x] Datos ficticios + controles (2026-11-07)
- [x] Diccionario de indicadores y guía de hallazgos
- [x] Tablero de dirección (escenario grande): nivel 1 → 2 → 3 · `03_tableros/tablero_direccion.html` (se arma con `02_codigo/armar_tablero.py`) (2026-11-07)
- [x] Comentarios de desvío (escribe el gerente de su local) y feedback de primera línea con categorías (supervisor/gerente), umbral de materialidad ±5 %, participación del local en su formato vs año anterior (2026-11-09)
- [ ] Versión mediana (Power BI) y versión chica (HTML)
- [x] Demo con login y permisos por usuario: Supabase + `03_tableros/demo_login.html` (sin datos adentro). Seguridad documentada en `07_docs/seguridad_demo.md` (2026-11-09)
- [x] Propuesta económica por escenario: `07_docs/propuesta_economica.md` (2026-11-09)
- [ ] Publicación en GitHub (falta OK de Matías)

Propuesta por tamaño de empresa: `07_docs/propuesta_economica.md`.
