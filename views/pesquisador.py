import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from infra.database import engine
from sqlalchemy import text

def render_pesquisador():
    st.title("🔍 Painel do Pesquisador")

    tab_mapa, tab_meus_envios = st.tabs(["📍 Zonas de Trabalho", "📋 Meus Envios"])

    with tab_mapa:
        st.subheader("Selecione uma área para iniciar o levantamento")
        # Só mostra áreas com status 'Pendente'
        df_areas = pd.read_sql("SELECT * FROM areas_pesquisa WHERE status = 'Pendente'", engine)

        if df_areas.empty:
            st.info("Você concluiu todas as zonas atribuídas! Aguarde novas ordens do coordenador.")
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

                    # Ativar formulário no session_state
                    if f"form_ativo_{area['id']}" not in st.session_state:
                        st.session_state[f"form_ativo_{area['id']}"] = False

                    if st.button("Iniciar Levantamento nesta Área", key=f"btn_ini_{area['id']}"):
                        st.session_state[f"form_ativo_{area['id']}"] = True

                    if st.session_state[f"form_ativo_{area['id']}"]:
                        st.markdown("---")
                        qtd_lojas = st.number_input("Quantas lojas você visitou nesta área?", min_value=1, step=1, key=f"n_lojas_{area['id']}")
                        
                        df_lojas = pd.read_sql("SELECT id, nome_loja FROM lojas WHERE status = 'Aprovada'", engine)
                        lista_lojas = ["Outros (Nova Loja)"] + df_lojas['nome_loja'].tolist()

                        # Loop de Lojas
                        for i in range(int(qtd_lojas)):
                            with st.container(border=True):
                                st.subheader(f"🏪 Loja #{i+1}")
                                l_sel = st.selectbox("Selecione a Loja", lista_lojas, key=f"loja_sel_{area['id']}_{i}")
                                if l_sel == "Outros (Nova Loja)":
                                    st.text_input("Nome da Loja Local", key=f"man_{area['id']}_{i}")

                                # Controle de quantos carros por esta loja específica
                                key_car_count = f"car_count_{area['id']}_{i}"
                                if key_car_count not in st.session_state:
                                    st.session_state[key_car_count] = 1
                                
                                # Loop de Carros dentro da Loja
                                for j in range(st.session_state[key_car_count]):
                                    st.markdown(f"**🚗 Veículo {j+1}**")
                                    c1, c2, c3, c4 = st.columns(4)
                                    with c1: st.text_input("Marca", key=f"ma_{area['id']}_{i}_{j}")
                                    with c2: st.text_input("Modelo", key=f"mo_{area['id']}_{i}_{j}")
                                    with c3: st.text_input("Ano", key=f"an_{area['id']}_{i}_{j}")
                                    with c4: st.text_input("Preço R$", key=f"pr_{area['id']}_{i}_{j}")
                                
                                if st.button(f"➕ Adicionar outro carro na Loja #{i+1}", key=f"add_car_{area['id']}_{i}"):
                                    st.session_state[key_car_count] += 1
                                    st.rerun()

                        # --- BOTÃO FINALIZAR ÁREA ---
                        if st.button("Finalizar e Enviar Área Completa", type="primary", key=f"final_{area['id']}"):
                            with engine.connect() as conn:
                                # 1. Salvar todas as coletas (Loop de Lojas e Carros)
                                for i in range(int(qtd_lojas)):
                                    num_carros = st.session_state.get(f"car_count_{area['id']}_{i}", 1)
                                    for j in range(num_carros):
                                        s = st.session_state
                                        # Captura dados
                                        l_sel = s.get(f"loja_sel_{area['id']}_{i}")
                                        l_man = s.get(f"man_{area['id']}_{i}", "")
                                        marca = s.get(f"ma_{area['id']}_{i}_{j}")
                                        modelo = s.get(f"mo_{area['id']}_{i}_{j}")
                                        ano = s.get(f"an_{area['id']}_{i}_{j}")
                                        preco = s.get(f"pr_{area['id']}_{i}_{j}")

                                        # Busca ID da loja se não for manual
                                        l_id = None
                                        if l_sel != "Outros (Nova Loja)":
                                            res_loja = conn.execute(text("SELECT id FROM lojas WHERE nome_loja = :nome"), {"nome": l_sel}).fetchone()
                                            if res_loja: l_id = res_loja[0]

                                        # Executa o INSERT
                                        conn.execute(text("""
                                            INSERT INTO coletas_campo 
                                            (area_id, loja_id, loja_nome_manual, marca, modelo, ano, preco_anunciado, status)
                                            VALUES (:a_id, :l_id, :l_man, :ma, :mo, :an, :pr, 'Aguardando Aprovação')
                                        """), {
                                            "a_id": area['id'], "l_id": l_id, "l_man": l_man,
                                            "ma": marca, "mo": modelo, "an": ano, "pr": preco
                                        })
                                
                                # 2. Atualizar status da ÁREA para sumir da lista
                                conn.execute(text("UPDATE areas_pesquisa SET status = 'Em Análise' WHERE id = :id"), {"id": area['id']})
                                conn.commit()
                            
                            st.success("Tudo enviado com sucesso!")
                            st.session_state[f"form_ativo_{area['id']}"] = False
                            st.rerun()

    # --- ABA 2: MEUS ENVIOS ---
    with tab_meus_envios:
        st.subheader("Histórico de Levantamentos Realizados")
        
        query_historico = """
            SELECT 
                c.marca, c.modelo, c.ano, c.preco_anunciado, c.status, c.data_coleta,
                COALESCE(l.nome_loja, c.loja_nome_manual) as local_pesquisa
            FROM coletas_campo c
            LEFT JOIN lojas l ON c.loja_id = l.id
            ORDER BY c.data_coleta DESC
        """
        df_historico = pd.read_sql(query_historico, engine)

        if df_historico.empty:
            st.info("Você ainda não realizou nenhuma coleta.")
        else:
            status_filtro = st.multiselect("Filtrar por Status:", ["Aguardando Aprovação", "Aprovado", "Descartado"], default=["Aguardando Aprovação", "Aprovado"])
            df_filtrado = df_historico[df_historico['status'].isin(status_filtro)]

            # Agrupamos por Local e Data/Hora para mostrar a Loja no topo
            for (local, data), group in df_filtrado.groupby(['local_pesquisa', 'data_coleta']):
                with st.container(border=True):
                    # --- CABEÇALHO DO CARD (Loja e Horário) ---
                    col_header_1, col_header_2 = st.columns([3, 1])
                    col_header_1.markdown(f"### 🏪 {local}")
                    col_header_2.write(f"🕒 {data.strftime('%H:%M')}")
                    st.caption(f"📅 Data: {data.strftime('%d/%m/%Y')}")
                    
                    st.divider() # Linha separadora
                    
                    # --- CORPO DO CARD (Lista de Carros) ---
                    for _, item in group.iterrows():
                        cor = "orange" if item['status'] == "Aguardando Aprovação" else "green" if item['status'] == "Aprovado" else "red"
                        
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"🚗 **{item['marca']} {item['modelo']}** ({item['ano']})")
                        
                        # Correção do R$: usamos markdown com o símbolo de escape ou apenas f-string limpa
                        c2.write(f"R$ {item['preco_anunciado']}") 
                        
                        c3.markdown(f":{cor}[**{item['status']}**]")