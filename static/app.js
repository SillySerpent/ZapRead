/**
 * ZapRead Application JavaScript
 * Enhanced UI interactions and loading animations
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializePageLoader();
    initializeTooltips();
    initializeAnimations();
    initializeDropzone();
    initializeNavbar();
    initializeFAQs();
    initializeFormValidation();
    initializeFlashMessages();
    initializeNewsletterForm();
    initializeFeedbackForm();
});

/**
 * Page Loading Management
 */
function initializePageLoader() {
    // Create page loader if it doesn't exist
    if (!document.querySelector('.page-loading-overlay')) {
        const loader = document.createElement('div');
        loader.className = 'page-loading-overlay hidden';
        loader.innerHTML = `
            <div class="loading-spinner"></div>
            <p class="loading-text">Loading<span class="loading-dots"></span></p>
        `;
        document.body.appendChild(loader);
    }

    // Hide the loader when page is fully loaded
    window.addEventListener('load', function() {
        hidePageLoader();
    });

    // Show loader during page navigation
    document.addEventListener('click', function(e) {
        // Check if the clicked element is a link that navigates to a new page
        const link = e.target.closest('a');
        if (link && link.href && !link.href.includes('#') && 
            !link.href.includes('javascript:') && 
            !link.getAttribute('download') && 
            !e.ctrlKey && !e.metaKey) {
            showPageLoader();
        }
    });

    // Handle form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        // Don't show loader for forms with data-no-loader attribute
        if (!form.hasAttribute('data-no-loader')) {
            showPageLoader('Processing your request...');
        }
    });
}

function showPageLoader(message = 'Loading<span class="loading-dots"></span>') {
    const loader = document.querySelector('.page-loading-overlay');
    if (loader) {
        const loadingText = loader.querySelector('.loading-text');
        if (loadingText) {
            loadingText.innerHTML = message;
        }
        loader.classList.remove('hidden');
    }
}

function hidePageLoader() {
    const loader = document.querySelector('.page-loading-overlay');
    if (loader) {
        loader.classList.add('hidden');
    }
}

/**
 * Bootstrap Tooltip Initialization
 */
function initializeTooltips() {
    // Initialize all tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Animations Management
 */
function initializeAnimations() {
    // Apply animations to elements with animation classes
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up, .slide-in-right, .slide-in-left, .scale-up');
    
    // Set initial opacity to 0
    animatedElements.forEach(element => {
        element.style.opacity = '0';
    });
    
    // Create an Intersection Observer to trigger animations when elements come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    // Observe all animated elements
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

/**
 * Dropzone File Upload Enhancement
 */
function initializeDropzone() {
    const dropZone = document.getElementById('drop-zone');
    if (!dropZone) return;
    
    const fileInput = document.getElementById('file-input');
    const fileDetails = document.getElementById('file-details');
    const selectedFileName = document.getElementById('selected-file-name');
    const selectedFileSize = document.getElementById('selected-file-size');
    const removeFileBtn = document.getElementById('remove-file');
    const uploadBtn = document.getElementById('upload-btn');
    
    // Open file browser when clicking on the drop zone
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle file selection from file browser
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    // Handle drag over
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    // Handle drag leave
    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, function() {
            dropZone.classList.remove('drag-over');
        });
    });
    
    // Handle drop
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });
    
    // Remove selected file
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', function() {
            fileInput.value = '';
            fileDetails.style.display = 'none';
            uploadBtn.disabled = true;
        });
    }
    
    // Handle selected files
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            selectedFileName.textContent = file.name;
            selectedFileSize.textContent = formatFileSize(file.size);
            fileDetails.style.display = 'block';
            uploadBtn.disabled = false;
            
            // Add animation to the file details
            fileDetails.classList.add('scale-up');
            setTimeout(() => {
                fileDetails.classList.remove('scale-up');
            }, 500);
        }
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

/**
 * Sticky Navbar Enhancement
 */
function initializeNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

/**
 * FAQ Accordion Functionality
 */
