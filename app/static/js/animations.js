// ===== ANIMACIONES Y DINÁMICAS DE LA APLICACIÓN =====

// Inicializar cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    setupFormAnimations();
    setupInteractiveElements();
    setupScrollAnimations();
});

// ===== ANIMACIONES INICIALES =====
function initializeAnimations() {
    console.log('🎬 Animaciones iniciales activadas');
    
    // Animar líneas de entrada de formulario
    const inputs = document.querySelectorAll('.form-group input');
    inputs.forEach((input, index) => {
        input.style.animationDelay = `${index * 0.1}s`;
    });

    // Animar texto de bienvenida (typewriter)
    animateWelcomeText();
}

// ===== ANIMAR TEXTO DE BIENVENIDA (TYPEWRITER LOOP) =====
function animateWelcomeText() {
    const titleElement = document.querySelector('.auth-image h2');
    if (!titleElement) return;

    const text = titleElement.textContent.trim() || "Hotel Gales";
    titleElement.textContent = '';
    titleElement.style.borderRight = '3px solid #ff6b6b';
    titleElement.style.paddingRight = '5px';
    titleElement.style.whiteSpace = 'nowrap';
    titleElement.style.overflow = 'hidden';

    let index = 0;
    let isDeleting = false;
    const typeSpeed = 150;
    const deleteSpeed = 100;
    const waitTime = 2000; // Tiempo que se queda el texto escrito
    const colors = ['#ff6b6b', '#ffd93d', '#6bcf7f', '#4d96ff'];
    let colorIndex = 0;

    function typeLoop() {
        const currentText = text.substring(0, index);
        titleElement.textContent = currentText;

        // Cambiar color del cursor
        colorIndex = Math.floor(index / 2) % colors.length;
        titleElement.style.borderRightColor = colors[colorIndex];

        let nextSpeed = isDeleting ? deleteSpeed : typeSpeed;

        if (!isDeleting && index === text.length) {
            // Terminó de escribir, esperar
            isDeleting = true;
            nextSpeed = waitTime;
        } else if (isDeleting && index === 0) {
            // Terminó de borrar, volver a empezar
            isDeleting = false;
            nextSpeed = 500;
        }

        if (isDeleting) {
            index--;
        } else {
            index++;
        }

        // Asegurar que el index no se salga de los límites para la próxima iteración
        if (index < 0) index = 0;
        if (index > text.length) index = text.length;

        setTimeout(typeLoop, nextSpeed);
    }

    typeLoop();
}

// Agregar animación de cursor parpadeante
if (!document.getElementById('cursor-blink-style')) {
    const style = document.createElement('style');
    style.id = 'cursor-blink-style';
    style.textContent = `
        @keyframes cursor-blink {
            0%, 50% {
                border-right: 3px solid currentColor;
            }
            51%, 100% {
                border-right: 3px solid transparent;
            }
        }
    `;
    document.head.appendChild(style);
}

// ===== ANIMACIONES DE FORMULARIO =====
function setupFormAnimations() {
    // Efecto focus en inputs
    const inputs = document.querySelectorAll('.form-group input');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });

        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });

        // Validar mientras se escribe
        input.addEventListener('input', function() {
            if (this.value.length > 0) {
                this.style.borderColor = '#10b981';
            } else {
                this.style.borderColor = '#e0e0e0';
            }
        });
    });

    // Validar contraseñas coincidan
    const passwordInput = document.getElementById('contraseña');
    const confirmPasswordInput = document.getElementById('confirmar_contraseña');

    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (passwordInput.value === this.value && this.value.length > 0) {
                this.style.borderColor = '#10b981';
                this.parentElement.title = '✓ Las contraseñas coinciden';
            } else if (this.value.length > 0) {
                this.style.borderColor = '#ef4444';
                this.parentElement.title = '✗ Las contraseñas no coinciden';
            } else {
                this.style.borderColor = '#e0e0e0';
            }
        });
    }
}

