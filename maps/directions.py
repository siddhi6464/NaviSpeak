import os
import googlemaps

def get_gmaps_client():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set in the environment.")
    return googlemaps.Client(key=api_key)

def get_route(origin: dict, destination: dict, preferences: dict = None) -> dict:
    """
    Fetch directions between origin and destination dicts (containing lat, lng).
    """
    if not origin or not destination:
        return {"error": "Origin and destination are required."}
        
    if "error" in origin: return origin
    if "error" in destination: return destination
    
    preferences = preferences or {}
    gmaps = get_gmaps_client()
    
    # Process preferences
    avoid = []
    if preferences.get("avoid_tolls"): avoid.append("tolls")
    if preferences.get("avoid_highways"): avoid.append("highways")
    
    origin_coords = f"{origin['lat']},{origin['lng']}"
    dest_coords = f"{destination['lat']},{destination['lng']}"
    
    try:
        directions_result = gmaps.directions(
            origin_coords,
            dest_coords,
            mode="driving",
            avoid="|".join(avoid) if avoid else None,
            departure_time="now" if preferences.get("avoid_traffic") else None
        )
        
        if not directions_result:
            return {"error": "No route found."}
            
        route = directions_result[0]
        legs = route['legs'][0]
        
        return {
            "distance": legs['distance']['text'],
            "duration": legs['duration']['text'],
            "start_address": legs['start_address'],
            "end_address": legs['end_address'],
            "steps": [
                {
                    "distance": step['distance']['text'],
                    "duration": step['duration']['text'],
                    "html_instructions": step['html_instructions']
                } for step in legs['steps']
            ],
            "polyline": route['overview_polyline']['points']
        }
    except Exception as e:
        return {"error": str(e)}
