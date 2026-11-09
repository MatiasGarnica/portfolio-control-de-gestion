# Propuesta económica · el mismo control de gestión, según el tamaño de la empresa

Caso 05 (empresa ficticia) · 2026-11-09 · Precios de lista en USD, sin impuestos, verificados el 2026-11-07 en las páginas oficiales salvo donde dice "sin verificar". Fuentes: `02_Formacion\Referencias\04_arquitectura-y-licencias-por-tamano.md` y `05_hosting-y-bases-para-demo.md`. **Antes de presentarla en una empresa real, volver a verificar los precios.**

## La pregunta que responde

"Queremos ver el desvío de cada local todos los meses. ¿Qué necesitamos, cuánto sale y quién lo hace?"

## Tres opciones

| | **A · Chica** | **B · Mediana** | **C · Grande** |
|---|---|---|---|
| **Para quién** | Dueño + 1 o 2 personas | Gerente general + 3 a 5 gerentes | Dirección, regionales y gerentes de local (≈200 lectores, ≈10 que construyen) |
| **Qué ven** | Tablero HTML o Looker Studio con el detalle y la conclusión del mes | Power BI con 3 páginas (general, por área, detalle) y alertas | Power BI con los 3 niveles (red → local → causa), ranking, puente del desvío y comentarios del responsable |
| **Seguridad** | Todos ven todo | Cada gerente ve su área (seguridad por filas) | Cada gerente ve su local o región; registro de accesos |
| **Actualización** | Script programado (Python o Apps Script) | Hasta 8 veces por día (Pro) | Hasta 48 veces por día (capacidad) |
| **Costo de licencias** | **USD 0** (Looker Studio y HTML gratis) | **≈ USD 84 / mes** (6 licencias Pro × USD 14) ≈ USD 1.000 / año | **≈ USD 2.940 / mes** con 210 licencias Pro, o capacidad F64 ≈ USD 5.000–8.500 / mes *(F64: sin verificar)*. Pro conviene hasta ≈ 350 usuarios |
| **Lo que pone Sistemas** | Nada, o una carpeta compartida | Gateway (gratis) en un servidor prendido + usuario de solo lectura a la base | Data warehouse o vistas, cuenta de servicio, cargas programadas, administración de accesos |
| **Lo que hago yo (control de gestión)** | Todo: datos, cálculo y tablero | Modelo, medidas, tablero y diccionario de indicadores | Modelo, indicadores, diseño de los 3 niveles, reglas de seguridad y circuito de comentarios |
| **Tiempo de armado** | 1 a 2 semanas | 3 a 5 semanas | 2 a 3 meses (depende de Sistemas) |
| **Riesgo principal** | El HTML lleva todos los datos adentro y se puede reenviar | Cada área con "su" número si no hay diccionario común | Lentitud de los cambios y dependencia de Sistemas |

## Alternativa sin licencias por usuario (mediana)

Si la empresa ya tiene **SQL Server 2025 Standard**, incluye **Power BI Report Server**: los tableros quedan en un servidor propio, los usuarios entran con su usuario de Windows y no hace falta pagar licencias por lector. El costo es el del servidor que ya existe más el trabajo de Sistemas. *(Verificar la edición y la licencia vigente con Sistemas).*

Variante aún más barata: **página interna generada por script** en un servidor con login de Windows. Gratis, pero **cada sector debe tener su propio archivo** (un HTML lleva todos los datos adentro).

## Recomendación según el punto de partida

- **Si hoy todo es Excel** → arrancar por **A** (1 o 2 semanas, costo cero) para validar qué números se miran. Pasar a **B** cuando haya 3 o más gerentes que necesiten ver distinto.
- **Si ya hay SQL Server** → **B con Report Server** antes que pagar licencias.
- **Si hay más de 50 lectores o datos sensibles por local** → **C**. La seguridad por filas y el registro de accesos dejan de ser opcionales.

## Lo que esta propuesta no incluye

- Horas de consultoría externa.
- Hardware nuevo.
- Licencias de Microsoft 365 que la empresa ya tenga.
- El costo de "no hacerlo": decisiones tomadas con números distintos en cada área.
