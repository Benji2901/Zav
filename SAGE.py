import os
import streamlit as st
import pandas as pd
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from PIL import Image
import base64
import re

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["data_description", "question"],
    template="""
    You are a chatbot called SAGE that specializes in sexual health. You respond to questions with empathy, respect and in a simple manner. You have access to the following sexual health data:
    {data_description}

    Question: {question}

    Please provide a short detailed answer based on the data, at most two sentences. A thirteen year old should be able to understand the answer.

    Answer:
    """
)

# Initialize the OpenAI model
llm = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
chain = LLMChain(llm=llm, prompt=prompt_template)

# Load the text data with caching
@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

file_path = '/content/sti_data.csv'
try:
    text_data = load_data(file_path)
except Exception as e:
    st.error(f"Error loading file: {e}")

# Function to generate data description
def generate_data_description():
    sample_entries = text_data.sample(min(len(text_data), 5))  # Get up to 5 random rows
    description = "The dataset contains information on the most common sexually transmitted diseases/infections found in the Caribbean. The data is structured with the following columns:\n"
    description += "- Keywords: The word that will be used to find the corresponding response.\n"
    description += "- Responses: The information that tells the user about the keyword.\n"
    description += "- Clinics: These are free healthcare centers in Antigua and Barbuda.\n"
    description += "- Locations: These are the villages where the free healthcare centers are located.\n"
    description += "- Contacts: The contact numbers for the free healthcare centers.\n"
    description += "Example entries:\n"
    description += "\n".join(f"Keywords: {row['Keywords']}, Responses: {row['Responses']}, Clinics: {row['Clinics']}, Locations: {row['Locations']}, Contacts: {row['Contacts']}" for _, row in sample_entries.iterrows())
    return description

def get_response(question):
    try:
        data_description = generate_data_description()
        response = chain.run(data_description=data_description, question=question)
        if not response:
            st.write("Debug: No response received.")
        return response
    except Exception as e:
        st.write(f"Error generating response: {e}")
        return "Sorry, there was an error generating the response."

# Initialize session state for conversational memory and input value
if 'history' not in st.session_state:
    st.session_state.history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

# Convert local images to Base64
def image_to_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    else:
        st.error(f"Image file not found: {image_path}")
        return None

# Ensure image paths are correctly set
sage_image_base64 = image_to_base64('images/SAGE.png')
user_image_base64 = image_to_base64('images/user_logo.jpg')

# Streamlit interface
st.title("SAGE - Sexual Awareness & Guidance Expert")
st.write("Ask me anything about sexual health!")

# Display avatar
avatar_path = 'images/SAGE.png'  # Replace with your actual avatar path
if os.path.exists(avatar_path):
    avatar = Image.open(avatar_path)
    st.sidebar.image(avatar, use_column_width=True)
else:
    st.sidebar.error(f"Error loading avatar image: {avatar_path}")

# Sidebar for additional information and avatar
st.sidebar.title("About SAGE")
st.sidebar.header("Disclaimer!")
st.sidebar.write(
    "This information is for educational purposes only and is not a substitute for professional medical advice. Please consult a healthcare professional for medical concerns."
)
st.sidebar.header("User Information")

# Collect user details
gender = st.sidebar.selectbox("Select your gender", ["Select Gender", "Male", "Female", "Prefer not to say"], key='gender_selectbox')
age_group = st.sidebar.selectbox("Select your age group", ["Select Age Group", "Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65 and over"], key='age_group_selectbox')

# Store user details in session state
st.session_state.gender = gender
st.session_state.age_group = age_group

st.sidebar.write("STIs are more common than you might think, and there's absolutely no reason to feel ashamed! At SAGE Tech, we’re committed to your privacy and will handle everything with the utmost confidentiality.")

# Display user information
user_info_display = f"**Your Information:**\n- **Gender:** {st.session_state.gender}\n- **Age Group:** {st.session_state.age_group}"
st.write(user_info_display)

# Handle greetings
def handle_greeting(user_input):
    if re.search(r'\bhello\b|\bhi\b|\bgreetings\b|\bhey\b', user_input, re.IGNORECASE):
        return "Hello! I'm SAGE - your Sexual Awareness & Guidance Expert. How can I assist you today?"
    elif re.search(r'\bhow are you\b|\bhow are you doing\b', user_input, re.IGNORECASE):
        return "I'm just a program, but I'm here and ready to help you with STI information. How can I assist you today?"
    elif re.search(r'\bthank you\b|\bthanks\b', user_input, re.IGNORECASE):
        return "You're welcome! If you have any more questions, feel free to ask."
    else:
        return None

# Display conversation history with images
if st.session_state.history:
    st.write("### Conversation History")
    for speaker, message in st.session_state.history:
        if speaker == "SAGE":
            if sage_image_base64:
                st.write(
                    f"<img src='data:image/png;base64,{sage_image_base64}' style='width:50px;height:50px;'> **SAGE**: {message}",
                    unsafe_allow_html=True
                )
        else:
            if user_image_base64:
                st.write(
                    f"<img src='data:image/jpeg;base64,{user_image_base64}' style='width:50px;height:50px;'> **YOU**: {message}",
                    unsafe_allow_html=True
                )

# User input handling with automatic processing
def process_input():
    if st.session_state.user_input:
        response = get_response(st.session_state.user_input)
        st.session_state.history.append(("User", st.session_state.user_input))  # Save the user question in history
        st.session_state.history.append(("SAGE", response))  # Save the response in history
        st.session_state.user_input = ""  # Clear the input field

# Text input field with automatic processing
st.text_input("Enter your question:", key='user_input', on_change=process_input, value=st.session_state.user_input)
