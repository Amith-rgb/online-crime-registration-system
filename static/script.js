// subtle fade-in for main regions and basic tooltip wiring
document.addEventListener('DOMContentLoaded', () => {
    // Apply fade-in for cards and hero
    document.querySelectorAll('.card, .hero-panel, .stats-container, .neon-table').forEach(el=>{
        el.classList.add('fade-up');
    });

    // Theme toggle: persist in localStorage
    const toggle = document.getElementById('themeToggle');
    function applyTheme(theme){
        if(theme === 'dark') document.documentElement.classList.add('theme-dark');
        else document.documentElement.classList.remove('theme-dark');
        if(toggle) toggle.setAttribute('aria-pressed', theme === 'dark');
    }
    const stored = localStorage.getItem('site-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(stored);
    if(toggle){
        toggle.addEventListener('click', ()=> {
            const current = document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem('site-theme', next);
            applyTheme(next);
        });
    }
    // Basic tooltip hookup (progressive enhancement)
    document.querySelectorAll('[data-tooltip]').forEach(el=>{
        el.addEventListener('mouseenter', ()=> el.setAttribute('title', el.dataset.tooltip||''));
    });

    // Multi-step form logic for #reportForm
    (function registerStepper(){
        const form = document.getElementById('reportForm');
        if (!form) return;
        const panels = Array.from(form.querySelectorAll('.step-panel'));
        const steps = Array.from(document.querySelectorAll('.form-stepper .step'));
        let current = 1;

        function showStep(n){
            panels.forEach(p => p.hidden = String(p.dataset.step) !== String(n));
            steps.forEach(s => {
                if (Number(s.dataset.step) === Number(n)) s.classList.add('active');
                else s.classList.remove('active');
            });
            current = Number(n);
            // focus first input in panel
            const first = form.querySelector(`.step-panel[data-step="${n}"] .neon-input, .step-panel[data-step="${n}"] input, .step-panel[data-step="${n}"] textarea, .step-panel[data-step="${n}"] select`);
            if(first) first.focus();
            // update review if on final
            if (Number(n) === 3) populateReview();
        }

        function validateStep(n){
            const panel = form.querySelector(`.step-panel[data-step="${n}"]`);
            if(!panel) return true;
            const requireds = Array.from(panel.querySelectorAll('[required]'));
            for(const el of requireds){
                if(!el.value || String(el.value).trim() === ''){
                    el.focus();
                    el.classList.add('input-error');
                    return false;
                } else {
                    el.classList.remove('input-error');
                }
            }
            return true;
        }

        function populateReview(){
            const type = document.getElementById('crime_type').value || '(not provided)';
            const desc = document.getElementById('description').value || '(not provided)';
            const loc = document.getElementById('location').value || '(not provided)';
            const add = document.getElementById('additional') ? document.getElementById('additional').value : '';
            document.getElementById('review-type').textContent = type;
            document.getElementById('review-description').textContent = desc;
            document.getElementById('review-location').textContent = loc;
            document.getElementById('review-additional').textContent = add || '(none)';
        }

        // wire next/back buttons (delegation)
        form.addEventListener('click', (ev)=>{
            const btn = ev.target.closest('button[data-action]');
            if(!btn) return;
            const action = btn.getAttribute('data-action');
            if(action === 'next'){
                if (!validateStep(current)) return;
                showStep(current + 1);
            } else if(action === 'back'){
                showStep(Math.max(1, current - 1));
            }
        });

        // intercept form submit only to allow final validation (otherwise let POST proceed)
        form.addEventListener('submit', (ev)=>{
            if(!validateStep(current)){
                ev.preventDefault();
                return;
            }
            // Ensure final step's required fields validated (location etc.)
            if(current !== 3){
                ev.preventDefault();
                showStep(3);
                return;
            }
            // allow normal submit to server
        });

        // initialize
        showStep(1);
    })();

    // Image preview for attachment in report form
    const attachment = document.getElementById('attachment');
    const previewWrap = document.getElementById('attachment-preview');
    const previewImg = document.getElementById('attachment-img');
    if (attachment && previewWrap && previewImg) {
        attachment.addEventListener('change', (e) => {
            const f = e.target.files && e.target.files[0];
            if (!f) { previewWrap.style.display = 'none'; previewImg.src = ''; return; }
            const url = URL.createObjectURL(f);
            previewImg.src = url;
            previewWrap.style.display = 'block';
        });
    }

    // Geolocation fill
    const useLoc = document.getElementById('use-location');
    if (useLoc) {
        useLoc.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('Geolocation not supported by your browser.');
                return;
            }
            useLoc.textContent = 'Detecting…';
            navigator.geolocation.getCurrentPosition((pos) => {
                const lat = pos.coords.latitude.toFixed(6);
                const lon = pos.coords.longitude.toFixed(6);
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lon;
                // optionally reverse-geocode later; fill location text with coords
                const locField = document.getElementById('location');
                if (locField && (!locField.value || locField.value.trim() === '')) {
                    locField.value = `${lat}, ${lon}`;
                }
                useLoc.textContent = 'Use my location';
            }, (err) => {
                alert('Unable to get location: ' + err.message);
                useLoc.textContent = 'Use my location';
            }, { timeout: 10000 });
        });
    }

    // Animated transitions between step panels (slide)
    function animatePanelHide(panel, dir='left') {
        panel.style.transition = 'transform 300ms ease, opacity 200ms ease';
        panel.style.opacity = '1';
        panel.style.transform = dir === 'left' ? 'translateX(-20px)' : 'translateX(20px)';
        panel.style.opacity = '0';
        setTimeout(()=> { panel.hidden = true; panel.style.transform=''; panel.style.opacity=''; panel.style.transition=''; }, 300);
    }
    function animatePanelShow(panel, dir='right') {
        panel.hidden = false;
        panel.style.opacity = '0';
        panel.style.transform = dir === 'right' ? 'translateX(20px)' : 'translateX(-20px)';
        panel.style.transition = 'transform 300ms ease, opacity 200ms ease';
        requestAnimationFrame(()=> {
            panel.style.transform = 'translateX(0)';
            panel.style.opacity = '1';
        });
        setTimeout(()=> { panel.style.transition=''; }, 300);
    }

    // Enhance showStep to use animations if available
    const originalShowStep = window.showStep;
    // if showStep not global, patch stepper internal function by re-querying panels when next/back clicked
    // Here we attach to the form click handler used earlier: override next/back behavior to animate.
    document.getElementById('reportForm')?.addEventListener('click', (ev) => {
        const btn = ev.target.closest('button[data-action]');
        if(!btn) return;
        const action = btn.getAttribute('data-action');
        const form = document.getElementById('reportForm');
        const panels = Array.from(form.querySelectorAll('.step-panel'));
        const currentPanel = panels.find(p => !p.hidden);
        const currentStep = Number(currentPanel.dataset.step);
        let target = currentStep;
        if (action === 'next') target = currentStep + 1;
        if (action === 'back') target = currentStep - 1;
        if (target === currentStep) return;
        // validate if moving forward
        if (action === 'next') {
            // simple required validation
            const requireds = Array.from(currentPanel.querySelectorAll('[required]'));
            for(const el of requireds){
                if(!el.value || String(el.value).trim() === ''){
                    el.focus();
                    el.classList.add('input-error');
                    ev.preventDefault();
                    return;
                } else {
                    el.classList.remove('input-error');
                }
            }
        }
        ev.preventDefault();
        const nextPanel = panels.find(p => Number(p.dataset.step) === target);
        if(!nextPanel) return;
        // animate
        animatePanelHide(currentPanel, 'left');
        animatePanelShow(nextPanel, 'right');
        // update step indicators
        document.querySelectorAll('.form-stepper .step').forEach(s => s.classList.toggle('active', Number(s.dataset.step) === target));
        // if review step show review content
        if (target === 3) {
            const populateReview = window.populateReview || function(){};
            populateReview();
        }
    });

});