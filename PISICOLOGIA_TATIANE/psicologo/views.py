# psicologo/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from core.models import Consulta, Paciente 
from django.core.paginator import Paginator
from .forms import DiagnosticoForm 
from django.contrib import messages

@login_required
def dashboard(request):
    # Proteção: Se não for psicólogo, manda para completar o perfil
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    psicologo_obj = request.user.usuario.psicologo
    hoje = timezone.now().date()
    
    # 1. Busca as consultas de hoje
    consultas_hoje = Consulta.objects.filter(
        psicologo=psicologo_obj, 
        data=hoje,
        status__in=['confirmada', 'pendente'] # Filtra só o que importa
    ).order_by('hora')
    
    # 2. Busca todos os pacientes únicos deste psicólogo
    pacientes_ids = Consulta.objects.filter(
        psicologo=psicologo_obj
    ).values_list('paciente_id', flat=True).distinct()
    
    meus_pacientes = Paciente.objects.filter(id__in=pacientes_ids)

    context = {
        'psicologo': psicologo_obj,
        'consultas_hoje': consultas_hoje,
        'meus_pacientes': meus_pacientes
    }
    return render(request, 'psicologo/dashboard.html', context)

@login_required
def agenda_completa(request):
    # Proteção: Garante que é um psicólogo
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    psicologo_obj = request.user.usuario.psicologo
    
    # Busca TODAS as consultas, ordenadas da mais recente para a mais antiga
    lista_consultas = Consulta.objects.filter(
        psicologo=psicologo_obj
    ).order_by('-data', '-hora') # '-' ordena decrescente
    
    # Configura a paginação: 10 consultas por página
    paginator = Paginator(lista_consultas, 10) 
    
    # Pega o número da página da URL (ex: ?page=2)
    page_number = request.GET.get('page')
    
    # Obtém o objeto Page correspondente
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj # Envia o objeto Page para o template
    }
    # Vamos criar este template a seguir
    return render(request, 'psicologo/agenda_completa.html', context)

@login_required
def consulta_detalhes(request, consulta_id):
    """Exibe os detalhes de uma consulta específica e as ações possíveis."""
    # Garante que o usuário é um psicólogo
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    # Busca a consulta, garantindo que pertence ao psicólogo logado
    consulta = get_object_or_404(
        Consulta, 
        id_consulta=consulta_id, 
        psicologo=request.user.usuario.psicologo
    )
    
    # Busca diagnósticos já registrados para esta consulta
    diagnosticos_registrados = consulta.diagnosticos.all()

    context = {
        'consulta': consulta,
        'diagnosticos_registrados': diagnosticos_registrados
    }
    # Vamos criar este template a seguir
    return render(request, 'psicologo/consulta_detalhes.html', context)

@login_required
def listar_consultas_diagnostico(request):
    """Mostra as consultas realizadas para que o psicólogo escolha qual diagnosticar."""
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    psicologo_obj = request.user.usuario.psicologo
    
    # Busca consultas realizadas, ordenadas por data
    consultas_realizadas = Consulta.objects.filter(
        psicologo=psicologo_obj,
        status='realizada' # Só permite diagnosticar consultas concluídas
    ).order_by('-data', '-hora')
    
    # (Opcional: Adicionar paginação aqui também, se a lista for longa)

    context = {
        'consultas_realizadas': consultas_realizadas
    }
    return render(request, 'psicologo/listar_consultas_diagnostico.html', context)


@login_required
def registrar_diagnostico(request, consulta_id):
    """Exibe o formulário para registrar um diagnóstico para uma consulta específica."""
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    # Busca a consulta específica ou retorna erro 404 se não existir
    # Garante também que a consulta pertence ao psicólogo logado
    consulta = get_object_or_404(Consulta, id_consulta=consulta_id, psicologo=request.user.usuario.psicologo)
    
    # Não permitir diagnosticar consulta que não foi realizada
    if consulta.status != 'realizada':
        messages.error(request, 'Só é possível adicionar diagnósticos a consultas já realizadas.')
        return redirect('psicologo:listar_consultas_diagnostico')

    if request.method == 'POST':
        form = DiagnosticoForm(request.POST)
        print("Erros do formulário:", form.errors)
        if form.is_valid():
            diagnostico = form.save(commit=False)
            diagnostico.consulta = consulta # Associa o diagnóstico à consulta
            diagnostico.save()
            messages.success(request, f'Diagnóstico para {consulta.paciente.usuario.nome} registrado com sucesso!')
            # Redireciona de volta para a lista de consultas a diagnosticar
            return redirect('psicologo:listar_consultas_diagnostico')
    else:
        # GET: Cria um formulário vazio
        form = DiagnosticoForm()

    context = {
        'form': form,
        'consulta': consulta # Envia a consulta para o template
    }
    return render(request, 'psicologo/registrar_diagnostico.html', context)

