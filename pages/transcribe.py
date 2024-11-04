
# Python imports
import os
from os import environ
from datetime import datetime
import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor

# External imports
import streamlit as st
from openai import OpenAI
#from audiorecorder import audiorecorder
import tiktoken

# Local imports
from functions.transcribe import transcribe_with_whisper_openai
import config as c
from functions.split_audio import split_audio_to_chunks
from functions.styling import page_config, styling
from functions.menu import menu

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

############

# Translation
if st.session_state['language'] == "Norsk":
    page_name = "Transkribering"
    upload_text = "Last opp"
    rec_text = "Ta opp"
    record_text = "Klikk på mikrofonikonet for å ta opp"
    splitting_audio_text = "Deler opp lydfilen i mindre biter..."
    transcribing_text = "Transkriberer alle lydbiter. Dette kan ta litt tid avhengig av hvor lang innspillingen er..."
    transcription_done_text = "Transkribering fullført!"
    record_stop = "Stopp opptak"


elif st.session_state['language'] == "English":
    page_name = "Transcribe"
    upload_text = "Upload"
    rec_text = "Record"
    record_text = "Click on the microfon icon to record"
    splitting_audio_text = "Splitting the audio file into smaller pieces..."
    transcribing_text = "Transcribing all audio pieces. This may take a while depending on how long the recording is..."
    transcription_done_text = "Transcription done!"
    record_stop = "Stop recording"


os.makedirs("data/audio", exist_ok=True) # Where audio/video files are stored for transcription
os.makedirs("data/audio_chunks", exist_ok=True) # Where audio/video files are stored for transcription
os.makedirs("data/text", exist_ok=True) # Where transcribed document are beeing stored


### SIDEBAR

menu()

st.markdown(f"""#### :material/graphic_eq: {page_name}
""")


# Check and set default values if not set in session_state
# of Streamlit

if "spoken_language" not in st.session_state: # What language source audio is in
    st.session_state["spoken_language"] = "Norsk"
if "file_name_converted" not in st.session_state: # Audio file name
    st.session_state["file_name_converted"] = None
if "gpt_template" not in st.session_state: # Audio file name
    st.session_state["gpt_template"] = "Whisper Prompt"
if "audio_file" not in st.session_state:
    st.session_state["audio_file"] = False


# Checking if uploaded or recorded audio file has been transcribed
def compute_file_hash(uploaded_file):

    print("\nSTART: Check if audio file has been transcribed - hash")

    # Compute the MD5 hash of a file
    hasher = hashlib.md5()
    
    for chunk in iter(lambda: uploaded_file.read(4096), b""):
        hasher.update(chunk)
    uploaded_file.seek(0)  # Reset the file pointer to the beginning

    print("DONE: Check if audio file has been transcribed - hash")
    
    return hasher.hexdigest()


# Count tokens 

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


### MAIN APP ###########################

def main():

    global translation
    global model_map_transcribe_model

    ### SIDEBAR

    ###### SIDEBAR SETTINGS
    
    #st.sidebar.warning("""Det här är en prototyp som transkriberar ljud och 
    #                   bearbetas med en språkmodell, baserat på den mall du väljer. 
    #                   Prototypen är __inte GDPR-säkrad__, då den använder AI-modeller 
    #                   som körs på servrar i USA. Testa endast med okej data.""")
    

    ### ### ### ### ### ### ### ### ### ### ###
    ### MAIN PAGE
    
    # CREATE THREE TWO FOR FILE UPLOAD VS RECORDED AUDIO    

    tab1, tab2 = st.tabs([f"{upload_text}", f"{rec_text}"])


    # FILE UPLOADER

    with tab1:
        
        uploaded_file = st.file_uploader(
            "Last opp din lyd- eller videofil her:",
            type=["mp3", "wav", "flac", "mp4", "m4a", "aifc"],
            help="Max 10GB stora filer", label_visibility="collapsed",
            )

        if uploaded_file:

            # Checks if uploaded file has already been transcribed
            current_file_hash = compute_file_hash(uploaded_file)

            # If the uploaded file hash is different from the one in session state, reset the state
            if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
                st.session_state.file_hash = current_file_hash
                
                if "transcribed" in st.session_state:
                    del st.session_state.transcribed

            
            # If audio has not been transcribed
            if "transcribed" not in st.session_state:

                with st.spinner(f'{splitting_audio_text}'):
                    chunk_paths = split_audio_to_chunks(uploaded_file)

                # Transcribe chunks in parallel
                with st.spinner(f'{transcribing_text}'):
                    with ThreadPoolExecutor() as executor:
                        # Open each chunk as a file object and pass it to transcribe_with_whisper_openai
                        transcriptions = list(executor.map(
                            lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                            chunk_paths
                        )) 
                
                # Combine all the transcriptions into one
                st.session_state.transcribed = "\n".join(transcriptions)
                st.success(f'{transcription_done_text}')
            
            token_count = num_tokens_from_string(st.session_state.transcribed, "o200k_base")
            #st.info(f"Antal tokens: {token_count}")

            st.markdown(f"#### {page_name}")
            st.markdown(st.session_state.transcribed)

            st.markdown("# ")

        
    # AUDIO RECORDER ###### ###### ######

    with tab2:

        # Creates the audio recorder
        audio = st.experimental_audio_input(f"{record_text}")

        # The rest of the code in tab2 works the same way as in tab1, so it's not going to be
        # commented.
        if audio:

            # Open the saved audio file and compute its hash
            current_file_hash = compute_file_hash(audio)

            # If the uploaded file hash is different from the one in session state, reset the state
            if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
                st.session_state.file_hash = current_file_hash
                
                if "transcribed" in st.session_state:
                    del st.session_state.transcribed
                
            if "transcribed" not in st.session_state:

                with st.status(f'{splitting_audio_text}'):
                    chunk_paths = split_audio_to_chunks(audio)

                # Transcribe chunks in parallel
                with st.status(f'{transcribing_text}'):
                    with ThreadPoolExecutor() as executor:
                        # Open each chunk as a file object and pass it to transcribe_with_whisper_openai
                        transcriptions = list(executor.map(
                            lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                            chunk_paths
                        )) 
                
                # Combine all the transcriptions into one
                st.session_state.transcribed = "\n".join(transcriptions)

            token_count = num_tokens_from_string(st.session_state.transcribed, "o200k_base")
            #st.info(f"Antal tokens: {token_count}")

            st.markdown(f"#### {page_name}")
            st.markdown(st.session_state.transcribed)
            
            st.markdown("# ")


if __name__ == "__main__":
    main()
