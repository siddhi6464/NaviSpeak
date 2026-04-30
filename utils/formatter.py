import re
from nlp.extractor import get_anthropic_client

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
    Takes route data and uses Claude to summarize it in a conversational tone.
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
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        # Fallback if Claude fails
        return f"**Route ({route_data.get('distance')}, {route_data.get('duration')}):**\n\n" + raw_text
