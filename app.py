import streamlit as st
from dotenv import load_dotenv
import os

from nlp.extractor import extract_intent, handle_confirmation
from maps.places import resolve_location
from maps.directions import get_route
from voice.stt import transcribe_audio
from utils.formatter import get_conversational_directions, get_route_summary
from streamlit_mic_recorder import mic_recorder
import pydeck as pdk
import streamlit.components.v1 as components
import json

# Load environment variables
load_dotenv()

st.set_page_config(page_title="NaviSpeak", page_icon="🗺️", layout="centered")

# --- UI Premium CSS: Glassmorphism & Dark Mode ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

.stApp {
    background: radial-gradient(circle at bottom left, #1b1e2b 0%, #0d1117 100%);
    color: #e6edf3;
    font-family: 'Outfit', sans-serif;
}
.stChatMessage {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3) !important;
    margin-bottom: 16px;
}
.stChatInputContainer {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
h1, h2, h3 {
    background: -webkit-linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.title("🗺️ NaviSpeak")
st.markdown("Your Conversational Navigation Assistant. Type or speak your destination!")

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "state" not in st.session_state:
    st.session_state.state = {"status": "idle"}

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Render map if it exists in history
        if message.get("map_coords"):
            coords = message["map_coords"]
            lats = [c[1] for c in coords]
            lngs = [c[0] for c in coords]
            layer = pdk.Layer("PathLayer", data=[{"path": coords, "color": [0, 242, 254]}], get_color="color", width_min_pixels=5, get_path="path")
            view_state = pdk.ViewState(latitude=sum(lats)/len(lats), longitude=sum(lngs)/len(lngs), zoom=12, pitch=45)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

def do_routing(origin_str, dest_str, prefs):
    if not origin_str or not dest_str:
        msg = "I need both an origin and destination to route you."
        st.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})
        return
        
    with st.status("Planning your route...", expanded=True) as status:
        st.write(f"📍 Resolving coordinates for {origin_str} and {dest_str}...")
        origin_loc = resolve_location(origin_str)
        dest_loc = resolve_location(dest_str)
        
        if not origin_loc or "error" in origin_loc:
            st.error(origin_loc.get("error", "Failed to resolve origin.")); return
        if not dest_loc or "error" in dest_loc:
            st.error(dest_loc.get("error", "Failed to resolve destination.")); return
            
        st.write("🚗 Fetching the best route...")
        route = get_route(origin_loc, dest_loc, prefs)
        
        if not route or "error" in route:
            st.error(route.get("error", "Failed to get route.")); return
            
        st.write("✨ Rendering map...")
        summary_text = get_route_summary(route)
        status.update(label="Route ready for preview!", state="complete", expanded=False)
    
    st.markdown(summary_text)
    
    # Render Interactive PyDeck Map
    polyline_coords = route.get("polyline", {}).get("coordinates", [])
    if polyline_coords:
        lats = [c[1] for c in polyline_coords]
        lngs = [c[0] for c in polyline_coords]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)
        
        layer = pdk.Layer(
            "PathLayer",
            data=[{"path": polyline_coords, "color": [0, 242, 254]}],
            get_color="color",
            width_min_pixels=5,
            get_path="path",
        )
        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lng, zoom=12, pitch=45)
        map_deck = pdk.Deck(layers=[layer], initial_view_state=view_state)
        
        st.pydeck_chart(map_deck)
        
    # Save to history including the map
    st.session_state.messages.append({
        "role": "assistant", 
        "content": summary_text, 
        "map_coords": polyline_coords
    })
    
    # Transition to preview state
    st.session_state.state = {"status": "preview_route", "route": route}
    st.rerun()

