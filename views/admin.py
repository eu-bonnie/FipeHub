import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_admin():
    st.title("📊 Painel Administrativo")
    st.subheader("Indicadores de Performance e Monitoramento")

    # --- 1. BUSCA DE DADOS PARA KPIs ---
    with engine.connect() as conn:
        qtd_lojas = conn.execute(text("SELECT COUNT(*) FROM lojas WHERE status = 'Aprovada'")).scalar()
        qtd_coletas = conn.execute(text("SELECT COUNT(*) FROM coletas_campo WHERE status = 'Aprovado'")).scalar()
        qtd_usuarios = conn.execute(text("SELECT COUNT(*) FROM buscas_log")).scalar() 

        query_top = text("SELECT modelo, COUNT(*) as total FROM coletas_campo GROUP BY modelo ORDER BY total DESC LIMIT 1")
        res_carro = conn.execute(query_top).fetchone()
        top_carro = res_carro[0] if res_carro else "N/A"

    # --- 2. CARDS DE INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏪 Lojas Ativas", qtd_lojas)
    c2.metric("🚗 Coletas Validadas", qtd_coletas)
    c3.metric("🔎 Buscas Realizadas", qtd_usuarios)
    c4.metric("🏆 Modelo em Alta", top_carro)

    st.divider()

    # --- 3. ABAS DE GESTÃO ---
    tab_dashboard, tab_usuarios = st.tabs(["📈 Monitoramento", "👤 Gerenciar Acessos"])

    with tab_dashboard:
        # 1.1 Tabela de Últimas Pesquisas (Log de Consultas)
        st.markdown("### 🕒 Últimas Consultas Realizadas")
        query_logs = "SELECT marca, modelo, ano, preco, data_consulta FROM buscas_log ORDER BY data_consulta DESC LIMIT 10"
        
        try:
            df_logs = pd.read_sql(query_logs, engine)
            if not df_logs.empty:
                # Formatando a data para exibição
                df_logs['data_consulta'] = pd.to_datetime(df_logs['data_consulta']).dt.strftime('%d/%m %H:%M')
                
                st.dataframe(
                    df_logs,
                    column_config={
                        "marca": "Marca",
                        "modelo": "Modelo",
                        "ano": "Ano",
                        "preco": "Valor",
                        "data_consulta": "Data/Hora"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhuma consulta registrada no sistema.")
        except Exception as e:
            st.error("Erro ao carregar a tabela de logs.")

        st.divider()

        # 1.2 Gráfico de Modelos Mais Pesquisados
        st.markdown("### 📊 Modelos Mais Pesquisados")
        query_grafico = """
            SELECT modelo, COUNT(*) as quantidade 
            FROM buscas_log 
            GROUP BY modelo 
            ORDER BY quantidade DESC LIMIT 10
        """
        
        try:
            df_grafico = pd.read_sql(query_grafico, engine)
            if not df_grafico.empty:
                st.bar_chart(df_grafico.set_index('modelo'), color="#29b5e8")
            else:
                st.info("Aguardando mais dados para gerar o gráfico.")
        except Exception as e:
            st.error("Erro ao gerar gráfico de tendências.")

    with tab_usuarios:
        st.markdown("### 🔑 Criar Novo Código de Acesso")
        
        # Formulário para criar novos usuários/códigos
        with st.form("form_novo_usuario", clear_on_submit=True):
            col_u1, col_u2 = st.columns(2)
            new_user = col_u1.text_input("Username (Ex: joao_pesquisa)")
            new_code = col_u2.text_input("Código de Acesso", type="password")
            new_perfil = st.selectbox("Perfil de Acesso", ["Pesquisador", "Coordenador", "Lojista", "Admin", "Gerente"])
            
            if st.form_submit_button("Gerar Acesso"):
                if new_user and new_code:
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO usuarios (username, codigo, perfil) 
                                VALUES (:u, :c, :p)
                            """), {"u": new_user, "c": new_code, "p": new_perfil})
                            conn.commit()
                        st.success(f"Acesso criado: {new_user} agora é {new_perfil}!")
                    except Exception as e:
                        st.error(f"Erro: Este username já existe.")
                else:
                    st.warning("Preencha todos os campos.")

        st.divider()
        st.markdown("### 👥 Usuários Cadastrados")
        df_users = pd.read_sql("SELECT username, perfil FROM usuarios", engine)
        st.table(df_users)