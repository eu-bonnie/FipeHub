import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_home():
    # --- DICIONÁRIO MANUAL ---
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    # --- ESTILIZAÇÃO ---
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

    try:
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
            with engine.connect() as conn:
                query_final = text("""
                    SELECT preco_anunciado, data_coleta 
                    FROM coletas_campo 
                    WHERE marca = :m AND modelo = :mo AND ano = :a AND status = 'Aprovado'
                    ORDER BY data_coleta DESC LIMIT 1
                """)
                
                resultado = conn.execute(query_final, {"m": marca_nome, "mo": modelo_nome, "a": ano_label}).fetchone()

                if resultado:
                    # --- TRATAMENTO E FORMATAÇÃO BONITA ---
                    valor_raw = str(resultado[0])
                    try:
                        # Converte para float puro primeiro
                        valor_numerico = float(valor_raw.replace('.', '').replace(',', '.'))
                        # Formata como string no padrão R$ 88.000,00
                        preco_bonito = f"{valor_numerico:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    except:
                        preco_bonito = valor_raw # Fallback caso falhe
                    
                    data_db = resultado[1]

                    # Gravação do log (usamos o float limpo para o banco)
                    valor_para_banco = float(valor_raw.replace('.', '').replace(',', '.'))
                    conn.execute(text("""
                        INSERT INTO buscas_log (marca, modelo, ano, preco, data_consulta)
                        VALUES (:ma, :mo, :an, :pr, CURRENT_TIMESTAMP)
                    """), {"ma": marca_nome, "mo": modelo_nome, "an": ano_label, "pr": valor_para_banco})
                    conn.commit()

                    try:
                        mes_idx, ano_idx = data_db.month, data_db.year
                    except:
                        dt = pd.to_datetime(data_db)
                        mes_idx, ano_idx = dt.month, dt.year

                    label_mes = meses_pt.get(mes_idx, "Desconhecido")

                    st.markdown(f"""
                        <div class="result-box">
                            <h2 style='color: white; margin-bottom: 5px;'>{marca_nome} {modelo_nome}</h2>
                            <p style='color: #AAA;'>Ano: {ano_label}</p>
                            <div class="price-highlight">
                                R$ {preco_bonito}
                            </div>
                            <p style='color: #29b5e8; font-weight: bold;'>Referência: {label_mes} de {ano_idx}</p>
                            <small style='color: #666; display: block; margin-top: 10px;'>Fonte: Pesquisa de Campo Local</small>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Nenhum preço encontrado.")
                    
    except Exception as e:
        st.error(f"Erro ao processar consulta: {e}")