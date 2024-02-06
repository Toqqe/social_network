from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from .forms import LoginForm
from user_profile.views import notifications


urlpatterns = [
    path("", views.MainFeedbackWallView.as_view(), name="main-page"),

    path("login", auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=LoginForm), name="login-page"),
    path("logout", auth_views.LogoutView.as_view(template_name="core/logout.html"), name="logout-page"),

    path("register", views.SignupPageView.as_view(), name="register-page"),
    
    path("post/<int:pk>", views.PostDetailView.as_view(), name="post-detail-page"),
    path("post/<int:pk>/update", views.PostUpdateView.as_view(), name="post-update-page"),
    path("post/<int:pk>/delete", views.PostDeleteView.as_view(), name="post-delete-page"),
    path("liked-posts/", views.liked_posts, name="liked-posts"),

    ## Password restart
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    path("notifications/", notifications, name='notification'),

    
] 

urlpatterns += static( settings.MEDIA_URL, document_root=settings.MEDIA_ROOT )
urlpatterns += static( settings.STATIC_URL, document_root=settings.STATIC_ROOT)