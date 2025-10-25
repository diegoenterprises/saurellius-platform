/**
 * Saurellius Platform - Interactive Animations
 * Makes the entire page feel alive with smooth animations and interactions
 */

// Count-up animation for stats
function animateCountUp(element, target, duration = 2000, suffix = '') {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format number with commas
        const formatted = Math.floor(current).toLocaleString();
        element.textContent = formatted + suffix;
    }, 16);
}

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            
            // Trigger count-up for stats
            if (entry.target.classList.contains('stat-number')) {
                const target = parseInt(entry.target.dataset.target);
                const suffix = entry.target.dataset.suffix || '';
                animateCountUp(entry.target, target, 2000, suffix);
                observer.unobserve(entry.target);
            }
        }
    });
}, observerOptions);

// Initialize animations on page load
document.addEventListener('DOMContentLoaded', () => {
    
    // Observe all animated elements
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up, .stat-number, .feature-card, .pricing-card');
    animatedElements.forEach(el => observer.observe(el));
    
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn, .cta-button, .pricing-button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.feature-card, .pricing-card, .employee-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = '0 12px 40px rgba(124, 58, 237, 0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        });
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Parallax effect for hero section
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                const hero = document.querySelector('.hero-section');
                if (hero && scrolled < window.innerHeight) {
                    hero.style.transform = `translateY(${scrolled * 0.5}px)`;
                    hero.style.opacity = 1 - (scrolled / window.innerHeight);
                }
                ticking = false;
            });
            ticking = true;
        }
    });
    
    // Add ripple effect to buttons
    function createRipple(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        ripple.style.width = ripple.style.height = `${diameter}px`;
        ripple.style.left = `${event.clientX - button.offsetLeft - radius}px`;
        ripple.style.top = `${event.clientY - button.offsetTop - radius}px`;
        ripple.classList.add('ripple');
        
        const existingRipple = button.querySelector('.ripple');
        if (existingRipple) {
            existingRipple.remove();
        }
        
        button.appendChild(ripple);
    }
    
    buttons.forEach(button => {
        button.addEventListener('click', createRipple);
    });
    
    // Stagger animation for feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Animated gradient background
    const hero = document.querySelector('.hero-section');
    if (hero) {
        let hue = 250;
        setInterval(() => {
            hue = (hue + 0.5) % 360;
            const color1 = `hsl(${hue}, 70%, 60%)`;
            const color2 = `hsl(${(hue + 60) % 360}, 70%, 55%)`;
            hero.style.background = `linear-gradient(135deg, ${color1}, ${color2})`;
        }, 50);
    }
    
    // Typing effect for hero headline (optional)
    const headline = document.querySelector('.hero-headline');
    if (headline && headline.dataset.typeEffect) {
        const text = headline.textContent;
        headline.textContent = '';
        let i = 0;
        
        function typeWriter() {
            if (i < text.length) {
                headline.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }
        }
        
        typeWriter();
    }
    
    // Add floating animation to icons
    const icons = document.querySelectorAll('.feature-icon, .pricing-icon');
    icons.forEach((icon, index) => {
        icon.style.animation = `float 3s ease-in-out ${index * 0.2}s infinite`;
    });
    
    // Progress bar animation for loading
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = bar.dataset.progress || '0';
        setTimeout(() => {
            bar.style.width = targetWidth + '%';
        }, 100);
    });
    
    // Add pulse animation to CTA buttons
    const ctaButtons = document.querySelectorAll('.cta-primary');
    ctaButtons.forEach(button => {
        setInterval(() => {
            button.style.animation = 'pulse 0.5s ease-in-out';
            setTimeout(() => {
                button.style.animation = '';
            }, 500);
        }, 3000);
    });
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar, nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // Add loading skeleton fade-out
    const skeletons = document.querySelectorAll('.skeleton');
    setTimeout(() => {
        skeletons.forEach(skeleton => {
            skeleton.style.opacity = '0';
            setTimeout(() => skeleton.remove(), 300);
        });
    }, 500);
    
});

// Utility function for stagger animations
function staggerAnimation(elements, delay = 100) {
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('animate-in');
        }, index * delay);
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { animateCountUp, staggerAnimation };
}

