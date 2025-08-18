// Mobile-specific JavaScript enhancements for Badminton Scheduler

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    initializeMobileMenu();
    
    // Touch interaction enhancements
    initializeTouchInteractions();
    
    // Mobile form enhancements
    initializeMobileFormEnhancements();
    
    // Swipe gestures for availability cards
    initializeSwipeGestures();
    
    // Mobile viewport adjustments
    initializeMobileViewport();
});

function initializeMobileMenu() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        // Add touch feedback
        mobileMenuButton.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        mobileMenuButton.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
        
        mobileMenuButton.addEventListener('click', function(e) {
            e.preventDefault();
            toggleMobileMenu();
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
                closeMobileMenu();
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeMobileMenu();
            }
        });
    }
}

function toggleMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    
    if (mobileMenu && mobileMenuButton) {
        const isHidden = mobileMenu.classList.contains('hidden');
        
        if (isHidden) {
            openMobileMenu();
        } else {
            closeMobileMenu();
        }
    }
}

function openMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    
    mobileMenu.classList.remove('hidden');
    mobileMenuButton.setAttribute('aria-expanded', 'true');
    
    // Update button icon to X
    const svg = mobileMenuButton.querySelector('svg path');
    if (svg) {
        svg.setAttribute('d', 'M6 18L18 6M6 6l12 12');
    }
    
    // Add animation
    mobileMenu.style.opacity = '0';
    mobileMenu.style.transform = 'translateY(-10px)';
    
    requestAnimationFrame(() => {
        mobileMenu.style.transition = 'opacity 0.2s ease-out, transform 0.2s ease-out';
        mobileMenu.style.opacity = '1';
        mobileMenu.style.transform = 'translateY(0)';
    });
}

function closeMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    
    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.style.transition = 'opacity 0.2s ease-out, transform 0.2s ease-out';
        mobileMenu.style.opacity = '0';
        mobileMenu.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            mobileMenu.classList.add('hidden');
            mobileMenuButton.setAttribute('aria-expanded', 'false');
            
            // Update button icon to hamburger
            const svg = mobileMenuButton.querySelector('svg path');
            if (svg) {
                svg.setAttribute('d', 'M4 6h16M4 12h16M4 18h16');
            }
        }, 200);
    }
}

function initializeTouchInteractions() {
    // Add touch feedback to all touch targets
    const touchTargets = document.querySelectorAll('.touch-target, button, a, input[type="submit"]');
    
    touchTargets.forEach(target => {
        // Skip if already has touch handlers
        if (target.hasAttribute('data-touch-initialized')) return;
        target.setAttribute('data-touch-initialized', 'true');
        
        target.addEventListener('touchstart', function(e) {
            // Add visual feedback
            this.style.transform = 'scale(0.98)';
            this.style.transition = 'transform 0.1s ease-out';
            
            // Add ripple effect for buttons
            if (this.tagName === 'BUTTON' || this.classList.contains('btn-neon')) {
                createRippleEffect(this, e);
            }
        }, { passive: true });
        
        target.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        }, { passive: true });
        
        target.addEventListener('touchcancel', function() {
            this.style.transform = 'scale(1)';
        }, { passive: true });
    });
}

function createRippleEffect(element, event) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = (event.touches[0].clientX - rect.left) - size / 2;
    const y = (event.touches[0].clientY - rect.top) - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    // Add ripple styles
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(0, 255, 65, 0.3)';
    ripple.style.transform = 'scale(0)';
    ripple.style.animation = 'ripple 0.6s linear';
    ripple.style.pointerEvents = 'none';
    
    // Ensure element has relative positioning
    if (getComputedStyle(element).position === 'static') {
        element.style.position = 'relative';
    }
    element.style.overflow = 'hidden';
    
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function initializeMobileFormEnhancements() {
    // Prevent zoom on input focus for iOS
    const inputs = document.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // Ensure minimum font size to prevent zoom
        if (window.innerWidth <= 768) {
            const computedStyle = getComputedStyle(input);
            const fontSize = parseFloat(computedStyle.fontSize);
            
            if (fontSize < 16) {
                input.style.fontSize = '16px';
            }
        }
        
        // Add focus/blur animations
        input.addEventListener('focus', function() {
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'transform 0.2s ease-out';
        });
        
        input.addEventListener('blur', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Auto-scroll to focused input on mobile
    if (window.innerWidth <= 768) {
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                setTimeout(() => {
                    this.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center',
                        inline: 'nearest'
                    });
                }, 300); // Wait for virtual keyboard
            });
        });
    }
}

