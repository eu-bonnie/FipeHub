import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from infra.database import engine
from sqlalchemy import text

def render_coordenador():
    st.title("📍 Definição de Zonas de Pesquisa")
    st.subheader("Desenhe o quadrado da área de atuação no mapa")

    mes = st.selectbox("Mês de Referência", ["Março/2026", "Abril/2026"])
    cidade = st.text_input("Nome da Região/Cidade")

    # Criar o mapa centralizado no Brasil
    m = folium.Map(location=[-15.78, -47.93], zoom_start=4)
    
    # Adiciona a ferramenta de desenho (apenas retângulos)
    draw = Draw(
        draw_options={
            'polyline': False, 'polygon': False, 'circle': False, 
            'marker': False, 'circlemarker': False, 'rectangle': True
        }
    )
    draw.add_to(m)

    # Renderiza o mapa e captura os dados do desenho
    output = st_folium(m, width=900, height=500)

    # Lógica para extrair as coordenadas do retângulo desenhado
    if output['all_drawings']:
        # Pega o último desenho feito
        desenho = output['all_drawings'][-1]
        if desenho['geometry']['type'] == 'Polygon':
            coords = desenho['geometry']['coordinates'][0]
            # Extrai os limites (lat_min, lat_max, lon_min, lon_max)
            lats = [c[1] for c in coords]
            lons = [c[0] for c in coords]
            
            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)

            st.write(f"✅ Área delimitada: Lat({lat_min:.4f} a {lat_max:.4f}) | Lon({lon_min:.4f} a {lon_max:.4f})")

            if st.button("Confirmar e Enviar para Pesquisador"):
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO areas_pesquisa (municipio, lat_min, lat_max, lon_min, lon_max, mes_referencia)
                        VALUES (:mun, :lmin, :lmax, :lonmin, :lonmax, :mes)
                    """), {"mun": cidade, "lmin": lat_min, "lmax": lat_max, "lonmin": lon_min, "lonmax": lon_max, "mes": mes})
                    conn.commit()
                st.success(f"Zona de pesquisa em '{cidade}' criada!")