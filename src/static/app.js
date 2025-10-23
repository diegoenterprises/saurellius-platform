/**
 * Saurellius Platform - Complete Frontend Application
 * Handles authentication, dashboard, paystub generation, and subscription management
 */

// API Configuration
const API_BASE = '/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// ============================================================================
// AUTHENTICATION FUNCTIONS
// ============================================================================

async function register() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const fullName = document.getElementById('register-name').value;
    const phone = document.getElementById('register-phone').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: fullName, phone })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            showNotification('Registration successful!', 'success');
            navigateTo('dashboard');
        } else {
            showNotification(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            showNotification('Login successful!', 'success');
            navigateTo('dashboard');
        } else {
            showNotification(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    navigateTo('login');
}

// ============================================================================
// DASHBOARD FUNCTIONS
// ============================================================================

async function loadDashboard() {
    if (!authToken) {
        navigateTo('login');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/dashboard/summary`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            renderDashboard(data.summary);
        } else {
            showNotification(data.error || 'Failed to load dashboard', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function renderDashboard(summary) {
    const dashboardContent = document.getElementById('dashboard-content');
    
    const ytdSummary = `
        <div class="summary-cards">
            <div class="card">
                <h3>Total Paystubs</h3>
                <p class="big-number">${summary.total_paystubs}</p>
            </div>
            <div class="card">
                <h3>YTD Gross</h3>
                <p class="big-number">$${summary.ytd_gross.toFixed(2)}</p>
            </div>
            <div class="card">
                <h3>YTD Net</h3>
                <p class="big-number">$${summary.ytd_net.toFixed(2)}</p>
            </div>
            <div class="card">
                <h3>Average Net</h3>
                <p class="big-number">$${summary.average_net.toFixed(2)}</p>
            </div>
        </div>
    `;
    
    const employeeCards = summary.employees.map(emp => `
        <div class="employee-card">
            <h3>${emp.name}</h3>
            <p><strong>Employer:</strong> ${emp.employer_name}</p>
            <p><strong>Pay Frequency:</strong> ${emp.pay_frequency}</p>
            ${emp.last_paystub ? `
                <p><strong>Last Paystub:</strong> #${emp.last_paystub.number} - ${emp.last_paystub.pay_date}</p>
                <p><strong>Last Net:</strong> $${emp.last_paystub.net.toFixed(2)}</p>
            ` : '<p>No paystubs yet</p>'}
            <div class="ytd-info">
                <p><strong>YTD Gross:</strong> $${emp.ytd_summary.gross.toFixed(2)}</p>
                <p><strong>YTD Net:</strong> $${emp.ytd_summary.net.toFixed(2)}</p>
            </div>
            <button onclick="navigateTo('generate-paystub', ${emp.id})">Generate Next Paystub</button>
            <button onclick="navigateTo('paystub-history', ${emp.id})">View History</button>
        </div>
    `).join('');
    
    dashboardContent.innerHTML = ytdSummary + '<h2>Your Employees</h2>' + employeeCards;
}

// ============================================================================
// PAYSTUB GENERATION FUNCTIONS
// ============================================================================

async function generatePaystub() {
    const employeeId = document.getElementById('employee-id').value;
    const grossPay = document.getElementById('gross-pay').value;
    const payPeriodStart = document.getElementById('pay-period-start').value;
    const payPeriodEnd = document.getElementById('pay-period-end').value;
    const payDate = document.getElementById('pay-date').value;
    const regularHours = document.getElementById('regular-hours').value;
    const regularRate = document.getElementById('regular-rate').value;
    const overtimeHours = document.getElementById('overtime-hours').value;
    const overtimeRate = document.getElementById('overtime-rate').value;
    const healthInsurance = document.getElementById('health-insurance').value;
    const retirement401k = document.getElementById('retirement-401k').value;
    const otherDeductions = document.getElementById('other-deductions').value;
    
    try {
        const response = await fetch(`${API_BASE}/paystubs/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                employee_id: parseInt(employeeId),
                gross_pay: parseFloat(grossPay),
                pay_period_start: payPeriodStart,
                pay_period_end: payPeriodEnd,
                pay_date: payDate,
                regular_hours: parseFloat(regularHours),
                regular_rate: parseFloat(regularRate),
                overtime_hours: parseFloat(overtimeHours),
                overtime_rate: parseFloat(overtimeRate),
                health_insurance: parseFloat(healthInsurance) || 0,
                retirement_401k: parseFloat(retirement401k) || 0,
                other_deductions: parseFloat(otherDeductions) || 0
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Paystub #${data.paystub.paystub_number} generated successfully! +${data.reward_points_earned} points earned!`, 'success');
            navigateTo('dashboard');
        } else {
            showNotification(data.error || 'Failed to generate paystub', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// SUBSCRIPTION FUNCTIONS
// ============================================================================

async function upgradePlan(planName) {
    try {
        const response = await fetch(`${API_BASE}/subscription/upgrade`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                plan_name: planName,
                billing_cycle: 'monthly'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Successfully upgraded to ${planName}!`, 'success');
            loadSubscriptionPlans();
        } else {
            showNotification(data.error || 'Upgrade failed', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function loadSubscriptionPlans() {
    try {
        const response = await fetch(`${API_BASE}/subscription/plans`);
        const data = await response.json();
        
        if (response.ok) {
            renderSubscriptionPlans(data.plans);
        }
    } catch (error) {
        console.error('Error loading plans:', error);
    }
}

function renderSubscriptionPlans(plans) {
    const plansContainer = document.getElementById('subscription-plans');
    
    const plansHTML = plans.map(plan => `
        <div class="plan-card">
            <h3>${plan.name.toUpperCase()}</h3>
            <p class="price">$${plan.price_monthly}/month</p>
            <ul>
                <li>Up to ${plan.max_employees} employee(s)</li>
                <li>${plan.max_paystubs_per_month} paystubs/month</li>
                <li>${plan.api_access ? '✓' : '✗'} API Access</li>
                <li>${plan.priority_support ? '✓' : '✗'} Priority Support</li>
            </ul>
            <button onclick="upgradePlan('${plan.name}')">Upgrade Now</button>
        </div>
    `).join('');
    
    if (plansContainer) {
        plansContainer.innerHTML = plansHTML;
    }
}

// ============================================================================
// NAVIGATION AND UI FUNCTIONS
// ============================================================================

function navigateTo(page, param = null) {
    // Hide all pages
    document.querySelectorAll('[data-page]').forEach(el => el.style.display = 'none');
    
    // Show selected page
    const pageEl = document.querySelector(`[data-page="${page}"]`);
    if (pageEl) {
        pageEl.style.display = 'block';
        
        // Load page-specific data
        if (page === 'dashboard') loadDashboard();
        if (page === 'subscription') loadSubscriptionPlans();
        if (page === 'generate-paystub' && param) {
            document.getElementById('employee-id').value = param;
        }
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 3000);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    if (authToken) {
        currentUser = JSON.parse(localStorage.getItem('user'));
        navigateTo('dashboard');
    } else {
        navigateTo('login');
    }
    
    // Load subscription plans
    loadSubscriptionPlans();
});
