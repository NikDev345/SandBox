class SettingsManager {
  constructor() {
    this.currentSection = 'profile';
    this.formsDirty = new Map();
    this.API_BASE_URL = "";
    this.init();
  }

  init() {
    this.cacheElements();
    this.attachEventListeners();
    this.loadProfile(); 
    this.loadSettings();
    this.setupNavigationVisibility();
  }

  cacheElements() {
    this.navLinks = document.querySelectorAll('.settings-nav-link');
    this.sections = document.querySelectorAll('.settings-section');
    this.profileForm = document.getElementById("profileForm");

    this.toggles = document.querySelectorAll('.toggle-input');
    this.themeRadios = document.querySelectorAll('input[name="theme"]');
    this.accentRadios = document.querySelectorAll('input[name="accent"]');
    this.passwordInput = document.getElementById('new-password');
    this.strengthBar = document.getElementById('strength-bar');
    this.requirementItems = document.querySelectorAll('.requirement-item');
    this.passwordEmail = document.getElementById("passwordEmail");
    this.sendOtpBtn = document.getElementById("sendPasswordOtpBtn");
    this.verifyOtpBtn = document.getElementById("verifyPasswordOtpBtn");
    this.changePasswordBtn = document.getElementById("changePasswordBtn");
    this.emailStep = document.getElementById("password-email-step");
    this.otpStep = document.getElementById("password-otp-step");
    this.passwordStep = document.getElementById("password-change-step");
    this.deleteAccountBtn = document.getElementById("deleteAccountBtn");
    this.deleteModal = document.getElementById("deleteModal");
    this.deleteExpectedText = document.getElementById("deleteExpectedText");
    this.deleteConfirmationInput = document.getElementById("deleteConfirmationInput");
    this.confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    this.cancelDeleteBtn = document.getElementById("cancelDeleteBtn");
  }

  attachEventListeners() {
    const btn = document.getElementById("profileSaveBtn");

    btn.addEventListener("click", (e) => {
        console.log("BUTTON CLICKED");

        console.log(document.getElementById("profileForm").checkValidity());

        document.getElementById("profileForm").requestSubmit();
    });

    if (this.sendOtpBtn) {
        this.sendOtpBtn.addEventListener("click", () => {
            this.sendPasswordOTP();
        });
    }
    if (this.verifyOtpBtn) {
        this.verifyOtpBtn.addEventListener("click", () => {
            this.verifyPasswordOTP();
        });
    }
    if (this.changePasswordBtn) {
        this.changePasswordBtn.addEventListener("click", () => {
            this.changePassword();
        });
    }

    if (this.profileForm) {

    console.log("Profile listener attached");
    // Delete account
    this.deleteAccountBtn?.addEventListener(
        "click",
        () => this.openDeleteModal()
    );

    this.cancelDeleteBtn?.addEventListener(
        "click",
        () => this.closeDeleteModal()
    );

    this.deleteConfirmationInput?.addEventListener(
        "input",
        () => {

            this.confirmDeleteBtn.disabled =
                this.deleteConfirmationInput.value.trim() !==
                this.deleteExpectedText.textContent.trim();

        }
    );

    this.confirmDeleteBtn?.addEventListener(
        "click",
        () => this.deleteAccount()
    );

    this.profileForm.addEventListener("submit", (e) => {
        console.log("PROFILE SUBMIT");
        this.handleFormSubmit(e);
    });

    this.profileForm.addEventListener("reset", (e) =>
        this.handleFormReset(e)
    );

    this.profileForm
        .querySelectorAll("input, textarea")
        .forEach(input => {

            input.addEventListener("input", () =>
                this.markFormDirty(this.profileForm)
            );

        });
    }
    this.navLinks.forEach(link => {
      link.addEventListener('click', (e) => this.handleNavClick(e));
    });

    if (this.profileForm) {

    this.profileForm.addEventListener("reset", (e) =>
        this.handleFormReset(e)
    );

    this.profileForm
        .querySelectorAll("input, textarea, select")
        .forEach(input => {

            input.addEventListener("change", () =>
                this.markFormDirty(this.profileForm)
            );

            input.addEventListener("input", () =>
                this.markFormDirty(this.profileForm)
            );

        });
  }
  const otpBoxes = document.querySelectorAll(".password-otp-box");

  otpBoxes.forEach((box, index) => {

      box.addEventListener("input", () => {

          box.value = box.value.replace(/\D/g, "");

          if (box.value && index < otpBoxes.length - 1) {
              otpBoxes[index + 1].focus();
          }

      });

      box.addEventListener("keydown", (e) => {

          if (
              e.key === "Backspace" &&
              !box.value &&
              index > 0
          ) {
              otpBoxes[index - 1].focus();
          }

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

  async openDeleteModal() {

    try {
        const response = await fetch(
            `${this.API_BASE_URL}/auth/confirm-delete`,
            {
                credentials: "include"
            }
        );
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        this.deleteExpectedText.textContent =
            data.confirmation_text;

        this.deleteConfirmationInput.value = "";

        this.confirmDeleteBtn.disabled = true;

        this.deleteModal.classList.add("open");

    }

    catch (err) {
        this.showToast(err.message, "error");
    }

  }

  closeDeleteModal() {
    this.deleteModal.classList.remove("open");
  }

  async deleteAccount() {

    try {

        this.confirmDeleteBtn.disabled = true;

        const response = await fetch(
            `${this.API_BASE_URL}/auth/account`,
            {
                method: "DELETE",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    confirmation_text:
                        this.deleteConfirmationInput.value
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        localStorage.clear();
        sessionStorage.clear();

        this.showToast(
            data.message,
            "success"
        );

        setTimeout(() => {

            window.location.href = "/login";

        }, 1000);

    }

    catch (err) {

        this.showToast(
            err.message,
            "error"
        );

        this.confirmDeleteBtn.disabled = false;

    }

  }

  async changePassword() {

    const newPassword = document.getElementById("newPassword").value.trim();
    const confirmPassword = document.getElementById("confirmPassword").value.trim();

    if (!newPassword) {
        this.showToast("Please enter a new password.", "error");
        return;
    }

    if (!confirmPassword) {
        this.showToast("Please confirm your password.", "error");
        return;
    }

    if (newPassword !== confirmPassword) {
        this.showToast("Passwords do not match.", "error");
        return;
    }

    try {

        this.changePasswordBtn.disabled = true;
        this.changePasswordBtn.textContent = "Updating...";

        const response = await fetch(
            `${this.API_BASE_URL}/auth/change-password`,
            {
                method: "PUT",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: this.passwordEmail.value,
                    new_password: newPassword,
                    confirm_password: confirmPassword
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Failed to update password."
            );
        }

        this.showToast(
            data.message,
            "success"
        );

        // Reset the UI
        document.getElementById("newPassword").value = "";
        document.getElementById("confirmPassword").value = "";

        document
            .querySelectorAll(".password-otp-box")
            .forEach(box => box.value = "");

        this.passwordStep.hidden = true;
        this.otpStep.hidden = true;
        this.emailStep.hidden = false;

    } catch (err) {

        console.error(err);

        this.showToast(
            err.message,
            "error"
        );

    } finally {

        this.changePasswordBtn.disabled = false;
        this.changePasswordBtn.textContent = "Update Password";

    }

  }

  async verifyPasswordOTP() {

    const otp = [...document.querySelectorAll(".password-otp-box")]
        .map(box => box.value)
        .join("");

    if (otp.length !== 6) {
        this.showToast("Please enter the 6-digit OTP.", "error");
        return;
    }

    try {

        const response = await fetch(
            `${this.API_BASE_URL}/auth/verify-password-otp`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: this.passwordEmail.value,
                    otp: otp
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "OTP verification failed");
        }

        this.showToast(data.message, "success");

        this.otpStep.hidden = true;
        this.passwordStep.hidden = false;

        document.getElementById("newPassword").focus();

    } catch (err) {

        this.showToast(err.message, "error");

        document.querySelectorAll(".password-otp-box")
            .forEach(box => box.value = "");

        document.querySelector(".password-otp-box").focus();

    }

  }

  async sendPasswordOTP() {

    try {
        this.sendOtpBtn.disabled = true;
        this.sendOtpBtn.textContent = "Sending...";
        const response = await fetch(
            `${this.API_BASE_URL}/auth/send-password-otp`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({
                    email: this.passwordEmail.value
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail);
        }

        this.showToast(data.message, "success");

        this.emailStep.hidden = true;
        this.otpStep.hidden = false;
        const firstBox = document.querySelector(".password-otp-box");

        if (firstBox) {
            firstBox.focus();
        }

    } catch (err) {

        this.showToast(err.message, "error");

    }finally {

      this.sendOtpBtn.disabled = false;
      this.sendOtpBtn.textContent = "Send OTP";

    } 
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

  async handleFormSubmit(e) {
    console.log("Profile form submitted");
    e.preventDefault();

    const form = e.target;

    // Only handle the profile form here
    if (form.id !== "profileForm") {
        return;
    }

    this.showLoadingState(form);

    try {
        const payload = {
            name: document.getElementById("profileFullName").value.trim(),
            bio: document.getElementById("profileBio").value.trim()
        };

        const response = await fetch(`${this.API_BASE_URL}/user/profile`, {
            method: "PUT",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (typeof renderProfile === "function") {
            renderProfile(data.user);
        }

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                "Failed to update profile."
            );
        }

        // Update the UI immediately
        document.querySelector(".settings-avatar-name").textContent =
            data.user.name;

        document.getElementById("profileFullName").value =
            data.user.name;

        document.getElementById("profileBio").value =
            data.user.bio || "";

        this.formsDirty.delete(form);
        this.hideUnsavedIndicator();

        this.showToast(
            data.message || "Profile updated successfully",
            "success"
        );

    } catch (err) {

        console.error(err);

        this.showToast(
            err.message || "Failed to update profile.",
            "error"
        );

    } finally {

        this.hideLoadingState(form);

    }
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

  async loadProfile() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/auth/me`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error("Failed to load profile");
      }

      const profile = await response.json();

      // Avatar
      const avatar = document.querySelector(".settings-avatar-img");
      if (avatar) {
        avatar.src =
          profile.avatar ||
          `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.name)}`;

          avatar.onerror = function () {
              this.src = "/assets/default_avatar.png";
          };
      }

      // Top card
      const topName = document.querySelector(".settings-avatar-name");
      if (topName) topName.textContent = profile.name;

      const topEmail = document.querySelector(".settings-avatar-email");
      if (topEmail) topEmail.textContent = profile.email;

      // Form
      const fullName = document.querySelector("#profileFullName")
      if (fullName) fullName.value = profile.name || "";

      const email = document.getElementById("profileEmail");
      if (email) email.value = profile.email || "";

      const bio = document.getElementById("profileBio");
      if (bio) bio.value = profile.bio || "";

      const role = document.getElementById("profileRole");
      if (role) role.value = profile.role || "User";

      // Auth Provider
      const providerField = document.querySelectorAll(".form-static-value")[0];
      if (providerField)
        providerField.innerHTML = profile.provider || "Local";

      // Member Since
      const memberField = document.querySelectorAll(".form-static-value")[1];
      if (memberField && profile.created_at) {
        memberField.textContent = new Date(profile.created_at)
          .toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          });
      }

    } catch (err) {
      console.error("Profile Load Error:", err);
    }
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