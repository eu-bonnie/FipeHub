import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from infra.database import engine
from sqlalchemy import text
from datetime import date

def render_pesquisador():
    st.title("🔍 Painel do Pesquisador")

    tab_mapa, tab_meus_envios = st.tabs(["📍 Zonas de Trabalho", "📋 Meus Envios"])

    with tab_mapa:
        st.subheader("Selecione uma área para iniciar o levantamento")
        df_areas = pd.read_sql("SELECT * FROM areas_pesquisa WHERE status = 'Pendente'", engine)

        if df_areas.empty:
            st.info("Você concluiu todas as zonas atribuídas!")
        else:
            for index, area in df_areas.iterrows():
                with st.expander(f"📍 Área: {area['municipio']} ({area['mes_referencia']})"):
                    # --- MAPA ---
                    centro_lat = (area['lat_min'] + area['lat_max']) / 2
                    centro_lon = (area['lon_min'] + area['lon_max']) / 2
                    map_missao = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
                    folium.Rectangle(
                        bounds=[[area['lat_min'], area['lon_min']], [area['lat_max'], area['lon_max']]],
                        color='#ff7800', fill=True, fill_opacity=0.2
                    ).add_to(map_missao)
                    st_folium(map_missao, width=700, height=300, key=f"map_{area['id']}")

                    if f"form_ativo_{area['id']}" not in st.session_state:
                        st.session_state[f"form_ativo_{area['id']}"] = False

                    if st.button("Iniciar Levantamento nesta Área", key=f"btn_ini_{area['id']}"):
                        st.session_state[f"form_ativo_{area['id']}"] = True

                    if st.session_state[f"form_ativo_{area['id']}"]:
                        st.markdown("---")
                        
                        # DATA DE REFERÊNCIA
                        data_ref_geral = st.date_input("Data de Referência", value=date.today(), key=f"dt_ref_{area['id']}")

                        qtd_lojas = st.number_input("Lojas visitadas", min_value=1, step=1, key=f"n_lojas_{area['id']}")
                        
                        df_lojas = pd.read_sql("SELECT id, nome_loja FROM lojas WHERE status = 'Aprovada'", engine)
                        lista_lojas = ["Outros (Nova Loja)"] + df_lojas['nome_loja'].tolist()

                        for i in range(int(qtd_lojas)):
                            with st.container(border=True):
                                st.subheader(f"🏪 Loja #{i+1}")
                                l_sel = st.selectbox("Selecione a Loja", lista_lojas, key=f"loja_sel_{area['id']}_{i}")
                                l_man_input = ""
                                if l_sel == "Outros (Nova Loja)":
                                    l_man_input = st.text_input("Nome da Loja Local", key=f"man_{area['id']}_{i}")

                                key_car_count = f"car_count_{area['id']}_{i}"
                                if key_car_count not in st.session_state:
                                    st.session_state[key_car_count] = 1
                                
                                for j in range(st.session_state[key_car_count]):
                                    st.markdown(f"**🚗 Veículo {j+1}**")
                                    c1, c2, c3, c4 = st.columns(4)
                                    with c1: 
                                        df_m = pd.read_sql("SELECT nome FROM marcas_custom ORDER BY nome", engine)
                                        marca_escolhida = st.selectbox("Marca", df_m['nome'].tolist(), key=f"ma_{area['id']}_{i}_{j}")
                                    with c2: 
                                        query_mod = text("SELECT nome FROM modelos_custom WHERE marca_nome = :m ORDER BY nome")
                                        df_mod = pd.read_sql(query_mod, engine, params={"m": marca_escolhida})
                                        st.selectbox("Modelo", df_mod['nome'].tolist(), key=f"mo_{area['id']}_{i}_{j}")
                                    with c3: st.text_input("Ano", key=f"an_{area['id']}_{i}_{j}")
                                    with c4: st.text_input("Preço R$", key=f"pr_{area['id']}_{i}_{j}")
                                
                                if st.button(f"➕ Add carro na Loja #{i+1}", key=f"add_car_{area['id']}_{i}"):
                                    st.session_state[key_car_count] += 1
                                    st.rerun()

                        if st.button("Finalizar e Enviar", type="primary", key=f"final_{area['id']}"):
                            with engine.connect() as conn:
                                for i in range(int(qtd_lojas)):
                                    num_carros = st.session_state.get(f"car_count_{area['id']}_{i}", 1)
                                    for j in range(num_carros):
                                        s = st.session_state
                                        l_sel_val = s.get(f"loja_sel_{area['id']}_{i}")
                                        l_man_val = s.get(f"man_{area['id']}_{i}", "")
                                        
                                        l_id = None
                                        if l_sel_val != "Outros (Nova Loja)":
                                            res = conn.execute(text("SELECT id FROM lojas WHERE nome_loja = :n"), {"n": l_sel_val}).fetchone()
                                            if res: l_id = res[0]

                                        conn.execute(text("""
                                            INSERT INTO coletas_campo 
                                            (area_id, loja_id, loja_nome_manual, marca, modelo, ano, preco_anunciado, data_coleta, status)
                                            VALUES (:a_id, :l_id, :l_man, :ma, :mo, :an, :pr, :dt, 'Pendente')
                                        """), {
                                            "a_id": area['id'], "l_id": l_id, "l_man": l_man_val,
                                            "ma": s.get(f"ma_{area['id']}_{i}_{j}"),
                                            "mo": s.get(f"mo_{area['id']}_{i}_{j}"),
                                            "an": s.get(f"an_{area['id']}_{i}_{j}"),
                                            "pr": s.get(f"pr_{area['id']}_{i}_{j}"),
                                            "dt": data_ref_geral
                                        })
                                conn.execute(text("UPDATE areas_pesquisa SET status = 'Em Análise' WHERE id = :id"), {"id": area['id']})
                                conn.commit()
                            st.success("Enviado!")
                            st.session_state[f"form_ativo_{area['id']}"] = False
                            st.rerun()

    # --- ABA 2: HISTÓRICO CORRIGIDA ---
    with tab_meus_envios:
        st.subheader("Histórico de Coletas")
        
        query_h = """
            SELECT 
                c.marca, c.modelo, c.ano, c.preco_anunciado, c.status, c.data_coleta,
                COALESCE(l.nome_loja, c.loja_nome_manual) as local_pesquisa
            FROM coletas_campo c
            LEFT JOIN lojas l ON c.loja_id = l.id
            ORDER BY c.data_coleta DESC
        """
        try:
            df_h = pd.read_sql(query_h, engine)
            if df_h.empty:
                st.info("Nenhuma coleta encontrada.")
            else:
                # --- CORREÇÃO AQUI: Converter para datetime e formatar ---
                df_h['data_coleta'] = pd.to_datetime(df_h['data_coleta'])
                df_h['status'] = df_h['status'].fillna('Pendente')
                
                status_opcoes = ["Pendente", "Aprovado", "Descartado", "Aguardando Aprovação"]
                filtro = st.multiselect("Filtrar status:", status_opcoes, default=["Pendente", "Aprovado", "Aguardando Aprovação"])
                
                df_mostra = df_h[df_h['status'].isin(filtro)]

                for (local, data), group in df_mostra.groupby(['local_pesquisa', 'data_coleta']):
                    with st.container(border=True):
                        # --- CORREÇÃO NA EXIBIÇÃO: data.strftime('%d/%m/%Y') ---
                        st.markdown(f"**🏪 {local}** | 📅 {data.strftime('%d/%m/%Y')}")
                        for _, item in group.iterrows():
                            cor = "orange" if "Pendente" in item['status'] or "Aguardando" in item['status'] else "green" if item['status'] == "Aprovado" else "red"
                            
                            c1, c2, c3 = st.columns([2, 1, 1])
                            c1.write(f"{item['marca']} {item['modelo']}")
                            c2.write(f"R$ {item['preco_anunciado']}")
                            c3.markdown(f":{cor}[{item['status']}]")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")