// ===== ELEMENTOS INTERACTIVOS =====
function setupInteractiveElements() {
    // Botones con efecto ripple
    const buttons = document.querySelectorAll('.btn-auth, .btn-secondary-auth, .sidebar-logout');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            createRipple(e, this);
        });
    });

    // Links con efecto hover mejorado
    const links = document.querySelectorAll('.auth-link, .auth-footer a');
    
    links.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });

        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });

    // Checkbox con efecto visual
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.style.transform = 'scale(1.3)';
                this.style.transition = 'transform 0.3s ease';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 200);
            }
        });
    });
}

// ===== EFECTO RIPPLE EN BOTONES =====
function createRipple(event, element) {
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        left: ${x}px;
        top: ${y}px;
        width: ${size}px;
        height: ${size}px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple-effect 0.6s ease-out;
        pointer-events: none;
    `;

    if (!element.style.position) {
        element.style.position = 'relative';
    }

    element.style.overflow = 'hidden';
    element.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
}

// Agregar estilos de ripple
if (!document.getElementById('ripple-style')) {
    const style = document.createElement('style');
    style.id = 'ripple-style';
    style.textContent = `
        @keyframes ripple-effect {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ===== ANIMACIONES AL SCROLL =====
function setupScrollAnimations() {
    // Observar elementos que entran en vista
    const cards = document.querySelectorAll('.card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'bounce-in 0.6s ease';
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => observer.observe(card));
}

// ===== EFECTOS DE LOADER =====
function showLoader() {
    if (document.getElementById('loader')) return;

    const loader = document.createElement('div');
    loader.id = 'loader';
    loader.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
    `;

    loader.innerHTML = `
        <div style="
            width: 50px;
            height: 50px;
            border: 4px solid rgba(26, 58, 82, 0.2);
            border-top: 4px solid #1a3a52;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <p style="color: #1a3a52; font-weight: 600;">Cargando...</p>
    `;

    document.body.appendChild(loader);

    // Agregar animación spin
    if (!document.getElementById('spin-style')) {
        const style = document.createElement('style');
        style.id = 'spin-style';
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.opacity = '0';
        loader.style.transition = 'opacity 0.3s ease';
        setTimeout(() => loader.remove(), 300);
    }
}

// ===== VALIDACIÓN EN TIEMPO REAL =====
function validateForm(formElement) {
    let isValid = true;
    const inputs = formElement.querySelectorAll('input[required]');

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#ef4444';
            isValid = false;
        }
    });

    return isValid;
}

// Agregar validación a formularios
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Por favor completa todos los campos', 'error');
            }
        });
    });
});

// ===== NOTIFICACIONES TOAST =====
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slide-in-right 0.3s ease;
        max-width: 300px;
        ${type === 'success' ? 'background: #10b981;' : 'background: #ef4444;'}
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;

    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slide-out-right 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Agregar estilos de slide-out
if (!document.getElementById('slide-out-style')) {
    const style = document.createElement('style');
    style.id = 'slide-out-style';
    style.textContent = `
        @keyframes slide-out-right {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }
    `;
    document.head.appendChild(style);
}

// ===== EFECTO PARALLAX =====
window.addEventListener('mousemove', function(e) {
    const authImage = document.querySelector('.auth-image-content');
    if (!authImage) return;

    const x = (e.clientX / window.innerWidth) * 10 - 5;
    const y = (e.clientY / window.innerHeight) * 10 - 5;

    authImage.style.transform = `perspective(1000px) rotateX(${y}deg) rotateY(${x}deg)`;
});

// Resetear perspectiva al salir del mouse
document.addEventListener('mouseleave', function() {
    const authImage = document.querySelector('.auth-image-content');
    if (authImage) {
        authImage.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
    }
});

// ===== ANIMACIÓN DE TRANSICIÓN DE PÁGINAS =====
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.href && !e.target.hasAttribute('target')) {
        // No mostrar loader para links internos sin navegar
        if (!e.target.href.includes(window.location.hostname)) return;
    }
});

console.log('✨ Animaciones JavaScript cargadas correctamente');
