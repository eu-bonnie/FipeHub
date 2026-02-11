import streamlit as st
import pandas as pd
from infra.database import engine

def render_admin():
    st.title("⚙️ Administração do Sistema")
    st.subheader("Logs de Consultas em Tempo Real")
    
    query = "SELECT * FROM buscas_log ORDER BY data_consulta DESC LIMIT 10"
    df_logs = pd.read_sql(query, engine)
    
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
        if st.button("Limpar Histórico (⚠️ Cuidado)"):
            st.error("Funcionalidade de exclusão restrita.")
    else:
        st.info("Nenhuma consulta registrada no banco ainda.")