from typing import Annotated, TypedDict, List
import re
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from .router import classify_intent
from retrieval.hybrid_retriever import get_hybrid_retriever
from retrieval.reranker import rerank_documents
from medical.medical_search import search_medical_knowledge
from medical.emergency import check_emergency, get_emergency_response
from medical.safety import apply_safety_guidelines

from generation.grounding_checker import verify_grounding, fallback_ungrounded_response
from generation.citation_checker import verify_citations


def _strip_thinking(text: str) -> str:
    """Strip <think>...</think> reasoning tokens from Qwen model output."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    # Also handle unclosed thinking tags (when output is truncated)
    cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL).strip()
    return cleaned if cleaned else text


# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The chat history"]
    user_id: str
    active_document: str
    intent: str
    safety_level: str
    requires_doctor: bool
    file_context: str
    medical_knowledge_context: str

def create_graph(llm):
    # 2. Nodes
    def router_node(state: AgentState):
        last_message = state['messages'][-1].content
        print(f"\n{'='*60}")
        print(f"ROUTER: Processing message: '{last_message[:80]}...'")
        
        # Check explicit emergency keywords first
        if check_emergency(last_message):
            print(f"  ROUTER: Emergency detected!")
            return {"intent": "EMERGENCY", "safety_level": "high_risk", "requires_doctor": True}
            
        classification = classify_intent(llm, last_message)
        print(f"  ROUTER: Final intent = {classification.intent}")
        return {
            "intent": classification.intent,
            "safety_level": classification.safety_level,
            "requires_doctor": classification.requires_doctor
        }

    def emergency_responder(state: AgentState):
        return {"messages": [AIMessage(content=get_emergency_response())]}

    def general_chat_responder(state: AgentState):
        """Handle greetings and general chat with a friendly LLM response instead of a static message."""
        query = state['messages'][-1].content
        print(f"  GENERAL_CHAT: Generating friendly response for: '{query}'")
        
        system_prompt = """You are a friendly, professional Medical AI Assistant. 
The user sent a greeting or general message. Respond warmly and let them know how you can help.

You can help with:
- Answering medical questions (diseases, conditions, symptoms, causes)
- Nutrition advice (food items, diet recommendations, supplements)
- Analyzing uploaded medical documents (lab reports, blood tests)
- Medication information
- Prevention and lifestyle recommendations

Keep your response concise but warm. If the user said hello, greet them back and briefly mention what you can help with."""

        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ])
            return {"messages": [AIMessage(content=_strip_thinking(response.content))]}
        except Exception as e:
            print(f"  GENERAL_CHAT error: {e}")
            return {"messages": [AIMessage(content="Hello! I'm your Medical AI Assistant. I can help you with medical questions, nutrition advice, analyzing lab reports, and more. How can I assist you today?")]}

    def retrieve_node(state: AgentState):
        query = state['messages'][-1].content
        user_id = state.get('user_id', '')
        active_document = state.get('active_document', '')
        
        print(f"  RETRIEVE: user_id={user_id}, active_doc='{active_document}'")
        
        # Rewrite query if there is history
        if len(state['messages']) > 1:
            from retrieval.query_rewriter import rewrite_query
            query = rewrite_query(llm, query, state['messages'][:-1])
            print(f"  RETRIEVE: Rewritten query: '{query}'")
        
        try:
            hybrid_search = get_hybrid_retriever(user_id=user_id, active_document=active_document)
            raw_docs = hybrid_search(query)
            
            # Rerank
            top_docs = rerank_documents(query, raw_docs, top_n=5)
            
            context = "\n".join([f"[{doc.metadata.get('source_filename', 'Unknown')}] {doc.page_content}" for doc in top_docs])
            print(f"  RETRIEVE: Got {len(top_docs)} documents, context length={len(context)}")
            return {"file_context": context}
        except Exception as e:
            print(f"  RETRIEVE ERROR: {e}")
            return {"file_context": ""}

    def medical_search_node(state: AgentState):
        query = state['messages'][-1].content
        
        # Rewrite query if there is history
        if len(state['messages']) > 1:
            from retrieval.query_rewriter import rewrite_query
            query = rewrite_query(llm, query, state['messages'][:-1])
            print(f"  MEDICAL_SEARCH: Rewritten query: '{query}'")
            
        try:
            results = search_medical_knowledge(query)
            context = "\n".join([f"[{r['title']} - {r['organization']}] {r['passage']}" for r in results])
            print(f"  MEDICAL_SEARCH: Got {len(results)} results, context length={len(context)}")
            return {"medical_knowledge_context": context}
        except Exception as e:
            print(f"  MEDICAL_SEARCH ERROR: {e}")
            return {"medical_knowledge_context": ""}

    def generator_node(state: AgentState):
        query = state['messages'][-1].content
        intent = state.get("intent", "")
        file_context = state.get('file_context', '')
        medical_context = state.get('medical_knowledge_context', '')
        
        print(f"  GENERATOR: intent={intent}, file_context_len={len(file_context)}, medical_context_len={len(medical_context)}")
        
        # Build a detailed, intent-specific system prompt
        system_prompt = _build_system_prompt(intent, file_context, medical_context)
            
        inputs = [SystemMessage(content=system_prompt)] + state['messages']
        
        sources = []
        if file_context:
            inputs.append(SystemMessage(content=f"=== PERSONAL DOCUMENTS CONTEXT ===\n{file_context}\n=== END PERSONAL DOCUMENTS ==="))
            sources.append("Personal Medical Documents")
            
        if medical_context:
            inputs.append(SystemMessage(content=f"=== TRUSTED MEDICAL KNOWLEDGE ===\n{medical_context}\n=== END MEDICAL KNOWLEDGE ==="))
            sources.append("Trusted External Medical Sources")
        
        # If no context at all, tell the LLM to use its own knowledge
        if not file_context and not medical_context:
            inputs.append(SystemMessage(content="No external context was retrieved. Use your own medical knowledge to provide a comprehensive, accurate, and helpful answer. Be detailed and specific."))
            
        try:
            response = llm.invoke(inputs)
            ai_content = _strip_thinking(response.content)
            print(f"  GENERATOR: LLM response length={len(ai_content)}")
        except Exception as e:
            print(f"  GENERATOR LLM ERROR: {e}")
            ai_content = "I apologize, but I encountered an error generating a response. Please try rephrasing your question."
        
        # Apply Safety, Grounding, and Citations
        is_grounded = verify_grounding(ai_content, file_context, medical_context)
        if not is_grounded:
            safe_content = fallback_ungrounded_response()
        else:
            safe_content = apply_safety_guidelines(query, ai_content)
            safe_content = verify_citations(safe_content, sources)
        
        return {"messages": [AIMessage(content=safe_content)]}

    # 3. Graph Construction
    workflow = StateGraph(AgentState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("emergency", emergency_responder)
    workflow.add_node("general_chat", general_chat_responder)
    workflow.add_node("retrieve_personal", retrieve_node)
    workflow.add_node("retrieve_medical", medical_search_node)
    workflow.add_node("generator", generator_node)

    def route_query(state: AgentState) -> str:
        intent = state.get("intent")
        print(f"  ROUTE: intent={intent}")
        if intent == "EMERGENCY":
            return "emergency"
        if intent == "GENERAL_CHAT":
            return "general_chat"
        if intent == "PERSONAL_DOCUMENT_QUERY":
            return "retrieve_personal"
        # All medical intents: search external sources first, then personal docs
        return "retrieve_medical"

    workflow.set_entry_point("router")
    
    workflow.add_conditional_edges(
        "router",
        route_query,
        {
            "emergency": "emergency",
            "general_chat": "general_chat",
            "retrieve_medical": "retrieve_medical",
            "retrieve_personal": "retrieve_personal"
        }
    )
    
    # Medical search → personal docs → generator
    workflow.add_edge("retrieve_medical", "retrieve_personal")
    workflow.add_edge("retrieve_personal", "generator")
    workflow.add_edge("emergency", END)
    workflow.add_edge("general_chat", END)
    workflow.add_edge("generator", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def _build_system_prompt(intent: str, file_context: str, medical_context: str) -> str:
    """Build an intent-specific system prompt for the generator LLM."""
    
    base = """You are a professional Medical AI Assistant. You provide accurate, detailed, and helpful medical information.

