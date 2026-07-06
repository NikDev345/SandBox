# Settings CSS - Quick Reference Guide

## File Structure Overview

```
settings.css (1,120 lines)
├── Header & License
│
├── SETTINGS LAYOUT (35 lines)
│   ├── .settings-view
│   ├── .settings-view-header
│   ├── .settings-view-title
│   ├── .settings-view-subtitle
│   └── .settings-page
│
├── SETTINGS NAVIGATION (150 lines)
│   ├── .settings-nav
│   ├── .settings-nav-header
│   ├── .settings-nav-title
│   ├── .settings-nav-list
│   ├── .settings-nav-link
│   ├── .settings-nav-link:hover
│   ├── .settings-nav-link.active
│   ├── .settings-nav-link--danger
│   └── .s-nav-icon
│
├── SETTINGS CONTENT (30 lines)
│   ├── .settings-content
│   ├── .settings-section
│   ├── .settings-heading
│   ├── .settings-description
│
├── SETTINGS CARDS (40 lines)
│   ├── .settings-card
│   ├── .settings-card--danger
│   ├── .settings-card--warning
│   └── .settings-card-heading
│
├── AVATAR SECTION (70 lines)
│   ├── .settings-avatar-row
│   ├── .settings-avatar
│   ├── .settings-avatar-img
│   ├── .settings-avatar-edit
│   ├── .settings-avatar-meta
│   ├── .settings-avatar-name
│   └── .settings-avatar-email
│
├── FORM ROWS & GROUPS (40 lines)
│   ├── .form-row
│   ├── .form-actions
│   ├── .form-static-value
│   └── .provider-badge
│
├── UNSAVED INDICATOR (20 lines)
│   ├── .unsaved-indicator
│   └── .unsaved-dot
│
├── BUTTON LOADING STATE (15 lines)
│   ├── .btn-spinner
│   └── .btn.loading
│
├── TOGGLE SWITCH (50 lines)
│   ├── .toggle-switch
│   ├── .toggle-input
│   ├── .toggle-track
│   ├── .toggle-thumb
│   └── Various :checked states
│
├── PREFERENCES ROW (35 lines)
│   ├── .preference-row
│   ├── .preference-info
│   ├── .preference-label
│   └── .preference-description
│
├── THEME SELECTOR (60 lines)
│   ├── .theme-selector
│   ├── .theme-option
│   ├── .theme-radio
│   ├── .theme-card
│   ├── .theme-preview
│   ├── .theme-preview--dark
│   ├── .theme-preview--light
│   ├── .theme-preview--system
│   └── .theme-label
│
├── ACCENT SELECTOR (50 lines)
│   ├── .accent-selector
│   ├── .accent-option
│   ├── .accent-radio
│   ├── .accent-swatch
│   └── .accent-swatch--[color]
│
├── PASSWORD STRENGTH METER (60 lines)
│   ├── .password-strength-meter
│   ├── .strength-bar
│   ├── .strength-bar.strength-*
│   ├── .password-requirements
│   ├── .requirements-list
│   └── .requirement-item
│
├── SESSIONS & ACCOUNTS (80 lines)
│   ├── .current-session
│   ├── .session-badge--current
│   ├── .session-details
│   ├── .connected-account-row
│   ├── .account-info
│   ├── .account-icon
│   ├── .account-name
│   └── .account-status--*
│
├── SESSIONS TABLE (40 lines)
│   ├── .sessions-table-wrapper
│   ├── .sessions-table
│   ├── .sessions-table th
│   ├── .sessions-table td
│   └── .skeleton-row
│
├── ABOUT & DANGER ZONE (60 lines)
│   ├── .about-list
│   ├── .about-row
│   ├── .about-term
│   ├── .about-definition
│   ├── .danger-card-content
│   ├── .danger-card-copy
│   ├── .danger-card-title
│   └── .danger-card-desc
│
├── SECURITY METHOD (50 lines)
│   ├── .security-method-row
│   ├── .security-method-info
│   ├── .security-method-icon
│   ├── .security-method-label
│   ├── .security-method-desc
│   └── .security-status--active
│
├── RESPONSIVE DESIGN (180 lines)
│   ├── @media (max-width: 1100px)
│   ├── @media (max-width: 768px)
│   └── @media (max-width: 480px)
│
└── UTILITY ANIMATIONS (20 lines)
    ├── @keyframes fadeUp
    ├── @keyframes pulse
    ├── @keyframes shimmer
    └── @keyframes spin
```

---

## Common Patterns & Usage

### Creating a Settings Section

