"""
Configuración de Django para el proyecto erp_project.

Generado por 'django-admin startproject' usando Django 5.2.8.
"""

from pathlib import Path

# Construir rutas dentro del proyecto de esta forma: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Configuración de desarrollo rápido - no apto para producción

# ADVERTENCIA DE SEGURIDAD: mantén la clave secreta en secreto en producción
SECRET_KEY = 'django-insecure-_dzsl&fh$p=&)+(w97^y5$e@z1@+mvf%=_l58r+7kz2!o%y0$1'

# ADVERTENCIA DE SEGURIDAD: no ejecutes con debug activado en producción
DEBUG = True

ALLOWED_HOSTS = []


# Definición de aplicaciones
#
# PASOS SIGUIENTES PARA CONFIGURACIÓN COMPLETA:
# =============================================
# 1. Ejecutar migraciones desde la consola:
#    > python manage.py makemigrations
#    > python manage.py migrate
#
# 2. Crear superusuario (si aún no existe):
#    > python manage.py createsuperuser
#
# 3. Acceder al panel de administración (/admin) y crear datos maestros:
#
#    INVENTORY:
#    ----------
#    - MovementType: Crear tipos de movimiento (ej: Entrada, Salida, Ajuste, 
#      Transferencia) con nombre y símbolo.
#    - InventoryLocation: Crear ubicaciones/almacenes con códigos, status 
#      (Activo/Inactivo) y jerarquía (main_location para agrupación).
#
#    ACCOUNTING:
#    -----------
#    - AccountNature: Crear naturalezas contables (Débito, Crédito) con 
#      nombre, símbolo y efecto en balance.
#    - AccountGroup: Crear grupos de cuentas con prefijos de códigos.
#    - AccountType: Crear tipos de cuenta (Activo, Pasivo, Patrimonio, 
#      Ingresos, Gastos).
#    - Currency: Crear monedas (USD, EUR, etc.) con código y símbolo.
#    - Country: Crear países necesarios.
#    - AccountAccount: Crear plan de cuentas usando las tablas auxiliares 
#      anteriores, incluyendo jerarquías (parent_account).
#
#    PURCHASES:
#    ----------
#    - OrderStatus: Crear los 8 estados de órdenes de compra:
#      1. Borrador
#      2. Enviado
#      3. Confirmado
#      4. Recepción parcial
#      5. Recibido
#      6. Facturado
#      7. Cancelado
#      8. Cerrado

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'users',
    'materials',
    'suppliers',
    'customers',
    'inventory',
    'accounting',
    'purchases',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_project.wsgi.application'


# Base de datos

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Validación de contraseñas

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internacionalización

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True


# Archivos estáticos (CSS, JavaScript, Imágenes)

STATIC_URL = 'static/'

# Tipo de campo de clave primaria predeterminado

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de autenticación

AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
