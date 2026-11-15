// Choclito mockups: interacciones mínimas (sin dependencias)
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Toast: más tiempo para leer y botón para cerrar
  const toast = $('.toast');
  let tId;
  function say(msg, ms = 7000) {
    if (!toast) return;
    const dlg = document.querySelector('dialog[open]');
    if (toast.parentNode !== (dlg || document.body)) (dlg || document.body).appendChild(toast);
    $('.toast-msg', toast).textContent = msg;
    toast.hidden = false;
    clearTimeout(tId);
    tId = setTimeout(() => (toast.hidden = true), ms);
  }
  window.say = say;
  if (toast && !$('.toast-x', toast)) {
    const x = document.createElement('button');
    x.className = 'toast-x'; x.setAttribute('aria-label', 'Cerrar'); x.textContent = '×';
    x.addEventListener('click', () => (toast.hidden = true));
    toast.appendChild(x);
  }

  // Voz: lee en voz alta el texto indicado (quechua: audio grabado por hablante nativo en la app real)
  $$('[data-speak]').forEach((b) =>
    b.addEventListener('click', () => {
      const lang = document.documentElement.lang;
      const el = document.querySelector(b.dataset.speak);
      const text = el ? el.innerText : b.dataset.text;
      if (lang === 'qu') { say('En quechua sonará un audio grabado por una persona de la zona.'); return; }
      try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); u.lang = 'es-BO'; u.rate = 0.92; speechSynthesis.speak(u); } catch (e) {}
      say('Leyendo en voz alta…', 3000);
    })
  );

  // Idioma ES / QU (borrador quechua, revisar con hablante nativo)
  function setLang(l) {
    $$('[data-qu]').forEach((el) => {
      if (!el.dataset.es) el.dataset.es = el.innerHTML;
      el.innerHTML = l === 'qu' ? el.dataset.qu : el.dataset.es;
    });
    $$('.lang button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === l)));
    document.documentElement.lang = l === 'qu' ? 'qu' : 'es';
    try { localStorage.setItem('lang', l); } catch (e) {}
  }
  window.setLang = setLang;
  $$('.lang button').forEach((b) => b.addEventListener('click', () => {
    const on = b.getAttribute('aria-pressed') === 'true';
    setLang(on ? (b.dataset.lang === 'es' ? 'qu' : 'es') : b.dataset.lang);
  }));
  try { const l = localStorage.getItem('lang'); if (l) setLang(l); } catch (e) {}

  // Botones de un toque que guardan solos
  $$('[data-one-tap]').forEach((b) =>
    b.addEventListener('click', () => {
      const group = b.dataset.group;
      if (group) $$(`[data-group="${group}"]`).forEach((o) => o !== b && o.setAttribute('aria-pressed', 'false'));
      const on = b.getAttribute('aria-pressed') !== 'true';
      b.setAttribute('aria-pressed', String(on));
      if (on) say(b.dataset.msg || 'Guardado. Se envía cuando haya señal.');
      if (on && b.dataset.reveal) { const r = document.querySelector(b.dataset.reveal); if (r) r.hidden = false; }
    })
  );
})();
