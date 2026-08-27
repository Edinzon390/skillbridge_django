// Archivo JS mínimo recreado. Mantener pequeño para evitar errores si los templates esperan este archivo.
document.addEventListener('DOMContentLoaded', function(){
  requestAnimationFrame(function(){
    document.body.classList.add('page-ready');
  });

  // Cerrar alertas
  document.querySelectorAll('.alert .alert-close').forEach(function(el){
    el.addEventListener('click', function(){
      var p = el.closest('.alert');
      if(p){
        p.classList.add('is-dismissing');
        window.setTimeout(function(){ p.style.display='none'; }, 220);
      }
    });
  });

  // Fade between internal GET navigations without delaying external or modified clicks.
  document.querySelectorAll('a[href]').forEach(function(link){
    link.addEventListener('click', function(event){
      if(event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
         event.shiftKey || event.altKey || link.target === '_blank' || link.hasAttribute('download')){
        return;
      }
      var url = new URL(link.href, window.location.href);
      if(url.origin !== window.location.origin || url.pathname === window.location.pathname){
        return;
      }
      event.preventDefault();
      document.body.classList.add('page-leaving');
      window.setTimeout(function(){ window.location.href = url.href; }, 180);
    });
  });

  // Theme toggle: busca preferencia en localStorage o en el atributo data-theme
  var current = localStorage.getItem('site-theme') || document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current);

  var toggle = document.getElementById('theme-toggle');
  if(toggle){
    toggle.addEventListener('click', function(){
      var t = (localStorage.getItem('site-theme') || 'light') === 'light' ? 'dark' : 'light';
      localStorage.setItem('site-theme', t);
      applyTheme(t);
    });
  }

  function applyTheme(name){
    if(name === 'dark'){
      // add dark stylesheet if not present
      if(!document.getElementById('theme-dark-css')){
        var l = document.createElement('link');
        l.rel = 'stylesheet';
        l.href = '/static/css/theme-dark.css';
        l.id = 'theme-dark-css';
        document.head.appendChild(l);
      }
      document.documentElement.setAttribute('data-theme','dark');
    } else {
      var e = document.getElementById('theme-dark-css');
      if(e) e.parentNode.removeChild(e);
      document.documentElement.setAttribute('data-theme','light');
    }
    // update toggle label if exists
    if(toggle) toggle.textContent = (name === 'dark') ? '🌙' : '☀️';
  }

  // Simple mobile menu toggle si se requiere más tarde
  var nav = document.querySelector('.navbar');
  if(nav){
    // placeholder: se puede añadir comportamiento de menú móvil
  }
});
