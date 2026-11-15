// Datos de ejemplo de la maqueta (sintéticos, etiquetados en pantalla).
// En la app real: NASA (IMERG, SMAP, POWER, GEOS) + SENAMHI + reportes del agricultor + nivel de La Angostura.
window.FS = (() => {
  const MES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  const MES3 = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  const WDL = ['domingo','lunes','martes','miércoles','jueves','viernes','sábado'];
  const WD3 = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
  const TODAY = new Date(2026, 10, 16); // lunes 16 nov 2026
  const d = (y, m, dd) => new Date(y, m, dd);
  const day = 864e5;
  const addDays = (t, n) => new Date(t.getTime() + n * day);
  const diff = (a, b) => Math.round((a - b) / day);
  const fmt = (t) => `${t.getDate()} ${MES3[t.getMonth()]}`;
  const part = (t) => { const x = t.getDate(); return `${x <= 10 ? 'inicios' : x <= 20 ? 'mediados' : 'fines'} de ${MES[t.getMonth()]}`; };

  // Fiestas que el agricultor usa como referencia
  const fiestas = [
    { t: d(2026, 10, 1), n: 'Todos Santos' }, { t: d(2026, 11, 25), n: 'Navidad' }, { t: d(2027, 0, 1), n: 'Año Nuevo' },
    { t: d(2027, 1, 8), n: 'Carnaval' }, { t: d(2027, 2, 28), n: 'Semana Santa' }, { t: d(2027, 4, 3), n: 'Santa Vera Cruz' },
  ];
  const fiestaNear = (t) => fiestas.reduce((b, f) => (Math.abs(diff(f.t, t)) < Math.abs(diff(b.t, t)) ? f : b));
  const fiestaRef = (t) => { const f = fiestaNear(t), k = diff(t, f.t); return Math.abs(k) <= 10 ? `para ${f.n}` : k < 0 ? `antes de ${f.n}` : `después de ${f.n}`; };

  // Perfil del agricultor (lo responde en "Tu agua y tu tierra")
  const perfil = {
    nombre: 'don Mario', zona: 'Itocta', distrito: 'Distrito 9',
    agua: 'La Angostura',
    represa: { nombre: 'La Angostura', nivel: 34, nota: 'poca agua para esta época' },
    tierra: 'algo de salitre',
  };

  // Mis cultivos actuales (cosecha como ventana, no un día)
  const crops = [
    { id: 'maiz', n: 'Maíz', parcela: 'Parcela grande', start: d(2026, 9, 20), color: '#C9A227',
      harvest: [d(2027, 1, 1), d(2027, 1, 28)], harvestName: 'choclo', stages: [[0, 'Recién sembrado'], [21, 'Creciendo'], [80, 'Floración'], [100, 'Choclo']] },
    { id: 'alfalfa', n: 'Alfalfa', parcela: 'Potrero', start: d(2026, 9, 25), color: '#2E7D4F', perenne: true,
      harvest: [d(2026, 11, 1), d(2026, 11, 8)], harvestName: 'corte', stages: [[0, 'Rebrotando'], [25, 'Lista pronto']] , lastCut: d(2026, 9, 25) },
    { id: 'papa', n: 'Papa', parcela: 'Parcela chica', start: d(2026, 9, 5), color: '#8C6A43',
      harvest: [d(2027, 1, 15), d(2027, 2, 10)], harvestName: 'cosecha', stages: [[0, 'Recién sembrada'], [25, 'Brotes'], [45, 'Floración'], [90, 'Engorde'], [125, 'Cosecha']] },
    // Haba: su cosecha fue ayer; hoy la app pregunta "¿Cómo salió?"
    { id: 'haba', n: 'Haba', parcela: 'Borde del canal', start: d(2026, 6, 15), color: '#6E8B3D',
      harvest: [d(2026, 10, 15), d(2026, 10, 25)], harvestName: 'cosecha', stages: [[0, 'Recién sembrada'], [30, 'Creciendo'], [70, 'Floración'], [100, 'Vainas'], [124, 'Cosecha']] },
  ];
  // Siembras planificadas (el agricultor las agregó desde Sembrar con fecha futura)
  const planned = [{ id: 'avena', n: 'Avena', t: d(2026, 11, 5) }];
  // Rotación elegida en "¿Qué sembrar después?": se siembra en abril, después del maíz
  const ROT = { haba: 'Haba', avena: 'Avena', papa: 'Papa' };
  let rot = null; try { rot = localStorage.getItem('plan'); } catch (e) {}
  let rd = null; try { rd = localStorage.getItem('planDate'); } catch (e) {}
  const rt = rd ? new Date(...rd.split('-').map((v, i) => (i === 1 ? v - 1 : +v))) : d(2027, 3, 5);
  if (ROT[rot]) planned.push({ id: rot, n: ROT[rot], t: rt, rot: true });
  const stageOf = (c, t = TODAY) => { const n = diff(t, c.start); let s = c.stages[0][1]; for (const [k, v] of c.stages) if (n >= k) s = v; return s; };
  const ago = (t) => { const n = diff(TODAY, t); return n < 14 ? `${n} días` : n < 60 ? `${Math.round(n / 7)} semanas` : `${Math.round(n / 30)} meses`; };
  const ahead = (t) => { const n = diff(t, TODAY); return n < 14 ? `${n} días` : n < 60 ? `${Math.round(n / 7)} semanas` : `${Math.round(n / 30)} meses`; };

  // Pronóstico 28 días (SENAMHI / NASA GEOS; semanas 3–4 menos seguras)
  const forecast = [
    ['sun', 28, 8, 0], ['sun', 29, 7, 0], ['sun', 30, 6, 0], ['cloud', 27, 4, 0], ['cloud', 25, 2, 1], ['frost', 24, -2, 0], ['sun', 27, 5, 0],
    ['cloud', 26, 7, 0], ['rain', 24, 9, 3], ['cloud', 26, 9, 0], ['hail', 23, 10, 8], ['rain', 22, 11, 6], ['cloud', 25, 10, 2], ['sun', 27, 9, 0],
    ['cloud', 26, 10, 1], ['rain', 24, 11, 4], ['cloud', 25, 10, 2], ['sun', 27, 9, 0], ['sun', 28, 9, 0], ['hail', 23, 11, 3], ['cloud', 25, 10, 2],
    ['cloud', 25, 11, 3], ['rain', 22, 12, 9], ['rain', 21, 12, 11], ['cloud', 24, 11, 2], ['sun', 26, 10, 0], ['rain', 23, 12, 6], ['cloud', 25, 11, 2],
  ].map(([ic, mx, mn, mm], i) => ({ t: addDays(TODAY, i), ic, mx, mn, mm }));

  // Palabras en vez de números
  const lluvia = (mm) => (mm <= 0 ? 'sin lluvia' : mm < 4 ? 'lluvia débil' : mm < 15 ? 'lluvia moderada' : 'lluvia fuerte');
  const tierra = (pct) => (pct < 15 ? 'seca' : pct < 30 ? 'medio húmeda' : 'húmeda');
  const SOIL = 12; // humedad superficial (NASA SMAP)

  // Clima típico por mes
  const tipico = ['lluvias fuertes', 'lluvias fuertes', 'últimas lluvias', 'seco', 'seco y frío', 'heladas', 'heladas fuertes', 'heladas', 'seco y ventoso', 'calor, poca lluvia', 'primeras lluvias', 'lluvias'];
  const riesgoMes = [['granizo', 'desbordes'], ['granizo', 'desbordes'], ['desbordes'], [], ['helada'], ['helada'], ['helada'], ['helada'], ['poca agua'], ['poca agua'], ['granizo', 'poca agua'], ['granizo']];

  // Temporadas del valle
  const seasons = [
    { from: 4, to: 7, n: 'Época seca y de heladas', ic: 'frost', note: 'Heladas más fuertes en julio. Casi no llueve.' },
    { from: 8, to: 9, n: 'Fin de la época seca', ic: 'nowater', note: 'Poca agua en las represas hasta que llegan las lluvias.' },
    { from: 10, to: 11, n: 'Inicio de lluvias y granizo', ic: 'hail', note: 'Primeras lluvias y granizadas, de noviembre a febrero.' },
    { from: 0, to: 1, n: 'Lluvias fuertes y granizo', ic: 'rain', note: 'Cuidado con desbordes de ríos y torrenteras.' },
    { from: 2, to: 3, n: 'Fin de lluvias', ic: 'waves', note: 'Marzo: desbordes como el del canal Valverde en 2024.' },
  ];
  const seasonOf = (m) => seasons.find((s) => (s.from <= s.to ? m >= s.from && m <= s.to : m >= s.from || m <= s.to));
  const anioSeco = true; // El Niño 2026–27

  return { MES, MES3, WDL, WD3, TODAY, perfil, crops, planned, forecast, seasons, seasonOf, stageOf, fmt, part, addDays, diff, ago, ahead,
    lluvia, tierra, SOIL, tipico, riesgoMes, fiestas, fiestaRef, anioSeco };
})();
