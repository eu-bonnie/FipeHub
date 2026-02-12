import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_lojista():
    st.title("🏪 Área do Lojista")

    tab_cadastro, tab_meus_envios, tab_lojas_ativas = st.tabs([
        "🆕 Solicitar Cadastro", 
        "📋 Minhas Solicitações",
        "✅ Lojas Ativas"
    ])

    # --- ABA 1: CADASTRO (Mantida conforme original) ---
    with tab_cadastro:
        st.subheader("Cadastre seu estabelecimento")
        with st.form("form_nova_loja", clear_on_submit=True):
            nome = st.text_input("Nome Fantasia")
            cnpj = st.text_input("CNPJ")
            endereco = st.text_input("Endereço Completo")
            if st.form_submit_button("Enviar Solicitação"):
                if nome and cnpj and endereco:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO lojas (nome_loja, cnpj, endereco, status)
                            VALUES (:nome, :cnpj, :end, 'Pendente')
                        """), {"nome": nome, "cnpj": cnpj, "end": endereco})
                        conn.commit()
                    st.success("✅ Solicitação enviada!")

    # --- ABA 2: MINHAS SOLICITAÇÕES (Mantida conforme original) ---
    with tab_meus_envios:
        st.subheader("Histórico de solicitações")
        df_lojas = pd.read_sql("SELECT * FROM lojas ORDER BY id DESC", engine)
        if df_lojas.empty:
            st.info("Nenhuma solicitação encontrada.")
        else:
            for _, loja in df_lojas.iterrows():
                cor = "orange" if loja['status'] == 'Pendente' else "green" if loja['status'] == 'Aprovada' else "red"
                with st.container(border=True):
                    st.markdown(f"**{loja['nome_loja']}** - :{cor}[{loja['status'].upper()}]")
                    st.caption(f"📍 {loja['endereco']}")

    # --- ABA 3: LOJAS ATIVAS (Apenas visualização do que está aprovado) ---
    with tab_lojas_ativas:
        st.subheader("Unidades em Operação")
        
        # Filtra apenas o que o coordenador já aprovou
        query_ativas = "SELECT nome_loja, cnpj, endereco FROM lojas WHERE status = 'Aprovada' ORDER BY nome_loja"
        df_ativas = pd.read_sql(query_ativas, engine)
        
        if df_ativas.empty:
            st.warning("Nenhuma loja ativa no momento. Aguarde a aprovação das suas solicitações.")
        else:
            # Exibe uma lista limpa das lojas
            for _, loja in df_ativas.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"### 🏪 {loja['nome_loja']}")
                        st.write(f"**CNPJ:** {loja['cnpj']}")
                        st.write(f"**Endereço:** {loja['endereco']}")
                    with c2:
                        st.write("") # Espaçador
                        st.success("ATIVO")