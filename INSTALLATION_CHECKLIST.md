# ✅ CHECKLIST DE INSTALACIÓN Y CONFIGURACIÓN

## 🚀 Pasos de Instalación Paso a Paso

### 1. Preparación del Entorno
- [ ] Verificar que Python 3.12+ está instalado: `python --version`
- [ ] Crear entorno virtual: `python -m venv venv`
- [ ] Activar entorno:
  - **Windows**: `venv\Scripts\activate`
  - **Linux/Mac**: `source venv/bin/activate`

### 2. Dependencias
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Verificar instalación: `pip list`

### 3. Base de Datos
- [ ] Ejecutar migraciones: `python manage.py migrate`
- [ ] Crear superusuario: `python manage.py createsuperuser`
  - Usuario: admin
  - Email: admin@example.com
  - Contraseña: (segura)

### 4. Archivos Estáticos
- [ ] Crear carpeta staticfiles: `mkdir staticfiles`
- [ ] Recolectar estáticos: `python manage.py collectstatic --noinput`

### 5. Prueba Inicial
- [ ] Ejecutar servidor: `python manage.py runserver`
- [ ] Acceder a: http://localhost:8000
- [ ] Verificar que carga la landing page
- [ ] Ir a: http://localhost:8000/admin/

### 6. Crear Datos de Prueba (Opcional)
- [ ] Crear usuarios de prueba en admin
- [ ] Asignar roles/grupos a usuarios
- [ ] Crear empresas de ejemplo

## 🔐 Verificaciones de Seguridad

- [ ] Cambiar SECRET_KEY en settings.py
- [ ] Establecer DEBUG = False en producción
- [ ] Configurar ALLOWED_HOSTS correctamente
- [ ] Configurar CSRF_TRUSTED_ORIGINS
- [ ] Revisar CORS si necesita acceso desde otro dominio

## 📋 Verificaciones Funcionales

### Rutas Públicas
- [ ] GET / → Landing page
- [ ] GET /login/ → Página de login
- [ ] GET /register/ → Página de registro
- [ ] GET /admin/ → Django admin

### Rutas Autenticadas (requieren login)
- [ ] GET /dashboard/ → Dashboard estudiante
- [ ] GET /internships/ → Lista de oportunidades
- [ ] GET /company/dashboard/ → Dashboard empresa
- [ ] GET /admin/dashboard/ → Dashboard admin

### API REST
- [ ] GET /api/accounts/users/ → Lista de usuarios (requiere token)
- [ ] GET /api/internships/opportunities/ → Lista de oportunidades
- [ ] POST /api/accounts/token/ → Obtener token JWT

## 🎨 Verificaciones de UI/UX

- [ ] Navbar aparece correctamente en todas las páginas
- [ ] Sidebar aparece en páginas autenticadas
- [ ] Responsive design funciona en móvil (F12 → Toggle device)
- [ ] Botones tienen efectos hover
- [ ] Modales se abren y cierran correctamente
- [ ] Formularios validan inputs
- [ ] Notificaciones aparecen en pantalla
- [ ] Colores del tema son consistentes

## 🔌 Verificaciones de Integración API

- [ ] Axios está cargado (console: `typeof axios`)
- [ ] SkillBridge está disponible (console: `SkillBridge`)
- [ ] Token se guarda en localStorage después del login
- [ ] Llamadas API incluyen header Authorization

## 🐛 Debugging Común

### Problema: Archivos estáticos no cargan (404)
**Solución:**
```bash
python manage.py collectstatic --clear --noinput
```

### Problema: Templates no encontrados
**Verificar:**
- TEMPLATES DIRS en settings.py incluye BASE_DIR / "templates"
- Archivos HTML están en directorio templates/

### Problema: CSRF token faltante
**Solución:**
```django
{% csrf_token %}  <!-- Agregar a formularios POST -->
```

### Problema: Permisos denegados en admin
**Verificar:**
- Usuario tiene `is_staff = True`
- Usuario tiene `is_superuser = True` o permisos específicos

### Problema: API retorna 401 (Unauthorized)
**Verificar:**
- Token JWT en localStorage es válido
- Header Authorization está siendo enviado
- Token no ha expirado

## 📱 Testing Responsivo

### Desktop (1920x1080)
- [ ] Sidebar visible completo
- [ ] Grid muestra múltiples columnas
- [ ] Navbar expandido

### Tablet (768x1024)
- [ ] Grid adapta a 2 columnas
- [ ] Sidebar puede ser colapsado
- [ ] Botones redimensionados

### Mobile (375x667)
- [ ] Sidebar colapsado por defecto
- [ ] Grid adapta a 1 columna
- [ ] Texto legible sin zoom
- [ ] Botones del tamaño correcto para touch

## 🎯 Checklist de Características

### Estudiantes
- [ ] Ver dashboard personal
- [ ] Buscar oportunidades con filtros
- [ ] Aplicar a oportunidad
- [ ] Ver estado de aplicación
- [ ] Ver pasantía activa
- [ ] Registrar horas
- [ ] Ver perfil
- [ ] Cambiar contraseña

### Empresas
- [ ] Ver dashboard empresarial
- [ ] Crear nueva oferta
- [ ] Editar oferta
- [ ] Eliminar oferta
- [ ] Ver aplicantes
- [ ] Revisar candidato
- [ ] Aceptar/Rechazar candidato
- [ ] Ver pasantías activas
- [ ] Validar horas registradas

### Administradores
- [ ] Ver dashboard administrativo
- [ ] Filtrar pasantías
- [ ] Ver estadísticas
- [ ] Ver alertas
- [ ] Gestionar usuarios
- [ ] Validar empresas
- [ ] Generar reportes

## 📊 Monitoreo en Producción

- [ ] Configurar logging
- [ ] Establecer error tracking (Sentry)
- [ ] Monitorear performance
- [ ] Backup de base de datos
- [ ] HTTPS habilitado
- [ ] Rate limiting configurado

## 🎉 Checklist Final

- [ ] Instalación completada sin errores
- [ ] Todas las rutas funcionan
- [ ] UI se ve correctamente
- [ ] API responde correctamente
- [ ] Tests pasan (si aplica)
- [ ] Documentación está actualizada
- [ ] Código está limpido (sin errores de console)
- [ ] Performance es aceptable (< 3s carga inicial)

## 📞 Soporte y Contacto

Si encuentras problemas:

1. Revisa los logs: `python manage.py runserver` muestra errores
2. Revisa la consola del navegador (F12)
3. Consulta la documentación en FRONTEND_README.md
4. Verifica que todas las dependencias estén instaladas

## ✨ Sugerencias de Mejora Futura

- [ ] Agregar más templates (applications, internship-detail, etc.)
- [ ] Implementar gráficos con Chart.js
- [ ] Agregar paginación real desde API
- [ ] Notificaciones en tiempo real (WebSocket)
- [ ] Búsqueda de texto completo
- [ ] Exportación a PDF/Excel
- [ ] Integración con calendario
- [ ] Sistema de mensajería privada
- [ ] Ratings y reviews
- [ ] Certificados digitales

---

**¡Tu plataforma SkillBridge está lista para el éxito! 🚀**
