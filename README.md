# NaviSpeak

NaviSpeak is a conversational navigation assistant that takes plain English queries (via voice or text), uses the Groq API (Llama 3) to understand intent and extract locations/preferences, resolves locations to coordinates via Google Places API, fetches routes via Google Directions API, and presents step-by-step directions in a conversational UI using Streamlit.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example` and add your API keys:
```bash
cp .env.example .env
```
Ensure you provide:
- `GROQ_API_KEY`
- `GOOGLE_MAPS_API_KEY` (must have Places and Directions API enabled)

3. Run the application:
```bash
streamlit run app.py
```
