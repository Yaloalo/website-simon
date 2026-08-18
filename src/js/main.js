document.documentElement.classList.add('has-js');

const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('[data-nav]');

if (navToggle && nav) {
  navToggle.hidden = false;

  const setMenuState = (open) => {
    navToggle.setAttribute('aria-expanded', String(open));
    nav.setAttribute('data-open', String(open));
  };

  setMenuState(false);

  navToggle.addEventListener('click', () => {
    const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
    setMenuState(!isOpen);
  });

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setMenuState(false));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      setMenuState(false);
    }
  });
}

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const revealItems = document.querySelectorAll('[data-reveal]');

if (revealItems.length > 0) {
  if (!reducedMotion && 'IntersectionObserver' in window) {
    document.documentElement.classList.add('reveal-enabled');

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.15,
        rootMargin: '0px 0px -10% 0px'
      }
    );

    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }
}
