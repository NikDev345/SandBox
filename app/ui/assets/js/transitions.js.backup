document.addEventListener('click', e => {
    const link = e.target.closest('a[href]');
    if (
        !link ||
        link.dataset.nativeLink !== undefined ||
        link.target === '_blank' ||
        link.href.startsWith('mailto')
    ) return;

    const url = link.getAttribute('href');

    // Skip hash links and external links
    if (!url || url.startsWith('#') || url.startsWith('http') && !url.startsWith(location.origin)) return;

    e.preventDefault();
    document.documentElement.classList.add('leaving');

    setTimeout(() => {
        window.location.href = url;
    }, 120); // matches transition duration
});