def verify_grounding(response: str, personal_context: str, medical_context: str) -> bool:
    """
    Verifies that the generated response is grounded in the provided context.
    Returns True if grounded, False otherwise.
    In a real system, this would use a fast classification LLM.
    """
    # Stub implementation
    if "guaranteed cure" in response.lower() or "100% cure" in response.lower():
        return False
        
    return True

def fallback_ungrounded_response() -> str:
    return "I apologize, but I could not verify all the information in my response against trusted medical sources or your personal documents. Please consult a healthcare professional."
