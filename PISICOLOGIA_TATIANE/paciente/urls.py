# paciente/urls.py
from django.urls import path
from . import views

app_name = 'paciente'  # <-- Define o "namespace" do app

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('consulta/<int:consulta_id>/confirmar-presenca/', views.paciente_confirma_presenca, name='confirmar_presenca'),
    
    path('consulta/<int:consulta_id>/detalhes/', views.consulta_detalhes_paciente, name='consulta_detalhes'),
    path('agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
    path('consulta/<int:consulta_id>/solicitar-remarcacao/', views.solicitar_remarcacao, name='solicitar_remarcacao'),
    # Ex: path('agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
]