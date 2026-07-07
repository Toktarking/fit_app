from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from planner import views as planner_views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("planner.urls")),

    path(
        "login/",
        auth_views.LoginView.as_view(template_name="planner/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
    path("register/", planner_views.register, name="register"),
    path("webpush/", include("webpush.urls")),
]