from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required

from . import auth_services
from .forms import UsuarioProfileForm, PacienteProfileForm, PsicologoProfileForm, ConsultaForm, FotoPerfilForm
from django.contrib import messages

from .models import Usuario

# Create your views here.

def home (request):
    return render(request, "core/home.html")


def account_view(request):
    
    # Variável para o script saber qual painel mostrar em caso de erro
    active_form = 'login' 
    redirect_response = None

    if request.method == 'POST':
        if 'login_submit' in request.POST:
            active_form = 'login'
            # Chama o serviço de login
            redirect_response, login_form = auth_services.handle_login_post(request)
            register_form = CustomUserCreationForm() # Cria um form de registro vazio
            auth_services.add_register_form_placeholders(register_form)

        elif 'register_submit' in request.POST:
            active_form = 'register'
            # Chama o serviço de cadastro
            redirect_response, register_form = auth_services.handle_register_post(request)
            login_form = AuthenticationForm() # Cria um form de login vazio
            auth_services.add_login_form_placeholders(login_form)
        
        # Se o login ou cadastro foi BEM SUCEDIDO, o serviço retornou um redirect
        if redirect_response:
            return redirect_response

    else:
        # GET: Cria formulários vazios e adiciona placeholders
        login_form = AuthenticationForm()
        register_form = CustomUserCreationForm()
        auth_services.add_login_form_placeholders(login_form)
        auth_services.add_register_form_placeholders(register_form)

    # Se o POST falhou ou se for um GET, renderiza a página
    # com os formulários (e os erros, se houver)
    context = {
        'login_form': login_form,
        'register_form': register_form,
        'active_form': active_form # A "dica" para o JS
    }
    return render(request, 'login_cadastro.html', context)

@login_required 
def completar_perfil_view(request):
    
    # Se o usuário já completou o perfil, manda embora
    if hasattr(request.user, 'usuario'):
        if hasattr(request.user.usuario, 'paciente'):
            return redirect('paciente:dashboard')
        elif hasattr(request.user.usuario, 'psicologo'):
            return redirect('psicologo:dashboard')
            
    # Variável para o template saber qual radio 'checar'
    profile_type = 'paciente' # Padrão

    if request.method == 'POST':
        # Pega o tipo de perfil escolhido (do radio button)
        profile_type = request.POST.get('profile_type')
        
        # Pega o formulário comum
        usuario_form = UsuarioProfileForm(request.POST)

        if profile_type == 'paciente':
            paciente_form = PacienteProfileForm(request.POST)
            psicologo_form = PsicologoProfileForm() # Vazio

            # Valida o form comum E o de paciente
            if usuario_form.is_valid() and paciente_form.is_valid():
                # Salva o Usuario
                usuario_profile = usuario_form.save(commit=False)
                usuario_profile.user = request.user
                usuario_profile.email = request.user.email
                usuario_profile.save()

                # Salva o Paciente
                paciente_profile = paciente_form.save(commit=False)
                paciente_profile.usuario = usuario_profile
                paciente_profile.save()

                return redirect('paciente:dashboard')

        elif profile_type == 'psicologo':
            psicologo_form = PsicologoProfileForm(request.POST)
            paciente_form = PacienteProfileForm() # Vazio

            # Valida o form comum E o de psicólogo
            if usuario_form.is_valid() and psicologo_form.is_valid():
                # Salva o Usuario
                usuario_profile = usuario_form.save(commit=False)
                usuario_profile.user = request.user
                usuario_profile.email = request.user.email
                usuario_profile.save()

                # Salva o Psicologo
                psicologo_profile = psicologo_form.save(commit=False)
                psicologo_profile.usuario = usuario_profile
                psicologo_profile.save()

                return redirect('psicologo:dashboard')
        
        else:
            # Erro: Nenhum tipo de perfil foi selecionado
            usuario_form.add_error(None, "Por favor, selecione um tipo de perfil.")
            paciente_form = PacienteProfileForm()
            psicologo_form = PsicologoProfileForm()
            
    else:
        # GET: Mostra todos os formulários vazios
        usuario_form = UsuarioProfileForm()
        paciente_form = PacienteProfileForm()
        psicologo_form = PsicologoProfileForm()

    context = {
        'usuario_form': usuario_form,
        'paciente_form': paciente_form,
        'psicologo_form': psicologo_form,
        'selected_profile_type': profile_type # Para o JS saber qual mostrar em caso de erro
    }
    return render(request, 'core/completar_perfil.html', context)

def logout_view(request):
    logout(request)
    # Redireciona para a URL 'home',
    # como definido no seu LOGOUT_REDIRECT_URL
    return redirect('home')

