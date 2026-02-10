import requests

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros/marcas"

def get_marcas():
    response = requests.get(BASE_URL)
    return response.json() if response.status_code == 200 else []

def get_modelos(marca_id):
    url = f"{BASE_URL}/{marca_id}/modelos"
    response = requests.get(url)
    return response.json()['modelos'] if response.status_code == 200 else []

def get_anos(marca_id, modelo_id):
    url = f"{BASE_URL}/{marca_id}/modelos/{modelo_id}/anos"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def get_preco(marca_id, modelo_id, ano_id):
    url = f"{BASE_URL}/{marca_id}/modelos/{modelo_id}/anos/{ano_id}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}