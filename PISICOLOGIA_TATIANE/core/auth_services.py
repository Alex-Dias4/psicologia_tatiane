# core/auth_services.py (NOVO ARQUIVO)

from django.shortcuts import redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

def add_login_form_placeholders(form):
    """Adiciona placeholders ao formulário de login."""
    form.fields['username'].widget.attrs.update({
        'placeholder': 'Username', 'required': True
    })
    form.fields['password'].widget.attrs.update({
        'placeholder': 'Password', 'required': True
    })

def add_register_form_placeholders(form):
    """Adiciona placeholders ao formulário de cadastro."""
    form.fields['username'].widget.attrs.update({
        'placeholder': 'Username', 'required': True
    })
    form.fields['email'].widget.attrs.update({
        'placeholder': 'Email', 'required': True
    })
    form.fields['password1'].widget.attrs.update({
        'placeholder': 'Password', 'required': True
    })
    form.fields['password2'].widget.attrs.update({
        'placeholder': 'Confirm Password', 'required': True
    })

def handle_login_post(request):
    """Processa uma tentativa de login. Retorna um redirect se for sucesso."""
    form = AuthenticationForm(request, data=request.POST)
    add_login_form_placeholders(form) # Adiciona placeholders em caso de erro

    if form.is_valid():
        user = authenticate(
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password')
        )
        if user is not None:
            login(request, user)
            
            # !! CORREÇÃO AQUI !!
            # Mude de:
            # return get_user_redirect_url(user)
            # Para (retornando dois valores):
            return get_user_redirect_url(user), form
            
    # Se falhou, retorna o formulário com erros (Isto já está correto)
    return None, form 

def handle_register_post(request):
    """Processa uma tentativa de cadastro. Retorna um redirect se for sucesso."""
    form = CustomUserCreationForm(request.POST)
    add_register_form_placeholders(form) # Adiciona placeholders em caso de erro

    if form.is_valid():
        user = form.save()
        login(request, user)
        # ESTA É A LÓGICA CORRETA: redireciona para completar o perfil
        
        # !! CORREÇÃO AQUI !!
        # Mude de:
        # return redirect('completar_perfil')
        # Para (retornando dois valores):
        return redirect('completar_perfil'), form
    
    # Se falhou, retorna o formulário com erros (Isto já está correto)
    return None, form

def get_user_redirect_url(user):
    """Verifica o tipo de perfil do usuário e retorna a URL do dashboard correto."""
    try:
        # 'hasattr' checa se o atributo existe
        if hasattr(user, 'usuario') and hasattr(user.usuario, 'psicologo'):
            return redirect('psicologo:dashboard')
        elif hasattr(user, 'usuario') and hasattr(user.usuario, 'paciente'):
            return redirect('paciente:dashboard')
        else:
            # Usuário logado mas sem perfil (Paciente/Psicologo)
            return redirect('completar_perfil')
            
    except AttributeError:
        # 'user.usuario' não existe (pode ser admin ou precisa completar)
        if user.is_superuser:
            return redirect('/admin')
        else:
            return redirect('completar_perfil')