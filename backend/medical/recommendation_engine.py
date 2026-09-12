def get_recommendation_categories(condition: str) -> list:
    """
    Returns relevant preventative recommendation categories based on the condition.
    """
    categories = []
    condition_lower = condition.lower()
    
    # Hypertension / High Blood Pressure
    if "hypertension" in condition_lower or "blood pressure" in condition_lower:
        categories = ["FOOD", "LIFESTYLE", "EXERCISE", "MEDICATION_ADHERENCE", "MONITORING", "FOLLOW_UP", "PRECAUTIONS"]
    
    # Diabetes / High Blood Sugar
    elif "diabetes" in condition_lower or "glucose" in condition_lower or "hba1c" in condition_lower:
        categories = ["FOOD", "LIFESTYLE", "EXERCISE", "MONITORING", "FOLLOW_UP", "PRECAUTIONS", "RED_FLAGS"]
        
    # Anemia / Low Hemoglobin
    elif "anemia" in condition_lower or "hemoglobin" in condition_lower:
        categories = ["FOOD", "FOLLOW_UP", "PRECAUTIONS"]
        
    else:
        categories = ["LIFESTYLE", "FOLLOW_UP", "PRECAUTIONS"]
        
    return categories
