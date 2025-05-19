import os
import json
import re
from flask import Flask, render_template, request, jsonify, url_for, session
from dotenv import load_dotenv
from urllib.parse import urlencode
import logging

# Only import 'Together' directly from the 'together' package
from together import Together
# Import requests for its specific exceptions, as the SDK might not wrap all network issues
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_very_secure_default_secret_key_for_cityscope_demo")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")

# Instantiate the Together client
try:
    if not TOGETHER_API_KEY:
        raise ValueError("TOGETHER_API_KEY environment variable not set.")
    client = Together(api_key=TOGETHER_API_KEY)
except ValueError as e:
    logging.critical(f"Failed to initialize Together client: {e}")
    client = None

LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free" # Or your preferred Llama 3 model like "meta-llama/Llama-3-70b-chat-hf"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_system_prompt():
    # Updated System Prompt for Cityscope Travel Experience Booking
    return """
You are "CityBot", a friendly and enthusiastic travel experience assistant for Cityscope.
Your goal is to help users plan and get details for exciting local experiences in their city of travel.
You need to collect the following information:
1.  User's Full Name (string, key: "name")
2.  City of Travel (string, key: "city")
3.  Arrival Date (string, key: "arrival_date", e.g., "July 15th, 2024", "next Monday")
4.  Arrival Time (string, key: "arrival_time", e.g., "around 2 PM", "evening")
5.  Departure Date (string, key: "departure_date")
6.  Departure Time (string, key: "departure_time")
7.  Preferred Experience Type/Details (string, key: "experience_details", e.g., "local events", "masterclasses", "cultural encounters", "just want to explore", "food tour")

You MUST respond in a JSON format. The JSON object should have two top-level keys:
- "response_to_user": (String) Your conversational reply to the user.
- "extracted_data": (Object) Contains the data you have extracted so far. It MUST include all keys: "name", "city", "arrival_date", "arrival_time", "departure_date", "departure_time", "experience_details". Use null if a piece of information has not been collected yet.

Interaction Flow:
1.  Greet the user warmly, introduce yourself as CityBot from Cityscope. Ask for their name to get started with planning their city adventure. Example: "Welcome to Cityscope! I'm CityBot, your guide to amazing local experiences. To help you plan your trip, could I get your name?"
2.  Politely ask for one missing piece of information at a time, prioritizing: name -> city -> arrival_date -> arrival_time -> departure_date -> departure_time -> experience_details.
3.  Acknowledge information provided. If multiple pieces are given, acknowledge all.
4.  Once all seven pieces of information are collected (non-null in "extracted_data"):
    - Your "response_to_user" should confirm all details enthusiastically (e.g., "Awesome, [Name]! Got all your travel plans for [City] from [Arrival Date] at [Arrival Time] until [Departure Date] at [Departure Time], and you're interested in [Experience Details]. I'm generating a link with your trip summary!").
    - The backend will then generate the redirect link.
5.  If the user wants to change information, update it in "extracted_data" and confirm.
6.  Cityscope helps people discover and book experiences, services, and activities. Experiences include local events, captivating masterclasses, and immersive cultural encounters. Keep this in mind if they ask what they can do, and you can suggest these categories if they are unsure about "experience_details".

Conversation Guidelines:
- Be upbeat, friendly, and helpful. Use travel-related language.
- Be concise but clear.
- Do not ask for information you already have (value is not null in `extracted_data`) unless the user wants to change it.

Current travel plan data (from previous turns, if any, otherwise all null):
{{{{current_booking_data_json}}}}

Your response MUST be a single well-formed JSON object and nothing else.
"""