@login_required
@require_POST # Garante que esta view só aceita requisições POST
def atualizar_status_consulta(request, consulta_id, novo_status):
    """Atualiza o status de uma consulta específica."""
    # Garante que o usuário é um psicólogo
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         # Teoricamente, não deveriam chegar aqui, mas é uma segurança extra
         messages.error(request, "Acesso não permitido.")
         return redirect('home') 

    # Busca a consulta, garantindo que pertence ao psicólogo logado
    consulta = get_object_or_404(
        Consulta, 
        id_consulta=consulta_id, # <-- CORRIGIDO
        psicologo=request.user.usuario.psicologo
    )
    
    # Valida se o novo_status é válido (está nas opções do modelo)
    valid_statuses = [status[0] for status in Consulta.STATUS_CHOICES]
    if novo_status not in valid_statuses:
        messages.error(request, "Status inválido.")
        # Redireciona de volta para a página anterior ou para a agenda
        return redirect(request.META.get('HTTP_REFERER', 'psicologo:agenda_completa'))

    # Lógica de transição de status (opcional, mas recomendado)
    # Ex: Não permitir confirmar uma consulta já cancelada, etc.
    # (Pode adicionar mais regras aqui se necessário)
    if consulta.status == 'cancelada' and novo_status != 'cancelada':
         messages.warning(request, "Não é possível alterar o status de uma consulta cancelada.")
         return redirect(request.META.get('HTTP_REFERER', 'psicologo:agenda_completa'))
         
    if consulta.status == 'realizada' and novo_status != 'realizada':
         messages.warning(request, "Não é possível alterar o status de uma consulta já realizada.")
         return redirect(request.META.get('HTTP_REFERER', 'psicologo:agenda_completa'))


    # Atualiza o status e salva
    consulta.status = novo_status
    consulta.save()
    
    messages.success(request, f"Status da consulta de {consulta.paciente.usuario.nome} atualizado para '{consulta.get_status_display()}'.")
    
    # Redireciona de volta para a página de onde veio (provavelmente a agenda)
    return redirect(request.META.get('HTTP_REFERER', 'psicologo:agenda_completa'))

@login_required
def meus_pacientes(request):
    # Proteção: Garante que é um psicólogo
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    psicologo_obj = request.user.usuario.psicologo

    # Busca todos os IDs de pacientes únicos que tiveram consulta com este psicólogo
    pacientes_ids = Consulta.objects.filter(
        psicologo=psicologo_obj
    ).values_list('paciente_id', flat=True).distinct()

    # Busca os objetos Paciente correspondentes, ordenados pelo nome do usuário
    lista_pacientes = Paciente.objects.filter(
        id__in=pacientes_ids
    ).select_related('usuario').order_by('usuario__nome') # select_related otimiza a busca do nome

    # Configura a paginação: 10 pacientes por página
    paginator = Paginator(lista_pacientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj # Envia o objeto Page (contendo pacientes) para o template
    }
    # Vamos criar este template a seguir
    return render(request, 'psicologo/meus_pacientes.html', context)

@login_required
def paciente_historico(request, paciente_id):
    # Proteção: Garante que é um psicólogo
    if not hasattr(request.user, 'usuario') or not hasattr(request.user.usuario, 'psicologo'):
         return redirect('completar_perfil')

    psicologo_obj = request.user.usuario.psicologo

    # Busca o Paciente específico ou retorna 404
    paciente_obj = get_object_or_404(Paciente, pk=paciente_id)
    
    # Busca todas as consultas DESTE paciente COM ESTE psicólogo
    # Ordenadas da mais recente para a mais antiga
    consultas_historico = ( # <-- ABRE PARÊNTESES AQUI
        Consulta.objects.filter(
            paciente=paciente_obj,
            psicologo=psicologo_obj
        )
        .select_related('paciente__usuario', 'psicologo__usuario') # Otimiza busca de nomes
        .prefetch_related('diagnosticos') # Otimiza busca de diagnósticos
        .order_by('-data', '-hora')
    )

    # (Opcional: Paginação para as consultas, se a lista for muito longa)
    paginator = Paginator(consultas_historico, 15) # 15 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'paciente': paciente_obj,
        'consultas': consultas_historico, # Ou 'page_obj' se usar paginação
        # 'page_obj': page_obj # Descomente se usar paginação
    }
    # Vamos criar este template a seguir
    return render(request, 'psicologo/paciente_historico.html', context)
