// Navigation handling
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    const featureCards = document.querySelectorAll('.feature-card');
    
    // Handle navigation link clicks
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');
            navigateToPage(targetPage);
        });
    });
    
    // Handle feature card clicks
    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            const targetPage = this.getAttribute('data-page');
            if (targetPage) {
                navigateToPage(targetPage);
            }
        });
    });
    
    // Navigate to specific page
    function navigateToPage(pageId) {
        // Hide all pages
        pages.forEach(page => {
            page.classList.remove('active');
        });
        
        // Remove active class from all nav links
        navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // Show target page
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
        }
        
        // Add active class to corresponding nav link
        const activeLink = document.querySelector(`[data-page="${pageId}"]`);
        if (activeLink && activeLink.classList.contains('nav-link')) {
            activeLink.classList.add('active');
        }
        
        // Scroll to top
        window.scrollTo(0, 0);
    }
});

// Export navigation function for use in other modules
window.navigateToPage = function(pageId) {
    const event = new CustomEvent('navigate', { detail: { page: pageId } });
    document.dispatchEvent(event);
    
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    
    pages.forEach(page => page.classList.remove('active'));
    navLinks.forEach(link => link.classList.remove('active'));
    
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    const activeLink = document.querySelector(`[data-page="${pageId}"]`);
    if (activeLink && activeLink.classList.contains('nav-link')) {
        activeLink.classList.add('active');
    }
    
    window.scrollTo(0, 0);
};