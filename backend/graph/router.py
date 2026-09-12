from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

class RouterOutput(BaseModel):
    intent: str = Field(description="One of: PERSONAL_DOCUMENT_QUERY, MEDICAL_GUIDANCE, FOOD_NUTRITION, MEDICATION_INFORMATION, DISEASE_EXPLANATION, PREVENTION, EMERGENCY, GENERAL_CHAT")
    safety_level: str = Field(description="One of: normal, high_risk")
    requires_doctor: bool = Field(description="True if the user is asking for a diagnosis, prescription, or medical decision.")
    reasoning: str = Field(description="Reasoning for classification")


def _keyword_fallback_classification(user_message: str) -> RouterOutput:
    """
    Keyword-based fallback classification when the LLM fails structured output.
    This ensures medical questions are NEVER silently routed to GENERAL_CHAT.
    """
    msg = user_message.lower().strip()
    
    # Greetings / trivial (only if VERY clearly non-medical)
    greeting_only = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon",
                     "good night", "thanks", "thank you", "bye", "goodbye", "ok", "okay"]
    if msg in greeting_only or msg.rstrip("!. ") in greeting_only:
        return RouterOutput(
            intent="GENERAL_CHAT", safety_level="normal",
            requires_doctor=False, reasoning="Greeting detected via keyword fallback"
        )
    
    # Food / nutrition keywords
    food_keywords = ["food", "eat", "diet", "nutrition", "fruit", "vegetable", "meal",
                     "recipe", "cook", "supplement", "vitamin", "mineral", "iron rich",
                     "b12 food", "calcium food", "protein", "fiber", "omega"]
    if any(k in msg for k in food_keywords):
        return RouterOutput(
            intent="FOOD_NUTRITION", safety_level="normal",
            requires_doctor=False, reasoning="Food/nutrition keywords detected"
        )
    
    # Document-related queries
    doc_keywords = ["report", "document", "uploaded", "lab report", "test result",
                    "what happened", "that boy", "that patient", "that girl", "his report",
                    "her report", "my report", "blood test", "cbc", "hemoglobin level",
                    "does he have", "does she have", "my values", "his values", "her values",
                    "what does my", "what does his", "what does her", "thyroid", "thyroid report"]
    if any(k in msg for k in doc_keywords):
        return RouterOutput(
            intent="PERSONAL_DOCUMENT_QUERY", safety_level="normal",
            requires_doctor=False, reasoning="Document/report query keywords detected"
        )
    
    # Disease explanation keywords
    disease_keywords = ["what is", "how it occurs", "how does", "causes of", "why does",
                        "explain", "what causes", "reason for", "how do you get",
                        "deficiency", "syndrome", "disorder", "condition", "disease",
                        "infection", "symptoms of", "signs of"]
    if any(k in msg for k in disease_keywords):
        return RouterOutput(
            intent="DISEASE_EXPLANATION", safety_level="normal",
            requires_doctor=False, reasoning="Disease explanation keywords detected"
        )
    
    # Medication keywords
    med_keywords = ["medicine", "medication", "drug", "tablet", "capsule", "dose",
                    "dosage", "prescription", "side effect", "interaction", "antibiotic"]
    if any(k in msg for k in med_keywords):
        return RouterOutput(
            intent="MEDICATION_INFORMATION", safety_level="high_risk",
            requires_doctor=True, reasoning="Medication keywords detected"
        )
    
    # Prevention keywords
    prevention_keywords = ["prevent", "avoid", "reduce risk", "how to stop",
                           "how to lower", "how to decrease", "how to improve",
                           "how to increase", "precaution", "protect"]
    if any(k in msg for k in prevention_keywords):
        return RouterOutput(
            intent="PREVENTION", safety_level="normal",
            requires_doctor=False, reasoning="Prevention keywords detected"
        )
    
    # General medical guidance (catch-all for anything medical-sounding)
    medical_keywords = ["health", "medical", "doctor", "hospital", "pain", "ache",
                        "treatment", "cure", "remedy", "therapy", "diagnos",
                        "fever", "cough", "cold", "flu", "blood", "sugar", "pressure",
                        "heart", "lung", "kidney", "liver", "brain", "bone", "muscle",
                        "joint", "skin", "eye", "ear", "nose", "throat", "stomach",
                        "chest", "head", "back", "leg", "arm", "anemia", "diabetes",
                        "cancer", "asthma", "allergy", "immune", "pregnant", "vitamin",
                        "b12", "iron", "cholesterol", "weight", "bmi", "calorie",
                        "exercise", "workout", "yoga", "sleep", "stress", "anxiety",
                        "depression", "mental health"]
    if any(k in msg for k in medical_keywords):
        return RouterOutput(
            intent="MEDICAL_GUIDANCE", safety_level="normal",
            requires_doctor=False, reasoning="General medical keywords detected"
        )
    
    # Default: treat as medical guidance (not GENERAL_CHAT!) since this is a medical app
    return RouterOutput(
        intent="MEDICAL_GUIDANCE", safety_level="normal",
        requires_doctor=False, reasoning="Default fallback - treating as medical query"
    )


def classify_intent(llm, user_message: str) -> RouterOutput:
    """
    Classifies user intent using LLM with structured output.
    Falls back to keyword-based classification if LLM fails.
    """
    structured_llm = llm.with_structured_output(RouterOutput)
    system_prompt = """You are a medical triage and intent classification system.
    Classify the user's intent based on their query.
    Intents:
    - PERSONAL_DOCUMENT_QUERY: Asking about values/details in their uploaded documents (lab reports, test results, medical records). Includes questions like "what happened to that patient", "does he have X", "what are the values".
    - MEDICAL_GUIDANCE: Asking how to improve a condition, general causes, treatments, etc.
    - FOOD_NUTRITION: Asking about diet, what to eat, food items, supplements, vitamins for a condition.
    - MEDICATION_INFORMATION: Asking about prescriptions, stopping meds, dosage, drug interactions.
    - DISEASE_EXPLANATION: Asking what a disease is, why it happens, how it occurs, its causes and mechanisms.
    - PREVENTION: Asking how to prevent a disease or worsening.
    - EMERGENCY: Severe chest pain, breathing issues, severe bleeding, loss of consciousness, stroke symptoms, allergic reactions.
    - GENERAL_CHAT: ONLY for greetings like "hello", "thanks", or clearly non-medical questions like "what is the weather".
    
    IMPORTANT: When in doubt, classify as MEDICAL_GUIDANCE rather than GENERAL_CHAT. 
    This is a medical app - assume the user's question is medically related unless it clearly is not.
    
    Safety Level:
    - high_risk if they ask to change dose, stop meds, want a guaranteed cure, or emergency.
    - normal otherwise.
    """
    try:
        result = structured_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_message)])
        print(f"  Router LLM classified: intent={result.intent}, safety={result.safety_level}, reasoning={result.reasoning}")
        return result
    except Exception as e:
        print(f"  Router LLM error: {e}")
        print(f"  Using keyword-based fallback classification...")
        fallback = _keyword_fallback_classification(user_message)
        print(f"  Fallback classified: intent={fallback.intent}, reasoning={fallback.reasoning}")
        return fallback
