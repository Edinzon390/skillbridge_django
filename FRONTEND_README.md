# SkillBridge - Plataforma Web Completa de Gestión de Pasantías

Un sistema integral, estético y funcional para gestionar pasantías técnicas entre instituciones educativas, estudiantes y empresas.

## ✨ Características Implementadas

### 🎨 Frontend Moderno y Responsivo

- **Interfaz Profesional**: Diseño moderno con gradientes, sombras y animaciones suaves
- **Responsive Design**: Compatible con desktop, tablet y móvil
- **Navegación Intuitiva**: Sidebar dinámico y navbar sticky
- **Sistema de Componentes**: Botones, tarjetas, formularios, tablas, modales reutilizables

### 👥 Dashboards Multi-rol

#### 📚 Dashboard de Estudiantes
- Estadísticas personalizadas (oportunidades, aplicaciones, pasantías)
- Búsqueda y filtrado de oportunidades
- Visualización de pasantía activa con progreso de horas
- Registro de horas de trabajo
- Histórico de aplicaciones
- Perfil de usuario

#### 🏢 Dashboard de Empresas
- Gestión de ofertas de pasantía
- Revisión de aplicantes
- Supervisión de pasantías activas
- Validación de horas registradas
- Métricas de desempeño
- Exportación de reportes

#### 👨‍💼 Dashboard Administrativo
- Monitoreo integral de pasantías
- Gestión de usuarios y roles
- Validación de empresas
- Alertas y tareas pendientes
- Reportes y estadísticas detalladas
- Control de permisos

### 🎯 Funcionalidades Principales

1. **Autenticación Segura**
   - Login y registro
   - Recuperación de contraseña
   - Control de sesiones
   - Roles y permisos

2. **Gestión de Oportunidades**
   - Crear, editar y eliminar ofertas de pasantía
   - Búsqueda avanzada con filtros
   - Visualización de detalles
   - Aplicación en un clic

3. **Seguimiento de Pasantías**
   - Registro de horas de trabajo
   - Validación por supervisores
   - Historial de actividades
   - Bitácora de eventos

4. **Evaluaciones**
   - Formularios de evaluación
   - Métricas de desempeño
   - Calificaciones
   - Retroalimentación

5. **Reportes y Análisis**
   - Dashboard con estadísticas
   - Gráficos interactivos
   - Exportación a PDF/Excel
   - Análisis de tendencias

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.12+
- Django 5.x
- pip
- Base de datos (SQLite para desarrollo)

### Pasos de Instalación

1. **Crear un entorno virtual**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Ejecutar migraciones**
```bash
python manage.py migrate
```

4. **Crear superusuario (Admin)**
```bash
python manage.py createsuperuser
```

5. **Recolectar archivos estáticos**
```bash
python manage.py collectstatic --noinput
```

6. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

7. **Acceder a la aplicación**
- Frontend: http://localhost:8000
- Admin: http://localhost:8000/admin/

## 📁 Estructura de Carpetas

```
skillbridge_django/
├── static/
│   ├── css/
│   │   └── style.css (Estilos principales)
│   ├── js/
│   │   └── main.js (Funcionalidad JavaScript y API)
│   └── images/
├── templates/
│   ├── base.html (Plantilla base)
│   ├── home.html (Landing page)
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── opportunities.html
│   │   └── profile.html
│   ├── company/
│   │   ├── dashboard.html
│   │   ├── offers.html
│   │   └── profile.html
│   └── admin/
│       └── dashboard.html
├── core/
│   ├── frontend_views.py (Vistas del frontend)
│   ├── frontend_urls.py (URLs del frontend)
│   └── settings.py (Configuración)
└── ... (aplicaciones Django: accounts, internships, companies, etc.)
```

## 🎨 Paleta de Colores

- **Primario**: #6366f1 (Índigo)
- **Secundario**: #ec4899 (Rosa)
- **Éxito**: #10b981 (Verde)
- **Advertencia**: #f59e0b (Ámbar)
- **Peligro**: #ef4444 (Rojo)
- **Fondo Oscuro**: #0f172a
- **Fondo Claro**: #f8fafc

