
# External imports
import streamlit as st
from llama_index.core.llms import ChatMessage
from openai import OpenAI
from groq import Groq

# Python imports
import hmac
import os
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
    chat_prompt = "Du er en hjelpsom AI-assistent. Svar på brukerens spørsmål."
    chat_clear_chat = "Tøm chat"
    chat_hello = "Hei! Hvordan kan jeg hjelpe deg?"
    chat_settings = "Innstillinger"
    chat_choose_llm = "Velg språkmodell"
    chat_choose_temp = "Temperatur"
    chat_system_prompt = "Systemprompt"
    chat_save = "Lagre"
    chat_imput_q = "Hva vil du snakke om?"


elif st.session_state['language'] == "English":
    chat_prompt = "You are a helpful AI assistant. Answer the user’s questions."
    chat_clear_chat = "Clear chat"
    chat_hello = "Hi! How can I help you?"
    chat_settings = "Settings"
    chat_choose_llm = "Choose language model"
    chat_choose_temp = "Temperature"
    chat_system_prompt = "System prompt"
    chat_save = "Save"
    chat_imput_q = "What do you want to talk about?"


prompt = f"{chat_prompt}"


if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = prompt


# Check and set default values if not set in session_state
if "llm_temperature" not in st.session_state:
    st.session_state["llm_temperature"] = 0.7
if "llm_chat_model" not in st.session_state:
    st.session_state["llm_chat_model"] = "OpenAI GPT-4o"


### SIDEBAR

menu()


### MAIN PAGE

col1, col2 = st.columns(2)

with col1:
    if st.button(f"{chat_clear_chat}", type="secondary"):
        if "messages" in st.session_state.keys(): # Initialize the chat message history
            st.session_state.messages = [
                {"role": "assistant", "content": f"""
                    {chat_hello}
                 """}
        ]

with col2:
    with st.expander(f"{chat_settings}"):
        llm_model = st.selectbox(
            f"{chat_choose_llm}", 
            ["LLaMa3.1 8B", "LLaMa3 8B", "OpenAI GPT-4o", "OpenAI GPT-4o mini", "OpenAI o1-preview", "OpenAI o1-mini"],
            index=["LLaMa3.1 8B", "LLaMa3 8B", "OpenAI GPT-4o", "OpenAI GPT-4o mini", "OpenAI o1-preview", "OpenAI o1-mini"].index(st.session_state["llm_chat_model"]),
        )

        llm_temp = st.slider(
            f"{chat_choose_temp}",
            min_value = 0.0,
            max_value = 1.0,
            step = 0.1,
            value = st.session_state["llm_temperature"],
        )

        # Update the session_state directly
        st.session_state["llm_chat_model"] = llm_model
        st.session_state["llm_temperature"] = llm_temp
        
        model_map = {
            "OpenAI GPT-4o": "gpt-4o",
            "OpenAI GPT-4o mini": "gpt-4o-mini",
            "LLaMa3 8B": "llama3-8b-8192", 
            "LLaMa3.1 8B": "llama-3.1-8b-instant",
            "OpenAI o1-preview": "o1-preview", 
            "OpenAI o1-mini": "o1-mini"
        }

        st.markdown("###### ")

        with st.form("my_form"):
            prompt_input = st.text_area(f"{chat_system_prompt}", prompt, height=200)
            st.session_state.system_prompt = prompt_input   
            st.form_submit_button(f"{chat_save}") 


if "OpenAI" in st.session_state["llm_chat_model"]:
    st.sidebar.success("Språkmodell: " + llm_model)
else:
    st.sidebar.success("Språkmodell: " + llm_model)


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"{chat_hello}"}]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if the content is an image URL
        if message["content"].startswith("http"):
            st.image(message["content"])
        else:
            st.markdown(message["content"])


# Define your system prompt here
system_prompt = st.session_state.system_prompt

if prompt := st.chat_input(f"{chat_imput_q}"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Preprocess messages to include the system prompt
        processed_messages = []
        for m in st.session_state.messages:
            # Prepend system prompt to the user's message
            if m["role"] == "user":
                content_with_prompt = system_prompt + " " + m["content"]
                processed_messages.append({"role": m["role"], "content": content_with_prompt})
            else:
                processed_messages.append(m)

        if "OpenAI" in st.session_state["llm_chat_model"]:

            if c.deployment == "streamlit":
                client = OpenAI(api_key = st.secrets.openai_key)
            else:
                client = OpenAI(api_key = environ.get("openai_key"))
    
            for response in client.chat.completions.create(
                model = model_map[st.session_state["llm_chat_model"]],
                temperature = st.session_state["llm_temperature"],
                messages = processed_messages,
                stream = True,
            ):
                if response.choices[0].delta.content:
                    full_response += str(response.choices[0].delta.content)
                message_placeholder.markdown(full_response + "▌")  
             
        else:

            if c.deployment == "streamlit":
                client = Groq(api_key = st.secrets.groq_key)
            else:
                client = Groq(api_key = environ.get("groq_key"))

            # Remove 'avatar' key for Groq messages
            processed_messages_no_avatar = [{"role": m["role"], "content": m["content"]} for m in processed_messages]
            stream = client.chat.completions.create(
                messages=processed_messages_no_avatar,
                model=model_map[st.session_state["llm_chat_model"]],
                temperature=st.session_state["llm_temperature"],
                max_tokens=1024,
                top_p=1,
                stop=None,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += str(chunk.choices[0].delta.content)
                message_placeholder.markdown(full_response + "▌")
                
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
