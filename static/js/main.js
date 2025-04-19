document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate on Scroll)
    AOS.init({
        duration: 800,
        easing: 'ease',
        once: true,
        offset: 100
    });
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Chat widget functionality
    const chatButton = document.querySelector('.chat-button');
    const chatContainer = document.querySelector('.chat-container');
    const chatClose = document.querySelector('.chat-close');
    
    if (chatButton && chatContainer && chatClose) {
        chatButton.addEventListener('click', function() {
            chatContainer.style.display = 'flex';
            chatButton.style.display = 'none';
        });
        
        chatClose.addEventListener('click', function() {
            chatContainer.style.display = 'none';
            chatButton.style.display = 'flex';
        });
    }
    
    // Handle flash messages timeout
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.classList.add('fade');
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Portfolio filter functionality
    const portfolioFilters = document.querySelectorAll('.portfolio-filter');
    if (portfolioFilters.length > 0) {
        portfolioFilters.forEach(filter => {
            filter.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Remove active class from all filters
                portfolioFilters.forEach(f => f.classList.remove('active'));
                
                // Add active class to clicked filter
                this.classList.add('active');
                
                const filterValue = this.getAttribute('data-filter');
                
                // Show/hide portfolio items based on filter
                const portfolioItems = document.querySelectorAll('.portfolio-item');
                portfolioItems.forEach(item => {
                    if (filterValue === 'all' || item.classList.contains(filterValue)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // Service tabs functionality
    const serviceTabs = document.querySelectorAll('.service-tab');
    if (serviceTabs.length > 0) {
        serviceTabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Remove active class from all tabs
                serviceTabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Hide all tab content
                const tabContents = document.querySelectorAll('.service-tab-content');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                // Show clicked tab content
                const targetContent = document.querySelector(this.getAttribute('data-target'));
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }
    
    // Mobile navigation toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('mobile-nav-active');
        });
    }
    
    // Close mobile nav when clicking outside
    document.addEventListener('click', function(e) {
        if (document.body.classList.contains('mobile-nav-active') && 
            !e.target.closest('.navbar') && 
            !e.target.closest('.navbar-toggler')) {
            document.body.classList.remove('mobile-nav-active');
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Star rating system
    const ratingInputs = document.querySelectorAll('.rating-input');
    if (ratingInputs.length > 0) {
        ratingInputs.forEach(input => {
            input.addEventListener('change', function() {
                const ratingValue = document.querySelector('.rating-value');
                if (ratingValue) {
                    ratingValue.textContent = this.value;
                }
                
                // Update stars visual
                const stars = document.querySelectorAll('.rating-star');
                stars.forEach((star, index) => {
                    if (index < this.value) {
                        star.classList.add('active');
                    } else {
                        star.classList.remove('active');
                    }
                });
            });
        });
    }
    
    // Check if we're on the booking page
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        // Initialize booking steps functionality
        initBookingSteps();
    }
});

// Booking steps functionality
function initBookingSteps() {
    const nextButtons = document.querySelectorAll('.next-step');
    const prevButtons = document.querySelectorAll('.prev-step');
    const bookingSteps = document.querySelectorAll('.booking-step');
    const stepContents = document.querySelectorAll('.step-content');
    
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = parseInt(this.getAttribute('data-current-step'));
            const nextStep = currentStep + 1;
            
            // Validate current step
            if (!validateStep(currentStep)) {
                return;
            }
            
            // Hide current step content
            stepContents[currentStep - 1].style.display = 'none';
            
            // Show next step content
            stepContents[nextStep - 1].style.display = 'block';
            
            // Update booking steps UI
            bookingSteps[currentStep - 1].classList.remove('active');
            bookingSteps[currentStep - 1].classList.add('completed');
            bookingSteps[nextStep - 1].classList.add('active');
            
            // Scroll to top of form
            window.scrollTo({
                top: document.getElementById('bookingForm').offsetTop - 100,
                behavior: 'smooth'
            });
        });
    });
    
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = parseInt(this.getAttribute('data-current-step'));
            const prevStep = currentStep - 1;
            
            // Hide current step content
            stepContents[currentStep - 1].style.display = 'none';
            
            // Show previous step content
            stepContents[prevStep - 1].style.display = 'block';
            
            // Update booking steps UI
            bookingSteps[currentStep - 1].classList.remove('active');
            bookingSteps[prevStep - 1].classList.remove('completed');
            bookingSteps[prevStep - 1].classList.add('active');
            
            // Scroll to top of form
            window.scrollTo({
                top: document.getElementById('bookingForm').offsetTop - 100,
                behavior: 'smooth'
            });
        });
    });
}

// Validate booking form step
function validateStep(stepNumber) {
    // Get fields in current step
    const currentStepContent = document.querySelector(`.step-content[data-step="${stepNumber}"]`);
    const requiredFields = currentStepContent.querySelectorAll('[required]');
    
    // Check if all required fields are filled
    let valid = true;
    requiredFields.forEach(field => {
        if (!field.value) {
            field.classList.add('is-invalid');
            valid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!valid) {
        // Show error message
        const errorMessage = currentStepContent.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.style.display = 'block';
        }
    }
    
    return valid;
}
