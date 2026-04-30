# NaviSpeak — Full Project Breakdown

NaviSpeak is a conversational navigation assistant that takes plain English queries (via voice or text), uses Claude API to understand intent and extract locations/preferences, resolves locations to coordinates via Google Places API, fetches routes via Google Directions API, and presents step-by-step directions in a conversational UI using Streamlit.

**V1 Core Feature**: NaviSpeak goes beyond simple mapping by supporting **Partial Routes**. If a user says "I know till X, guide me from there to Y", Claude will extract the known segment and the unknown segment, confirm with the user, and begin live guidance only from point X to point Y.

## User Review Required
> [!IMPORTANT]
> You will need to provide your own API keys for the integrations:
> - **Anthropic API Key**: Required for Claude to handle NLP tasks.
> - **Google Maps API Key**: Required with Google Places API and Google Directions API enabled.
> 
> Once the project structure is ready, you will need to add these to the `.env` file in your workspace.

## Open Questions
> [!NOTE]
> - Do you have the Anthropic and Google Maps API keys ready?
> - For the voice input (`SpeechRecognition`), since it will run in a web browser, we will need a Streamlit audio recorder component (like `streamlit-mic-recorder` or `audorecord`) so that voice input works natively in the web UI. Does this approach sound good to you?

## Proposed Changes

We will build the application in `e:\Navispeak` with the following structure:

### Configuration and Setup
#### [NEW] [requirements.txt](file:///e:/Navispeak/requirements.txt)
Will include `streamlit`, `anthropic`, `googlemaps`, `SpeechRecognition`, `python-dotenv`, and a Streamlit audio recorder package.

#### [NEW] [.env.example](file:///e:/Navispeak/.env.example)
Template for API keys.

#### [NEW] [README.md](file:///e:/Navispeak/README.md)
Documentation for setting up and running the app.

### NLP Brain (Claude API)
#### [NEW] [nlp/extractor.py](file:///e:/Navispeak/nlp/extractor.py)
Handles communication with Claude. Given a query, it will return structured JSON with:
- origin, destination, preferences
- **Partial Route Detection**: Identifying `known_segment` and `guidance_start`
- **Confirmation Flow**: Checking if the user needs to confirm the route before starting navigation (`awaiting_confirmation`)
- Ambiguity detection. 

### Location & Routing (Google Maps APIs)
#### [NEW] [maps/places.py](file:///e:/Navispeak/maps/places.py)
Uses Google Places API to resolve fuzzy location names into exact latitude and longitude coordinates, or complete addresses.

#### [NEW] [maps/directions.py](file:///e:/Navispeak/maps/directions.py)
Uses Google Directions API to fetch the route based on the origin, destination, and user preferences (avoid tolls, highways, etc.).

### Voice Processing
#### [NEW] [voice/stt.py](file:///e:/Navispeak/voice/stt.py)
Uses the `SpeechRecognition` library to transcribe voice input (audio files or raw bytes from the browser) into text.

### Utilities
#### [NEW] [utils/formatter.py](file:///e:/Navispeak/utils/formatter.py)
Takes the raw JSON steps from Google Directions and formats them into a conversational, easy-to-read list, optionally using Claude to make them sound natural.

### Frontend UI (Streamlit)
#### [NEW] [app.py](file:///e:/Navispeak/app.py)
The main entry point. Will feature a chat-like UI, process user input (text or mic), orchestrate the flow across all components, and display the final conversational directions and map.

## Verification Plan
### Automated Tests
We will initially run simple unit test functions to verify:
1. Claude extraction outputs correct JSON.
2. Places API returns valid responses.
3. Directions API returns a valid route based on coordinates.
4. Voice STT transcribes sample audio correctly.

### Manual Verification
- Run `streamlit run app.py`.
- Type "Take me from Koregaon Park to Shivajinagar, avoid tolls".
- Observe the extraction, routing, and final conversational steps in the UI.
- **Partial Route Test**: Type "I know till Koregaon Park, guide me from there to Baner". Ensure it asks for confirmation before showing the route from Koregaon Park.
- Test ambiguity handling: type an ambiguous place and observe if the assistant asks a follow-up question.
- Test voice input using the Streamlit mic component.

## Future Roadmap (Beyond V1)
- **Level 2 (Smart Context)**: Multi-stop routes, memory across sessions, landmark-based routing.
- **Level 3 (Personalization)**: Saved places, commute patterns, preference learning.
- **Level 4 (Multimodal)**: Voice readouts, image input, chat app bot integration.
- **Level 5 (Product-level)**: Hyperlocal AI navigation for Indian users with vernacular support (local languages, community landmarks).
