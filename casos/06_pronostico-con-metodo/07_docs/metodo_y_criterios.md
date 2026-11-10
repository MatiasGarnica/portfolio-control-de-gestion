# Método y criterios · Caso 06 (Fogón Express, empresa ficticia)

**Para quién es esta nota:** el analista o el gerente que quiere auditar el pronóstico. El tablero muestra el dato; acá está de dónde sale, por qué se decidió así y qué preguntas conviene tener respondidas.

Datos: los del Caso 05 (12 locales, nov-2024 a oct-2026, 24 meses). Cálculo: `02_codigo/pronosticar.py` (pandas y numpy, sin aleatoriedad). Los números de esta nota salen de esa corrida.

---

## 1. Definiciones

| Término | Qué es | Fórmula |
|---|---|---|
| **Moneda constante** | Pesos de octubre de 2026, sin inflación. | Real: importe × IPC(oct-26) / IPC(mes). Presupuesto: se deflacta con el IPC **que supuso el propio presupuesto**, para que su error en moneda constante sea de volumen y no de inflación. |
| **Backtest** | Pronosticar el pasado con lo que se sabía en ese momento y comparar con lo que pasó. | Se "corta" la historia en un mes, se entrena con lo anterior y se mide el error en los meses siguientes. |
| **Rolling origin** | Repetir el backtest moviendo el corte, para no depender de un solo mes. | Cortes de ene-26 a sep-26, pronóstico de 1 a 3 meses (24 pares mes-corte por local). |
| **WAPE** (error) | Cuánto se equivoca, en % de lo real, sin importar el signo. | Σ \|pronóstico − real\| / Σ real. Se calcula a nivel red (sumando locales cada mes) y a nivel local. |
| **MAPE** | Promedio de los errores % de cada mes. | Se calcula en el código, pero no se usa para elegir: un mes chico con un error chico en pesos pesa igual que diciembre. El WAPE pondera por tamaño. |
| **Sesgo** | Si el error va siempre para el mismo lado. | Σ (pronóstico − real) / Σ real. Positivo = pronosticó de más. |
| **Intervalo (rango probable 80 %)** | La zona donde debería caer 8 de cada 10 veces. | Pronóstico × (1 ± 1,28 × σ), con σ = error cuadrático medio relativo del backtest. Para totales de varios meses: σ = √(sesgo² + ruido² / n): el sesgo se repite todos los meses, el ruido se compensa. |
| **Bandas de control** | El "ruido normal" de un local. | Centro ± 2 desvíos, con centro y desvío robustos (mediana y MAD × 1,4826). |
| **Señal** | Un desvío que merece explicación. | Reglas de Western Electric: (1) un mes fuera de ±3 desvíos; (2) 2 de 3 meses seguidos fuera de ±2 del mismo lado; (3) 8 meses seguidos del mismo lado del centro. |

## 2. Qué se pronostica y cómo

1. **Ventas por local y mes, en moneda constante.** Se pronostica sin inflación y se reinfla después: así el modelo aprende volumen y precio relativo, y la inflación queda como un supuesto explícito (escenarios).
2. **Contribución por local** = margen variable × ventas pronosticadas − costos fijos, estimados con una regresión simple sobre los últimos 12 meses de cada local. Capta el apalancamiento operativo: en diciembre el margen sube porque los fijos se diluyen.
3. **Red** = suma de los locales (de abajo hacia arriba).
4. **Pesos corrientes** = moneda constante × (1 + inflación del escenario)^meses desde oct-26.

### Métodos comparados (todos en moneda constante)

| Método | Qué hace | Para qué está en la comparación |
|---|---|---|
| Ingenuo estacional | Mismo mes del año anterior | El mínimo a vencer: si un modelo no le gana, no sirve |
| Ingenuo + crecimiento | Mismo mes del año anterior × crecimiento interanual de los últimos 3 meses | Lo que hace a mano la mayoría de los analistas |
| Promedio móvil 3 meses | Promedio de los últimos 3 meses, plano | Muestra qué pasa si se ignora la estacionalidad |
| Regresión, estacionalidad propia de cada local | log(ventas) = nivel del local + 11 coeficientes de mes del local + tendencia común | Muestra el sobreajuste: 11 coeficientes con 2 datos cada uno |
| Regresión, estacionalidad de la red | Igual, con un solo patrón de meses para todos | Junta datos para estimar mejor la estacionalidad |
| **Regresión, estacionalidad por tipo de local** (elegido) | Igual, con un patrón para locales urbanos (calle y shopping) y otro para los de ruta | Los de ruta tienen temporada de verano marcada; mezclarlos con los urbanos distorsiona a los dos |
| **Presupuesto** | Lo que se presupuestó para cada mes | El "método" que usa hoy la empresa |

