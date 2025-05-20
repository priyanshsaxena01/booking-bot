# Cityscope - AI Powered Trip Planner Chatbot

## Project Overview

This project is an AI-powered chatbot integrated into a web page to simulate a travel experience booking flow for "Cityscope," a fictional local guide and marketplace platform. The chatbot engages users in a natural conversation to collect travel details (name, city, travel dates/times, experience preferences) and then generates a redirect URL to a booking summary page with the user's data pre-filled.

The primary goal was to demonstrate capabilities in working with Large Language Models (LLMs via Together AI), frontend-backend communication (Flask, HTML, JavaScript), and dynamic data transfer between systems.

**Video Demo:** [[Link to Video](https://www.loom.com/share/4fe980ac3f794577b3c5a0113700e6f5?sid=4a1503c3-f0c4-4659-9d3c-2a0c1392c713)]

## Features

*   **Conversational AI Chatbot:**
    *   Utilizes an LLM (e.g., Llama 3 70B via Together AI) for natural language understanding and response generation.
    *   Collects user details for trip planning:
        *   Full Name
        *   City of Travel
        *   Arrival Date & Time
        *   Departure Date & Time
        *   Preferred Experience Type/Details
    *   Maintains conversation state using server-side sessions.
    *   Handles potential API errors gracefully.
*   **Dynamic Booking Summary Page:**
    *   A simple, aesthetically pleasing web page displaying a summary of the collected trip details.
    *   Form fields are automatically pre-filled using data passed in the URL query parameters.
    *   Allows users to "edit" details on the client-side (changes are not persisted in this demo).
*   **Seamless Integration:**
    *   The chatbot generates a redirect link to the booking summary page.
    *   Data is transferred securely and efficiently via URL query parameters.
*   **User Interface:**
    *   Clean, modern, and responsive UI for both the chatbot and the booking summary page, inspired by a "Cityscope" brand aesthetic.
    *   Chat history is cleared on new visits to the main chat page for a fresh experience.

## Tech Stack

*   **Backend:**
    *   Python 3.10+
    *   Flask (Web framework)
    *   Python-dotenv (Environment variable management)
*   **LLM Provider:**
    *   Together AI (for LLM inference, specifically Llama 3 models)
    *   `together-python` SDK
*   **Frontend:**
    *   HTML5
    *   CSS3 (with modern styling techniques)
    *   JavaScript (Vanilla JS for interactivity and API communication)
    *   Jinja2 (Templating engine with Flask)
    *   Google Fonts (Poppins)

## Setup and Installation

**Prerequisites:**

*   Python 3.10 or higher
*   `pip` (Python package installer)
*   A Together AI API Key

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone [URL of your GitHub repository]
    cd [repository-name]
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    *   Create a `.env` file in the project root directory by copying `.env.example` (if you provide one) or creating it manually.
    *   Add your API keys and secrets to the `.env` file:
        ```env
        TOGETHER_API_KEY="your_together_ai_api_key_here"
        FLASK_SECRET_KEY="a_very_strong_random_secret_key_for_flask_sessions"
        # Optional: PORT=5001 (if you want to specify a port other than default)
        ```
    *   Replace placeholders with your actual values. Generate a strong `FLASK_SECRET_KEY`.

5.  **Run the Flask Application:**
    ```bash
    python app.py
    ```

6.  **Access the Application:**
    *   Open your web browser and navigate to `http://127.0.0.1:5001` (or the port specified if you changed it).

**(If using GitHub Codespaces):**
*   The environment should be pre-configured by the `.devcontainer/devcontainer.json` file.
*   Dependencies will be installed automatically via `postCreateCommand`.
*   You will still need to create the `.env` file manually within the Codespace and add your API keys.
*   The application will be accessible via a forwarded port URL provided by Codespaces.

## Usage Flow

1.  Navigate to the main chat page.
2.  The CityBot will greet you and ask for your name.
3.  Engage in a natural conversation, providing details about your desired trip:
    *   City of travel
    *   Arrival and departure dates/times
    *   Your preferences for local experiences (e.g., "food tours," "museum visits," "local music events").
4.  Once all necessary details are collected, the chatbot will confirm them and provide a redirect link.
5.  Click the link to open the "Trip Summary" page, where your collected data will be pre-filled.
6.  On the summary page, you can optionally click "Edit Details" to make client-side modifications (these are not saved back to any server in this demo).

## Key Learnings & Challenges

*   **LLM Prompt Engineering:** Crafting effective system prompts to guide the LLM's conversational flow, data extraction format (JSON), and persona.
*   **State Management:** Using Flask server-side sessions to maintain conversation history and extracted booking data.
*   **Frontend-Backend Communication:** Implementing AJAX calls from the frontend JavaScript to the Flask backend for chat interaction.
*   **Dynamic URL Generation:** Creating redirect URLs with query parameters and ensuring they work correctly, especially in a Codespaces environment with port forwarding.
*   **Error Handling:** Implementing robust error handling for API calls to the LLM service and for unexpected issues within the application.
*   **UI/UX Design:** Focusing on creating a clean, user-friendly, and aesthetically consistent interface for both the chat and summary pages.
*   **SDK Versioning:** Adapting to potential differences in SDK error structures if specific versions are not well-documented.

## Future Enhancements (Potential)

*   **Actual Booking Integration:** Connect to mock or real booking APIs.
*   **Database Storage:** Persist user conversations and booking details in a database.
*   **User Authentication:** Allow users to sign in and view past trip plans.
*   **Advanced RAG:** Integrate a more sophisticated Retrieval Augmented Generation system for answering complex queries about specific cities or experiences.
*   **Date/Time Picker UI:** Implement a visual date/time picker instead of relying purely on text input.
