import streamlit as st
from infra.database import init_db

# Importando TODAS as visualizações
from views.home import render_home
from views.admin import render_admin
from views.gerente import render_gerente
from views.coordenador import render_coordenador
from views.pesquisador import render_pesquisador
from views.lojista import render_lojista
from src.auth import check_login

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
            "⚙️ Administrador", 
            "📊 Gerente", 
            "📍 Coordenador", 
            "🔍 Pesquisador", 
            "🏪 Lojista"
        ]
    )
    
    st.markdown("---")
    # Rodapé do Sidebar com Logout
    if st.session_state.get('logged_in'):
        st.write(f"Logado como: **{st.session_state.get('username')}**")
        if st.button("Sair (Logout)"):
            st.session_state.clear()
            st.rerun()

# --- CONTROLE DE NAVEGAÇÃO E ACESSO ---

if menu == "🏠 Home":
    render_home()

elif menu == "⚙️ Administrador":
    if check_login("Admin"):
        render_admin()

elif menu == "📊 Gerente":
    if check_login("Gerente"):
        render_gerente()

elif menu == "📍 Coordenador":
    if check_login("Coordenador"):
        render_coordenador()

elif menu == "🔍 Pesquisador":
    if check_login("Pesquisador"):
        render_pesquisador()

elif menu == "🏪 Lojista":
    if check_login("Lojista"):
        render_lojista()