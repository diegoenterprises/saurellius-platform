/**
 * State-Aware Paystub Form
 * Dynamically show/hide fields based on state and locality selections
 */

const StateAwareForm = {
    // States with disability insurance
    SDI_STATES: ['CA', 'NY', 'NJ', 'RI', 'HI', 'PR'],
    
    // States with local income tax
    LOCAL_TAX_STATES: ['AL', 'AR', 'CO', 'DE', 'IA', 'IN', 'KS', 'KY', 'MD', 'MI', 'MO', 'NJ', 'NY', 'OH', 'OR', 'PA', 'WV'],
    
    // States with no income tax
    NO_TAX_STATES: ['AK', 'FL', 'NV', 'SD', 'TN', 'TX', 'WA', 'WY'],
    
    // Cities with local tax
    CITIES_WITH_TAX: {
        'NY': ['New York City', 'Yonkers'],
        'PA': ['Philadelphia', 'Pittsburgh', 'Scranton'],
        'OH': ['Cincinnati', 'Cleveland', 'Columbus', 'Toledo', 'Akron', 'Dayton'],
        'MI': ['Detroit', 'Grand Rapids', 'Flint'],
        'MD': ['Baltimore'],
        'KY': ['Louisville', 'Lexington'],
        'IN': ['Indianapolis', 'Fort Wayne'],
        'MO': ['Kansas City', 'St. Louis']
    },
    
    init() {
        // Attach event listeners
        const stateSelect = document.getElementById('employee_state');
        const cityInput = document.getElementById('employee_city');
        
        if (stateSelect) {
            stateSelect.addEventListener('change', () => this.onStateChange());
        }
        
        if (cityInput) {
            cityInput.addEventListener('blur', () => this.onCityChange());
        }
        
        // Initial state check
        if (stateSelect && stateSelect.value) {
            this.onStateChange();
        }
    },
    
    onStateChange() {
        const state = document.getElementById('employee_state').value;
        
        if (!state) {
            this.hideAllConditionalFields();
            return;
        }
        
        // Show/hide state income tax fields
        if (this.NO_TAX_STATES.includes(state)) {
            this.hideField('state_income_tax_section');
        } else {
            this.showField('state_income_tax_section');
        }
        
        // Show/hide state disability insurance
        if (this.SDI_STATES.includes(state)) {
            this.showField('state_disability_section');
            this.updateSDILabel(state);
        } else {
            this.hideField('state_disability_section');
        }
        
        // Show/hide local tax fields
        if (this.LOCAL_TAX_STATES.includes(state)) {
            this.showField('local_tax_section');
            this.updateLocalTaxOptions(state);
        } else {
            this.hideField('local_tax_section');
        }
        
        // Update form labels based on state
        this.updateStateSpecificLabels(state);
    },
    
    onCityChange() {
        const state = document.getElementById('employee_state').value;
        const city = document.getElementById('employee_city').value;
        
        if (!state || !city) return;
        
        // Check if city has local tax
        const citiesInState = this.CITIES_WITH_TAX[state] || [];
        const cityHasTax = citiesInState.some(c => 
            city.toLowerCase().includes(c.toLowerCase())
        );
        
        if (cityHasTax) {
            this.showField('local_tax_fields');
            this.showLocalTaxInfo(state, city);
        } else if (state === 'OH' || state === 'PA') {
            // Ohio and PA have widespread local taxes
            this.showField('local_tax_fields');
            this.showLocalTaxInfo(state, city);
        } else {
            this.hideField('local_tax_fields');
        }
    },
    
    updateSDILabel(state) {
        const labels = {
            'CA': 'California SDI',
            'NY': 'New York Disability',
            'NJ': 'New Jersey TDI',
            'RI': 'Rhode Island TDI',
            'HI': 'Hawaii TDI',
            'PR': 'Puerto Rico SINOT'
        };
        
        const label = document.querySelector('label[for="state_disability_tax"]');
        if (label) {
            label.textContent = labels[state] || 'State Disability Insurance';
        }
    },
    
    updateLocalTaxOptions(state) {
        const cities = this.CITIES_WITH_TAX[state] || [];
        const citySelect = document.getElementById('local_jurisdiction');
        
        if (!citySelect) return;
        
        // Clear existing options
        citySelect.innerHTML = '<option value="">Select City/Jurisdiction</option>';
        
        // Add cities for this state
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
        
        // Show info message
        const infoDiv = document.getElementById('local_tax_info');
        if (infoDiv) {
            if (state === 'OH') {
                infoDiv.textContent = 'Most Ohio municipalities have local income tax (typically 1-2.5%)';
                infoDiv.style.display = 'block';
            } else if (state === 'PA') {
                infoDiv.textContent = 'Most Pennsylvania localities have local income tax (typically 1%)';
                infoDiv.style.display = 'block';
            } else if (cities.length > 0) {
                infoDiv.textContent = `${state} has local income tax in certain cities`;
                infoDiv.style.display = 'block';
            } else {
                infoDiv.style.display = 'none';
            }
        }
    },
    
    showLocalTaxInfo(state, city) {
        const infoDiv = document.getElementById('local_tax_info');
        if (!infoDiv) return;
        
        const taxRates = {
            'NYC': '3.876%',
            'PHI': '3.398%',
            'DET': '2.4%',
            'COL': '2.5%',
            'CIN': '2.1%',
            'CLE': '2.5%'
        };
        
        // Find matching city code
        let rate = null;
        for (const [code, cityName] of Object.entries(this.CITIES_WITH_TAX[state] || {})) {
            if (city.toLowerCase().includes(cityName.toLowerCase())) {
                rate = taxRates[code];
                break;
            }
        }
        
        if (rate) {
            infoDiv.textContent = `${city} local tax rate: ${rate}`;
            infoDiv.style.display = 'block';
        } else {
            infoDiv.textContent = 'Local tax may apply - check with your municipality';
            infoDiv.style.display = 'block';
        }
    },
    
    updateStateSpecificLabels(state) {
        // Update labels for state-specific terminology
        const stateTerminology = {
            'CA': {
                'state_tax': 'California Income Tax',
                'sdi': 'CA SDI (1.2%)'
            },
            'NY': {
                'state_tax': 'New York State Tax',
                'sdi': 'NY Disability (0.5%)'
            },
            'NJ': {
                'state_tax': 'New Jersey Income Tax',
                'sdi': 'NJ TDI/UI (0.26%)'
            }
        };
        
        const terms = stateTerminology[state];
        if (terms) {
            const stateTaxLabel = document.querySelector('label[for="state_income_tax"]');
            if (stateTaxLabel && terms.state_tax) {
                stateTaxLabel.textContent = terms.state_tax;
            }
        }
    },
    
    showField(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.style.display = 'block';
            field.classList.remove('hidden');
        }
    },
    
    hideField(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.style.display = 'none';
            field.classList.add('hidden');
        }
    },
    
    hideAllConditionalFields() {
        this.hideField('state_disability_section');
        this.hideField('local_tax_section');
        this.hideField('local_tax_fields');
    },
    
    // PTO Section Toggle
    togglePTOSection(show) {
        const ptoSection = document.getElementById('pto_section');
        if (ptoSection) {
            ptoSection.style.display = show ? 'block' : 'none';
        }
    },
    
    // Garnishment Section Toggle
    toggleGarnishmentSection(show) {
        const garnishmentSection = document.getElementById('garnishment_section');
        if (garnishmentSection) {
            garnishmentSection.style.display = show ? 'block' : 'none';
        }
    },
    
    // Auto-calculate gross pay from hours and rate
    calculateGrossPay() {
        const regularHours = parseFloat(document.getElementById('regular_hours')?.value || 0);
        const overtimeHours = parseFloat(document.getElementById('overtime_hours')?.value || 0);
        const payRate = parseFloat(document.getElementById('pay_rate')?.value || 0);
        const overtimeRate = payRate * 1.5;
        
        const regularPay = regularHours * payRate;
        const overtimePay = overtimeHours * overtimeRate;
        const grossPay = regularPay + overtimePay;
        
        const grossPayField = document.getElementById('gross_pay');
        if (grossPayField) {
            grossPayField.value = grossPay.toFixed(2);
        }
        
        return grossPay;
    },
    
    // Load employee data and pre-fill form
    async loadEmployeeData(employeeId) {
        try {
            const response = await fetch(`/api/employees/${employeeId}`);
            const employee = await response.json();
            
            // Pre-fill form with employee data
            if (employee.address_state) {
                document.getElementById('employee_state').value = employee.address_state;
                this.onStateChange();
            }
            
            if (employee.address_city) {
                document.getElementById('employee_city').value = employee.address_city;
                this.onCityChange();
            }
            
            if (employee.pay_rate) {
                document.getElementById('pay_rate').value = employee.pay_rate;
            }
            
            // Load YTD continuation data
            const ytdResponse = await fetch(`/api/paystubs/continuation/${employeeId}`);
            const ytdData = await ytdResponse.json();
            
            if (ytdData.next_pay_date) {
                document.getElementById('pay_date').value = ytdData.next_pay_date;
            }
            
            if (ytdData.suggested_values) {
                document.getElementById('regular_hours').value = ytdData.suggested_values.regular_hours;
            }
            
        } catch (error) {
            console.error('Error loading employee data:', error);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    StateAwareForm.init();
});