function initializeSwipeGestures() {
    const availabilityCards = document.querySelectorAll('.availability-card, .availability-entry-mobile');
    
    availabilityCards.forEach(card => {
        let startX = 0;
        let startY = 0;
        let currentX = 0;
        let currentY = 0;
        let isDragging = false;
        
        card.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            currentX = startX;
            currentY = startY;
            isDragging = true;
        }, { passive: true });
        
        card.addEventListener('touchmove', function(e) {
            if (!isDragging) return;
            
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
            
            const deltaX = currentX - startX;
            const deltaY = currentY - startY;
            
            // Only handle horizontal swipes
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
                e.preventDefault();
                
                // Add visual feedback
                const opacity = Math.max(0.7, 1 - Math.abs(deltaX) / 200);
                this.style.opacity = opacity;
                this.style.transform = `translateX(${deltaX * 0.3}px)`;
            }
        }, { passive: false });
        
        card.addEventListener('touchend', function(e) {
            if (!isDragging) return;
            isDragging = false;
            
            const deltaX = currentX - startX;
            const deltaY = currentY - startY;
            
            // Reset visual state
            this.style.opacity = '1';
            this.style.transform = 'translateX(0)';
            this.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            
            setTimeout(() => {
                this.style.transition = '';
            }, 300);
            
            // Handle swipe actions
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    // Swipe right - could trigger edit action
                    const editButton = this.querySelector('a[href*="edit"]');
                    if (editButton) {
                        // Visual feedback for swipe action
                        showSwipeHint(this, 'Edit', 'right');
                    }
                } else {
                    // Swipe left - could trigger delete action
                    const deleteButton = this.querySelector('button[type="submit"]');
                    if (deleteButton) {
                        // Visual feedback for swipe action
                        showSwipeHint(this, 'Delete', 'left');
                    }
                }
            }
        }, { passive: true });
    });
}

function showSwipeHint(element, action, direction) {
    const hint = document.createElement('div');
    hint.textContent = `Swipe ${direction} to ${action.toLowerCase()}`;
    hint.style.position = 'absolute';
    hint.style.top = '50%';
    hint.style.left = '50%';
    hint.style.transform = 'translate(-50%, -50%)';
    hint.style.background = 'rgba(0, 255, 65, 0.9)';
    hint.style.color = 'black';
    hint.style.padding = '8px 16px';
    hint.style.borderRadius = '20px';
    hint.style.fontSize = '12px';
    hint.style.fontWeight = 'bold';
    hint.style.zIndex = '1000';
    hint.style.pointerEvents = 'none';
    hint.style.opacity = '0';
    hint.style.transition = 'opacity 0.3s ease-out';
    
    // Ensure element has relative positioning
    if (getComputedStyle(element).position === 'static') {
        element.style.position = 'relative';
    }
    
    element.appendChild(hint);
    
    requestAnimationFrame(() => {
        hint.style.opacity = '1';
    });
    
    setTimeout(() => {
        hint.style.opacity = '0';
        setTimeout(() => {
            hint.remove();
        }, 300);
    }, 2000);
}

function initializeMobileViewport() {
    // Handle viewport changes (orientation, keyboard)
    let initialViewportHeight = window.innerHeight;
    
    window.addEventListener('resize', function() {
        // Detect virtual keyboard
        const currentHeight = window.innerHeight;
        const heightDifference = initialViewportHeight - currentHeight;
        
        if (heightDifference > 150) {
            // Virtual keyboard is likely open
            document.body.classList.add('keyboard-open');
            
            // Adjust focused element position
            const focusedElement = document.activeElement;
            if (focusedElement && (focusedElement.tagName === 'INPUT' || focusedElement.tagName === 'TEXTAREA')) {
                setTimeout(() => {
                    focusedElement.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }, 100);
            }
        } else {
            // Virtual keyboard is likely closed
            document.body.classList.remove('keyboard-open');
        }
    });
    
    // Handle orientation change
    window.addEventListener('orientationchange', function() {
        setTimeout(() => {
            initialViewportHeight = window.innerHeight;
            
            // Force layout recalculation
            document.body.style.height = window.innerHeight + 'px';
            setTimeout(() => {
                document.body.style.height = '';
            }, 100);
        }, 500);
    });
}

// Add CSS for ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .keyboard-open {
        height: 100vh;
        overflow: hidden;
    }
    
    .keyboard-open .mobile-menu {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
    }
`;
document.head.appendChild(style);