import streamlit as st
import json
import os
import textwrap
import uuid
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()  # take environment variables from .env.
st.set_page_config()


if "GOOGLE_API_KEY" in os.environ:
    genai_api_key = os.getenv("GOOGLE_API_KEY")
else: genai_api_key = st.secrets["GOOGLE_API_KEY"]

genai.configure(api_key = genai_api_key)

# Set model configuration
model_name = 'models/embedding-001'
model = genai.GenerativeModel('gemini-pro')

# path & data
path = os.path.dirname(__file__)
resume_file = os.path.join(path, "data", "resume.txt")
prompt_file = os.path.join(path, "data", "prompt.txt")
resume_content = open(resume_file, "r").read()
prompt_content = open(prompt_file, "r").read()


def extract_json(data):
    data = data.replace("```json", "").replace("```", "") #hacky solution to extracr json from response
    try:
        data = json.loads(data)
    except data.JSONDecodeError:
        data = '{"answered":"false", "response":"Hmm... Something is not right. I\'m experiencing technical difficulties. Try asking your question again or ask another question about Eswaran Krishnamoorthy\'s professional background and qualifications. Thank you for your understanding.", "questions":["What is Eswar\'s professional experience?","What projects has Eswar worked on?","What are Eswar\'s career goals?"]}'
        
    answered = data.get("answered")
    response = data.get("response")
    questions = data.get("questions")
    return answered, response, questions

# Get the embeddings of each text and add to an embeddings column in the dataframe
def embed_fn(text):
  return genai.embed_content(model=model_name,
                             content=text,
                             task_type="retrieval_query")["embedding"]

def make_prompt(query, relevant_passage):
  escaped = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
  prompt = textwrap.dedent(prompt_content).format(context=escaped, question=query)
  return prompt

def get_gemini_response(query):
    escaped = resume_content.replace("'", "").replace('"', "").replace("\n", " ")
    question_prompt = textwrap.dedent(prompt_content).format(context=escaped, question=query)
    response = model.generate_content(question_prompt)
    return response


def query_content(query):
    result = get_gemini_response(query)
    answered, response, questions = extract_json(result.text)
    full_response="--"
    
    if ('I am tuned to only answer questions' in response) or (response == ""):
        full_response = """Unfortunately, I can't answer this question. My capabilities are limited to providing information about Eswaran Krishnamoorthy's professional background and qualifications. If you have other inquiries, I recommend reaching out to Eswar on [LinkedIn](https://www.linkedin.com/in/eswaran/). I can answer questions like: \n - What is Eswaran Krishnamoorthy's educational background? \n - Can you list Eswaran Krishnamoorthy's professional experience? \n - What skills does Eswaran Krishnamoorthy possess? \n"""
        
    else: 
        markdown_list = ""
        for item in questions:
            markdown_list += f"- {item}\n"
        full_response = response + "\n\n What else would you like to know about Eswar? You can ask me: \n" + markdown_list
    return(full_response)

def load_html():
    if "uuid" not in st.session_state:
        st.session_state["uuid"] = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            welcome_message = """
                Welcome! I'm **Resume Bot**, specialized in providing information about Eswaran Krishnamoorthy's professional background and qualifications. Feel free to ask me questions such as:

                - What is Eswaran Krishnamoorthy's educational background?
                - Can you outline Eswaran Krishnamoorthy's professional experience?
                - What skills and expertise does Eswaran Krishnamoorthy bring to the table?

                I'm here to assist you. What would you like to know?
                """
            message_placeholder.markdown(welcome_message)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about Eswaran Krishnamoorthy"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            
            user_input=prompt
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("Thinking..."):
                full_response = query_content(user_input)
                
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    load_html() 