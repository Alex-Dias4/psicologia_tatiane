# psicologo/urls.py
from django.urls import path
from . import views

app_name = 'psicologo'  # <-- Define o "namespace" do app

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('agenda/', views.agenda_completa, name='agenda_completa'),
    path('diagnosticos/listar/', views.listar_consultas_diagnostico, name='listar_consultas_diagnostico'),
    path('diagnosticos/registrar/<int:consulta_id>/', views.registrar_diagnostico, name='registrar_diagnostico'),
    path('consulta/<int:consulta_id>/detalhes/', views.consulta_detalhes, name='consulta_detalhes'),
    path('consulta/<int:consulta_id>/atualizar/<str:novo_status>/', views.atualizar_status_consulta, name='atualizar_status_consulta'),
    path('pacientes/', views.meus_pacientes, name='meus_pacientes'),
    path('paciente/<int:paciente_id>/historico/', views.paciente_historico, name='paciente_historico'),
]