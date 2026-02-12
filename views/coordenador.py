import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from infra.database import engine
from sqlalchemy import text
import pandas as pd

def render_coordenador():
    st.title("⚖️ Painel de Controle do Coordenador")

    # Criando abas para separar as funções
    tab_zonas, tab_lojas, tab_coletas = st.tabs([
        "📍 Definir Zonas", 
        "🏪 Aprovar Lojas", 
        "🚗 Validar Coletas"
    ])

    # --- ABA 1: DEFINIÇÃO DE ZONAS (Seu código original aqui) ---
    with tab_zonas:
        st.subheader("Desenhe o quadrado da área de atuação no mapa")
        
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            mes = st.selectbox("Mês de Referência", ["Março/2026", "Abril/2026"], key="mes_coord")
        with col_input2:
            cidade = st.text_input("Nome da Região/Cidade", key="cidade_coord")

        m = folium.Map(location=[-15.78, -47.93], zoom_start=4)
        draw = Draw(
            draw_options={
                'polyline': False, 'polygon': False, 'circle': False, 
                'marker': False, 'circlemarker': False, 'rectangle': True
            }
        )
        draw.add_to(m)

        output = st_folium(m, width=900, height=500, key="mapa_coordenador")

        if output['all_drawings']:
            desenho = output['all_drawings'][-1]
            if desenho['geometry']['type'] == 'Polygon':
                coords = desenho['geometry']['coordinates'][0]
                lats = [c[1] for c in coords]
                lons = [c[0] for c in coords]
                
                lat_min, lat_max = min(lats), max(lats)
                lon_min, lon_max = min(lons), max(lons)

                st.write(f"✅ Área delimitada: Lat({lat_min:.4f} a {lat_max:.4f}) | Lon({lon_min:.4f} a {lon_max:.4f})")

                if st.button("Confirmar e Enviar para Pesquisador"):
                    if not cidade:
                        st.error("Por favor, digite o nome da cidade/região.")
                    else:
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO areas_pesquisa (municipio, lat_min, lat_max, lon_min, lon_max, mes_referencia)
                                VALUES (:mun, :lmin, :lmax, :lonmin, :lonmax, :mes)
                            """), {"mun": cidade, "lmin": lat_min, "lmax": lat_max, "lonmin": lon_min, "lonmax": lon_max, "mes": mes})
                            conn.commit()
                        st.success(f"Zona de pesquisa em '{cidade}' enviada!")

    # --- ABA 2: APROVAR LOJAS ---
    with tab_lojas:
        st.subheader("Solicitações de Cadastro de Lojas")
        query_lojas = "SELECT * FROM lojas WHERE status = 'Pendente'"
        df_lojas_pendentes = pd.read_sql(query_lojas, engine)

        if df_lojas_pendentes.empty:
            st.info("Não há lojas aguardando aprovação.")
        else:
            for index, loja in df_lojas_pendentes.iterrows():
                with st.expander(f"🏪 Loja: {loja['nome_loja']}"):
                    st.write(f"**CNPJ:** {loja['cnpj']}")
                    st.write(f"**Endereço:** {loja['endereco']}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Aprovar Loja", key=f"app_loja_{loja['id']}"):
                        with engine.connect() as conn:
                            conn.execute(text("UPDATE lojas SET status = 'Aprovada' WHERE id = :id"), {"id": loja['id']})
                            conn.commit()
                        st.success("Loja Aprovada!")
                        st.rerun()
                    
                    if c2.button("❌ Rejeitar", key=f"rej_loja_{loja['id']}"):
                        with engine.connect() as conn:
                            conn.execute(text("UPDATE lojas SET status = 'Rejeitada' WHERE id = :id"), {"id": loja['id']})
                            conn.commit()
                        st.rerun()

    # --- ABA 3: VALIDAR COLETAS (O que o pesquisador mandou) ---
    with tab_coletas:
        st.subheader("📋 Validação de Levantamentos de Campo")
        
        # SQL que traz as coletas pendentes e informações da área relacionada
        query_coletas = """
            SELECT 
                c.id, c.marca, c.modelo, c.ano, c.preco_anunciado, c.data_coleta,
                a.municipio, a.mes_referencia,
                COALESCE(l.nome_loja, c.loja_nome_manual) as nome_local
            FROM coletas_campo c
            JOIN areas_pesquisa a ON c.area_id = a.id
            LEFT JOIN lojas l ON c.loja_id = l.id
            WHERE c.status = 'Aguardando Aprovação'
            ORDER BY a.municipio, c.data_coleta DESC
        """
        df_coletas = pd.read_sql(query_coletas, engine)

        if df_coletas.empty:
            st.info("Nenhuma coleta pendente de validação.")
        else:
            # Agrupamos primeiro pela ÁREA (Município + Mês)
            for (mun, mes), grupo_area in df_coletas.groupby(['municipio', 'mes_referencia']):
                st.markdown(f"### 📍 Região: {mun} ({mes})")
                
                # Dentro da área, agrupamos por LOJA e HORA da coleta
                for (loja, data), grupo_loja in grupo_area.groupby(['nome_local', 'data_coleta']):
                    with st.container(border=True):
                        # Cabeçalho da Coleta
                        c_head1, c_head2 = st.columns([3, 1])
                        c_head1.write(f"🏠 **Loja:** {loja}")
                        c_head2.write(f"🕒 {data.strftime('%d/%m/%Y %H:%M')}")
                        
                        st.divider()

                        # Lista de Carros coletados naquela loja naquele momento
                        for _, row in grupo_loja.iterrows():
                            col_car, col_btn = st.columns([3, 1])
                            
                            with col_car:
                                st.write(f"🚗 **{row['marca']} {row['modelo']}** - Ano: {row['ano']}")
                                # Correção visual do R$ (sem LaTeX)
                                st.write(f"💰 Preço Informado: R$ {row['preco_anunciado']}")
                            
                            with col_btn:
                                # Botões de ação por veículo
                                if st.button("✅ Validar", key=f"val_{row['id']}"):
                                    with engine.connect() as conn:
                                        conn.execute(text("UPDATE coletas_campo SET status = 'Aprovado' WHERE id = :id"), {"id": row['id']})
                                        conn.commit()
                                    st.rerun()
                                
                                if st.button("🗑️ Descartar", key=f"des_{row['id']}"):
                                    with engine.connect() as conn:
                                        conn.execute(text("UPDATE coletas_campo SET status = 'Descartado' WHERE id = :id"), {"id": row['id']})
                                        conn.commit()
                                    st.rerun()
                st.write("---") # Separador entre áreas diferentes