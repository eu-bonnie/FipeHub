import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine
import re

def render_admin():
    st.title("📊 Painel Administrativo")
    st.subheader("Indicadores de Performance e Monitoramento")

    # --- 1. BUSCA DE DADOS PARA KPIs ---
    try:
        with engine.connect() as conn:
            qtd_lojas = conn.execute(text("SELECT COUNT(*) FROM lojas WHERE status = 'Aprovada'")).scalar() or 0
            qtd_coletas = conn.execute(text("SELECT COUNT(*) FROM coletas_campo WHERE status = 'Aprovado'")).scalar() or 0
            qtd_buscas = conn.execute(text("SELECT COUNT(*) FROM buscas_log")).scalar() or 0 

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
        st.markdown("### 🕒 Histórico Recente de Consultas")
        query_logs = "SELECT marca, modelo, ano, preco, data_consulta FROM buscas_log ORDER BY data_consulta DESC LIMIT 10"
        
        try:
            df_logs = pd.read_sql(text(query_logs), engine)
            
            if not df_logs.empty:
                # 1. AJUSTE DA DATA: Converte para datetime e formata para o padrão brasileiro
                df_logs['data_consulta'] = pd.to_datetime(df_logs['data_consulta']).dt.strftime('%d/%m/%Y')

                # 2. LIMPEZA DO PREÇO: Função robusta para converter qualquer formato em float
                def limpar_preco_para_float(valor):
                    if valor is None or valor == '': return 0.0
                    if isinstance(valor, (int, float)): return float(valor)
                    
                    # Remove R$, espaços e pontos de milhar, garante que o decimal seja ponto
                    texto = str(valor).replace('R$', '').replace(' ', '')
                    
                    # Se houver vírgula e ponto, remove o ponto (milhar) e troca a vírgula (decimal)
                    if ',' in texto and '.' in texto:
                        texto = texto.replace('.', '').replace(',', '.')
                    # Se houver apenas vírgula, troca por ponto
                    elif ',' in texto:
                        texto = texto.replace(',', '.')
                        
                    try:
                        return float(texto)
                    except ValueError:
                        return 0.0

                df_logs['preco'] = df_logs['preco'].apply(limpar_preco_para_float)

                # 3. EXIBIÇÃO EM TABELA: Uso de column_config para formatação de moeda
                st.dataframe(
                    df_logs,
                    column_config={
                        "marca": "Marca",
                        "modelo": "Modelo",
                        "ano": "Ano",
                        "preco": st.column_config.NumberColumn(
                            "Preço Médio",
                            format="R$ %.2f", # Formata visualmente como moeda
                            help="Valor capturado durante a consulta"
                        ),
                        "data_consulta": "Data da Consulta"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhuma consulta registrada na Home ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")

        st.divider()

        # --- GRÁFICO DE TENDÊNCIA ---
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
        except Exception as e:
            st.error("Erro ao gerar gráfico.")

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
                        st.success(f"Acesso criado para {new_user}!")
                        st.rerun() 
                    except Exception as e:
                        st.error("Erro: Este username já existe ou houve falha no banco.")
                else:
                    st.warning("Preencha todos os campos.")

        st.divider()
        st.markdown("### 👥 Usuários Cadastrados")
        try:
            df_users = pd.read_sql(text("SELECT username, perfil FROM usuarios ORDER BY perfil, username"), engine)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        except:
            st.info("Nenhum usuário cadastrado.")