IMPORTANT RULES:
- Always provide comprehensive, structured answers
- Use bullet points and clear formatting
- Be specific with examples (food items, medications, causes, etc.)
- If context from documents or external sources is provided, USE IT to answer
- Always add a disclaimer to consult a healthcare professional for personalized advice
- Never refuse to answer a medical question - provide the best information you can
"""

    if intent == "FOOD_NUTRITION":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- List specific food items with details (e.g., "Liver (beef/chicken) - richest source of B12, ~70μg per 100g")
- Group foods by category (Animal Sources, Plant Sources, Fortified Foods, etc.)
- Mention recommended daily intake values
- Suggest supplements if relevant
- Include practical tips for incorporating these foods into diet
"""

    elif intent == "DISEASE_EXPLANATION":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- Explain what the disease/condition is clearly
- List ALL possible causes and risk factors
- Explain the mechanism (how/why it occurs in the body)
- Mention common symptoms
- Briefly mention treatment approaches
- Mention who is most at risk
"""

    elif intent == "PERSONAL_DOCUMENT_QUERY":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- Analyze the provided document context carefully
- Reference specific values and numbers from the documents
- Compare values against normal ranges if available
- Explain what abnormal values could mean
- Summarize the overall health picture from the documents
- If asked about a specific condition (e.g., thyroid), check the relevant values in the report
"""

    elif intent == "MEDICAL_GUIDANCE":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- Provide comprehensive medical guidance
- Include both general information and specific actionable advice
- Mention lifestyle changes, dietary recommendations, and when to see a doctor
- Be thorough and cover multiple aspects of the topic
"""

    elif intent == "MEDICATION_INFORMATION":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- Provide information about the medication(s) asked about
- Include common uses, dosage ranges, side effects
- ALWAYS emphasize consulting a doctor before starting/stopping/changing medication
- Mention important drug interactions if relevant
"""

    elif intent == "PREVENTION":
        base += """
SPECIFIC INSTRUCTIONS FOR THIS QUERY:
- List specific preventive measures
- Include lifestyle changes, dietary recommendations, exercise guidelines
- Mention screening and regular checkup recommendations
- Provide actionable, practical advice
"""
    
    # Add context awareness
    if file_context:
        base += "\nYou have access to the user's personal medical documents. Use this data to personalize your answer."
    if medical_context:
        base += "\nYou have access to trusted medical knowledge from external sources. Incorporate this information into your answer."
    if not file_context and not medical_context:
        base += "\nNo external context was found. Use your own comprehensive medical knowledge to answer thoroughly."
    
    return base
