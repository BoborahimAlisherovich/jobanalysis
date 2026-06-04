// ============================================
// Aura Career - Main JavaScript
// Pro UI/UX Interactions v2.0
// ============================================

document.addEventListener('DOMContentLoaded', function() {

  // --- Mobile Menu Toggle ---
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const mobileNav = document.getElementById('mobileNav');
  
  if (mobileMenuBtn && mobileNav) {
    mobileMenuBtn.addEventListener('click', function() {
      const isOpen = mobileNav.classList.contains('open');
      mobileNav.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', !isOpen);
      document.body.style.overflow = isOpen ? '' : 'hidden';
      
      // Animate hamburger
      const bars = mobileMenuBtn.querySelectorAll('span');
      if (!isOpen) {
        bars[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        bars[1].style.opacity = '0';
        bars[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else {
        bars[0].style.transform = '';
        bars[1].style.opacity = '';
        bars[2].style.transform = '';
      }
    });

    // Close on link click
    mobileNav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      });
    });
  }

  // --- Navbar Scroll Effect ---
  const navbar = document.querySelector('.glass-nav');
  if (navbar) {
    let lastScroll = 0;
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;
      if (currentScroll > 100) {
        navbar.style.background = 'rgba(4, 5, 10, 0.85)';
        navbar.style.borderBottomColor = 'rgba(255,255,255,0.08)';
      } else {
        navbar.style.background = 'rgba(4, 5, 10, 0.6)';
        navbar.style.borderBottomColor = 'rgba(255,255,255,0.05)';
      }
      
      // Hide/show on scroll direction
      if (currentScroll > lastScroll && currentScroll > 300) {
        navbar.style.transform = 'translateY(-100%)';
      } else {
        navbar.style.transform = 'translateY(0)';
      }
      lastScroll = currentScroll;
    });
  }

  // --- Password Toggle ---
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const input = this.closest('.relative').querySelector('input');
      if (!input) return;
      
      if (input.type === 'password') {
        input.type = 'text';
        this.innerHTML = `<svg class="w-5 h-5 text-accent-neon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>`;
      } else {
        input.type = 'password';
        this.innerHTML = `<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>`;
      }
    });
  });

  // --- Message Toasts Auto-Dismiss ---
  document.querySelectorAll('.message-toast').forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px) scale(0.95)';
      toast.style.transition = 'all 0.4s ease-out';
      setTimeout(() => toast.remove(), 400);
    }, 4000);

    toast.addEventListener('click', function() {
      this.style.opacity = '0';
      this.style.transform = 'translateY(-10px) scale(0.95)';
      this.style.transition = 'all 0.3s ease-out';
      setTimeout(() => this.remove(), 300);
    });
  });

  // --- Intersection Observer for Scroll Animations ---
  if ('IntersectionObserver' in window) {
    const animObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-slide-up');
          animObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      animObserver.observe(el);
    });
  }

  // --- Smooth Anchor Scroll ---
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // --- Chart.js Global Defaults ---
  if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#9CA3AF';
    Chart.defaults.font.family = 'Inter, sans-serif';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
  }

  // --- Copy to Clipboard ---
  document.querySelectorAll('[data-copy]').forEach(el => {
    el.addEventListener('click', function() {
      const text = this.getAttribute('data-copy');
      navigator.clipboard.writeText(text).then(() => {
        const original = this.innerHTML;
        this.innerHTML = 'Copied!';
        setTimeout(() => { this.innerHTML = original; }, 1500);
      });
    });
  });

  console.log('Aura Career UI v2.0 loaded');
});