```html
<section class="settings-section active" data-section="profile">
  <div class="settings-section-header">
    <h2 class="settings-heading">Profile</h2>
    <p class="settings-description">Update your personal information.</p>
  </div>

  <div class="settings-card">
    <p class="settings-card-heading">Basic Information</p>
    <p class="settings-card-subtext">Your public profile details.</p>
    
    <!-- Form content here -->
    <form>
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input class="form-input" type="text">
      </div>
    </form>
  </div>
</section>
```

### Creating a Card with Content

```html
<div class="settings-card">
  <p class="settings-card-heading">Security</p>
  <p class="settings-card-subtext">Manage your security settings.</p>
  
  <!-- Content goes here -->
</div>
```

### Creating a Preference Row

```html
<div class="preference-row">
  <div class="preference-info">
    <p class="preference-label">Dark Mode</p>
    <p class="preference-description">Use dark theme automatically</p>
  </div>
  <label class="toggle-switch">
    <input class="toggle-input" type="checkbox">
    <span class="toggle-track">
      <span class="toggle-thumb"></span>
    </span>
  </label>
</div>
```

### Creating a Form Row (2 Columns)

```html
<div class="form-row">
  <div class="form-group">
    <label class="form-label">Email</label>
    <input class="form-input" type="email">
  </div>
  <div class="form-group">
    <label class="form-label">Phone</label>
    <input class="form-input" type="tel">
  </div>
</div>
```

### Using Theme Selector

```html
<div class="theme-selector">
  <label class="theme-option">
    <input type="radio" name="theme" value="dark" class="theme-radio">
    <div class="theme-card">
      <div class="theme-preview theme-preview--dark"></div>
      <p class="theme-label">Dark</p>
    </div>
  </label>
  <!-- More theme options -->
</div>
```

### Using Accent Color Swatches

```html
<div class="accent-selector">
  <label class="accent-option">
    <input type="radio" name="accent" value="blue" class="accent-radio">
    <span class="accent-swatch accent-swatch--blue"></span>
  </label>
  <!-- More accent options -->
</div>
```

### Password Strength Indicator

```html
<div class="form-group">
  <label class="form-label">New Password</label>
  <input class="form-input" type="password" id="newPassword">
  
  <div class="password-strength-meter">
    <div class="strength-bar strength-weak" id="strengthBar"></div>
  </div>
  
  <div class="password-requirements">
    <p class="password-requirements-label">Requirements:</p>
    <ul class="requirements-list">
      <li class="requirement-item" data-requirement="length">8+ characters</li>
      <li class="requirement-item" data-requirement="uppercase">One uppercase letter</li>
      <li class="requirement-item" data-requirement="lowercase">One lowercase letter</li>
      <li class="requirement-item" data-requirement="number">One number</li>
      <li class="requirement-item" data-requirement="special">One special character</li>
    </ul>
  </div>
</div>
```

### Sessions Table

```html
<div class="sessions-table-wrapper">
  <table class="sessions-table">
    <thead>
      <tr>
        <th>Device</th>
        <th>Browser</th>
        <th>Location</th>
        <th>Activity</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Windows Desktop</td>
        <td>Chrome 123</td>
        <td>San Francisco, US</td>
        <td>Now</td>
        <td>
          <button class="btn btn-ghost btn-sm">Sign Out</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### Connected Accounts

```html
<div class="connected-account-row">
  <div class="account-info">
    <div class="account-icon">
      <svg><!-- Google icon --></svg>
    </div>
    <div class="account-details">
      <p class="account-name">Google</p>
      <p class="account-status--connected">Connected</p>
    </div>
  </div>
  <button class="btn btn-ghost btn-sm">Disconnect</button>
</div>
```

### Danger Zone Card

```html
<div class="settings-card settings-card--danger">
  <div class="danger-card-content">
    <div class="danger-card-copy">
      <p class="danger-card-title">Delete Account</p>
      <p class="danger-card-desc">Permanently delete your account and all data.</p>
    </div>
    <button class="btn btn-danger">Delete</button>
  </div>
</div>
```

### About Section

```html
<div class="about-list">
  <div class="about-row">
    <dt class="about-term">Version</dt>
    <dd class="about-definition">1.0.0</dd>
  </div>
  <div class="about-row">
    <dt class="about-term">Last Updated</dt>
    <dd class="about-definition">December 15, 2024</dd>
  </div>
</div>
```

---

## CSS Variables Reference

### Colors
```css
--ink-0:    #ffffff
--ink-1:    #f4f4f5
--ink-2:    #a1a1aa
--ink-3:    #71717a
--ink-4:    #3f3f46
--ink-5:    #27272a
--ink-6:    #18181b
--ink-7:    #0f0f10
--ink-8:    #09090b