@login_required
def agendar_consulta_view(request):
    # 1. Checa se o usuário tem perfil. Se não, manda completar.
    if not hasattr(request.user, 'usuario'):
        messages.error(request, 'Você precisa completar seu perfil antes de agendar consultas.')
        return redirect('completar_perfil')

    if request.method == 'POST':
        # 2. Passa o 'user' E os dados do 'POST' para o formulário
        form = ConsultaForm(request.POST, user=request.user)
        if form.is_valid():
            nova_consulta = form.save(commit=False)
            
            # O status padrão já é 'pendente' (definido no models.py)
            # Mas podemos ser explícitos se quisermos:
            # nova_consulta.status = 'pendente' 
            
            nova_consulta.save()
            messages.success(request, 'Consulta agendada com sucesso! Aguardando confirmação.')
            
            # 3. Redireciona para o dashboard correto
            if hasattr(request.user.usuario, 'paciente'):
                return redirect('paciente:dashboard')
            else:
                return redirect('psicologo:dashboard')
    
    else:
        # 4. É um GET: Cria um form em branco, passando o 'user'
        form = ConsultaForm(user=request.user)

    context = {
        'form': form
    }
    # Vamos criar este template a seguir
    return render(request, 'core/agendar_consulta.html', context)

@login_required
def meu_perfil(request):
    try:
        usuario_profile = request.user.usuario
    except Usuario.DoesNotExist:
        # Se NÃO encontrar o perfil:
        messages.warning(request, 'Você precisa completar seu perfil primeiro.')
        # INTERROMPE a função e redireciona
        return redirect('completar_perfil')
        
    foto_form = FotoPerfilForm(instance=usuario_profile) # Cria form vazio com a instância atual

    if request.method == 'POST':
        # Verifica se o POST veio do formulário de foto
        # (Podemos adicionar um name="submit_foto" ao botão depois)
        foto_form = FotoPerfilForm(request.POST, request.FILES, instance=usuario_profile)
        if foto_form.is_valid():
            foto_form.save()
            messages.success(request, 'Foto de perfil atualizada com sucesso!')
            # Redireciona para a mesma página para evitar reenvio do form
            return redirect('meu_perfil') 
        else:
            # Se o formulário de foto for inválido (raro para ImageField), 
            # exibe a página novamente com os erros
             messages.error(request, 'Erro ao atualizar a foto.')

    # --- Lógica existente para buscar paciente/psicologo ---
    paciente_profile = None
    psicologo_profile = None
    if hasattr(usuario_profile, 'paciente'):
        paciente_profile = usuario_profile.paciente
    elif hasattr(usuario_profile, 'psicologo'):
        psicologo_profile = usuario_profile.psicologo
    # --- Fim da lógica existente ---

    context = {
        'usuario': usuario_profile,
        'paciente': paciente_profile,
        'psicologo': psicologo_profile,
        'foto_form': foto_form, # <-- Envia o formulário da foto para o template
    }
    return render(request, 'core/meu_perfil.html', context)

@login_required
def editar_perfil_view(request):
    # Tenta buscar o perfil 'Usuario'. Se não existir, manda completar.
    try:
        usuario_profile = request.user.usuario
    except Usuario.DoesNotExist:
        messages.warning(request, 'Você precisa completar seu perfil para poder editá-lo.')
        return redirect('completar_perfil')

    # Busca o perfil específico (Paciente ou Psicologo) se existir
    paciente_profile = getattr(usuario_profile, 'paciente', None)
    psicologo_profile = getattr(usuario_profile, 'psicologo', None)

    if request.method == 'POST':
        # Cria os formulários com os dados do POST E a instância atual para edição
        usuario_form = UsuarioProfileForm(request.POST, instance=usuario_profile)
        
        # Cria o form específico apenas se o perfil existir
        paciente_form = None
        psicologo_form = None
        if paciente_profile:
            paciente_form = PacienteProfileForm(request.POST, instance=paciente_profile)
        elif psicologo_profile:
            psicologo_form = PsicologoProfileForm(request.POST, instance=psicologo_profile)

        # Validação: Checa o form comum E o form específico (se aplicável)
        is_paciente_valid = paciente_form is None or paciente_form.is_valid()
        is_psicologo_valid = psicologo_form is None or psicologo_form.is_valid()

        if usuario_form.is_valid() and is_paciente_valid and is_psicologo_valid:
            # Salva o formulário Usuario (commit=False se precisar ajustar algo)
            usuario_form.save() 
            
            # Salva o formulário específico (se existir)
            if paciente_form:
                paciente_form.save()
            elif psicologo_form:
                psicologo_form.save()

            messages.success(request, 'Perfil atualizado com sucesso!')
            # Redireciona de volta para a página "Meu Perfil"
            return redirect('meu_perfil') 
        else:
            messages.error(request, 'Erro ao atualizar o perfil. Verifique os campos.')
            # Se a validação falhar, a view renderizará os forms com os erros

    else: # Método GET
        # Cria os formulários preenchidos com os dados da instância atual
        usuario_form = UsuarioProfileForm(instance=usuario_profile)
        
        paciente_form = None
        psicologo_form = None
        if paciente_profile:
            paciente_form = PacienteProfileForm(instance=paciente_profile)
        elif psicologo_profile:
            psicologo_form = PsicologoProfileForm(instance=psicologo_profile)

    context = {
        'usuario_form': usuario_form,
        'paciente_form': paciente_form, # Será None se não for paciente
        'psicologo_form': psicologo_form, # Será None se não for psicólogo
    }
    # Vamos criar este template a seguir
    return render(request, 'core/editar_perfil.html', context)