function initializeFAQs() {
    const faqItems = document.querySelectorAll('.faq-item');
    if (faqItems.length === 0) return;
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', function() {
            // Toggle active class
            item.classList.toggle('active');
            
            // Update icon
            const icon = question.querySelector('i');
            if (icon) {
                if (item.classList.contains('active')) {
                    icon.classList.remove('bi-plus');
                    icon.classList.add('bi-dash');
                } else {
                    icon.classList.remove('bi-dash');
                    icon.classList.add('bi-plus');
                }
            }
        });
    });
}

/**
 * Form Validation Enhancement
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                // Add loading state to submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.hasAttribute('data-no-loading')) {
                    submitBtn.classList.add('btn-loading');
                    submitBtn.disabled = true;
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Enhanced Flash Messages
 */
function initializeFlashMessages() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

/**
 * Newsletter Form Handling
 */
function initializeNewsletterForm() {
    const newsletterForm = document.querySelector('.newsletter-form');
    if (!newsletterForm) return;
    
    newsletterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const emailInput = this.querySelector('input[type="email"]');
        const submitBtn = this.querySelector('button[type="submit"]');
        
        if (!emailInput.value.trim()) {
            // Show error
            emailInput.classList.add('is-invalid');
            return;
        }
        
        // Add loading state
        emailInput.disabled = true;
        submitBtn.disabled = true;
        submitBtn.classList.add('btn-loading');
        
        // Simulate AJAX request (replace with actual AJAX)
        setTimeout(() => {
            // Reset form
            newsletterForm.reset();
            emailInput.disabled = false;
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn-loading');
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'alert alert-success mt-3 fade-in';
            successMessage.innerHTML = 'Thank you for subscribing to our newsletter!';
            newsletterForm.parentNode.appendChild(successMessage);
            
            // Remove after 5 seconds
            setTimeout(() => {
                successMessage.remove();
            }, 5000);
        }, 1500);
    });
}

/**
 * Feedback Form Handling
 */
function initializeFeedbackForm() {
    const feedbackForm = document.querySelector('.feedback-form');
    if (!feedbackForm) return;
    
    feedbackForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitBtn = this.querySelector('button[type="submit"]');
        
        // Add loading state
        submitBtn.classList.add('btn-loading');
        submitBtn.disabled = true;
        
        // Disable all inputs
        feedbackForm.querySelectorAll('input, textarea').forEach(input => {
            input.disabled = true;
        });
        
        // Simulate AJAX request (replace with actual AJAX)
        setTimeout(() => {
            // Reset form
            feedbackForm.reset();
            
            // Enable inputs
            feedbackForm.querySelectorAll('input, textarea').forEach(input => {
                input.disabled = false;
            });
            
            // Reset button
            submitBtn.disabled = false;
            submitBtn.classList.remove('btn-loading');
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'alert alert-success mt-3 fade-in';
            successMessage.innerHTML = 'Thank you for your feedback! We appreciate your input.';
            feedbackForm.parentNode.appendChild(successMessage);
            
            // Remove after 5 seconds
            setTimeout(() => {
                successMessage.remove();
            }, 5000);
        }, 1500);
    });
}

/**
 * File Processing Status Updates
 */
function updateProcessingStatus(status, percentage = null) {
    const statusElement = document.getElementById('processing-status');
    if (!statusElement) return;
    
    statusElement.textContent = status;
    
    if (percentage !== null) {
        const progressBar = document.querySelector('.progress-bar-fill');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }
}

/**
 * Button Loading State
 */
function setButtonLoading(button, isLoading, loadingText = null) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.classList.add('btn-loading');
        if (loadingText) {
            button.dataset.originalText = button.textContent;
            button.textContent = loadingText;
        }
    } else {
        button.disabled = false;
        button.classList.remove('btn-loading');
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

/**
 * Stripe Payment Button Enhancement
 */
if (document.getElementById('checkout-button')) {
    document.getElementById('checkout-button').addEventListener('click', function() {
        setButtonLoading(this, true, 'Processing...');
    });
} 