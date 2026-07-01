class SettingsManager {
  constructor() {
    this.currentSection = 'profile';
    this.formsDirty = new Map();
    this.init();
  }

  init() {
    this.cacheElements();
    this.attachEventListeners();
    this.loadSettings();
    this.setupNavigationVisibility();
  }

  cacheElements() {
    this.navLinks = document.querySelectorAll('.settings-nav-link');
    this.sections = document.querySelectorAll('.settings-section');
    this.forms = document.querySelectorAll('.settings-form');
    this.toggles = document.querySelectorAll('.toggle-input');
    this.themeRadios = document.querySelectorAll('input[name="theme"]');
    this.accentRadios = document.querySelectorAll('input[name="accent"]');
    this.passwordInput = document.getElementById('new-password');
    this.strengthBar = document.getElementById('strength-bar');
    this.requirementItems = document.querySelectorAll('.requirement-item');
  }

  attachEventListeners() {
    this.navLinks.forEach(link => {
      link.addEventListener('click', (e) => this.handleNavClick(e));
    });

    this.forms.forEach(form => {
      form.addEventListener('submit', (e) => this.handleFormSubmit(e));
      form.addEventListener('reset', (e) => this.handleFormReset(e));
      form.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('change', () => this.markFormDirty(form));
        input.addEventListener('input', () => this.markFormDirty(form));
      });
    });

    this.toggles.forEach(toggle => {
      toggle.addEventListener('change', (e) => this.handleToggleChange(e));
    });

    this.themeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => this.handleThemeChange(e));
    });

    this.accentRadios.forEach(radio => {
      radio.addEventListener('change', (e) => this.handleAccentChange(e));
    });

    if (this.passwordInput) {
      this.passwordInput.addEventListener('input', (e) => this.updatePasswordStrength(e));
    }

    document.querySelectorAll('.settings-avatar-edit input').forEach(input => {
      input.addEventListener('change', (e) => this.handleAvatarUpload(e));
    });

    document.querySelectorAll('[data-settings-section]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const section = link.getAttribute('data-settings-section');
        this.switchSection(section);
      });
    });
  }

  setupNavigationVisibility() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const sectionId = entry.target.getAttribute('data-settings-section');
          this.updateActiveNav(sectionId);
        }
      });
    }, { threshold: 0.5 });

    this.sections.forEach(section => observer.observe(section));
  }

  handleNavClick(e) {
    e.preventDefault();
    const section = e.currentTarget.getAttribute('data-settings-section');
    this.switchSection(section);
  }

  switchSection(sectionId) {
    this.navLinks.forEach(link => {
      const isActive = link.getAttribute('data-settings-section') === sectionId;
      link.classList.toggle('active', isActive);
    });

    this.sections.forEach(section => {
      const isActive = section.getAttribute('data-settings-section') === sectionId;
      section.classList.toggle('active', isActive);
    });

    this.currentSection = sectionId;
    window.history.pushState(null, '', `#settings-${sectionId}`);
  }

  updateActiveNav(sectionId) {
    this.navLinks.forEach(link => {
      const isActive = link.getAttribute('data-settings-section') === sectionId;
      link.classList.toggle('active', isActive);
    });
  }

  markFormDirty(form) {
    this.formsDirty.set(form, true);
    this.showUnsavedIndicator();
  }

  handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    
    this.showLoadingState(form);
    
    setTimeout(() => {
      this.hideLoadingState(form);
      this.formsDirty.delete(form);
      this.hideUnsavedIndicator();
      this.showToast('Changes saved successfully', 'success');
    }, 800);
  }

  handleFormReset(e) {
    const form = e.target;
    this.formsDirty.delete(form);
    if (Array.from(this.formsDirty.values()).every(v => !v)) {
      this.hideUnsavedIndicator();
    }
  }

  handleToggleChange(e) {
    const isChecked = e.target.checked;
    const label = e.target.closest('.preference-row')?.querySelector('.preference-label')?.textContent || 'Setting';
    
    this.showToast(`${label} ${isChecked ? 'enabled' : 'disabled'}`, 'info');
  }

  handleThemeChange(e) {
    const theme = e.target.value;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('settings-theme', theme);
    this.showToast(`Theme set to ${theme}`, 'success');
  }

  handleAccentChange(e) {
    const accent = e.target.value;
    document.documentElement.setAttribute('data-accent', accent);
    localStorage.setItem('settings-accent', accent);
    this.showToast(`Accent color updated`, 'success');
  }

  updatePasswordStrength(e) {
    const password = e.target.value;
    const strength = this.calculatePasswordStrength(password);
    
    this.strengthBar.className = 'strength-bar';
    this.strengthBar.classList.add(`strength-${strength.level}`);
    
    this.requirementItems.forEach(item => {
      const requirement = item.getAttribute('data-requirement');
      const isMet = strength.requirements[requirement];
      item.classList.toggle('met', isMet);
    });
  }

  calculatePasswordStrength(password) {
    const requirements = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    };

    const metCount = Object.values(requirements).filter(Boolean).length;
    let level = 'weak';
    if (metCount >= 4) level = 'strong';
    else if (metCount >= 2) level = 'medium';

    return { level, requirements };
  }

  handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = e.target.closest('.settings-avatar').querySelector('img');
      img.src = event.target.result;
      this.showToast('Avatar updated', 'success');
    };
    reader.readAsDataURL(file);
  }

  showLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
    }
  }

  hideLoadingState(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.classList.remove('loading');
      submitBtn.disabled = false;
    }
  }

  showUnsavedIndicator() {
    const indicator = document.querySelector('.unsaved-indicator');
    if (indicator) {
      indicator.classList.add('active');
    }
  }

  hideUnsavedIndicator() {
    const indicator = document.querySelector('.unsaved-indicator');
    if (indicator) {
      indicator.classList.remove('active');
    }
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      background: var(--${type === 'error' ? 'error' : type === 'success' ? 'success' : 'accent'});
      color: var(--ink-8);
      padding: var(--space-4) var(--space-6);
      border-radius: var(--radius-md);
      margin: var(--space-2);
      animation: slideInRight var(--dur-base) var(--ease) both;
    `;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  loadSettings() {
    const savedTheme = localStorage.getItem('settings-theme') || 'system';
    const savedAccent = localStorage.getItem('settings-accent') || 'blue';

    const themeRadio = document.querySelector(`input[name="theme"][value="${savedTheme}"]`);
    if (themeRadio) themeRadio.checked = true;

    const accentRadio = document.querySelector(`input[name="accent"][value="${savedAccent}"]`);
    if (accentRadio) accentRadio.checked = true;

    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.setAttribute('data-accent', savedAccent);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new SettingsManager();
});