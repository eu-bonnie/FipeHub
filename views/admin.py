import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_admin():
    st.title("📊 Painel Administrativo")
    st.subheader("Indicadores de Performance e Monitoramento")

    # --- 1. BUSCA DE DADOS PARA KPIs ---
    try:
        with engine.connect() as conn:
            # Status 'Aprovada' para Lojas e 'Aprovado' para Coletas
            qtd_lojas = conn.execute(text("SELECT COUNT(*) FROM lojas WHERE status = 'Aprovada'")).scalar() or 0
            qtd_coletas = conn.execute(text("SELECT COUNT(*) FROM coletas_campo WHERE status = 'Aprovado'")).scalar() or 0
            
            # Buscas totais capturadas pela Home
            qtd_buscas = conn.execute(text("SELECT COUNT(*) FROM buscas_log")).scalar() or 0 

            # Modelo mais pesquisado pelos usuários (visto no Log da Home)
            query_top = text("""
                SELECT modelo, COUNT(*) as total 
                FROM buscas_log 
                GROUP BY modelo 
                ORDER BY total DESC LIMIT 1
            """)
            res_carro = conn.execute(query_top).fetchone()
            top_carro = res_carro[0] if res_carro else "N/A"
    except Exception as e:
        st.error(f"Erro ao carregar KPIs: {e}")
        qtd_lojas, qtd_coletas, qtd_buscas, top_carro = 0, 0, 0, "Erro"

    # --- 2. CARDS DE INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏪 Lojas Ativas", qtd_lojas)
    c2.metric("🚗 Coletas Validadas", qtd_coletas)
    c3.metric("🔎 Buscas Realizadas", qtd_buscas)
    c4.metric("🏆 Modelo mais Procurado", top_carro)

    st.divider()

    # --- 3. ABAS DE GESTÃO ---
    tab_dashboard, tab_usuarios = st.tabs(["📈 Monitoramento", "👤 Gerenciar Acessos"])

    with tab_dashboard:
        # 1.1 Tabela de Últimas Pesquisas (Puxando dados da Home)
        st.markdown("### 🕒 Últimas Consultas Realizadas")
        query_logs = "SELECT marca, modelo, ano, preco, data_consulta FROM buscas_log ORDER BY data_consulta DESC LIMIT 10"
        
        try:
            df_logs = pd.read_sql(text(query_logs), engine)
            if not df_logs.empty:
                # AJUSTE: Convertendo para datetime e formatando para mostrar APENAS A DATA
                df_logs['data_consulta'] = pd.to_datetime(df_logs['data_consulta']).dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_logs,
                    column_config={
                        "marca": "Marca",
                        "modelo": "Modelo",
                        "ano": "Ano",
                        "preco": st.column_config.NumberColumn("Preço Médio", format="R$ %.2f"),
                        "data_consulta": "Data da Busca"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhuma consulta registrada na Home ainda.")
        except Exception as e:
            st.error("Erro ao carregar a tabela de logs de consulta.")

        st.divider()

        # 1.2 Gráfico de Tendência (O que os clientes estão buscando na Home)
        st.markdown("### 📊 Tendência: Modelos mais Pesquisados")
        query_grafico = """
            SELECT modelo, COUNT(*) as quantidade 
            FROM buscas_log 
            GROUP BY modelo 
            ORDER BY quantidade DESC LIMIT 10
        """
        
        try:
            df_grafico = pd.read_sql(text(query_grafico), engine)
            if not df_grafico.empty:
                st.bar_chart(df_grafico.set_index('modelo'), color="#29b5e8")
            else:
                st.info("Aguardando dados de buscas para gerar o gráfico.")
        except Exception as e:
            st.error("Erro ao gerar gráfico de tendências.")

    with tab_usuarios:
        st.markdown("### 🔑 Criar Novo Código de Acesso")
        
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
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Erro: Este username já existe.")
                else:
                    st.warning("Preencha todos os campos.")

        st.divider()
        st.markdown("### 👥 Usuários Cadastrados")
        try:
            df_users = pd.read_sql(text("SELECT username, perfil FROM usuarios ORDER BY perfil, username"), engine)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        except:
            st.info("Nenhum usuário cadastrado.")