--surface-0: rgba(255,255,255,0.03)
--surface-1: rgba(255,255,255,0.055)
--surface-2: rgba(255,255,255,0.08)
--surface-3: rgba(255,255,255,0.12)

--border-0: rgba(255,255,255,0.06)
--border-1: rgba(255,255,255,0.10)
--border-2: rgba(255,255,255,0.16)

--text:        var(--ink-0)
--text-soft:   var(--ink-2)
--text-muted:  var(--ink-3)

--accent:  #e4e4e7
--success: #22c55e
--error:   #ef4444
--warning: #f59e0b
```

### Typography
```css
--text-xs:   11px
--text-sm:   13px
--text-base: 15px
--text-md:   17px
--text-lg:   20px
--text-xl:   24px
--text-2xl:  32px

--weight-normal: 400
--weight-medium: 500
--weight-semi:   600
--weight-bold:   700
```

### Spacing
```css
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

### Radius
```css
--radius-sm:  8px
--radius-md:  12px
--radius-lg:  16px
--radius-xl:  20px
--radius-2xl: 28px
--radius-pill: 999px
```

### Shadows
```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)
--shadow-md: 0 4px 16px rgba(0,0,0,0.5), 0 2px 6px rgba(0,0,0,0.3)
--shadow-lg: 0 16px 48px rgba(0,0,0,0.6), 0 6px 20px rgba(0,0,0,0.4)
--shadow-xl: 0 32px 80px rgba(0,0,0,0.7), 0 12px 32px rgba(0,0,0,0.5)
```

### Motion
```css
--ease:       cubic-bezier(0.22, 1, 0.36, 1)
--ease-in:    cubic-bezier(0.4, 0, 1, 1)
--ease-out:   cubic-bezier(0, 0, 0.2, 1)
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1)

--dur-fast:  120ms
--dur-base:  200ms
--dur-slow:  320ms
--dur-enter: 500ms
```

### Layout
```css
--sidebar-w: 240px
--topbar-h:  64px
```

---

## Integration Checklist

When adding Settings to Dashboard, ensure:

- [ ] Settings HTML wraps with `.settings-view` class
- [ ] Settings imported after dashboard.css in HTML
- [ ] All form elements use dashboard `.form-*` classes
- [ ] All buttons use dashboard `.btn*` classes
- [ ] Modal dialogs use dashboard `.modal-*` classes
- [ ] Navigation uses `.settings-nav-*` classes
- [ ] Cards use `.settings-card` class
- [ ] Responsive breakpoints tested (1100px, 768px, 480px)
- [ ] Dark/light theme switching works
- [ ] Animations are smooth (no flashing)
- [ ] Touch targets are 44px+ on mobile
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Accessibility features work (focus-visible, labels)

---

## Common Issues & Solutions

### Issue: Styles not applying
**Solution**: Ensure CSS import order: tokens.css → animations.css → dashboard.css → settings.css

### Issue: Colors looking different
**Solution**: Use CSS variables, not hardcoded colors. Check tokens.css values.

### Issue: Spacing feels off
**Solution**: Use `--space-*` variables. Don't mix with hardcoded px values.

### Issue: Animations too fast/slow
**Solution**: Adjust `--dur-*` values or timing functions. Keep professional (200-500ms).

### Issue: Mobile layout broken
**Solution**: Check responsive media queries. Test at actual breakpoints (768px, 480px).

### Issue: Cards not hovering properly
**Solution**: Ensure `.settings-card:hover` isn't being overridden. Check CSS specificity.

---

## Performance Tips

1. **Minimize CSS changes** - Edit tokens.css instead of settings.css
2. **Use variables** - CSS variables are efficient and maintainable
3. **Avoid deep nesting** - Keep CSS specificity low
4. **Reuse dashboard styles** - Don't duplicate button/form CSS
5. **Test file size** - Keep settings.css under 1,500 lines
6. **Use critical CSS** - Load settings.css only on settings page

---

## Future Enhancements

- [ ] Dark theme optimization (use dark color scale)
- [ ] High contrast mode support
- [ ] Print styles for preferences export
- [ ] Animation preferences (prefers-reduced-motion)
- [ ] Custom properties for theme customization
- [ ] CSS Grid subgrid for complex layouts
- [ ] Container queries for responsive components

---

**Last Updated**: 2026-06-28
**Status**: ✅ Production Ready
**Maintainer**: Frontend Team
