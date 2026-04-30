import os
import requests

def get_ors_key():
    api_key = os.environ.get("ORS_API_KEY")
    if not api_key:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("ORS_API_KEY is not set in the environment.")
    return api_key

def resolve_location(location_name: str) -> dict:
    if not location_name:
        return None
        
    api_key = get_ors_key()
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": api_key,
        "text": location_name,
        "size": 1
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "features" not in data or not data["features"]:
            return {"error": f"Could not find coordinates for {location_name}"}
            
        feature = data["features"][0]
        lng, lat = feature["geometry"]["coordinates"]
        props = feature["properties"]
        
        return {
            "name": location_name,
            "formatted_address": props.get("label", location_name),
            "lat": lat,
            "lng": lng
        }
    except Exception as e:
        return {"error": str(e)}
