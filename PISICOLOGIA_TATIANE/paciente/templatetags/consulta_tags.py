# paciente/templatetags/consulta_tags.py

from django import template
from django.utils import timezone
from datetime import datetime, time, timedelta

# Cria uma instância de Library para registrar as tags/filtros
register = template.Library()

@register.filter
def can_reschedule(consulta):
    """
    Verifica se uma consulta pode ser remarcada pelo paciente.
    Condições:
    1. Status deve ser 'pendente' ou 'confirmada'.
    2. Deve ser mais de 6 horas antes do horário agendado.
    Retorna True se puder, False caso contrário.
    """
    # 1. Verifica o Status da Consulta
    # Só permite solicitar remarcação se estiver pendente ou confirmada
    if consulta.status not in ['pendente', 'confirmada']:
        return False

    # 2. Verifica o Limite de Tempo (6 horas antes)
    try:
        # Combina data e hora da consulta em um objeto datetime
        # Assumindo que consulta.data é um DateField e consulta.hora é um TimeField
        consulta_datetime = datetime.combine(consulta.data, consulta.hora)

        # Pega a data/hora atual (com fuso horário, se USE_TZ=True)
        now = timezone.now()

        # Calcula o limite de tempo para remarcação (6 horas antes da consulta)
        limite_remarcacao = consulta_datetime - timedelta(hours=6)

        # Compara os datetimes, ajustando fuso horário se necessário
        # Esta parte é importante se settings.USE_TZ for True
        if timezone.is_aware(now) and not timezone.is_aware(limite_remarcacao):
            # Torna 'limite_remarcacao' ciente do fuso horário atual para comparação
            limite_remarcacao = timezone.make_aware(limite_remarcacao, timezone.get_current_timezone())
        elif not timezone.is_aware(now) and timezone.is_aware(limite_remarcacao):
            # Torna 'now' ciente do fuso horário (menos comum precisar disso)
            now = timezone.make_aware(now, timezone.get_current_timezone())

        # Retorna True se o momento atual (now) for ANTES do limite de remarcação
        return now < limite_remarcacao

    except (TypeError, ValueError):
        # Em caso de erro ao combinar data/hora (ex: valores None ou inválidos),
        # considera que não pode remarcar por segurança.
        return False
    except Exception:
        # Captura qualquer outro erro inesperado e retorna False
        # (Idealmente, logar o erro aqui)
        return False

# Você pode adicionar outros filtros ou tags personalizados para o app 'paciente' aqui no futuro.
# Exemplo:
# @register.simple_tag
# def get_paciente_info(user):
#     # ... lógica para buscar informações extras ...
#     return "Informação Extra"