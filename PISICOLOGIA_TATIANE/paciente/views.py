# paciente/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .templatetags.consulta_tags import can_reschedule
from core.models import Consulta # Importe o modelo

@login_required
def dashboard(request):
    # ... (proteção paciente) ...
        
    paciente_obj = request.user.usuario.paciente
    hoje = timezone.now().date()
    agora = timezone.now().time() # Para desempate no mesmo dia

    # --- CONSULTAS FUTURAS (Próximas 3 Pendentes ou Confirmadas) ---
    consultas_futuras = Consulta.objects.filter(
        paciente=paciente_obj,
        data__gte=hoje, # Data maior ou igual a hoje
        status__in=['confirmada', 'pendente']
    ).exclude( # Exclui as de hoje que já passaram da hora
        data=hoje, 
        hora__lt=agora 
    ).order_by('data', 'hora')[:3] # Pega as próximas 3
    
    # --- CONSULTAS REALIZADAS (Últimas 5) ---
    consultas_realizadas = Consulta.objects.filter(
        paciente=paciente_obj,
        status='realizada'
    ).order_by('-data', '-hora')[:5] 
    
    # --- CONSULTAS CANCELADAS (Últimas 3) ---
    consultas_canceladas = Consulta.objects.filter(
        paciente=paciente_obj,
        status='cancelada'
    ).order_by('-data', '-hora')[:3] # Pega as últimas 3 canceladas


    context = {
        'paciente': paciente_obj,
        'consultas_futuras': consultas_futuras,
        'consultas_realizadas': consultas_realizadas, # Renomeado de 'consultas_passadas'
        'consultas_canceladas': consultas_canceladas,
    }
    return render(request, 'paciente/dashboard.html', context)

@login_required
@require_POST # Só permite POST
def paciente_confirma_presenca(request, consulta_id):
    """Marca que o paciente confirmou presença em uma consulta."""
    # Garante que é um paciente
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'paciente'):
        messages.error(request, "Ação não permitida.")
        return redirect('home')

    # Busca a consulta, garantindo que pertence ao paciente logado
    consulta = get_object_or_404(
        Consulta, 
        id_consulta=consulta_id, 
        paciente=request.user.usuario.paciente
    )

    # Só permite confirmar se o status for 'confirmada' (pelo psicólogo)
    if consulta.status != 'confirmada':
        messages.warning(request, "Você só pode confirmar presença em consultas confirmadas pelo psicólogo.")
        return redirect('paciente:dashboard')

    # Marca a confirmação e salva
    consulta.paciente_confirmou_presenca = True
    consulta.save()
# Use strftime para formatar a data e hora em Python
    data_formatada = consulta.data.strftime('%d/%m/%Y')
    hora_formatada = consulta.hora.strftime('%H:%M')
    messages.success(request, f"Sua presença na consulta de {data_formatada} às {hora_formatada} foi confirmada!")
    # ↑↑↑ CORREÇÃO AQUI ↑↑↑
    # Redireciona de volta para o dashboard do paciente
    return redirect('paciente:dashboard')

@login_required
def consulta_detalhes_paciente(request, consulta_id):
    """Exibe os detalhes de uma consulta específica para o paciente."""
    # Garante que é um paciente
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'paciente'):
        messages.error(request, "Acesso não permitido.")
        return redirect('home')

    # Busca a consulta, garantindo que pertence ao paciente logado
    consulta = get_object_or_404(
        Consulta,
        id_consulta=consulta_id,
        paciente=request.user.usuario.paciente
    )

    # Busca diagnósticos já registrados para esta consulta
    # (O prefetch_related na view do histórico já ajuda, mas buscamos de novo aqui por segurança)
    diagnosticos_registrados = consulta.diagnosticos.all()

    context = {
        'consulta': consulta,
        'diagnosticos_registrados': diagnosticos_registrados
    }
    # Vamos criar este template a seguir
    return render(request, 'paciente/consulta_detalhes.html', context)

@login_required
def meus_agendamentos(request):
    # Garante que é um paciente
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'paciente'):
        messages.error(request, "Acesso não permitido.")
        return redirect('home')

    paciente_obj = request.user.usuario.paciente

    # Busca TODAS as consultas do paciente, ordenadas da mais recente para a mais antiga
    lista_consultas = Consulta.objects.filter(
        paciente=paciente_obj
    ).select_related('psicologo__usuario').order_by('-data', '-hora') # select_related otimiza

    # Configura a paginação: 10 consultas por página
    paginator = Paginator(lista_consultas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj # Envia o objeto Page para o template
    }
    # Vamos criar este template a seguir
    return render(request, 'paciente/meus_agendamentos.html', context)

@login_required
def solicitar_remarcacao(request, consulta_id):
    # Busca a consulta, garantindo que pertence ao paciente
    consulta = get_object_or_404(Consulta, id_consulta=consulta_id, paciente=request.user.usuario.paciente)
    
    # Verifica se AINDA PODE remarcar (status e tempo)
    if not can_reschedule(consulta): 
         messages.error(request, "Já não é possível solicitar remarcação para esta consulta (muito próximo ou status inválido).")
         # Redireciona de volta para onde o usuário estava
         return redirect(request.META.get('HTTP_REFERER', 'paciente:dashboard'))

    # Se chegou aqui, pode remarcar: ATUALIZA O STATUS
    consulta.status = 'aguardando_remarcacao'
    consulta.save()

    # Informa o paciente e redireciona
    messages.success(request, f"Solicitação de remarcação enviada para a consulta de {consulta.data.strftime('%d/%m')} às {consulta.hora.strftime('%H:%M')}. Aguarde o contato do psicólogo.")
    # Redireciona de volta para onde o usuário estava (ex: meus_agendamentos ou detalhes)
    return redirect(request.META.get('HTTP_REFERER', 'paciente:dashboard'))

# # (Não esqueça de importar timedelta e timezone se for usar can_reschedule aqui)
# from datetime import timedelta 
# from django.utils import timezone