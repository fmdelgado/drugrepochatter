import requests, json
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama

import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '../.env')
# dotenv_path = "/Users/fernando/Documents/Research/drugrepochatter/.env"
load_dotenv(dotenv_path)

protocol = "https"
hostname = "chat.cosy.bio"
host = f"{protocol}://{hostname}"
auth_url = f"{host}/api/v1/auths/signin"
api_url = f"{host}/ollama"
account = {
    'email': os.getenv("ollama_user"),
    'password': os.getenv("ollama_pw")
}
auth_response = requests.post(auth_url, json=account)
jwt = auth_response.json()["token"]
headers = {"Authorization": "Bearer " + jwt}

ollama_embeddings = OllamaEmbeddings(base_url=api_url, model="nomic-embed-text", client_kwargs={'headers': headers})
# ollama_embeddings.embed_query("hello, who are you?")
ollama_model = 'llama3.2:latest'
ollama_llm = ChatOllama(
    base_url=api_url,
    model=ollama_model,
    temperature=0.0,
    seed=28,
    num_ctx=25000,
    num_predict=-1,
    top_k=100,
    top_p=0.95,
    format="json",
    client_kwargs={'headers': headers})

# ollama_llm.invoke("hello, who are you?")
# What are the major databases for anticancer drug sensitivity screening?
# What role does network-based inference play in drug repurposing?
# How can we use deep learning for drug repurposing?
# What's NeDRex?
