from typing import Dict, Any

def apply_safety_guidelines(query: str, generated_response: str) -> str:
    """
    Applies strict medical safety guidelines to the generated response.
    In a real system, this would use another LLM pass to verify the content.
    Here we append strict disclaimers based on the intent of the query.
    """
    query_lower = query.lower()
    safety_appended_response = generated_response
    
    # Medication Safety (Task 16)
    medication_keywords = ["dose", "stop", "change medicine", "tablet", "replace medicine", "prescription"]
    if any(k in query_lower for k in medication_keywords):
        safety_appended_response += "\n\n⚠️ **Medication Safety:** Follow the medication instructions provided by your clinician. Do not start, stop, or change medication dosages without discussing it with them."
        
    # Unsupported Cure Claims (Task 18)
    cure_keywords = ["cure", "natural way to get rid", "will this fix"]
    if any(k in query_lower for k in cure_keywords):
        safety_appended_response += "\n\n⚠️ **Medical Disclaimer:** These measures may support management but should not be considered a guaranteed cure or replacement for prescribed treatment."
        
    # Unsupported Diagnosis (Task 17)
    diagnosis_keywords = ["what disease", "do i have", "my diagnosis"]
    if any(k in query_lower for k in diagnosis_keywords):
        safety_appended_response += "\n\n⚠️ **Diagnosis Disclaimer:** Your report alone does not establish a complete clinical diagnosis. Seek professional evaluation for persistent or worsening abnormalities."

    return safety_appended_response
