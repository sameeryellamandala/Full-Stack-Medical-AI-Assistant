def check_emergency(query: str) -> bool:
    """
    Checks if the user query contains emergency keywords.
    """
    emergency_keywords = [
        "severe chest pain", "difficulty breathing", "stroke", "loss of consciousness",
        "severe bleeding", "allergic reaction", "suicide", "kill myself", "heart attack",
        "severe confusion"
    ]
    query_lower = query.lower()
    for keyword in emergency_keywords:
        if keyword in query_lower:
            return True
    return False

def get_emergency_response() -> str:
    return "This sounds like a potential medical emergency. Please contact your local emergency services immediately (e.g., dial 911) or visit the nearest hospital. I am an AI and cannot provide emergency medical assistance or diagnoses."
