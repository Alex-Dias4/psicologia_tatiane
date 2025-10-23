from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name= "home"),
    
    path('conta/', views.account_view, name='account_view'), 
    path('logout/', views.logout_view, name='logout'),
    path('conta/completar-perfil/', views.completar_perfil_view, name='completar_perfil'),
    
    path('agendar-consulta/', views.agendar_consulta_view, name='agendar_consulta'),
    
    path('meu-perfil/', views.meu_perfil, name='meu_perfil'),
    path('editar-perfil/', views.editar_perfil_view, name='editar_perfil'),
    
]