/**
 * VOZ DE PRIMERA LINEA - Resumen semanal (Google Apps Script)
 * ------------------------------------------------------------------
 * Que hace:
 *   Cada lunes arma una hoja "Resumen semanal" en la planilla de respuestas del
 *   formulario, con:
 *     1) Reportes de la semana pasada por ruta (filas) y por motivo (columnas).
 *     2) Un AVISO cuando un motivo sube mucho contra el promedio de las 4
 *        semanas anteriores (por ruta y para todas las rutas juntas).
 *
 * Como instalarlo (5 minutos, no hace falta saber programar):
 *   1. Abrí la planilla donde caen las respuestas del formulario.
 *   2. Menu: Extensiones > Apps Script.
 *   3. Borrá lo que haya, pegá TODO este archivo y apretá el disquete (Guardar).
 *   4. Revisá la seccion CONFIGURACION de abajo (nombres de hoja y de columnas).
 *   5. En el selector de funciones (arriba) elegí "resumenSemanal" y apretá
 *      Ejecutar. La primera vez Google pide permisos: Revisar permisos > tu
 *      cuenta > Avanzado > Continuar > Permitir. Es tu propia planilla.
 *   6. Mirá que aparezca la hoja "Resumen semanal".
 *   7. Para que corra solo cada lunes: elegí "crearDisparadorSemanal" y
 *      apretá Ejecutar UNA vez. (A mano: icono del reloj > Agregar activador >
 *      funcion resumenSemanal > Segun el tiempo > Semanal > Lunes > 7 a 8 h.)
 *
 * Que NO hace: no manda mails ni toca las respuestas. Solo lee y escribe
 * la hoja "Resumen semanal" (si existe, la reescribe entera).
 */

// ===================== CONFIGURACION (lo unico que se toca) =====================
var CONFIG = {
  // Nombre de la hoja donde Forms guarda las respuestas.
  // Suele ser "Respuestas de formulario 1" (o "Form Responses 1" si tu cuenta esta en ingles).
  HOJA_RESPUESTAS: 'Respuestas de formulario 1',
  HOJA_RESUMEN: 'Resumen semanal',

  // Texto que tiene que aparecer en el ENCABEZADO de cada columna (no importa
  // mayuscula ni tilde). Se busca en la fila 1 de la hoja de respuestas.
  COL_FECHA: 'marca temporal',
  COL_RUTA: 'ruta',
  COL_MOTIVO: 'motivo',

  // Regla del aviso: el motivo tiene que tener al menos MIN_REPORTES esa semana
  // Y ser MULTIPLO veces el promedio semanal de las 4 semanas anteriores.
  MIN_REPORTES: 4,
  MULTIPLO: 2,        // 2 = el doble. Bajalo a 1.5 para avisos mas sensibles.
  SEMANAS_PROMEDIO: 4
};
// ================================================================================

var DIA_MS = 24 * 60 * 60 * 1000;