Detalles de la regresión:
- Mínimos cuadrados con numpy sobre el logaritmo (los efectos de mes y de tendencia son porcentuales).
- **Robusta en dos pasadas**: se ajusta, se sacan los meses con residuo mayor a 3 desvíos robustos y se vuelve a ajustar. Así la obra de L03 (−25 % durante 6 meses) no contamina el nivel del local ni la tendencia de la red. La regla es automática y se aplica en cada corte del backtest con la información de ese momento.
- **Tendencia solo con 18 meses o más.** Con 12 meses cada mes del año aparece una vez: un enero alto puede ser estacionalidad o tendencia y la regresión no tiene cómo distinguirlos.
- **Rampa de apertura**: los primeros 6 meses de un local nuevo no entrenan el modelo (afecta a L05, que abrió en nov-25).

## 3. Backtest y elección

Dos pruebas, solo con los 11 locales abiertos todo el período:

| Prueba | Corte | Meses evaluados | Imita a… |
|---|---|---|---|
| A 1-3 meses | 9 cortes, ene-26 a sep-26 | 24 pares corte-mes | Un pronóstico de cierre (nov-dic = 1 y 2 meses adelante) |
| A 12 meses | oct-25 | nov-25 a oct-26 | Un presupuesto anual |

Resultados (WAPE de la red · sesgo):

| Método | 1-3 meses | 12 meses | Error por local, 12 meses |
|---|---|---|---|
| Ingenuo estacional | 2,6 % · +2,5 % | 2,2 % · +2,1 % | 4,3 % |
| Ingenuo + crecimiento | 2,2 % · 0 % | 2,2 % · +2,1 % | 4,3 % |
| Promedio móvil 3 meses | 6,0 % · +1,9 % | 4,8 % · −0,4 % | 5,9 % |
| Regresión, estacionalidad propia | 2,0 % · +1,4 % | 2,2 % · +2,1 % | 4,3 % |
| Regresión, estacionalidad de la red | 2,0 % · +0,9 % | 2,1 % · +1,7 % | 4,3 % |
| **Regresión, por tipo de local** | **1,9 % · +1,4 %** | **2,1 % · +2,0 %** | **3,8 %** |
| Presupuesto | 7,5 % · +7,5 % | 6,7 % · +6,7 % | 6,7 % |

**Criterio de elección, fijado antes de mirar:** el menor promedio de los cuatro WAPE (red y local, 1-3 y 12 meses), porque el pronóstico se usa para la red (cierre, presupuesto) y para cada local (metas). Gana la regresión por tipo de local.

**Lo que hay que decir con honestidad:** a nivel red, los métodos razonables empatan (1,9 % a 2,6 %): las diferencias de décimas son menores que el ruido. La regresión gana por local, sirve para L05 (que todavía no tiene "mismo mes del año anterior" normal) y separa estacionalidad de tendencia. Lo que pierde por lejos es el presupuesto: error 3 veces mayor y todo sesgo.

**Control de cordura (solo posible con datos ficticios):** la estacionalidad estimada se parece a la que se usó para generar los datos. Urbano: enero 1,04 (real 1,05), julio 1,06 (1,06), diciembre 1,09 (1,10). Ruta: enero 1,22 (1,25), junio 0,87 (0,88).

### Contribución

| Cómo se pasa de ventas a contribución | 1-3 meses | 12 meses |
|---|---|---|
| **Margen variable × ventas − fijos** (elegido) | 9,5 % · +6,6 % | 9,6 % · +6,0 % |
| Margen promedio 12 meses × ventas | 14,8 % · +11,1 % | 14,1 % · +6,2 % |
| Mismo método aplicado directo a la contribución | 11,0 % · +9,1 % | 10,2 % · +4,1 % |
| Presupuesto | 27,2 % · +27,2 % | 22,4 % · +22,4 % |

La contribución es una resta: cualquier error en ventas o costos se agranda. Y el sesgo positivo (+6 %) es real: 2026 tuvo tres problemas operativos que ningún método prevé. Recomendación: presupuestar la contribución con una reserva de ese tamaño.

## 4. Resultados

| | Ventas | Contribución |
|---|---|---|
| Cierre 2026 (real ene-oct + pronóstico nov-dic, IPC base) | $ 18.926,9 M (+5,7 % vs ppto) | $ 3.002,6 M (−9,3 % vs ppto) |
| Rango 80 % del cierre | $ 18.813 M a $ 19.040 M | $ 2.913 M a $ 3.092 M |
| 2027 en moneda constante (pesos de oct-26) | $ 20.305 M (−0,1 % vs 2026) | $ 3.222 M (+0,3 %) |
| Rango 80 % 2027 | $ 19.822 M a $ 20.788 M | $ 2.883 M a $ 3.561 M |
| 2027 en pesos corrientes, IPC base 2,0 % mensual | $ 24.102 M (+27,3 %) | $ 3.831 M |

