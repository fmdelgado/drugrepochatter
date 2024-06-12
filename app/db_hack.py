import time
import streamlit as st
import sys
from my_pdf_lib import load_index_from_db, store_index_in_db, get_index_for_pdf
from db_management import *
from db_chat import user_message, bot_message
import json
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
import markdown
import hashlib
from streamlit_option_menu import option_menu
from ollama_connector import ollama_embeddings, ollama_llm
from langchain.prompts import PromptTemplate
import time
import os
import base64


def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


MAX_REQUESTS = 10
WAIT_TIME = 60 # seconds


def is_user_logged_in():
    return "user" in st.session_state.keys() and len(st.session_state["user"]) > 0


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def get_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def store_data_as_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)


def chat_page_styling():
    st.title("DrugRepoChatter")
    st.header("Questions and  Answering Chatbot")
    st.write(
        """
        This chatbot is your expert assistant in the field of drug repurposing. 
           Leveraging a knowledge base derived from a variety of scientific documents related to your topic of choice,
           it can provide detailed insights and answers to your queries! 📚

           To customize the knowledge base, please navigate to the *Configure Knowledge Base* page.
            """
    )


def reproduce_chat_if_user_logged_in(typeOfMessage):
    # reproduce chat if user is logged in from DB
    if is_user_logged_in():
        if typeOfMessage == "messagesqanda":
            messages = get_qandadata(st.session_state["user"])
            st.session_state[typeOfMessage] = []
        for message in messages:
            st.session_state[typeOfMessage].append({"role": message[3], "content": message[2]})


def is_chat_empty(typeOfChat):
    return typeOfChat not in st.session_state.keys() or len(st.session_state[typeOfChat]) == 0


def start_new_chat_if_empty(typeOfChat):
    # start a new chat
    if is_chat_empty(typeOfChat):
        message = {"role": "assistant", "content": "Hi there, how can I help?"}
        st.session_state[typeOfChat] = [message]
        if is_user_logged_in():
            save_message_in_db(typeOfChat, message)


def print_current_chat(typeOfChat):
    for message in st.session_state[typeOfChat]:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="DrugRepoChatter")


def clear_chat(typeOfChat):
    # clear chat data
    st.session_state[typeOfChat] = []
    # delete chat in DB as well
    if typeOfChat == "messagesqanda":
        delete_qanda(st.session_state["user"])
    st.experimental_rerun()


def save_message_in_db(typeOfChat, message):
    if typeOfChat == "messagesqanda":
        add_qandadata(st.session_state["user"], message["content"], message["role"])


def get_user_message(typeOfChat):
    if prompt := st.chat_input():
        message = {"role": "user", "content": prompt}
        st.session_state[typeOfChat].append(message)
        if is_user_logged_in():
            save_message_in_db(typeOfChat, message)
    return prompt


def config_page():
    st.title("Configure knowledge base")
    if not is_user_logged_in():
        st.warning("You are not logged in. Please login or create a new account to configure a knowledge base.")
        return

    try:
        indices = []
        public_knowledgebase = get_public_knowledgebase()
        for knowledgebase in public_knowledgebase:
            indices.append(knowledgebase[1])
        if is_user_logged_in():
            private_knowledgebases = get_private_knowledgebase(st.session_state["user"])
            for knowledgebase in private_knowledgebases:
                indices.append(st.session_state["user"] + "_" + knowledgebase[2])
    except Exception as e:
        # st.write(e)
        indices = []

    dip = indices + ["Create New"]
    if not st.session_state["knowledgebase"] == "Create New" and is_user_logged_in():
        try:
            chosen_base = dip.index(st.session_state["knowledgebase"])
        except:
            # knowledgebase might have been deleted etc.
            chosen_base = 0
    else:
        # default
        chosen_base = 0

    st.session_state["knowledgebase"] = st.selectbox("Select knowledge base", options=dip, index=chosen_base)

    if st.session_state["knowledgebase"] == "Create New":
        with st.form(key="index"):
            st.write("##### Create a new knowledge base")
            files = st.file_uploader(
                "Step 1 - Upload files", type="pdf", accept_multiple_files=True
            )

            name = st.text_input("Step 2 - Choose a name for your index")
            index_name = "index_" + name
            user_name = st.session_state["user"] + "_" + name
            button = st.form_submit_button("Create Index")
            if index_name in indices or user_name in indices:
                st.warning("Please use an unique name!")
                st.stop()
            if button:
                try:
                    with st.spinner("Indexing"):
                        index = get_index_for_pdf(files)
                        if is_user_logged_in():
                            user_index = st.session_state["user"] + "_" + name
                            store_index_in_db(index, name=user_index)
                            add_private_knowledgebase(st.session_state["user"], name)
                        else:
                            index_name = "index_" + name
                            store_index_in_db(index, name=index_name)
                            add_public_knowledgebase(name, False)
                    st.success("Finished creating new index")
                    time.sleep(1)
                    st.experimental_rerun()
                except Exception as e:
                    # st.write(e)
                    st.error("Could not create new index.")
    else:
        delete = st.button("Delete")

        if delete:
            data = st.session_state["knowledgebase"].split("_")
            base_name = st.session_state["knowledgebase"][len(data[0]) + 1:]
            # Only delete the files if the index is not protected
            if not check_if_public_knowledgebase_protected(base_name):
                folder = f"indexes/{st.session_state['knowledgebase']}"
                # folder = f"indexes/index_repo4euD21openaccess"
                # Delete the files
                import shutil
                if os.path.exists(folder):
                    shutil.rmtree(folder)

                if st.session_state["knowledgebase"].startswith("index_"):
                    delete_public_knowledgebase(base_name)
                else:
                    delete_private_knowledgebase(st.session_state["user"], base_name)
                st.success("Knowledgebase has been deleted successfully.")
                time.sleep(1)
            else:
                st.warning("Database is protected and cannot be deleted.")
                time.sleep(1)
            st.experimental_rerun()


