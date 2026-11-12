# Método y criterios · Costo de servir

## El modelo de negocio

Mayorista Ruta Sur compra a fabricantes y reparte a comercios con 5 camiones propios. Gana por margen bruto (lo que compra contra lo que vende) y gasta en tres cosas que dependen de cada cliente: **preparar** el pedido en el depósito, **llevarlo** y **esperar a cobrarlo**. Las devoluciones suman un cuarto costo. Gerencia, administración y alquiler son estructura: no dependen de un cliente en particular.

El problema típico: el informe de rentabilidad por cliente muestra margen bruto, o reparte los gastos por ventas. Así, el que compra poco, seguido y lejos parece tan bueno como el que compra mucho una vez por semana.

## Del estado de resultados a la tasa

| Paso | Qué se hace | Ejemplo |
|---|---|---|
| 1. Cuenta → actividad | Cada cuenta del estado de resultados va a una actividad | Sueldos del depósito → Preparación |
| 2. Actividad → driver | Se elige qué hace crecer ese costo | Preparación: 55 % fijo por pedido, 45 % por bulto (relevamiento de tiempos) |
| 3. Tasa | Costo de la actividad ÷ cantidad del driver | $ 7.232 mil ÷ 582 pedidos = $ 12,4 mil por pedido |
| 4. Cliente | Tasa × lo que consume cada cliente | 13,8 pedidos × 12,4 = $ 171 mil |

Drivers del caso:

| Actividad | Driver | Por qué ese |
|---|---|---|
| Preparación | Pedidos y bultos | Armar remito, controlar y cargar es casi igual para 2 que para 20 bultos; el picking crece con los bultos |
| Reparto | Visitas y km | Tiempo en la parada (descargar, cobrar, firmar) y tiempo manejando; combustible y mantenimiento por km |
| Urgentes | Visita + 3 veces el km de desvío | Es un viaje fuera de ruta, ida y vuelta desde el depósito |
| Financiamiento | Ventas × días de cobro ÷ 30 × 3 % | El saldo que se financia, al costo del descubierto (o lo que rendiría la plata) |
| Devoluciones | 30 % de lo devuelto | 20 % de merma y 10 % de manipuleo y re-entrega |

## Preguntas frecuentes

**¿Por qué no repartir por ventas, que es más simple?**
Porque supone que vender $ 1 cuesta lo mismo en cualquier cliente. En el caso, el prorrateo les pasa $ 6,3 M por mes de costo a los clientes grandes y bien atendidos, y los 18 que pierden aparecen con ganancia.

**¿Los porcentajes de reparto (55 % fijo por pedido, 50 % en la parada) no son arbitrarios?**
Salen de un relevamiento de dos semanas. Y se prueba si importan: la sección de sensibilidad los mueve entre 30 % y 80 %. Con criterios extremos pierden entre 13 y 26 clientes; al menos 13 de los 18 siguen en la lista. Cambia el monto, no la conclusión.

**Si dejo de atender a los 18, ¿gano $ 2,8 M por mes?**
No. El camión sale igual: hasta que se achique la flota o las horas, el costo de reparto queda. Además se pierde su margen bruto. Por eso el caso propone cambiar cómo se los atiende antes que dejarlos.

**¿Por qué la estructura no se asigna?**
Porque no cambia con un cliente más o menos. Asignarla por ventas haría parecer que un cliente chico pierde plata cuando en realidad cubre su costo y aporta algo a la estructura.

**¿Qué pasa con la inflación?**
Los montos están en moneda de octubre de 2026. Con inflación alta, el plazo de cobro pesa más: por eso la tasa del 3 % mensual se revisa cuando cambia la tasa del banco.

**¿Cada cuánto se actualiza?**
El ranking, todos los meses con facturas, hoja de ruta y cobranzas. Las tasas, cada trimestre o cuando cambia algo grande (sueldos, combustible, un camión más).

**¿Sirve para una empresa que no reparte?**
Sí, cambian los drivers. En un servicio técnico: visitas, horas y repuestos; en un BPO: llamadas, minutos y reclamos; en un e-commerce: envíos, devoluciones y medio de pago.

## Supuestos

- Los costos del mes no cambian con el volumen en el corto plazo; las tasas son promedio del semestre.
- Un pedido es una visita (salvo los urgentes, que son una visita aparte).
- El km de desvío ya incluye la parte del recorrido troncal que le toca al cliente por su zona.
- En el simulador, el pedido mínimo junta los pedidos chicos sin cambiar los bultos del mes, salvo el porcentaje de ventas perdidas elegido.
