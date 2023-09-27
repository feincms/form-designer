from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path


urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    path("", include("feincms.urls")),
] + staticfiles_urlpatterns()
