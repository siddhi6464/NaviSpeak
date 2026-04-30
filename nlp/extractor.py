import os
import json
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in the environment.")
    return Groq(api_key=api_key)

class NavigationIntent(BaseModel):
    origin: Optional[str] = Field(None, description="The starting point of the journey. None if not specified.")
    destination: Optional[str] = Field(None, description="The final destination of the journey. None if not specified.")
    known_segment: Optional[str] = Field(None, description="The segment of the journey the user already knows (e.g., 'Home to Koregaon Park'). None if not mentioned.")
    guidance_start: Optional[str] = Field(None, description="Where the actual step-by-step navigation should start from (e.g., 'Koregaon Park'). This is usually the end of the known segment.")
    preferences: Dict[str, bool] = Field(
        default={"avoid_tolls": False, "avoid_highways": False, "avoid_traffic": False},
        description="Dictionary with boolean keys 'avoid_tolls', 'avoid_highways', 'avoid_traffic'."
    )
    awaiting_confirmation: bool = Field(False, description="Set to true if there is a known_segment and we need to confirm starting guidance from the guidance_start location.")
    confirmation_message: Optional[str] = Field(None, description="The message to ask the user to confirm starting from the guidance_start. e.g. 'Got it! Should I start navigation from Koregaon Park to Baner?'")
    ambiguous: bool = Field(False, description="True if the locations or intent are too vague and need clarification.")
    follow_up: Optional[str] = Field(None, description="The question to ask the user if the request is ambiguous.")

def extract_intent(user_query: str) -> dict:
    """
    Given a user query, extract the navigation intent into a structured JSON format using Groq.
    """
    client = get_groq_client()
    
    system_prompt = '''You are the intelligent core of NaviSpeak, a conversational navigation assistant.
Your job is to extract navigation intent from the user's input and record it using the provided tool.
Crucially, look out for "Partial Routes". If a user says "I know till X, guide me from there to Y", 
identify the known_segment ("start to X") and set guidance_start to "X". In this case, set awaiting_confirmation to true, and provide a friendly confirmation_message asking if they want to start navigation from X to Y.
If a location is very ambiguous or missing entirely (e.g., "take me to the place"), set ambiguous to true and ask a follow_up.
Always use the record_navigation_intent tool.'''

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "record_navigation_intent",
                    "description": "Record the extracted navigation intent.",
                    "parameters": NavigationIntent.model_json_schema()
                }
            }],
            tool_choice={"type": "function", "function": {"name": "record_navigation_intent"}},
            temperature=0,
            max_tokens=1024
        )
        
        message = response.choices[0].message
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "record_navigation_intent":
                    return json.loads(tool_call.function.arguments)
                    
        return {"error": "Failed to extract intent."}
    except Exception as e:
        return {"error": str(e)}

def handle_confirmation(user_query: str, previous_state: dict) -> dict:
    """
    If the user was awaiting confirmation, this parses their response.
    Returns the updated state.
    """
    client = get_groq_client()
    
    system_prompt = f'''The user was asked: "{previous_state.get('confirmation_message')}"
Their response is: "{user_query}"
Did they say yes/confirm or no/cancel?
Return ONLY a JSON object with a single boolean key "confirmed". Nothing else. Example: {{"confirmed": true}}'''
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only returns JSON."},
                {"role": "user", "content": system_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=150
        )
        
        text = response.choices[0].message.content
        result = json.loads(text)
        is_confirmed = result.get("confirmed", False)
        
        return {
            "confirmed": is_confirmed,
            "guidance_start": previous_state.get("guidance_start"),
            "destination": previous_state.get("destination"),
            "begin_navigation": is_confirmed,
            "preferences": previous_state.get("preferences", {})
        }
    except Exception as e:
        return {"error": str(e)}
