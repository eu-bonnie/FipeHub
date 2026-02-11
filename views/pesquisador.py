import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from infra.database import engine

def render_pesquisador():
    st.title("🔍 Minhas Zonas de Trabalho")

    df_areas = pd.read_sql("SELECT * FROM areas_pesquisa WHERE status = 'Pendente'", engine)

    if df_areas.empty:
        st.info("Nenhuma área de pesquisa atribuída.")
    else:
        for index, area in df_areas.iterrows():
            with st.expander(f"📍 Área: {area['municipio']} ({area['mes_referencia']})"):
                # Criar mapa mostrando o retângulo
                centro_lat = (area['lat_min'] + area['lat_max']) / 2
                centro_lon = (area['lon_min'] + area['lon_max']) / 2
                
                map_missao = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
                
                # Desenha o quadrado no mapa do pesquisador
                folium.Rectangle(
                    bounds=[[area['lat_min'], area['lon_min']], [area['lat_max'], area['lon_max']]],
                    color='#ff7800',
                    fill=True,
                    fill_color='#ffff00',
                    fill_opacity=0.2
                ).add_to(map_missao)

                st_folium(map_missao, width=700, height=300, key=f"map_{area['id']}")
                
                st.write("---")
                st.button(f"Registrar Coleta nesta Zona", key=f"btn_{area['id']}")