// static/js/loading_modal.js
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('game-form');
    const loadingModal = document.getElementById('loading-modal');

    if (form && loadingModal) {
        form.addEventListener('submit', function() {
            loadingModal.style.display = 'block';
        });
    }
});
