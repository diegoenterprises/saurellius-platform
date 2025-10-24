// Page Navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show the requested page
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
        window.scrollTo(0, 0);
    }
}

// Plan Selection
let selectedPlan = null;

function selectPlan(plan) {
    selectedPlan = plan;
    localStorage.setItem('selectedPlan', plan);
    showPage('register');
}

// Authentication
function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // Call the backend API
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access_token) {
            // Store the token
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Show success message
            alert('Login successful! Welcome back.');
            
            // Redirect to dashboard
            showPage('dashboard');
        } else {
            alert('Login failed: ' + (data.message || 'Invalid credentials'));
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    });
}

function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const phone = document.getElementById('register-phone').value;
    const password = document.getElementById('register-password').value;

    // Get selected plan from localStorage
    const plan = localStorage.getItem('selectedPlan') || 'starter';

    // Call the backend API
    fetch('/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            name, 
            email, 
            phone, 
            password,
            subscription_tier: plan
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access_token) {
            // Store the token
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Show success message
            alert('Registration successful! Welcome to Saurellius. You received 500 bonus points!');
            
            // Clear selected plan
            localStorage.removeItem('selectedPlan');
            
            // Redirect to dashboard
            showPage('dashboard');
        } else {
            alert('Registration failed: ' + (data.message || 'Please try again'));
        }
    })
    .catch(error => {
        console.error('Registration error:', error);
        alert('Registration failed. Please try again.');
    });
}

function logout() {
    // Clear stored data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('selectedPlan');
    
    // Show success message
    alert('You have been logged out successfully.');
    
    // Redirect to landing page
    showPage('landing');
}

// Check if user is already logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    
    if (token) {
        // User is logged in, show dashboard
        showPage('dashboard');
    } else {
        // User is not logged in, show landing page
        showPage('landing');
    }
});

// API Helper Functions
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Dashboard Data Loading
function loadDashboardData() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        showPage('landing');
        return;
    }

    // Load user dashboard data
    fetch('/api/dashboard/summary', {
        headers: getAuthHeaders()
    })
    .then(response => response.json())
    .then(data => {
        // Update dashboard with user data
        console.log('Dashboard data:', data);
    })
    .catch(error => {
        console.error('Error loading dashboard:', error);
    });
}

