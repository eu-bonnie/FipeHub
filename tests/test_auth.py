import pytest

# Simulando uma função que você terá no seu código principal
def verificar_acesso(username, codigo):
    # Exemplo: Usuario 'admin' tem código '1234'
    usuarios_mock = {"admin": "1234"}
    return usuarios_mock.get(username) == codigo

def test_login_sucesso():
    assert verificar_acesso("admin", "1234") is True

def test_login_falha():
    assert verificar_acesso("admin", "9999") is False