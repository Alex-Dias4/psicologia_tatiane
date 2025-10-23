from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Psicologo, Usuario, Paciente, Consulta

class CustomUserCreationForm(UserCreationForm):
    # O email está ótimo
    email = forms.EmailField(required=True, help_text="Obrigatório. Um email válido.")

    class Meta(UserCreationForm.Meta):
        model = User
        # !! CORRIJA AQUI !!
        # Deixe o form pai cuidar de 'password1' e 'password2'
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # Esta linha está perfeita, pois o campo 'password2' existe
        self.fields['password2'].label = "Confirmação de Senha"
        
        # !! ADICIONE ESTA LINHA !!
        # Mude o label de 'password1' também
        self.fields['password1'].label = "Senha"


    def clean_email(self):
        # ... (seu clean_email está perfeito, não mude) ...
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email já está em uso.")
        return email

    def save(self, commit=True):
        # ... (seu save está perfeito, não mude) ...
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class UsuarioProfileForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nome', 'cpf', 'idade', 'rua', 'numero', 'bairro', 'cidade', 'cep']

    def __init__(self, *args, **kwargs):
        super(UsuarioProfileForm, self).__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'placeholder': 'Seu nome completo'})
        self.fields['cpf'].widget.attrs.update({'placeholder': 'CPF (apenas números)'})
        self.fields['idade'].widget.attrs.update({'placeholder': 'Sua idade'})
        self.fields['rua'].widget.attrs.update({'placeholder': 'Nome da Rua / Av.'})
        self.fields['numero'].widget.attrs.update({'placeholder': 'Nº'})
        self.fields['bairro'].widget.attrs.update({'placeholder': 'Bairro'})
        self.fields['cidade'].widget.attrs.update({'placeholder': 'Cidade'})
        self.fields['cep'].widget.attrs.update({'placeholder': 'CEP (apenas números)'})
        for field_name in self.fields:
            self.fields[field_name].label = ''


# --- ADICIONE ESTA CLASSE ---
class PacienteProfileForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['responsavel', 'plano_saude']

    def __init__(self, *args, **kwargs):
        super(PacienteProfileForm, self).__init__(*args, **kwargs)
        self.fields['responsavel'].widget.attrs.update({'placeholder': 'Nome do Responsável (se aplicável)'})
        self.fields['plano_saude'].widget.attrs.update({'placeholder': 'Plano de Saúde (se aplicável)'})
        self.fields['responsavel'].label = ''
        self.fields['plano_saude'].label = ''
  
class PsicologoProfileForm(forms.ModelForm):
    class Meta:
        model = Psicologo
        # Pega os campos do seu models.py
        fields = ['crp', 'especialidade']

    def __init__(self, *args, **kwargs):
        super(PsicologoProfileForm, self).__init__(*args, **kwargs)
        # Adiciona placeholders
        self.fields['crp'].widget.attrs.update({'placeholder': 'CRP (ex: 06/123456)'})
        self.fields['especialidade'].widget.attrs.update({'placeholder': 'Sua especialidade (ex: Terapia Cognitivo-Comportamental)'})
        
        # Oculta os labels
        self.fields['crp'].label = ''
        self.fields['especialidade'].label = ''
        
class ConsultaForm(forms.ModelForm):
    
    class Meta:
        model = Consulta
        # Campos que o usuário deve preencher ao agendar
        fields = ['paciente', 'psicologo', 'data', 'hora', 'observacao']
        
        # Widgets para deixar os campos mais bonitos (HTML5)
        widgets = {
            'data': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'hora': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'}
            ),
            'observacao': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Alguma observação sobre a consulta? (opcional)'}
            ),
        }

    def __init__(self, *args, **kwargs):
        # --- A MÁGICA ACONTECE AQUI ---
        
        # 1. Pega o 'user' que a view vai nos passar
        user = kwargs.pop('user', None)
        
        super(ConsultaForm, self).__init__(*args, **kwargs)
        
        if not user:
            # Se, por algum motivo, não recebermos o user, não faz nada
            return

        # 2. Adapta o formulário baseado no tipo de usuário
        if hasattr(user, 'usuario') and hasattr(user.usuario, 'paciente'):
            # --- O USUÁRIO É UM PACIENTE ---
            
            # Define o 'paciente' como o próprio usuário e esconde o campo
            self.fields['paciente'].queryset = Paciente.objects.filter(id=user.usuario.paciente.id)
            self.fields['paciente'].initial = user.usuario.paciente
            self.fields['paciente'].widget = forms.HiddenInput()
            
            # Mostra todos os psicólogos no dropdown
            self.fields['psicologo'].queryset = Psicologo.objects.all()
            self.fields['psicologo'].label = "Escolha o Psicólogo"

        elif hasattr(user, 'usuario') and hasattr(user.usuario, 'psicologo'):
            # --- O USUÁRIO É UM PSICÓLOGO ---
            
            # Define o 'psicologo' como o próprio usuário e esconde o campo
            self.fields['psicologo'].queryset = Psicologo.objects.filter(id=user.usuario.psicologo.id)
            self.fields['psicologo'].initial = user.usuario.psicologo
            self.fields['psicologo'].widget = forms.HiddenInput()
            
            # Mostra todos os pacientes no dropdown
            self.fields['paciente'].queryset = Paciente.objects.all()
            self.fields['paciente'].label = "Escolha o Paciente"
            
        else:
            # Usuário não é nem paciente nem psicólogo (ex: admin ou perfil incompleto)
            # Esconde os dois para evitar erros.
            self.fields['paciente'].widget = forms.HiddenInput()
            self.fields['psicologo'].widget = forms.HiddenInput()
            
class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['foto_perfil']
        labels = {
            'foto_perfil': 'Alterar Foto de Perfil' 
        }