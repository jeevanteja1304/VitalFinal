document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Get the value from the new 'fullname' input field
    const fullname = document.getElementById('fullname').value; 
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('error-message');

    // Make sure all fields are filled (simple validation)
    if (!fullname || !username || !password) {
        errorMessage.textContent = 'Please fill out all fields.';
        return;
    }

    const response = await fetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Add the 'fullname' to the body of the request
        body: JSON.stringify({ fullname, username, password })
    });
    
    const data = await response.json();

    if (response.ok) {
        // Redirect to login page after successful signup
        window.location.href = '/login';
    } else {
        errorMessage.textContent = data.error || 'Signup failed.';
    }
});