def process_llm_response(llm_response, doc_content=True):
    sources = '<ol style="white-space: pre-wrap;">'  # Changed from <ul> to <ol>
    for source in llm_response["source_documents"]:
        source_info = "<li>"
        if doc_content:
            source_info += f"Content: {source.page_content}, "
        source_info += f"{source.metadata['source'].split('/')[-1].replace('.pdf', '')}, Page: {source.metadata['page']}</li>"
        sources += source_info
    sources += "</ol>"  # Changed from </ul> to </ol>
    return sources


def qanda_page():
    chaintype="stuff"
    chaintype = st.selectbox("Please select chain type", options=['stuff', "map_reduce", "refine"] ,index=0)
    default_k = 4
    selected_k = st.slider("k", min_value=1, max_value=50, value=default_k, step=1)
    default_fetch_k = 20
    selected_fetch_k = st.slider("fetch_k", min_value=1, max_value=50, value=default_fetch_k, step=1)
    show_sources = st.checkbox("Show texts in original docs", False)

    st.title("DrugRepoChatter")
    st.header("Questions and Answering with sources")

    if "knowledgebase" in st.session_state.keys() and len(st.session_state["knowledgebase"]) > 0:
        # index = load_index_from_db( "index_repo4euD21openaccess")
        index = load_index_from_db(st.session_state["knowledgebase"])
        if index is not None:
            st.write("Index loaded successfully")
        else:
            st.write("Failed to load the index")

    else:
        st.info("No knowledge base found. Please configure one!")
        st.stop()

    reproduce_chat_if_user_logged_in("messagesqanda")
    start_new_chat_if_empty("messagesqanda")
    print_current_chat("messagesqanda")
     
    if st.session_state.lock_until_qanda > time.time():
        st.write(f"You have reached your limit of {MAX_REQUESTS} questions. Please wait {int(st.session_state.lock_until_qanda - time.time())} seconds.")
        st.session_state.request_count_qanda = 0
        return
    
    st.session_state.request_count_qanda += 1  

    if st.session_state.request_count_qanda > MAX_REQUESTS:
        st.session_state.lock_until_qanda = time.time() + WAIT_TIME 

    prompt = get_user_message("messagesqanda")
    if prompt:
        with st.container():
            user_message(prompt)
            botmsg = bot_message("...", bot_name="DrugRepoChatter")

        try:

            PROMPT_TEMPLATE = """Answer the question based only on the following context:\
                                {context}\
                                You are allowed to rephrase the answer based on the context. \
                                Do not answer any questions using your pre-trained knowledge, only use the information provided in the context.\
                                Do not answer any questions that do not relate to drug repurposing, omics data, bioinformatics and data anlaysis.\
                                Question: {question}
                              """
            PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)

            # tag::qa[]
            qa_chain = RetrievalQA.from_chain_type(
                llm=ollama_llm,
                chain_type=chaintype,
                chain_type_kwargs={"prompt": PROMPT},
                retriever=index.as_retriever(search_type="mmr",
                                             search_kwargs={'fetch_k': selected_fetch_k,
                                                            'k': selected_k}),
                return_source_documents=True
            )

            llm_response = qa_chain({"query": prompt})

            # text = f"{llm_response['result']}\nSources:\n{process_llm_response(llm_response, doc_content=showdocs)}"
            # Convert Markdown to HTML
            html_content = markdown.markdown(llm_response['result'])
            if "In your provided context i don" in llm_response['result']:
                text = f"{html_content}"
            else:
                text = f"{html_content}<br><strong>Sources:</strong><br>{process_llm_response(llm_response, doc_content=show_sources)}"
            result = "".join(text).strip()
            botmsg.update(result)
            message = {"role": "assistant", "content": result}
            st.session_state["messagesqanda"].append(message)
            if is_user_logged_in():
                save_message_in_db("messagesqanda", message)
        except Exception as e:
            # st.write(e)
            st.error("Something went wrong while producing a response.")
    if len(st.session_state["messagesqanda"]) != 0 and st.button("Clear Chat"):
        clear_chat("messagesqanda")


