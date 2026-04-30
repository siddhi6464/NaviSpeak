import os
import googlemaps

def get_gmaps_client():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set in the environment.")
    return googlemaps.Client(key=api_key)

def resolve_location(location_name: str) -> dict:
    """
    Given a fuzzy location name, return its exact coordinates and formatted address.
    """
    if not location_name:
        return None
        
    gmaps = get_gmaps_client()
    try:
        geocode_result = gmaps.geocode(location_name)
        if not geocode_result:
            return {"error": f"Could not find coordinates for {location_name}"}
            
        location = geocode_result[0]
        return {
            "name": location_name,
            "formatted_address": location.get("formatted_address"),
            "lat": location["geometry"]["location"]["lat"],
            "lng": location["geometry"]["location"]["lng"]
        }
    except Exception as e:
        return {"error": str(e)}
