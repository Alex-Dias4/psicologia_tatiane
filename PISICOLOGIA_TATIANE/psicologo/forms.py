# psicologo/forms.py
from django import forms
from core.models import Diagnostico # Importa o modelo

class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        # Campos que o psicólogo vai preencher
        fields = ['descricao', 'cid10']
        widgets = {
            'descricao': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Descreva o diagnóstico...'}
            ),
            'cid10': forms.TextInput(
                attrs={'placeholder': 'Ex: F41.1 (Opcional)'}
            ),
        }
        labels = {
            'descricao': 'Descrição do Diagnóstico',
            'cid10': 'Código CID-10 (Opcional)'
        }