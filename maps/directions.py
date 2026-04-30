import os
import requests

def get_ors_key():
    api_key = os.environ.get("ORS_API_KEY")
    if not api_key:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("ORS_API_KEY is not set in the environment.")
    return api_key

def get_route(origin: dict, destination: dict, preferences: dict = None) -> dict:
    """
    Fetch directions between origin and destination dicts (containing lat, lng).
    """
    if not origin or not destination:
        return {"error": "Origin and destination are required."}
        
    if "error" in origin: return origin
    if "error" in destination: return destination
    
    preferences = preferences or {}
    api_key = get_ors_key()
    
    # ORS expects coordinates as [longitude, latitude]
    start_coords = f"{origin['lng']},{origin['lat']}"
    end_coords = f"{destination['lng']},{destination['lat']}"
    
    url = f"https://api.openrouteservice.org/v2/directions/driving-car"
    params = {
        "api_key": api_key,
        "start": start_coords,
        "end": end_coords
    }
    
    # Process preferences (ORS supports avoiding tolls, highways)
    avoid_features = []
    if preferences.get("avoid_tolls"): avoid_features.append("tollways")
    if preferences.get("avoid_highways"): avoid_features.append("highways")
    
    if avoid_features:
        params["options"] = f'{{"avoid_features":{str(avoid_features).replace("'", '"')}}}'
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            return {"error": data["error"].get("message", "Route error")}
        if "features" not in data or not data["features"]:
            return {"error": "No route found."}
            
        route = data["features"][0]
        segments = route["properties"]["segments"][0]
        
        # Convert distance to readable format
        total_dist_km = segments["distance"] / 1000
        total_dur_min = segments["duration"] / 60
        
        return {
            "distance": f"{total_dist_km:.1f} km",
            "duration": f"{int(total_dur_min)} mins",
            "start_address": origin.get("formatted_address", "Origin"),
            "end_address": destination.get("formatted_address", "Destination"),
            "steps": [
                {
                    "distance": f"{step['distance']} meters",
                    "duration": f"{step['duration']} seconds",
                    "html_instructions": step['instruction'] 
                } for step in segments['steps']
            ],
            "polyline": route['geometry']
        }
    except Exception as e:
        return {"error": str(e)}
