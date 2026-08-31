// Archivo JS mínimo recreado. Mantener pequeño para evitar errores si los templates esperan este archivo.
document.addEventListener('DOMContentLoaded', function(){
  // Cerrar alertas
  document.querySelectorAll('.alert .alert-close').forEach(function(el){
    el.addEventListener('click', function(){
      var p = el.closest('.alert'); if(p) p.style.display='none';
    });
  });

  var navMenu = document.querySelector('.navbar-menu');
  var navToggle = document.querySelector('.mobile-nav-toggle');

  if(navToggle && navMenu){
    navToggle.addEventListener('click', function(){
      navMenu.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', navMenu.classList.contains('is-open') ? 'true' : 'false');
    });
  }

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
      if(!document.getElementById('theme-dark-css')){
        var l = document.createElement('link');
        l.rel = 'stylesheet';
        l.href = '/static/css/theme-dark.css';
        l.id = 'theme-dark-css';
        document.head.appendChild(l);
      }
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      var e = document.getElementById('theme-dark-css');
      if(e) e.parentNode.removeChild(e);
      document.documentElement.setAttribute('data-theme', 'light');
    }
    if(toggle) toggle.textContent = (name === 'dark') ? '🌙' : '☀️';
  }
});
