import streamlit as st
from dotenv import load_dotenv
import os

from nlp.extractor import extract_intent, handle_confirmation
from maps.places import resolve_location
from maps.directions import get_route
from voice.stt import transcribe_audio
from utils.formatter import get_conversational_directions
from streamlit_mic_recorder import mic_recorder

# Load environment variables
load_dotenv()

st.set_page_config(page_title="NaviSpeak", page_icon="🗺️", layout="centered")

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
            
        st.write("✨ Formatting directions...")
        final_text = get_conversational_directions(route)
        status.update(label="Route ready!", state="complete", expanded=False)
    
    st.markdown(final_text)
    st.session_state.messages.append({"role": "assistant", "content": final_text})

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

# Layout for chat input and microphone
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
