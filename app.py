#import streamlit as st

#st.title("🚗 FipeHUb")
#st.write("A base do projeto está pronta!")

#if st.button('Testar Banco de Dados'):
    # Importar sua lógica de conexão aqui depois
    #st.success("Botão funcionando!")

import streamlit as st
from infra.api_client import get_marcas, get_modelos, get_anos, get_preco
from infra.database import init_db, salvar_consulta

# Inicializar Banco
init_db()

st.set_page_config(page_title="VeloGeo - Consulta FIPE", layout="wide")

# Sidebar para Abstração de Papéis
st.sidebar.title("Menu de Acesso")
papel = st.sidebar.selectbox("Seu Papel", ["Usuário (Consulta)", "Coordenador (Regiões)", "Pesquisador (Coleta)"])

if papel == "Usuário (Consulta)":
    st.title("🚗 Consulta de Preços FIPE")
    
    # Colunas para os Seletores
    col1, col2, col3 = st.columns(3)
    
    with col1:
        marcas = get_marcas()
        marca_nome = st.selectbox("Selecione a Marca", [m['nome'] for m in marcas])
        marca_id = next(m['codigo'] for m in marcas if m['nome'] == marca_nome)

    with col2:
        modelos = get_modelos(marca_id)
        modelo_nome = st.selectbox("Selecione o Modelo", [mod['nome'] for mod in modelos])
        modelo_id = next(mod['codigo'] for mod in modelos if mod['nome'] == modelo_nome)

    with col3:
        anos = get_anos(marca_id, modelo_id)
        ano_label = st.selectbox("Selecione o Ano", [a['nome'] for a in anos])
        ano_id = next(a['codigo'] for a in anos if a['nome'] == ano_label)

    if st.button("Verificar Preço"):
        dados_preco = get_preco(marca_id, modelo_id, ano_id)
        
        if dados_preco:
            st.metric(label=f"Preço Médio - {dados_preco['Modelo']}", value=dados_preco['Valor'])
            st.info(f"Referência: {dados_preco['MesReferencia']} | Combustível: {dados_preco['Combustivel']}")
            
            # Persistência no Banco (Parte do seu TD)
            salvar_consulta({
                'marca': marca_nome,
                'modelo': modelo_nome,
                'ano': ano_label,
                'preco': dados_preco['Valor']
            })
            st.toast("Consulta salva no banco de dados!")

elif papel == "Coordenador (Regiões)":
    st.header("📍 Painel do Coordenador")
    st.warning("Área sob abstração: Aqui seriam integrados os dados do IBGE para visão regional.")
    # Aqui entraria o mapa futuro

else:
    st.header("📝 Área do Pesquisador")
    st.info("Área sob abstração: Interface para input manual de novos dados de mercado.")