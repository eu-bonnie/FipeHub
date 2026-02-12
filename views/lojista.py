import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_lojista():
    st.title("🏪 Área do Lojista")

    tab_cadastro, tab_meus_envios, tab_insights = st.tabs([
        "🆕 Solicitar Cadastro", 
        "📋 Minhas Solicitações",
        "📊 Posicionamento de Mercado"
    ])

    # --- ABA 1: CADASTRO (Mantemos o código anterior) ---
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

    # --- ABA 2: MINHAS SOLICITAÇÕES ---
    with tab_meus_envios:
        df_lojas = pd.read_sql("SELECT * FROM lojas ORDER BY id DESC", engine)
        if df_lojas.empty:
            st.info("Nenhuma solicitação encontrada.")
        else:
            for _, loja in df_lojas.iterrows():
                cor = "orange" if loja['status'] == 'Pendente' else "green" if loja['status'] == 'Aprovada' else "red"
                with st.container(border=True):
                    st.markdown(f"**{loja['nome_loja']}** - :{cor}[{loja['status'].upper()}]")
                    st.caption(f"📍 {loja['endereco']}")

    # --- ABA 3: INSIGHTS (Simplificada) ---
    with tab_insights:
        st.subheader("Análise de Visitas")
        
        # Busca a primeira loja aprovada
        loja_aprovada = pd.read_sql("SELECT id, nome_loja FROM lojas WHERE status = 'Aprovada' LIMIT 1", engine)
        
        if loja_aprovada.empty:
            st.warning("📊 Os insights ficarão disponíveis assim que sua loja for aprovada.")
        else:
            # Conversão segura para int (evita o erro numpy que tivemos antes)
            id_loja = int(loja_aprovada.iloc[0]['id'])
            nome_loja = loja_aprovada.iloc[0]['nome_loja']

            # Query para contar visitas validadas
            metrics_query = text("SELECT COUNT(*) FROM coletas_campo WHERE loja_id = :id AND status = 'Aprovado'")
            with engine.connect() as conn:
                total_coletas = conn.execute(metrics_query, {"id": id_loja}).scalar()

            # Exibição de métricas simples
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Visitas Validadas", f"{total_coletas}")
            col_m2.metric("Loja Credenciada", "Ativa")