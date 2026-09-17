from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig
from django.contrib.sessions.apps import SessionsConfig
from django.contrib.messages.apps import MessagesConfig
from django.contrib.staticfiles.apps import StaticFilesConfig


class MongoAdminConfig(AdminConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoAuthConfig(AuthConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoSessionsConfig(SessionsConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoMessagesConfig(MessagesConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoStaticFilesConfig(StaticFilesConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