## 🔐 Seguridad

- Autenticación JWT
- CSRF Protection
- Validación de formularios
- Sanitización de inputs
- Permisos basados en roles

## 📊 Componentes UI Disponibles

### Botones
- `.btn-primary` - Botón principal
- `.btn-secondary` - Botón secundario
- `.btn-success` - Botón de éxito
- `.btn-danger` - Botón de peligro
- `.btn-outline` - Botón con borde

### Tarjetas
- `.card` - Tarjeta estándar
- `.stat-card` - Tarjeta de estadísticas
- `.card-header` - Encabezado de tarjeta

### Badges
- `.badge-primary`, `.badge-secondary`, `.badge-success`, etc.

### Tablas
- `.table` - Tabla estilizada

### Alertas
- `.alert-success`, `.alert-danger`, `.alert-warning`, `.alert-info`

## 🔌 API JavaScript

El archivo `main.js` expone un objeto global `SkillBridge` con funciones para:

```javascript
// Autenticación
SkillBridge.login(email, password)
SkillBridge.logout()
SkillBridge.register(userData)

// Oportunidades
SkillBridge.getOpportunities(filters)
SkillBridge.applyToOpportunity(opportunityId)
SkillBridge.getMyApplications()

// Pasantías
SkillBridge.getMyInternships()
SkillBridge.logHours(internshipId, hours, date, description)
SkillBridge.validateHours(hoursLogId, approved, feedback)

// Ofertas (Empresas)
SkillBridge.createOffer(offerData)
SkillBridge.getMyOffers()
SkillBridge.updateOffer(offerId, offerData)
SkillBridge.deleteOffer(offerId)

// Utilidades
SkillBridge.showNotification(message, type, duration)
SkillBridge.formatDate(date, format)
SkillBridge.toggleModal(modalId, show)
```

## 📱 Rutas Principales

### Públicas
- `/` - Home
- `/login/` - Iniciar sesión
- `/register/` - Registro
- `/help/` - Ayuda

### Estudiantes
- `/dashboard/` - Panel principal
- `/internships/` - Oportunidades
- `/applications/` - Mis aplicaciones
- `/my-internships/` - Mis pasantías
- `/profile/` - Perfil

### Empresas
- `/company/dashboard/` - Panel empresarial
- `/company/offers/` - Mis ofertas
- `/company/offers/create/` - Crear oferta
- `/company/internships/` - Pasantías activas
- `/company/hours-validation/` - Validar horas

### Administración
- `/admin/dashboard/` - Panel administrativo
- `/admin/students/` - Gestión de estudiantes
- `/admin/companies/` - Gestión de empresas
- `/admin/internships/` - Monitoreo
- `/admin/users/` - Gestión de usuarios

## 🧪 Datos de Prueba

Para probar la plataforma, usa las siguientes credenciales:

| Usuario | Email | Contraseña | Rol |
|---------|-------|-----------|-----|
| Estudiante | student@example.com | Demo@123 | Estudiante |
| Empresa | company@example.com | Demo@123 | Empresa |
| Admin | admin@example.com | Demo@123 | Administrador |

## 🔧 Configuración Adicional

### Habilitar DEBUG en Producción (NO RECOMENDADO)
Edita `skillbridge/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['tudominio.com', 'www.tudominio.com']
SECRET_KEY = 'una-clave-segura-aleatoria'
```

### Base de Datos Productiva
Para usar PostgreSQL en producción:
```bash
pip install psycopg2-binary
```

Actualiza `DATABASES` en `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'skillbridge',
        'USER': 'usuario',
        'PASSWORD': 'contraseña',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📞 Soporte y Contacto

Para preguntas o problemas, por favor:
1. Consulta la sección de Ayuda en la plataforma
2. Contacta al equipo administrativo
3. Revisa la documentación de la API en `/api/`

## 📄 Licencia

Este proyecto es software privado. Todos los derechos reservados.

## 🎉 Gracias por usar SkillBridge

Conectando talento joven con oportunidades empresariales desde 2024.
