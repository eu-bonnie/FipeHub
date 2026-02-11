import streamlit as st
from infra.api_client import get_marcas, get_modelos, get_anos, get_preco
from infra.database import salvar_consulta

def render_home():
    st.title("🚗 Consulta de Preços FIPE")
    st.write("Selecione os detalhes do veículo para obter o valor médio de mercado.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        marcas = get_marcas()
        marca_nome = st.selectbox("Marca", [m['nome'] for m in marcas])
        marca_id = next(m['codigo'] for m in marcas if m['nome'] == marca_nome)

    with col2:
        modelos = get_modelos(marca_id)
        modelo_nome = st.selectbox("Modelo", [mod['nome'] for mod in modelos])
        modelo_id = next(mod['codigo'] for mod in modelos if mod['nome'] == modelo_nome)

    with col3:
        anos = get_anos(marca_id, modelo_id)
        ano_label = st.selectbox("Ano Modelo", [a['nome'] for a in anos])
        ano_id = next(a['codigo'] for a in anos if a['nome'] == ano_label)

    if st.button("Visualizar Preço Atualizado"):
        dados = get_preco(marca_id, modelo_id, ano_id)
        if dados:
            st.success(f"### Valor: {dados['Valor']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Combustível", dados['Combustivel'])
            c2.metric("Ano", dados['AnoModelo'])
            c3.metric("Referência", dados['MesReferencia'])
            
            salvar_consulta({
                'marca': marca_nome,
                'modelo': modelo_nome,
                'ano': ano_label,
                'preco': dados['Valor']
            })
            st.toast("Busca registrada no banco!")