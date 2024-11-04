
import streamlit as st
import config as c

def update_language():
    # Update session state when the language is changed
    st.session_state['language'] = st.session_state['selected_language']

def menu():

    # Check if language is already in session_state, else initialize it with a default value
    if 'language' not in st.session_state:
        st.session_state['language'] = "Svenska"  # Default language
    
    if 'app_version' not in st.session_state:
        st.session_state['app_version'] = c.app_version
    if 'update_date' not in st.session_state:
        st.session_state['update_date'] = c.update_date

    # Sidebar for language selection
    st.sidebar.selectbox(
        "Språk", 
        ("Norsk", "English"),
        index = ["Norsk", "English"].index(st.session_state['language']),
        key = "selected_language",  # Temporary key for selected value
        on_change = update_language,  # Trigger update when changed
        label_visibility = "collapsed"
    )

    if st.session_state['language'] == "Norsk":

        st.sidebar.markdown("### Meny")

        st.sidebar.page_link("Start.py", label="Start", icon=":material/home:")
        st.sidebar.markdown("###### ")

        st.sidebar.markdown("###### ")
        st.sidebar.markdown("### IJs AI-lab")

        st.sidebar.page_link("pages/chatbot.py", label="Chat", icon=":material/forum:")
        st.sidebar.page_link("pages/image.py", label="Bilder", icon=":material/image:")
        st.sidebar.page_link("pages/image_analysis.py", label="Bildeanalyse", icon=":material/image:")
        st.sidebar.page_link("pages/chat_with_document.py", label="Chat med dine dokumenter", icon=":material/description:")
        st.sidebar.page_link("pages/transcribe.py", label="Transkribering", icon=":material/transcribe:")

        st.sidebar.markdown("# ")
        with st.sidebar.container(border = True):
            st.markdown(f"""__Version:__ {st.session_state["app_version"]}  
            __Uppdaterad:__ {st.session_state["update_date"]}
            """)

    if st.session_state['language'] == "English":

        st.sidebar.markdown("### Menu")

        st.sidebar.page_link("Start.py", label="Start", icon=":material/home:")
        st.sidebar.markdown("###### ")

        st.sidebar.markdown("###### ")
        st.sidebar.markdown("### AI-lab")

        st.sidebar.page_link("pages/chatbot.py", label="Chat", icon=":material/forum:")
        st.sidebar.page_link("pages/image.py", label="Image", icon=":material/image:")
        st.sidebar.page_link("pages/image_analysis.py", label="Image analysis", icon=":material/image:")
        st.sidebar.page_link("pages/chat_with_document.py", label="Chat with your documents", icon=":material/description:")
        st.sidebar.page_link("pages/transcribe.py", label="Transcribe", icon=":material/transcribe:")

        st.sidebar.markdown("# ")
        with st.sidebar.container(border = True):
            st.markdown(f"""__Version:__ {st.session_state["app_version"]}  
            __Updated:__ {st.session_state["update_date"]}
            """)
