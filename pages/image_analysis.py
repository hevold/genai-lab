
# External importa
import streamlit as st
from openai import OpenAI

# Python imports
import requests
import base64
from PIL import Image
import io
import os
import hmac
from os import environ

# Local imports
from functions.styling import page_config, styling
from functions.menu import menu
import config as c

### CSS AND STYLING

st.logo("images/logo_main.png", icon_image = "images/logo_small.png")

page_config()
styling()

# Check if language is already in session_state, else initialize it with a default value
if 'language' not in st.session_state:
    st.session_state['language'] = "Norsk"  # Default language

st.session_state["pwd_on"] = st.secrets.pwd_on

### PASSWORD

if st.session_state["pwd_on"] == "true":

    def check_password():

        if c.deployment == "streamlit":
            passwd = st.secrets["password"]
        else:
            passwd = environ.get("password")

        def password_entered():

            if hmac.compare_digest(st.session_state["password"], passwd):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
            else:
                st.session_state["password_correct"] = False

        if st.session_state.get("password_correct", False):
            return True

        st.text_input("Lösenord", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("😕 Ooops. Feil passord.")
        return False


    if not check_password():
        st.stop()

### ### ### ###

# Translation

if st.session_state['language'] == "Norsk":
    image_title = "Bildeanalyse"
    image_upload_image = "Last opp bilde"
    image_allowed_formats = "Tillatte formater: PNG, JPG, JPEG"
    image_user_input = "Din melding"
    image_error_upload_image = "Du må laste opp et bilde før du sender."
    image_error_upload_text = "Skriv inn en prompt først."
    image_analyzing = "Analyserer bildet..."
    image_send = "Send"

    
elif st.session_state['language'] == "English":
    image_title = "Image Analysis"
    image_upload_image = "Upload Image"
    image_allowed_formats = "Allowed formats: PNG, JPG, JPEG"
    image_user_input = "Your Message"
    image_error_upload_image = "You must upload an image before submitting."
    image_error_upload_text = "Please enter a prompt first."
    image_analyzing = "Analyzing the image..."
    image_send = "Send"


### SIDEBAR

menu()


# Title of the app
st.markdown(f"### :material/image: {image_title}")

if c.deployment == "streamlit":
    api_key = st.secrets.openai_key
else:
    api_key = environ.get("openai_key")

# Image uploader
uploaded_image = st.file_uploader(
    f"{image_upload_image}",
    type = ["png", "jpg", "jpeg"],
    help = f"{image_allowed_formats}",
)

if uploaded_image:
    st.image(uploaded_image)

# Chat input for user message
user_input = st.text_input(f"{image_user_input}", "")

# If an image is uploaded, store it in the session state
if uploaded_image:
    try:
        # Open the image and convert it if necessary
        image = Image.open(uploaded_image)
        if image.mode == "RGBA":
            image = image.convert("RGB")
        
        # Save image to session state
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        st.session_state['uploaded_image'] = f"data:image/jpeg;base64,{base64_image}"

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


# Send button
if st.button(f":material/send: {image_send}"):
    if 'uploaded_image' not in st.session_state:
        st.error(f"{image_error_upload_image}")
    elif not user_input.strip():
        st.error(f"{image_error_upload_text}")
    else:
        try:
            # Get the base64 image from session state
            data_uri = st.session_state['uploaded_image']

            # Construct the payload for the OpenAI Vision API
            with st.status(f"{image_analyzing}", expanded=True):
                payload = {
                    "model": "gpt-4o",  # Replace with the correct model name if different
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_input},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_uri,
                                    },
                                },
                            ],
                        }
                    ],
                    "max_tokens": 300,
                }

                # Set up headers for the request
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                }

                # Make the POST request to OpenAI's Chat Completions API
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )

                # Check for successful response
                if response.status_code == 200:
                    response_json = response.json()
                    assistant_reply = response_json['choices'][0]['message']['content']
                    st.markdown("__Svar:__")
                    st.write(assistant_reply)
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

st.markdown("# ")