def call_together_ai(messages_history, current_booking_data):
    global client
    if client is None:
        logger.error("Together AI client is not initialized (API Key missing?).")
        raise ValueError("AI Service client not initialized.") # Will be caught by /chat

    system_prompt_template = get_system_prompt()
    system_prompt_filled = system_prompt_template.replace(
        "{{{{current_booking_data_json}}}}", json.dumps(current_booking_data)
    )

    current_messages = [{"role": "system", "content": system_prompt_filled}]
    for msg in messages_history:
        if msg.get("role") != "system":
            current_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = {
        "model": LLM_MODEL,
        "messages": current_messages,
        "temperature": 0.6,
        "max_tokens": 550, # Allow for longer confirmation and JSON
        "response_format": {"type": "json_object"}
    }
    
    response_obj = None # Initialize for use in except block if request fails before assignment
    try:
        logger.info(f"Sending payload to Together AI: {LLM_MODEL}")
        response_obj = client.chat.completions.create(**payload)
        
        logger.info(f"Raw LLM SDK response object: {response_obj}")
        llm_content_str = response_obj.choices[0].message.content
        
        try:
            parsed_content = json.loads(llm_content_str)
        except json.JSONDecodeError:
            logger.warning(f"Initial JSON parse failed for LLM content: {llm_content_str}")
            match = re.search(r"```json\s*([\s\S]*?)\s*```|({[\s\S]*})", llm_content_str)
            if match:
                json_str = match.group(1) or match.group(2)
                try:
                    parsed_content = json.loads(json_str)
                    logger.info(f"Successfully parsed extracted JSON: {json_str}")
                except json.JSONDecodeError as e_inner:
                    raise ValueError("LLM did not return valid JSON despite extraction attempt.") from e_inner
            else:
                raise ValueError("No JSON object found in LLM response.")
        
        # Validate core structure
        if "response_to_user" not in parsed_content or "extracted_data" not in parsed_content:
            raise ValueError("LLM JSON response missing 'response_to_user' or 'extracted_data'.")

        # Ensure extracted_data has all required keys, defaulting to None if missing from LLM
        required_keys = ["name", "city", "arrival_date", "arrival_time", "departure_date", "departure_time", "experience_details"]
        validated_extracted_data = {key: parsed_content["extracted_data"].get(key) for key in required_keys}
        parsed_content["extracted_data"] = validated_extracted_data
        
        logger.info(f"Successfully parsed and validated LLM content: {parsed_content}")
        return parsed_content

    except requests.exceptions.Timeout as e:
        logger.error(f"Underlying HTTP Request Timeout: {e}")
        raise TimeoutError("Network request to AI Service timed out.") from e
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Underlying HTTP Connection Error: {e}")
        raise ConnectionError("Failed to connect to AI Service (network issue).") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e: # Parsing errors for LLM response
        logger.error(f"Error processing LLM response: {e}. Response object: {response_obj if response_obj else 'N/A'}")
        raise ValueError(f"Invalid or malformed response from LLM: {str(e)}")
    except Exception as e: # Catch any other exception, then check if it's from Together SDK
        module_name = getattr(e, '__module__', '')
        if module_name and ('together' in module_name): # Check if it's an error from the 'together' package
            logger.error(f"Together AI SDK Error: {e} (Type: {type(e).__name__}, Module: {module_name})")
            status_code = getattr(e, 'status_code', None) # Standard attribute for HTTP errors in SDKs
            message_from_sdk = str(e)
            custom_message = f"AI Service Error: {message_from_sdk}" # Default
            if status_code: # Map status codes to user-friendly messages
                if status_code == 400: custom_message = "Invalid request to AI service (misconfigured request)."
                elif status_code == 401: custom_message = "Authentication error with AI service (check API Key)."
                elif status_code == 402: custom_message = "Payment required for AI service (account issue or spending limit)."
                elif status_code == 403: custom_message = "Request forbidden by AI service (input token limit or permissions)."
                elif status_code == 404: custom_message = "AI model or endpoint not found."
                elif status_code == 429: custom_message = "AI service rate limit hit. Please try again shortly."
                elif status_code == 500: custom_message = "AI server error. Please try again later."
                elif status_code == 503: custom_message = "AI engine overloaded. Please try again later."
                else: custom_message = f"AI Service API Error (Status: {status_code}): {message_from_sdk}"
            raise ValueError(custom_message) from e
        else: # If it's not from 'together' and not one of the other specific ones, it's truly unexpected
            logger.error(f"Unexpected error calling Together AI or processing its response: {e}", exc_info=True)
            raise RuntimeError(f"An unexpected issue occurred: {str(e)}") from e

@app.route('/')
def home():
    session.pop('conversation_history', None)
    session.pop('booking_data', None)
    logger.info("Session cleared for new visit to home page.")

    session['conversation_history'] = []
    session['booking_data'] = {
        "name": None, "city": None, 
        "arrival_date": None, "arrival_time": None,
        "departure_date": None, "departure_time": None,
        "experience_details": None
    }
    
    initial_bot_message = "Welcome to Cityscope! I'm CityBot, your guide to amazing local experiences. To help you plan your trip, could I get your name?"
    
    session['conversation_history'].append({"role": "assistant", "content": initial_bot_message})
    session.modified = True
    
    return render_template('chat.html', history=session['conversation_history'])

