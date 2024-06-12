import requests, json
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

protocol = os.getenv('protocol_ollama')
hostname = os.getenv('hostname_ollama')
host = f"{protocol}://{hostname}"
suffix = os.getenv('auth_url_suffix_ollama')
auth_url = f"{host}/{suffix}"
suffix = os.getenv('api_url_suffix_ollama')
api_url = f"{host}/{suffix}"

account = {'email': os.getenv('ollama_user'), 'password': os.getenv('ollama_pw')}
auth_response = requests.post(auth_url, json=account)
jwt = json.loads(auth_response.text)["token"]

ollama_embeddings = OllamaEmbeddings(base_url=api_url, model="nomic-embed-text", headers={"Authorization": "Bearer " + jwt})
ollama_llm = Ollama(base_url=api_url, model= os.getenv('ollama_model'), temperature=0.0, headers={"Authorization": "Bearer " + jwt})