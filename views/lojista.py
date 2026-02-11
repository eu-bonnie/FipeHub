import streamlit as st

def render_lojista():
    st.title("🏪 Portal do Lojista")
    st.subheader("Comparativo de Estoque vs FIPE")
    
    st.write("Gerencie os veículos da sua loja e veja a margem em relação à tabela oficial.")
    
    # Exemplo de funcionalidade futura
    st.text_input("Nome do Veículo no Estoque")
    st.number_input("Preço de Aquisição", min_value=0.0)
    st.button("Calcular Margem FIPE")