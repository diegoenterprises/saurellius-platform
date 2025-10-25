import json

# List of states/territories with mandatory employee State Disability Insurance (SDI)
SDI_STATES = ["CA", "NY", "NJ", "RI", "HI", "PR"]

# List of states/territories with local income taxes (examples)
LOCAL_TAX_JURISDICTIONS = {
    "PA": ["Philadelphia", "Pittsburgh"],
    "OH": ["Cincinnati", "Cleveland", "Columbus"],
    "MD": ["Baltimore", "Montgomery County"],
    "KY": ["Louisville", "Lexington"],
    "MI": ["Detroit", "Grand Rapids"],
    "NY": ["New York City", "Yonkers"],
    "DE": ["Wilmington"],
    "PR": ["San Juan"]
}

def get_state_form_config(state_code):
    """
    Returns a configuration dictionary for the paystub generation form
    based on the selected state/territory.
    
    :param state_code: The two-letter state or territory code (e.g., 'CA', 'NY', 'PR').
    :return: A dictionary with form field visibility and label configurations.
    """
    config = {
        # Default visibility
        "show_state_income_tax": True,
        "show_state_disability_tax": False,
        "show_local_tax_fields": False,
        
        # Default labels
        "state_income_tax_label": "State Income Tax",
        "state_disability_tax_label": "State Disability Insurance (SDI)",
        "local_tax_label": "Local Income Tax",
        "state_unemployment_tax_label": "State Unemployment Tax (SUI)",
    }
    
    # 1. Handle states with no income tax
    # (Assuming the frontend can check if the state is in the no-income-tax list
    # or the backend can check the tax_calculator data)
    # For now, we rely on the tax calculation engine to return 0.00 for no-tax states,
    # but we can set the visibility here for the form.
    # No-tax states: AK, FL, NV, NH, SD, TN, TX, WA, WY
    NO_INCOME_TAX_STATES = ["AK", "FL", "NV", "NH", "SD", "TN", "TX", "WA", "WY"]
    if state_code in NO_INCOME_TAX_STATES:
        config["show_state_income_tax"] = False
    
    # 2. Handle State Disability Insurance (SDI)
    if state_code in SDI_STATES:
        config["show_state_disability_tax"] = True
        
        # Special labels for specific states
        if state_code == "NJ":
            config["state_disability_tax_label"] = "State Disability Insurance (SDI) / Family Leave Insurance (FLI)"
        elif state_code == "NY":
            config["state_disability_tax_label"] = "Disability Benefits Law (DBL)"
        elif state_code == "RI":
            config["state_disability_tax_label"] = "Temporary Disability Insurance (TDI)"
        
    # 3. Handle Local Tax Fields
    if state_code in LOCAL_TAX_JURISDICTIONS:
        config["show_local_tax_fields"] = True
        config["local_jurisdictions"] = LOCAL_TAX_JURISDICTIONS[state_code]
        
    # 4. Handle state-specific terminology
    if state_code == "PR":
        config["state_income_tax_label"] = "Puerto Rico Income Tax"
        config["state_disability_tax_label"] = "Disability Benefits Fund (FSE)"
        
    return config

def get_local_tax_config(state_code, city_name):
    """
    Returns a configuration dictionary for local tax fields based on city and state.
    
    :param state_code: The two-letter state or territory code.
    :param city_name: The city name.
    :return: A dictionary with local tax field visibility and label configurations.
    """
    config = {
        "show_city_tax": False,
        "show_county_tax": False,
        "show_school_district_tax": False,
        "city_tax_label": "City Tax",
        "county_tax_label": "County Tax",
        "school_district_tax_label": "School District Tax"
    }
    
    # Placeholder for complex local tax logic
    if state_code == "PA" and city_name == "Philadelphia":
        config["show_city_tax"] = True
        config["city_tax_label"] = "Philadelphia City Wage Tax"
        
    return config

if __name__ == '__main__':
    print("--- California (CA) ---")
    print(json.dumps(get_state_form_config("CA"), indent=4))
    
    print("\n--- New York (NY) ---")
    print(json.dumps(get_state_form_config("NY"), indent=4))
    
    print("\n--- Texas (TX) ---")
    print(json.dumps(get_state_form_config("TX"), indent=4))
    
    print("\n--- Pennsylvania (PA) Local ---")
    print(json.dumps(get_state_form_config("PA"), indent=4))
    print(json.dumps(get_local_tax_config("PA", "Philadelphia"), indent=4))
    
    print("\n--- Puerto Rico (PR) ---")
    print(json.dumps(get_state_form_config("PR"), indent=4))
