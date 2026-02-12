import requests

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

def get_marcas():
    response = requests.get(f"{BASE_URL}/marcas")
    return response.json() if response.status_code == 200 else []

def get_modelos(marca_id):
    response = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos")
    return response.json()['modelos'] if response.status_code == 200 else []

def get_anos(marca_id, modelo_id):
    response = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos/{modelo_id}/anos")
    return response.json() if response.status_code == 200 else []

def get_preco(marca_id, modelo_id, ano_id):
    response = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_id}")
    return response.json() if response.status_code == 200 else None