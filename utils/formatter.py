import re
from nlp.extractor import get_groq_client

def format_directions_html(steps: list) -> str:
    """
    Converts Google Maps html_instructions to a simple text list.
    """
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        instruction = re.sub('<[^<]+>', '', step.get('html_instructions', ''))
        dist = step.get('distance', '')
        formatted_steps.append(f"{i}. {instruction} ({dist})")
    return "\n".join(formatted_steps)

def get_conversational_directions(route_data: dict) -> str:
    """
    Takes route data and uses Groq to summarize it in a conversational tone.
    """
    if not route_data or "error" in route_data:
        return route_data.get("error", "No route data available.")
        
    raw_text = format_directions_html(route_data.get('steps', []))
    
    prompt = f"""You are NaviSpeak, a friendly navigation assistant. 
Given these raw Google Maps directions, summarize them in a conversational way.
Highlight the main roads, key turns, and overall estimated time/distance. 
Make it natural, like a friend giving directions.

Distance: {route_data.get('distance')}
Duration: {route_data.get('duration')}

Raw Steps:
{raw_text}
"""
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful and conversational navigation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback if Groq fails
        return f"**Route ({route_data.get('distance')}, {route_data.get('duration')}):**\n\n" + raw_text

def get_route_summary(route_data: dict) -> str:
    """
    Returns a quick markdown summary of the route for the preview screen.
    """
    dist = route_data.get('distance', 'Unknown')
    dur = route_data.get('duration', 'Unknown')
    return f"**Route Found!** 🚗\n\n**Distance:** {dist}  |  **Duration:** {dur}"
