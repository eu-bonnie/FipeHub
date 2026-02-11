import streamlit as st
from infra.database import init_db

# Importando TODAS as visualizações
from views.home import render_home
from views.admin import render_admin
from views.gerente import render_gerente
from views.coordenador import render_coordenador
from views.pesquisador import render_pesquisador
from views.lojista import render_lojista

# Inicialização do Banco
init_db()

# Configuração de Página
st.set_page_config(page_title="FipeHub", layout="wide", page_icon="🚗")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/741/741407.png", width=80)
    st.title("FipeHub System")
    st.markdown("---")
    
    menu = st.selectbox(
        "Selecione o Portal de Acesso:",
        [
            "🏠 Home", 
            "⚙️ Área do Administrador", 
            "📊 Área do Gerente", 
            "📍 Área do Coordenador", 
            "🔍 Área do Pesquisador", 
            "🏪 Área do Lojista"
        ]
    )
    
    st.markdown("---")
    st.caption(f"Acesso Nível: **{menu.split()[-1]}**")

# --- DICIONÁRIO DE ROTEAMENTO ---
# Mapeia o nome do menu para a função correspondente
paginas = {
    "🏠 Home": render_home,
    "⚙️ Área do Administrador": render_admin,
    "📊 Área do Gerente": render_gerente,
    "📍 Área do Coordenador": render_coordenador,
    "🔍 Área do Pesquisador": render_pesquisador,
    "🏪 Área do Lojista": render_lojista
}

# Executa a função da página selecionada
paginas[menu]()