/** Funcion principal: es la que corre cada lunes. */
function resumenSemanal() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hoja = ss.getSheetByName(CONFIG.HOJA_RESPUESTAS);
  if (!hoja) throw new Error('No encuentro la hoja "' + CONFIG.HOJA_RESPUESTAS + '". Revisá CONFIG.HOJA_RESPUESTAS.');

  var datos = hoja.getDataRange().getValues();
  if (datos.length < 2) throw new Error('Todavia no hay respuestas.');
  var enc = datos[0];
  var iFecha = buscarColumna(enc, CONFIG.COL_FECHA);
  var iRuta = buscarColumna(enc, CONFIG.COL_RUTA);
  var iMotivo = buscarColumna(enc, CONFIG.COL_MOTIVO);

  // Semana que se resume = la ultima semana COMPLETA (lunes a domingo).
  var lunesActual = lunesDe(new Date());
  var lunesResumen = new Date(lunesActual.getTime() - 7 * DIA_MS);

  // Contadores:  conteo[semanaIndice][ruta][motivo]
  //   semanaIndice 0 = la semana resumida, 1 = la anterior, ... hasta SEMANAS_PROMEDIO
  var conteo = {};
  var rutas = {}, motivos = {};
  for (var i = 1; i < datos.length; i++) {
    var f = datos[i][iFecha];
    var ruta = String(datos[i][iRuta]).trim();
    var motivo = String(datos[i][iMotivo]).trim();
    if (!(f instanceof Date) || !ruta || !motivo) continue;
    var k = Math.round((lunesResumen.getTime() - lunesDe(f).getTime()) / (7 * DIA_MS));
    if (k < 0 || k > CONFIG.SEMANAS_PROMEDIO) continue; // futuro o muy viejo
    rutas[ruta] = true; motivos[motivo] = true;
    if (!conteo[k]) conteo[k] = {};
    if (!conteo[k][ruta]) conteo[k][ruta] = {};
    conteo[k][ruta][motivo] = (conteo[k][ruta][motivo] || 0) + 1;
  }
  var listaRutas = Object.keys(rutas).sort();
  var listaMotivos = Object.keys(motivos).sort();

  // ---------- armado de la hoja ----------
  var out = ss.getSheetByName(CONFIG.HOJA_RESUMEN) || ss.insertSheet(CONFIG.HOJA_RESUMEN);
  out.clear();
  var zona = ss.getSpreadsheetTimeZone();
  var desde = Utilities.formatDate(lunesResumen, zona, 'dd/MM/yyyy');
  var hasta = Utilities.formatDate(new Date(lunesResumen.getTime() + 6 * DIA_MS), zona, 'dd/MM/yyyy');
  var fila = 1;

  out.getRange(fila, 1).setValue('Resumen semanal: ' + desde + ' al ' + hasta)
     .setFontSize(14).setFontWeight('bold');
  out.getRange(fila + 1, 1).setValue('Generado el ' + Utilities.formatDate(new Date(), zona, 'dd/MM/yyyy HH:mm') +
     '. Es una señal de la primera línea, no una encuesta estadística.').setFontColor('#666666');
  fila += 3;

  // 1) AVISOS
  var avisos = calcularAvisos(conteo, listaRutas, listaMotivos);
  out.getRange(fila, 1).setValue('Avisos (suben mucho contra el promedio de las ' + CONFIG.SEMANAS_PROMEDIO + ' semanas anteriores)')
     .setFontWeight('bold');
  fila++;
  if (avisos.length === 0) {
    out.getRange(fila, 1).setValue('Sin avisos esta semana.');
    fila++;
  } else {
    var cab = [['Dónde', 'Motivo', 'Esta semana', 'Promedio previo', 'Veces']];
    out.getRange(fila, 1, 1, 5).setValues(cab).setFontWeight('bold').setBackground('#e9eef4');
    out.getRange(fila + 1, 1, avisos.length, 5).setValues(avisos);
    out.getRange(fila + 1, 1, avisos.length, 5).setBackground('#fdeaea');
    fila += avisos.length + 1;
  }
  fila += 2;

  // 2) TABLA ruta x motivo de la semana
  out.getRange(fila, 1).setValue('Reportes de la semana por ruta y motivo').setFontWeight('bold');
  fila++;
  var enc2 = ['Ruta'].concat(listaMotivos, ['Total']);
  var tabla = [];
  var totalesCol = listaMotivos.map(function () { return 0; });
  var totalGeneral = 0;
  listaRutas.forEach(function (ruta) {
    var linea = [ruta], sumaRuta = 0;
    listaMotivos.forEach(function (m, j) {
      var n = valor(conteo, 0, ruta, m);
      linea.push(n); sumaRuta += n; totalesCol[j] += n;
    });
    linea.push(sumaRuta); totalGeneral += sumaRuta;
    tabla.push(linea);
  });
  tabla.push(['TOTAL'].concat(totalesCol, [totalGeneral]));
  out.getRange(fila, 1, 1, enc2.length).setValues([enc2]).setFontWeight('bold').setBackground('#e9eef4').setWrap(true);
  out.getRange(fila + 1, 1, tabla.length, enc2.length).setValues(tabla);
  out.getRange(fila + tabla.length, 1, 1, enc2.length).setFontWeight('bold');
  // Escala de color simple: mas reportes = mas oscuro
  var rango = out.getRange(fila + 1, 2, listaRutas.length, listaMotivos.length);
  var regla = SpreadsheetApp.newConditionalFormatRule()
    .setGradientMinpoint('#ffffff').setGradientMaxpoint('#f4a6a6').setRanges([rango]).build();
  out.setConditionalFormatRules([regla]);
  fila += tabla.length + 3;

  // 3) Motivos de la semana, de mayor a menor (para todas las rutas)
  out.getRange(fila, 1).setValue('Ranking de motivos (todas las rutas)').setFontWeight('bold');
  fila++;
  var ranking = listaMotivos.map(function (m, j) { return [m, totalesCol[j]]; })
    .sort(function (a, b) { return b[1] - a[1]; });
  if (ranking.length) out.getRange(fila, 1, ranking.length, 2).setValues(ranking);

  out.setColumnWidth(1, 230);
  out.autoResizeColumns(2, Math.max(enc2.length - 1, 1));
  SpreadsheetApp.flush();
}

