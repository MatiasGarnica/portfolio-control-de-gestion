# Criterios y mapeo: del Excel de gestión al tablero

Un BPO de cobranzas suele manejar su control de gestión con una serie de planillas Excel. Esta tabla muestra qué hace cada una, cómo se llama esa práctica en FP&A y dónde quedó en el tablero. Todos los datos del caso son ficticios ("Cobranzas del Sur S.A.").

## Mapeo

| Planilla típica | Qué hace | Término FP&A | En el tablero |
|---|---|---|---|
| Presupuesto anual | Estado de resultados proyectado con supuestos de inflación, TC y paritarias; escenarios | Driver-based budget | Escenario Presupuesto y pestaña Planificador (presupuesto 2026) |
| Proyecciones semanales | Proyección por cartera, reversas, control de cumplimiento | Rolling forecast, forecast accuracy | Escenario Forecast, alerta de desvío, "Cómo fue la proyección" por cartera |
| Estado de resultados de gestión (ARS y USD) | Real contra forecast, presupuesto y año anterior | Budget vs actual, variance analysis | Pestaña Estado de resultados (3 niveles) |
| Diario por centro de costo | Reclasificación del mayor, eliminaciones, devengamiento de SMS, mails y telefonía | Conciliación contable → gestión | Botón "De contable a gestión" |
| Matriz de rentabilidad | Costos compartidos asignados por driver (minutos, SMS, mails, dotación, licencias, pagos) | Activity-based costing, rentabilidad por cliente | Pestaña Rentabilidad por cartera y diagrama de flujo de costos |
| Ingreso por hora | Ingreso y costo por operador y por hora | Unit economics, productividad | Tarjeta Ingreso por hora |
| Cotizaciones de carteras | Deuda × % recupero × fee; costo de agentes, supervisión y canales; escenarios | Deal pricing, break-even | Cotizador de carteras y propuesta descargable |
| Gastos a recuperar y deuda en USD | Gastos corporativos (TI, Gerencia) distribuidos entre países; diferencia de cambio sobre la cuenta corriente en USD | Intercompany allocation, FX remeasurement | Pestaña Intercompany y TC |
| Remuneraciones e indicadores de RRHH | Costo por negocio, dotación, rotación, ausentismo | Headcount planning | Efecto dotación contra paritaria; montos ocultos por rol |
| Valor unitario de canales | Precio unitario por proveedor y canal | Unit cost tracking | Alerta de costo por SMS |

## Criterios de diseño
- La audiencia y la frecuencia definen el formato: gerencia mira tarjetas y alertas; supervisión, su cartera; control de gestión, el detalle.
- Explicar el desvío antes de juzgarlo: "creció, pero no llegó porque el presupuesto suponía más inflación".
- Notación de escenarios estilo IBCS (real, presupuesto, forecast, año anterior); formato numérico es-AR; decimales solo cuando aportan.
- Datos sensibles: los sueldos solo los ven RRHH, gerencia y control de gestión. Por eso hay un informe por audiencia y la dotación muestra montos solo al activarla.
- La metodología y las fuentes se documentan acá, no dentro del tablero.