**Por qué la venta real no crece:** en los 6 locales sin señales, los tickets crecieron +0,3 % y el ticket promedio real cayó −1,0 % (la carta se actualiza con un mes de atraso y traslada menos que la inflación). La tendencia de la regresión, −1,2 % anual, lo confirma. L05 (un año completo en 2027) y la vuelta de L03 a la normalidad compensan esa caída.

**El presupuesto de nov-dic 2026 no está en los datos.** Se completó con los supuestos del propio presupuesto: el valor de oct-26 de cada local, llevado con la relación nov/oct y dic/oct que tenía el presupuesto 2025 para su tipo de local, ajustada de 1,8 % a 1,6 % de inflación mensual. Da $ 3.441 M de ventas y $ 745 M de contribución para esos dos meses.

## 5. Inflación

Se pronostica en moneda constante y se reinfla con tres escenarios de inflación mensual para nov-26 a dic-27:

| Escenario | Mensual | Anual 2027 | De dónde sale |
|---|---|---|---|
| Bajo | 1,6 % | 21,0 % | La que supuso el presupuesto 2026, que resultó corta |
| Base | 2,0 % | 26,8 % | Promedio de los últimos 3 meses (1,97 %) |
| Alto | 2,5 % | 34,5 % | Promedio de los últimos 12 meses (2,47 %) |

En los tres, el crecimiento en pesos de 2027 (+23 % a +33 %) es todo precio: el volumen queda en −0,1 %. Efecto precio = (1 + crecimiento nominal) / (1 + crecimiento real) − 1.

El IPC es el ficticio de `dim_calendario` (Caso 05). En los últimos 12 meses hubo 33,9 % de inflación; el presupuesto había supuesto 21,5 %.

## 6. Ruido o señal: bandas de control

**Indicadores** (los dos limpian estacionalidad, inflación y lo que le pasó a toda la red):
- **Ventas**: crecimiento interanual del local en moneda constante − crecimiento mediano de los locales ese mes (p.p.). Desvío típico: 3,6 p.p.
- **Margen**: cambio interanual del margen de contribución del local − cambio mediano de los locales (p.p.). Desvío típico: 2,2 p.p.

**Decisiones:**
- **Referencia = mediana de los locales, no el total de la red.** Si un local se cae 25 %, el total baja y todos los demás parecen "crecer más que la red" sin haber hecho nada.
- **Desvío robusto (MAD).** El desvío clásico da 6,5 p.p. en ventas y 4,5 p.p. en margen porque lo inflan los propios meses raros: con esa banda, la obra de L03 casi no se vería.
- **Interanual y no contra el presupuesto.** Con la regla "±5 % contra presupuesto", los 11 locales piden explicación (7 de cada 12 meses en promedio): el presupuesto sesgado genera alarmas en todos lados.
- **Reglas de racha, no solo puntos.** Un problema persistente pero moderado (L07: −7 % de tickets) no saca ningún mes de la banda en ventas, pero sí arma una racha en el margen.
- L05 no entra: no tiene año anterior.

**Resultado (nov-25 a oct-26):**

| Local | Ventas | Margen | Causa registrada (Caso 05) | ¿Coincide? |
|---|---|---|---|---|
| L03 | Señal mar-ago, abajo | Señal mar-ago, abajo | Obra vial en el acceso (mar-ago) | Sí |
| L07 | Ruido | Señal feb-oct, abajo (2 de 3 y racha de 8) | Renuncia del encargado, rotación desde enero | Sí, solo en margen |
| L10 | Ruido | Señal jun, abajo | Rotura de cámara de frío (jun) | Sí |
| L01 | Señal jun, arriba | Señal jun, arriba | — | Mes aislado hacia arriba |
| L09 | Señal may, arriba | Señal may, arriba | — | Mes aislado hacia arriba |

Las tres situaciones plantadas aparecen. Las dos sobrantes son un mes aislado hacia arriba, sin causa: con 264 mediciones alguna falsa alarma es esperable, y los márgenes tienen colas más pesadas que una normal. Se pregunta (puede haber algo para copiar) pero no se premia ni se castiga.

## 7. Limitaciones