/**
 * Compara cada motivo (por ruta y para el total) contra el promedio semanal
 * de las semanas anteriores. Devuelve filas: [donde, motivo, esta semana, promedio, veces]
 */
function calcularAvisos(conteo, listaRutas, listaMotivos) {
  var avisos = [];
  var destinos = listaRutas.concat(['TODAS LAS RUTAS']);
  destinos.forEach(function (ruta) {
    listaMotivos.forEach(function (m) {
      var ahora = valor(conteo, 0, ruta, m);
      var suma = 0;
      for (var k = 1; k <= CONFIG.SEMANAS_PROMEDIO; k++) suma += valor(conteo, k, ruta, m);
      var promedio = suma / CONFIG.SEMANAS_PROMEDIO;
      if (ahora >= CONFIG.MIN_REPORTES && ahora >= promedio * CONFIG.MULTIPLO) {
        var veces = promedio > 0 ? Math.round(ahora / promedio * 10) / 10 : 'nuevo';
        avisos.push([ruta, m, ahora, Math.round(promedio * 10) / 10, veces]);
      }
    });
  });
  // Primero los que mas reportes tienen
  avisos.sort(function (a, b) { return b[2] - a[2]; });
  return avisos;
}

/** Cantidad de reportes de una semana/ruta/motivo. Con 'TODAS LAS RUTAS' suma todas. */
function valor(conteo, k, ruta, motivo) {
  var s = conteo[k];
  if (!s) return 0;
  if (ruta === 'TODAS LAS RUTAS') {
    var t = 0;
    for (var r in s) t += (s[r][motivo] || 0);
    return t;
  }
  return (s[ruta] && s[ruta][motivo]) || 0;
}

/** Lunes (a las 00:00) de la semana a la que pertenece la fecha. */
function lunesDe(fecha) {
  var d = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
  var dia = (d.getDay() + 6) % 7; // lunes = 0 ... domingo = 6
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - dia);
}

/** Busca la columna cuyo encabezado contiene el texto (sin mayusculas ni tildes). */
function buscarColumna(encabezados, texto) {
  var quitar = function (s) { return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
  for (var i = 0; i < encabezados.length; i++) {
    if (quitar(encabezados[i]).indexOf(quitar(texto)) !== -1) return i;
  }
  throw new Error('No encuentro una columna que diga "' + texto + '" en la fila 1. Revisá CONFIG.');
}

/**
 * Corré esta funcion UNA sola vez: deja programado el resumen todos los
 * lunes entre las 7 y las 8 de la mañana. Si la corrés dos veces no duplica:
 * borra el disparador anterior antes de crear el nuevo.
 */
function crearDisparadorSemanal() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'resumenSemanal') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('resumenSemanal')
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).create();
  Logger.log('Listo: resumenSemanal va a correr los lunes a las 7 h.');
}
