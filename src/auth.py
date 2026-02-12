import streamlit as st
import pandas as pd
from infra.database import engine
from sqlalchemy import text

def check_login(perfil_esperado):
    """Retorna True se o login for bem-sucedido para o perfil específico."""
    
    # Se já estiver logado nesta sessão com o perfil certo, libera direto
    if st.session_state.get('logged_in') and st.session_state.get('perfil') == perfil_esperado:
        return True

    with st.container(border=True):
        st.subheader(f"🔐 Acesso Restrito: {perfil_esperado}")
        user = st.text_input("Username", key=f"user_{perfil_esperado}")
        code = st.text_input("Código de Acesso", type="password", key=f"code_{perfil_esperado}")
        
        if st.button("Entrar", key=f"btn_{perfil_esperado}"):
            query = text("SELECT perfil FROM usuarios WHERE username = :u AND codigo = :c")
            with engine.connect() as conn:
                res = conn.execute(query, {"u": user, "c": code}).fetchone()
                
            if res and res[0] == perfil_esperado:
                st.session_state['logged_in'] = True
                st.session_state['perfil'] = res[0]
                st.session_state['username'] = user
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Usuário ou código incorretos para este perfil.")
    return False