- **24 meses**: cada mes del año se vio dos veces. La estacionalidad se estima por tipo de local y la tendencia recién con 18 meses.
- **Un solo año de backtest** (2026), con tres problemas operativos. Otro año podría dar errores distintos.
- **Meses 13 y 14** (nov-dic 2027) sin respaldo en el backtest.
- **El intervalo supone que el error futuro se parece al pasado** y que es aproximadamente normal. No incluye la inflación (eso va por escenarios) ni shocks nuevos.
- **Supuestos de negocio**: L07 sigue igual, no abren ni cierran locales, los precios mantienen el atraso de 2026.
- **Presupuesto nov-dic 2026** estimado (ver punto 4).
- Datos ficticios: el método es el punto, no los números.

## 8. Preguntas que te pueden hacer y cómo responderlas

**1. ¿Cómo sabés si un desvío es ruido o señal?**
Comparo cada local con su propio año anterior y con lo que le pasó al resto de los locales ese mes. Mido cuánto se mueve eso normalmente (el desvío típico) y pido explicación cuando un mes sale de ±3 desvíos o cuando varios meses seguidos se van para el mismo lado. Con eso, de 11 locales 5 tienen señal, y las 3 con causa conocida aparecen.

**2. ¿Por qué no usás el desvío contra presupuesto, que es lo que mira todo el mundo?**
Porque si el presupuesto está sesgado, todos los locales parecen desviados. Acá el presupuesto sobreestimó el volumen 6,7 %: con un umbral de ±5 %, los 11 locales pedían explicación. El desvío contra presupuesto sirve para ver si cumplimos; para decidir a quién llamar, sirve el desvío contra lo esperable.

**3. ¿Con qué método proyectás y por qué ese?**
Regresión con tendencia y estacionalidad por tipo de local. Lo elegí con un backtest: lo comparé contra métodos simples y contra el presupuesto, con un criterio fijado antes de mirar. En la red empata con un ingenuo con crecimiento; por local es mejor (3,8 % contra 4,3 %) y sirve para el local nuevo.

**4. ¿Qué tan bueno es tu forecast?**
En la red se equivoca en promedio 1,9 % por mes a 1-3 meses y 2,1 % pronosticando un año entero. El presupuesto, 7,5 % y 6,7 %. Por local, 3,8 %. En contribución el error es mayor: 9,6 %.

**5. ¿Por qué no un modelo más sofisticado (ARIMA, Prophet, machine learning)?**
Con 24 meses no hay historia para estimar muchos parámetros; el backtest muestra que hasta 11 coeficientes por local ya empeoran. Lo sofisticado no garantiza menos error: lo que garantiza algo es medirlo. Si el método simple empata, prefiero el que se explica en una reunión.

**6. Tu método también tiene sesgo positivo, ¿no?**
Sí: +1,4 % a +2,0 % en ventas y +6 % en contribución. Viene de 2026: una obra, una rotura y un problema de personal que nadie podía prever. Es chico comparado con el del presupuesto (+6,7 % en ventas, +22 % en contribución), pero lo informo y propongo una reserva para la contribución.

**7. ¿Cómo tratás la inflación?**
Proyecto en moneda constante y reinflo con escenarios explícitos (1,6 %, 2,0 % y 2,5 % mensual). Así se ve que en 2027 el crecimiento en pesos es todo precio, y si la inflación cambia, se cambia un supuesto sin rehacer el modelo. El presupuesto 2026 mezcló los dos supuestos y erró los dos.

**8. ¿Qué tan confiable es la estacionalidad con solo dos años?**
Poco si la estimo local por local: dos datos por mes. Por eso la estimo por tipo de local, juntando los datos de varios. El backtest confirma que así se equivoca menos que con un patrón por local.

**9. ¿Qué significa el rango del 80 %?**
Que, si el futuro se parece al pasado, 8 de cada 10 meses deberían caer adentro. Sale de los errores que el método cometió en el backtest. No cubre shocks nuevos ni la inflación.

**10. ¿Qué harías distinto con datos reales?**
Más historia (36 meses o más), variables que explican la venta (precios, promociones, días hábiles, aperturas de la competencia), y un control mensual del error del pronóstico para recalibrar. Y un registro de incidentes confiable: es lo que permite separar "algo pasó" de "algo cambió".

**11. ¿Qué decisión tomarías con esto?**
Tres: presupuestar 2027 en moneda constante, sin suponer crecimiento de clientes y con el IPC explícito; ocuparme de L07, que es el único problema abierto y vale $ 83 M de contribución; y revisar la política de precios, porque el ticket real cae 1 % por año.

**12. ¿Y si el gerente dice "el presupuesto es el compromiso, no un pronóstico"?**
Tiene razón: son dos cosas distintas. El presupuesto puede ser una meta exigente; el pronóstico es la mejor estimación de lo que va a pasar. El problema es usar la meta como pronóstico para planificar compras, personal y caja, o para juzgar a los locales: ahí el sesgo se paga.
