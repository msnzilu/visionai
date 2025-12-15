// CVision Help Center JavaScript

// Search functionality
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('helpSearch');
    const faqItems = document.querySelectorAll('.faq-item');

    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();

            faqItems.forEach(item => {
                const question = item.querySelector('button span').textContent.toLowerCase();
                const answer = item.querySelector('.faq-answer p').textContent.toLowerCase();

                if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});

// Toggle FAQ accordion
function toggleFAQ(button) {
    const answer = button.nextElementSibling;
    const icon = button.querySelector('svg');
    const isOpen = !answer.classList.contains('hidden');

    // Close all other FAQs
    document.querySelectorAll('.faq-answer').forEach(item => {
        if (item !== answer) {
            item.classList.add('hidden');
        }
    });

    document.querySelectorAll('.faq-item button svg').forEach(svg => {
        if (svg !== icon) {
            svg.style.transform = 'rotate(0deg)';
        }
    });

    // Toggle current FAQ
    if (isOpen) {
        answer.classList.add('hidden');
        icon.style.transform = 'rotate(0deg)';
    } else {
        answer.classList.remove('hidden');
        icon.style.transform = 'rotate(180deg)';
    }
}

// Filter FAQs by category
function filterFAQs(category) {
    const faqItems = document.querySelectorAll('.faq-item');
    const filterButtons = document.querySelectorAll('.faq-filter-btn');

    // Update active button
    filterButtons.forEach(btn => {
        btn.classList.remove('active');
        btn.style.backgroundColor = 'transparent';
        btn.style.color = '#4b5563';
    });

    event.target.classList.add('active');
    event.target.style.backgroundColor = '#667eea';
    event.target.style.color = 'white';

    // Filter FAQ items
    faqItems.forEach(item => {
        if (category === 'all') {
            item.style.display = 'block';
        } else {
            const itemCategory = item.getAttribute('data-category');
            if (itemCategory === category) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        }
    });
}

// Initialize filter buttons styling
document.addEventListener('DOMContentLoaded', function () {
    const filterButtons = document.querySelectorAll('.faq-filter-btn');

    filterButtons.forEach(btn => {
        if (btn.classList.contains('active')) {
            btn.style.backgroundColor = '#667eea';
            btn.style.color = 'white';
        } else {
            btn.style.backgroundColor = 'transparent';
            btn.style.color = '#4b5563';
        }
    });
});

// Open live chat (placeholder)


// Contact form submission
document.addEventListener('DOMContentLoaded', function () {
    const contactForm = document.getElementById('contactForm');

    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // Show success message
            const formData = new FormData(contactForm);

            // In a real implementation, you would send this to your backend
            alert('Thank you for your message! Our support team will get back to you within 24 hours.');

            // Reset form
            contactForm.reset();
        });
    }
});

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function () {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Mobile menu toggle (if needed)
document.addEventListener('DOMContentLoaded', function () {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
        });
    }
});