def about_page():
    # Define the paths to the images
    image_dir = "/app/img"
    image_cosybio = os.path.join(image_dir, "logo_cosybio.png")
    image_repo4eu = os.path.join(image_dir, "REPO4EU-logo-main.png")
    image_eu_funded = os.path.join(image_dir, "eu_funded_logo.jpeg")
    image_logo = os.path.join(image_dir, "logo.png")

    # Convert images to base64
    cosybio_base64 = get_image_base64(image_cosybio)
    repo4eu_base64 = get_image_base64(image_repo4eu)
    eu_funded_base64 = get_image_base64(image_eu_funded)
    logo_base64 = get_image_base64(image_logo)

    st.markdown(
        f'<p align="center"> <img src="data:image/png;base64,{logo_base64}" width="300"/> </p>',
        unsafe_allow_html=True,
    )
    st.title("DrugRepoChatter")
    st.header("AI-powered assistant for academic research")

    st.markdown("""
    DrugRepoChatter is an AI-powered assistant for academic research. It is a tool that helps researchers to find relevant information in a large corpus of scientific documents.
    To begin, just upload your PDF files and DrugRepoChatter will create a knowledge base that you can query using natural language. 
    """)

    # Display images using HTML
    st.markdown(
        f'''
        <div style="text-align:center">
            <img src="data:image/png;base64,{cosybio_base64}" width="100" style="margin:0px 15px 0px 15px;"/>
            <img src="data:image/png;base64,{repo4eu_base64}" width="120" style="margin:0px 15px 0px 15px;"/>
            <img src="data:image/png;base64,{eu_funded_base64}" width="120" style="margin:0px 15px 0px 15px;"/>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # Displaying the funding information
    st.markdown("""
    ---
    **Funding Information:**

    This project is funded by the European Union under grant agreement No. 101057619. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Health and Digital Executive Agency (HADEA). Neither the European Union nor the granting authority can be held responsible for them. This work was also partly supported by the Swiss State Secretariat for Education, Research and Innovation (SERI) under contract No. 22.00115.
    """)

def sign_up():
    st.subheader("Create an Account")
    user = st.text_input('Username')
    pw = make_hashes(st.text_input('Password', type='password'))

    if len(pw) > 5:
        st.session_state["user"] = user
        st.session_state["password"] = pw
    else:
        st.warning("At least 4 characters are required for the password!")
        st.stop()
    if "_" in st.session_state["user"] or len(st.session_state["user"]) < 4 or len(st.session_state["password"]) < 4 or \
            st.session_state["user"].lower() == "index":
        st.warning(
            "You cannot use \"_\" in the username. Username and password need at least 4 digits. Index is a forbidden username!")
        st.stop()
    if st.button('SignUp'):
        # user does not exist yet and can be created
        if check_if_user_already_exists(st.session_state["user"]):
            add_userdata(st.session_state["user"], st.session_state["password"])
            st.success("You have successfully created an account. You are already logged in.")
        # user already exists
        else:
            st.error("The user already exists. Please create a new user or login.")


def login():
    st.subheader("Login")
    if not is_user_logged_in():
        # new login
        with st.form("login"):
            st.session_state["user"] = st.text_input('Username')
            st.session_state["password"] = make_hashes(st.text_input('Password', type='password'))
            st.form_submit_button("login")
    result = login_user(st.session_state["user"], st.session_state["password"])
    # user could be logged in
    if result:
        user = st.session_state["user"]
        st.success("Logged In as {}".format(user))

    # Login failed
    elif "user" in st.session_state.keys() and "password" in st.session_state.keys() and len(
            st.session_state["user"]) > 0 and len(st.session_state["password"]) > 0:
        st.error("Incorrect login!")


def logout():
    st.session_state["user"] = ""
    st.session_state["password"] = ""
    st.session_state["messagesqanda"] = []


def main():
    if "messages" not in st.session_state.keys() and "messagesqanda" not in st.session_state.keys():
        st.session_state["user"] = ""
        st.session_state["password"] = ""
        st.session_state["messagesqanda"] = []

        create_usertable()
        create_qandatable()
        create_knowledgebases_private()
        create_knowledgebases_public()
        if 'request_count_qanda' not in st.session_state:
            st.session_state.request_count_qanda = 0
        if 'lock_until_qanda' not in st.session_state:
            st.session_state.lock_until_qanda = 0
    if "knowledgebase" not in st.session_state.keys():
        # default knowledge base
        # default_db_name =  "index_repo4euD21openaccess"
        st.session_state["knowledgebase"] = "index_repo4euD21openaccess"

    with st.sidebar:
        page = option_menu("Choose a page", ["Login", "Sign up", "Q&A", "Configure knowledge base", "About"])
        if st.button("logout"):
            logout()

    if page == "Sign up":
        sign_up()
    elif page == "Login":
        login()
    elif page == "Configure knowledge base":
        config_page()
    elif page == "Q&A":
        qanda_page()
    elif page == "About":
        about_page()



if __name__ == "__main__":
    main()
