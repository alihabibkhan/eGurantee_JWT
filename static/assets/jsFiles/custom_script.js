$(document).on('submit', 'form.form-show-processing', function (e) {
    // Find the submit button within the form
    const $form = $(this);
    const $button = $form.find('button[type="submit"], input[type="submit"]');

    // Exit if no submit button is found
    if (!$button.length) {
        return;
    }

    // Exit if the button is already processing
    if ($button.hasClass('processing')) {
        e.preventDefault(); // Prevent form resubmission
        return;
    }

    // Store original state
    const originalHtml = $button.html();
    const originalDisabled = $button.prop('disabled');
    const processingText = $button.data('processing-text') || 'Processing...';

    // Update button to processing state
    $button
        .addClass('processing')
        .prop('disabled', true)
        .data('original-html', originalHtml)
        .data('original-disabled', originalDisabled)
        .html(`${processingText} <i class="fas fa-spinner fa-spin ms-2"></i>`);

    // Optional: Allow form submission to proceed
    // If you need to prevent submission (e.g., for AJAX), add:
    // e.preventDefault();
    // Then handle submission manually (e.g., via $.ajax)
});

function logout() {
    const token = localStorage.getItem('access_token');

    // Call backend first while token still exists
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token || ''}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Logout response:', data);
    })
    .catch(err => console.warn('Logout API failed:', err))
    .finally(() => {
        // Clear storage AFTER backend call
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_rights');
        window.location.href = '/login';
    });
}


// Intercept all fetch calls to add token automatically
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    options.headers = options.headers || {};
    if (token && !url.includes('/login')) {  // skip login page
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return originalFetch(url, options);
};