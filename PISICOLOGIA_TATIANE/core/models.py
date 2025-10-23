import os
from django.db import models
from django.contrib.auth.models import User # Importa o DjangoUser

# --- 1. Modelos de Perfil e Usuário ---

class Usuario(models.Model):
    """
    Modelo central de perfil, linkado ao 'User' padrão do Django.
    Contém todos os dados pessoais comuns.
    """
    # O link 1-para-1 com o sistema de login do Django.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usuario')
    
    # Dados do diagrama
    cpf = models.CharField("CPF", max_length=11, unique=True) # CPF é único
    nome = models.CharField("Nome Completo", max_length=100)
    idade = models.IntegerField("Idade", null=True, blank=True)
    rua = models.CharField("Rua/Avenida", max_length=100, null=True, blank=True)
    numero = models.CharField("Número", max_length=10, null=True, blank=True)
    bairro = models.CharField("Bairro", max_length=50, null=True, blank=True)
    cidade = models.CharField("Cidade", max_length=50, null=True, blank=True)
    cep = models.CharField("CEP", max_length=8, null=True, blank=True)
    
    # O email do diagrama (embora o 'User' já tenha um, vamos seguir o diagrama)
    email = models.EmailField("Email", unique=True) 
    
    foto_perfil = models.ImageField(
        "Foto de Perfil", 
        upload_to='fotos_perfil/', # Salvará as fotos em MEDIA_ROOT/fotos_perfil/
        null=True, 
        blank=True, # Permite que o campo seja opcional
        default='fotos_perfil/default.png' # Opcional: Uma imagem padrão
    )

    def __str__(self):
        return self.nome

class Telefone(models.Model):
    """
    Um usuário pode ter múltiplos telefones (relação 1-para-N).
    """
    # O 'related_name' permite fazer 'usuario.telefones.all()'
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='telefones')
    telefone = models.CharField("Telefone", max_length=15)

    def __str__(self):
        return f"{self.usuario.nome} - {self.telefone}"

class Paciente(models.Model):
    """
    Perfil específico de Paciente. Linkado ao Usuário.
    """
    # O 'related_name' permite fazer 'usuario.paciente'
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='paciente')
    responsavel = models.CharField("Responsável", max_length=100, null=True, blank=True)
    plano_saude = models.CharField("Plano de Saúde", max_length=100, null=True, blank=True)

    def __str__(self):
        # Retorna o nome do Usuário associado
        return self.usuario.nome

class Psicologo(models.Model):
    """
    Perfil específico de Psicólogo. Linkado ao Usuário.
    """
    # O 'related_name' permite fazer 'usuario.psicologo'
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='psicologo')
    crp = models.CharField("CRP", max_length=20, unique=True) # CRP é único
    especialidade = models.CharField("Especialidade", max_length=100, null=True, blank=True)
    
    # A relação N-N com Clínica será definida abaixo
    # (veja 'clinicas')

    def __str__(self):
        # Retorna o nome do Usuário associado
        return self.usuario.nome

# --- 2. Modelos da Clínica ---

class Clinica(models.Model):
    """
    Modelo para as clínicas onde os psicólogos atendem.
    """
    id_clinica = models.AutoField(primary_key=True) # Seguindo o diagrama
    nome = models.CharField("Nome da Clínica", max_length=100)
    endereco = models.CharField("Endereço", max_length=150)
    cidade = models.CharField("Cidade", max_length=50)
    estado = models.CharField("Estado", max_length=2)
    cep = models.CharField("CEP", max_length=8)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Link N-N com Psicologo, usando a tabela 'PsicologoClinica'
    psicologos = models.ManyToManyField(
        Psicologo, 
        through='PsicologoClinica',
        related_name='clinicas'
    )

    def __str__(self):
        return self.nome

class PsicologoClinica(models.Model):
    """
    Esta é a tabela "through" (de ligação) para a relação N-N 
    entre Psicologo e Clinica. Ela armazena o 'horario_trabalho'.
    """
    psicologo = models.ForeignKey(Psicologo, on_delete=models.CASCADE)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    horario_trabalho = models.CharField("Horário", max_length=100, null=True, blank=True)

    class Meta:
        # Garante que um psicólogo não possa ser adicionado 
        # à mesma clínica duas vezes
        unique_together = ('psicologo', 'clinica')

    def __str__(self):
        return f"{self.psicologo} @ {self.clinica}"


# --- 3. Modelos de Consulta ---

class Consulta(models.Model):
    """
    Modelo central de Consultas, linkando Paciente e Psicologo.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('aguardando_remarcacao', 'Aguardando Remarcação'),
        ('cancelada', 'Cancelada'),
        ('realizada', 'Realizada'),
    ]

    id_consulta = models.AutoField(primary_key=True)
    
    # Links (Chaves Estrangeiras)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    psicologo = models.ForeignKey(Psicologo, on_delete=models.CASCADE, related_name='consultas')
    
    # Dados da consulta
    data = models.DateField("Data")
    hora = models.TimeField("Hora")
    observacao = models.TextField("Observação", null=True, blank=True)
    prescricao = models.TextField("Prescrição", null=True, blank=True)
    diagnostico_texto = models.TextField("Diagnóstico (texto)", null=True, blank=True, help_text="Campo 'diagnostico' do diagrama")
    status = models.CharField("Status", max_length=25, choices=STATUS_CHOICES, default='pendente')
    
    paciente_confirmou_presenca = models.BooleanField(
        "Presença Confirmada pelo Paciente", 
        default=False,
        help_text="Indica se o paciente clicou em 'Confirmar Presença'"
    )

    def __str__(self):
        return f"Consulta de {self.paciente} com {self.psicologo} em {self.data}"

class Diagnostico(models.Model):
    """
    Modelo para diagnósticos formais (CID-10), 
    linkados a uma Consulta.
    """
    id_diagnostico = models.AutoField(primary_key=True)
    
    # Uma consulta pode ter múltiplos diagnósticos
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='diagnosticos')
    
    descricao = models.TextField("Descrição")
    cid10 = models.CharField("CID-10", max_length=10, null=True, blank=True)
    data = models.DateField("Data do Diagnóstico", auto_now_add=True) # auto_now_add preenche a data de criação

    def __str__(self):
        return f"{self.cid10} - {self.consulta.paciente.usuario.nome}"
