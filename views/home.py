import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_home():
    # --- DICIONÁRIO MANUAL (INFALÍVEL) ---
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    # --- ESTILIZAÇÃO MANTIDA ---
    st.markdown("""
        <style>
        .blue-text { color: #29b5e8; font-weight: bold; font-size: 1.2rem; margin-bottom: 5px; }
        .stButton>button {
            width: 100%; background-color: #005599 !important; color: white !important;
            font-weight: bold !important; border-radius: 8px !important; height: 3.5rem; border: none !important;
        }
        .result-box {
            border: 3px solid #005599; background-color: #121212; padding: 30px;
            border-radius: 15px; text-align: center; margin-top: 25px;
        }
        .price-highlight {
            background-color: #005599; color: white; padding: 15px 30px;
            border-radius: 8px; display: inline-block; margin: 15px 0;
            font-size: 2.2rem; font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🚗 Fipe<span style='color: #29b5e8;'>Hub</span> Local</h1>", unsafe_allow_html=True)
    st.divider()

    # --- CONSULTA DE DADOS ---
    try:
        # Busca as marcas disponíveis no banco
        df_marcas = pd.read_sql("SELECT DISTINCT marca FROM coletas_campo WHERE status = 'Aprovado'", engine)
        
        if df_marcas.empty:
            st.warning("⚠️ Nenhuma pesquisa aprovada encontrada no banco de dados.")
            return

        st.markdown('<p class="blue-text"> 1. SELECIONE A MARCA</p>', unsafe_allow_html=True)
        marca_nome = st.selectbox("Marca", df_marcas['marca'].unique(), label_visibility="collapsed")

        st.markdown('<p class="blue-text"> 2. ESCOLHA O MODELO</p>', unsafe_allow_html=True)
        query_mod = text("SELECT DISTINCT modelo FROM coletas_campo WHERE marca = :m AND status = 'Aprovado'")
        df_modelos = pd.read_sql(query_mod, engine, params={"m": marca_nome})
        modelo_nome = st.selectbox("Modelo", df_modelos['modelo'].unique(), label_visibility="collapsed")

        st.markdown('<p class="blue-text"> 3. DEFINA O ANO</p>', unsafe_allow_html=True)
        query_ano = text("SELECT DISTINCT ano FROM coletas_campo WHERE marca = :m AND modelo = :mo AND status = 'Aprovado'")
        df_anos = pd.read_sql(query_ano, engine, params={"m": marca_nome, "mo": modelo_nome})
        ano_label = st.selectbox("Ano Modelo", df_anos['ano'].unique(), label_visibility="collapsed")

        if st.button("BUSCAR PREÇO ATUAL"):
            # AQUI ESTÁ O SEGREDO: Buscamos a data exata da coleta
            query_final = text("""
                SELECT preco_anunciado, data_coleta 
                FROM coletas_campo 
                WHERE marca = :m AND modelo = :mo AND ano = :a AND status = 'Aprovado'
                ORDER BY data_coleta DESC LIMIT 1
            """)
            
            with engine.connect() as conn:
                resultado = conn.execute(query_final, {"m": marca_nome, "mo": modelo_nome, "a": ano_label}).fetchone()

            if resultado:
                valor_anunciado = resultado[0]
                data_db = resultado[1] # Pegamos o campo Date/Datetime do SQL

                # DEBUG: Isso vai mostrar para você exatamente o que o banco respondeu
                #st.write(f"DEBUG: A data que veio do banco é: {data_db}")

                # Conversão forçada usando o objeto de data do Python
                # Se data_db for string, tentamos converter, se for objeto, usamos direto
                try:
                    mes_idx = data_db.month
                    ano_idx = data_db.year
                except:
                    # Fallback caso o banco devolva string
                    dt = pd.to_datetime(data_db)
                    mes_idx = dt.month
                    ano_idx = dt.year

                label_mes = meses_pt.get(mes_idx, "Desconhecido")
                referencia_final = f"{label_mes} de {ano_idx}"

                st.markdown(f"""
                    <div class="result-box">
                        <h2 style='color: white; margin-bottom: 5px;'>{marca_nome} {modelo_nome}</h2>
                        <p style='color: #AAA;'>Ano: {ano_label}</p>
                        <div class="price-highlight">
                            R$ {valor_anunciado}
                        </div>
                        <p style='color: #29b5e8; font-weight: bold;'>Referência: {referencia_final}</p>
                        <small style='color: #666; display: block; margin-top: 10px;'>Fonte: Pesquisa de Campo Local</small>
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao processar consulta: {e}")