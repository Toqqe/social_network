import django.conf
from django.urls import path
from django.conf.urls.static import static
from . import views

urlpatterns =[
    path('profile', views.index,name="user-profiles"),
    path('profile/<str:user>', views.ProfileDetailView.as_view(),name="user-profile"),
    path('search', views.search, name="user-search"),
    path('settings', views.user_settings, name="user-settings"),
    ##path('search', views.ProfilesListView.as_view(),name="user-profile")
]