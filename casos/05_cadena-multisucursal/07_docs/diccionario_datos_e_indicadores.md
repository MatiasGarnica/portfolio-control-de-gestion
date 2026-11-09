# Diccionario de datos e indicadores · Caso 05 (Cadena Demo S.A., empresa ficticia)

**De dónde sale cada número, cómo se calcula y qué cambia si se calcula distinto.**
Moneda: pesos argentinos nominales, salvo que diga "moneda constante". Períodos: nov-2024 a oct-2026 (24 meses).

## Tablas (modelo estrella)

| Tabla | Grano (una fila = …) | Columnas clave | Para qué |
|---|---|---|---|
| `dim_local` | un local | local_id, local, region, formato (Calle/Shopping/Ruta), m2, apertura | Filtrar, agrupar y comparar locales parecidos (mismo formato) |
| `dim_rubro` | un rubro del resultado | rubro_id, rubro, tipo, **signo** (+1 ingreso / −1 costo), grupo_puente | Ordenar el estado de resultados y armar el puente del desvío |
| `dim_calendario` | un mes | periodo, ipc_indice, inflacion_mensual_pct, ipc_ppto_indice | Fechas y pasaje a moneda constante |
| `fact_resultados` | mes × local × rubro | real, presupuesto | Resultado por local: el corazón del tablero |
| `fact_operativo` | mes × local | tickets, ticket_promedio, dotacion, horas_trabajadas, bajas_personal, tickets_ppto, ticket_promedio_ppto | Explicar el "por qué" de las ventas y del personal |
| `fact_nomina` | mes × local × puesto | dotacion, horas_normales, horas_extra, costo_total | Detalle de Personal (nivel 3) |
| `fact_incidentes` | un incidente | fecha, local_id, tipo, horas_afectadas, impacto_estimado_ventas, detalle | Contexto: qué pasó ese día |
| `usuarios_demo` | un usuario de prueba | usuario, rol, region, local_id | Seguridad por filas: quién ve qué |

**Reglas de trazabilidad** (las controla `02_codigo/validar_datos.py`):
- Personal del resultado = suma exacta de `fact_nomina.costo_total` del mismo mes y local.
- Ventas = tickets × ticket promedio (diferencia menor al 0,1 % por redondeo).
- Los importes se guardan positivos. El signo lo da `dim_rubro`, así se evita el error clásico de sumar costos como si fueran ventas.

## Indicadores

| Indicador | Fórmula | Fuente | Variantes y qué implica cada una |
|---|---|---|---|
| **Contribución del local** | Ventas − todos los costos del local | fact_resultados × signo | Es antes de gastos de estructura central. Si se reparte la estructura (por ventas, por m² o por partes iguales), el ranking puede cambiar: **siempre decir cuál se usó** |
| **Margen de contribución %** | Contribución / Ventas | ídem | Sirve para comparar locales de distinto tamaño. Un local chico puede tener mejor margen y menos pesos |
| **Desvío contra presupuesto** | Real − Presupuesto (en contribución, el signo ya lo da dim_rubro) | ídem | Nominal o en moneda constante. Con inflación, **el nominal engaña**: ver abajo |
| **Desvío en moneda constante** | Real / IPC real − Presupuesto / IPC supuesto en el ppto (base nov-2024) | fact_resultados + dim_calendario | Separa "vendimos más caro porque hubo inflación" de "vendimos más". Variante: deflactar todo por el IPC real (más simple, mezcla el error de supuesto con el de gestión) |
| **Food cost (CMV %)** | Costo de mercadería / Ventas | fact_resultados | Teórico (receta × ventas) contra real (inventario inicial + compras − final). La diferencia es la **merma**. Acá solo está el real |
| **Costo laboral %** | Personal / Ventas | fact_resultados / fact_nomina | Con o sin cargas sociales, con o sin horas extra, con o sin encargado. Cambia 3–6 p.p. según la definición |
| **Prime cost %** | (Mercadería + Personal) / Ventas | ídem | El indicador de gestión más usado en comida rápida: junta los dos costos que el local controla |
| **Ticket promedio** | Ventas / Tickets | fact_operativo | Sube con la inflación aunque no se venda más. Comparalo en moneda constante |
| **Ventas por hora trabajada** | Ventas / Horas trabajadas | fact_resultados + fact_operativo | Productividad del personal. Las horas extra la bajan aunque el local "venda bien" |
| **Ventas por m²** | Ventas / m² | + dim_local | Para comparar locales de distinto tamaño. Solo dentro del mismo formato |
| **Ventas mismos locales (comparables)** | Variación de ventas solo de los locales abiertos los dos períodos | + dim_local.apertura | El local L05 abrió en nov-2025: si se lo incluye, el crecimiento de la red parece mayor |
| **Rotación de personal** | Bajas / Dotación promedio | fact_operativo | Mensual o anualizada (× 12). Se dispara antes que el costo: es un indicador adelantado |
| **Efecto precio / efecto volumen** | Volumen = (Tickets real − Tickets ppto) × Ticket ppto. Precio = (Ticket real − Ticket ppto) × Tickets real | fact_operativo + presupuesto | Explica el desvío de ventas: ¿vendimos más tickets o más caro? El orden de cálculo cambia el reparto (convención: volumen primero) |

## Seguridad: qué ve cada usuario de prueba

| Rol | Ve | No ve |
|---|---|---|
| Dirección | Todo | — |
| Gerente regional | Su región en detalle; el resto de la red solo como promedio | El detalle de los locales de otras regiones |
| Gerente de local | Su local + el promedio de la red y de su formato | Los demás locales uno por uno; la nómina detallada de otros |
| Supervisor | Los incidentes de su local (puede cargarlos) | Resultados económicos |

El filtro se aplica **en la base**, no en la página: ver `02_Formacion\Referencias\05_hosting-y-bases-para-demo.md`.
