import streamlit as st
import pandas as pd
from infra.database import engine

def render_gerente():
    st.title("📊 Relatórios de Gestão")
    st.write("Aqui o gerente visualiza métricas de desempenho e buscas populares.")
    
    query = "SELECT marca, COUNT(*) as total FROM buscas_log GROUP BY marca"
    df_counts = pd.read_sql(query, engine)
    if not df_counts.empty:
        st.bar_chart(df_counts.set_index('marca'))
    else:
        st.warning("Dados insuficientes para gerar gráficos.")