def process_query(query: str):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
        
    with st.chat_message("assistant"):
        # Check if we are awaiting confirmation for a partial route
        if st.session_state.state["status"] == "awaiting_confirmation":
            with st.spinner("Processing..."):
                res = handle_confirmation(query, st.session_state.state["data"])
                if "error" in res:
                    st.error(res["error"])
                    return
                    
                if res.get("confirmed"):
                    msg = "Great! Starting navigation."
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    
                    origin_str = res.get("guidance_start")
                    dest_str = res.get("destination")
                    prefs = res.get("preferences", {})
                    
                    st.session_state.state = {"status": "idle"}
                    do_routing(origin_str, dest_str, prefs)
                else:
                    msg = "Okay, navigation cancelled. Where would you like to go instead?"
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    st.session_state.state = {"status": "idle"}
            return
            
        # Check if we are in preview mode
        if st.session_state.state["status"] == "preview_route":
            if "start" in query.lower() or "yes" in query.lower():
                route = st.session_state.state["route"]
                st.session_state.state = {"status": "navigating", "route": route}
                st.rerun()
                return
            else:
                # User typed something else, cancel preview and process as new intent
                st.session_state.state = {"status": "idle"}
                
        # Idle state - Extract new intent
        with st.spinner("Understanding..."):
            intent = extract_intent(query)
            
            if "error" in intent:
                st.error(intent["error"])
                return
                
            if intent.get("ambiguous"):
                msg = intent.get("follow_up", "Can you please clarify?")
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                return
                
            if intent.get("awaiting_confirmation"):
                msg = intent.get("confirmation_message", "Should I start navigation?")
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.session_state.state = {"status": "awaiting_confirmation", "data": intent}
                return
                
            # Standard routing immediately
            origin_str = intent.get("origin") or intent.get("guidance_start")
            dest_str = intent.get("destination")
            prefs = intent.get("preferences", {})
            
        do_routing(origin_str, dest_str, prefs)

# Layout for Start Navigation Button
if st.session_state.state["status"] == "preview_route":
    st.write("")
    if st.button("📍 Start Navigation", use_container_width=True, type="primary"):
        route = st.session_state.state["route"]
        st.session_state.state = {"status": "navigating", "route": route}
        st.rerun()

# Layout for Live Navigation
if st.session_state.state["status"] == "navigating":
    route = st.session_state.state["route"]
    polyline_coords = route.get("polyline", {}).get("coordinates", [])
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ height: 600px; width: 100%; border-radius: 16px; margin-top: 10px; }}
            body {{ margin: 0; padding: 0; background: transparent; }}
            .nav-status {{
                position: absolute;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 1000;
                background: rgba(13, 17, 23, 0.85);
                color: #00f2fe;
                padding: 10px 20px;
                border-radius: 20px;
                font-family: 'Outfit', sans-serif;
                font-weight: 600;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        </style>
    </head>
    <body>
        <div id="status" class="nav-status">Waiting for GPS...</div>
        <div id="map"></div>
        <script>
            var route = {json.dumps(polyline_coords)};
            var latlngs = route.map(c => [c[1], c[0]]);
            
            var map = L.map('map').setView(latlngs[0], 15);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; OpenStreetMap &copy; CARTO'
            }}).addTo(map);

            var polyline = L.polyline(latlngs, {{color: '#00f2fe', weight: 6, opacity: 0.8}}).addTo(map);
            map.fitBounds(polyline.getBounds());

            var userMarker = L.circleMarker(latlngs[0], {{
                color: '#ff2a5f',
                fillColor: '#ff2a5f',
                fillOpacity: 1,
                radius: 8,
                weight: 2
            }}).addTo(map);

            if ("geolocation" in navigator) {{
                navigator.geolocation.watchPosition(function(position) {{
                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    
                    userMarker.setLatLng([lat, lng]);
                    map.panTo([lat, lng]);
                    
                    document.getElementById('status').innerText = "Live Tracking Active 📍";
                }}, function(error) {{
                    document.getElementById('status').innerText = "GPS Error: " + error.message;
                    console.error("GPS Error: ", error);
                }}, {{
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 5000
                }});
            }} else {{
                document.getElementById('status').innerText = "GPS Not Supported";
            }}
        </script>
    </body>
    </html>
    """
    
    st.markdown("### Live Navigation 📍")
    st.write("Please grant Location permissions in your browser. The red dot will track your physical movement!")
    components.html(html_code, height=650)
    
    if st.button("🛑 Stop Navigation", type="secondary", use_container_width=True):
        st.session_state.state = {"status": "idle"}
        st.rerun()

# Layout for chat input and microphone
if st.session_state.state["status"] != "navigating":
    col1, col2 = st.columns([0.9, 0.1])

with col1:
    user_input = st.chat_input("Type your destination...")

with col2:
    # Adding some top margin to align the mic button nicely with the chat input
    st.write("") 
    audio = mic_recorder(start_prompt="🎙️", stop_prompt="🛑", key="mic")

    if user_input:
        process_query(user_input)

    # We check if audio was recorded and hasn't been processed yet
    if audio and audio.get("bytes"):
        # Since the component re-renders with the same bytes sometimes, 
        # we use session state to ensure we only process an audio clip once.
        audio_id = audio.get("id")
        if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_id:
            st.session_state.last_audio_id = audio_id
            with st.spinner("Transcribing..."):
                text = transcribe_audio(audio["bytes"])
                if text:
                    process_query(text)
                else:
                    st.warning("Could not understand the audio. Please try again.")
