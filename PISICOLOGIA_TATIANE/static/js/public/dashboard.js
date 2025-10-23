// arquivo: static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Adiciona efeito de clique nos cards
    const cards = document.querySelectorAll('.dashboard-card');
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Evita que o clique em links dentro do card dispare o evento
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                return;
            }
            
            // Adiciona uma classe temporária para feedback visual
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
    });
    
    // Animação para os cards quando entram na tela
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Aplica a animação aos cards
    document.querySelectorAll('.dashboard-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
    
    // Funcionalidade para confirmar presença na consulta
});