@app.route('/booking-page')
def booking_page_route():
    return render_template('booking.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if client is None: # Check if client was initialized
        error_message = "AI Service is currently unavailable (configuration error). Please try again later."
        logger.error(error_message)
        session.setdefault('conversation_history', []).append({"role": "assistant", "content": error_message})
        session.modified = True
        return jsonify({"reply": error_message, "error_details": "AI client not initialized"}), 503

    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Retrieve current session data or initialize if somehow missing
    conversation_history = session.get('conversation_history', [])
    current_booking_data = session.get('booking_data', {
        "name": None, "city": None, "arrival_date": None, "arrival_time": None,
        "departure_date": None, "departure_time": None, "experience_details": None
    })
    conversation_history.append({"role": "user", "content": user_input})

    error_message = "An unexpected internal error occurred. Please try again." # Default error message
    status_code_for_error = 500 # Default status code

    try:
        llm_response_data = call_together_ai(conversation_history, current_booking_data)
        
        bot_reply_text = llm_response_data.get("response_to_user", "I'm having a little trouble processing that. Could you try rephrasing?")
        extracted_data_from_llm = llm_response_data.get("extracted_data", {})

        # Update session booking_data robustly
        for key in current_booking_data.keys():
            if key in extracted_data_from_llm: # Check if LLM provided the key
                 current_booking_data[key] = extracted_data_from_llm[key] # Update with LLM's value (even if null)
        
        all_data_collected = all(current_booking_data.get(key) is not None for key in current_booking_data.keys())

        redirect_url = None
        if all_data_collected:
            logger.info("All data collected, generating redirect URL.")
            query_params = {k: v for k, v in current_booking_data.items() if v is not None}
            
            codespace_name = os.environ.get("CODESPACE_NAME")
            forwarding_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
            app_port = str(os.environ.get('PORT', 5001)) # Get port from env or default

            if codespace_name and forwarding_domain:
                path_to_booking_page = url_for('booking_page_route')
                final_redirect_base = f"https://{codespace_name}-{app_port}.{forwarding_domain}{path_to_booking_page}"
            else:
                final_redirect_base = url_for('booking_page_route', _external=True, _scheme='http')

            redirect_url = f"{final_redirect_base}?{urlencode(query_params)}"
            
            if redirect_url and "http" not in bot_reply_text: 
                bot_reply_text += f" Your trip summary link is ready: {redirect_url}"

        conversation_history.append({"role": "assistant", "content": bot_reply_text})
        
        session['conversation_history'] = conversation_history
        session['booking_data'] = current_booking_data
        session.modified = True

        return jsonify({
            "reply": bot_reply_text,
            "extracted_data": current_booking_data,
            "redirect_url": redirect_url
        })

    except ValueError as ve: # Catches our custom ValueErrors from call_together_ai
        error_message = str(ve)
        logger.error(f"ValueError in /chat (from AI call or parsing): {ve}")
    except TimeoutError as te:
        error_message = "Sorry, the request to the AI service timed out. Please try again."
        logger.error(f"TimeoutError in /chat: {te}")
        status_code_for_error = 503
    except ConnectionError as ce:
        error_message = "Sorry, I couldn't connect to the AI service. Please check your connection or try again later."
        logger.error(f"ConnectionError in /chat: {ce}")
        status_code_for_error = 503
    except RuntimeError as rte: # Catches our custom RuntimeErrors from call_together_ai
        error_message = str(rte)
        logger.error(f"RuntimeError in /chat (unexpected AI issue): {rte}")
    except Exception as e: # General fallback for other unexpected errors in this endpoint
        logger.error(f"Truly unexpected error in /chat endpoint: {e}", exc_info=True)
        # error_message remains the default "An unexpected internal error occurred..."

    # Common error response pathway
    session.setdefault('conversation_history', []).append({"role": "assistant", "content": error_message})
    session.modified = True
    return jsonify({"reply": error_message, "error_details": error_message}), status_code_for_error


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))