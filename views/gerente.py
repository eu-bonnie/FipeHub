import streamlit as st
import pandas as pd
from sqlalchemy import text
from infra.database import engine

def render_gerente():
    st.title("⚙️ Painel de Gestão de Frota")
    st.caption("Perfil: Gerente de Inventário")

    tab_marcas, tab_modelos, tab_ajustes = st.tabs(["🏗️ Marcas", "🚘 Modelos", "🛠️ Ajustes e Correções"])

    # --- ABA 1: GESTÃO DE MARCAS ---
    with tab_marcas:
        st.markdown("### Criar Nova Marca")
        with st.form("nova_marca_form", clear_on_submit=True):
            nome_marca = st.text_input("Nome da Marca (Ex: TESLA, BYD)")
            btn_cadastrar_marca = st.form_submit_button("Cadastrar Marca")

        if btn_cadastrar_marca and nome_marca:
            marca_limpa = nome_marca.strip().upper()
            try:
                with engine.connect() as conn:
                    check = conn.execute(text("SELECT 1 FROM marcas_custom WHERE nome = :n"), {"n": marca_limpa}).fetchone()
                    if check:
                        st.error(f"A marca '{marca_limpa}' já existe.")
                    else:
                        conn.execute(text("INSERT INTO marcas_custom (nome) VALUES (:n)"), {"n": marca_limpa})
                        conn.commit()
                        st.success(f"Marca {marca_limpa} cadastrada!")
                        st.rerun()
            except Exception:
                st.error("Erro ao acessar o banco.")

        st.divider()
        df_marcas = pd.read_sql("SELECT nome FROM marcas_custom ORDER BY nome", engine)
        st.dataframe(df_marcas, use_container_width=True, hide_index=True)

    # --- ABA 2: GESTÃO DE MODELOS ---
    with tab_modelos:
        st.markdown("### Vincular Modelo a uma Marca")
        df_m_custom = pd.read_sql("SELECT nome FROM marcas_custom ORDER BY nome", engine)
        lista_marcas = df_m_custom['nome'].tolist()

        if not lista_marcas:
            st.warning("⚠️ Cadastre uma Marca primeiro.")
        else:
            with st.form("novo_modelo_form", clear_on_submit=True):
                marca_alvo = st.selectbox("Selecione a Marca", lista_marcas)
                nome_modelo = st.text_input("Nome do Modelo")
                btn_cadastrar_modelo = st.form_submit_button("Cadastrar Modelo")

            if btn_cadastrar_modelo and nome_modelo:
                modelo_limpo = nome_modelo.strip().upper()
                with engine.connect() as conn:
                    check = conn.execute(text("SELECT 1 FROM modelos_custom WHERE marca_nome = :m AND nome = :n"), 
                                        {"m": marca_alvo, "n": modelo_limpo}).fetchone()
                    if not check:
                        conn.execute(text("INSERT INTO modelos_custom (marca_nome, nome) VALUES (:m, :n)"), 
                                    {"m": marca_alvo, "n": modelo_limpo})
                        conn.commit()
                        st.success(f"Modelo {modelo_limpo} cadastrado!")
                        st.rerun()

        st.divider()
        df_modelos = pd.read_sql("SELECT marca_nome as Marca, nome as Modelo FROM modelos_custom ORDER BY marca_nome, nome", engine)
        st.dataframe(df_modelos, use_container_width=True, hide_index=True)

    # --- ABA 3: AJUSTES E CORREÇÕES (NOVA) ---
    with tab_ajustes:
        st.markdown("### 🛠️ Corrigir Erros de Cadastro")
        
        # Sub-seção: Editar Modelos
        st.markdown("#### Editar/Mover Modelo")
        df_mod_edit = pd.read_sql("SELECT id, nome, marca_nome FROM modelos_custom ORDER BY marca_nome, nome", engine)
        
        if not df_mod_edit.empty:
            df_mod_edit['display'] = df_mod_edit['marca_nome'] + " - " + df_mod_edit['nome']
            mod_selecionado = st.selectbox("Selecione o Modelo para Corrigir", df_mod_edit['display'].tolist())
            
            # Dados atuais do modelo selecionado
            dados_mod = df_mod_edit[df_mod_edit['display'] == mod_selecionado].iloc[0]
            
            c1, c2 = st.columns(2)
            novo_nome_mod = c1.text_input("Corrigir Nome do Modelo", value=dados_mod['nome']).upper()
            nova_marca_mod = c2.selectbox("Mover para a Marca Correta", lista_marcas, 
                                         index=lista_marcas.index(dados_mod['marca_nome']))
            
            col_b1, col_b2, _ = st.columns([1, 1, 2])
            if col_b1.button("Salvar Alteração", key="save_mod"):
                with engine.connect() as conn:
                    conn.execute(text("UPDATE modelos_custom SET nome = :n, marca_nome = :m WHERE id = :id"),
                                {"n": novo_nome_mod, "m": nova_marca_mod, "id": int(dados_mod['id'])})
                    conn.commit()
                st.success("Modelo atualizado!")
                st.rerun()
                
            if col_b2.button("🗑️ Excluir Modelo", key="del_mod"):
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM modelos_custom WHERE id = :id"), {"id": int(dados_mod['id'])})
                    conn.commit()
                st.rerun()

        st.divider()
        
        # Sub-seção: Editar Marcas
        st.markdown("#### Editar Nome da Marca")
        marca_para_editar = st.selectbox("Selecione a Marca para Renomear", lista_marcas)
        novo_nome_marca = st.text_input("Novo Nome da Marca", value=marca_para_editar).upper()
        
        if st.button("Renomear Marca"):
            with engine.connect() as conn:
                # Atualiza a marca e todos os modelos vinculados a ela em cascata
                conn.execute(text("UPDATE marcas_custom SET nome = :novo WHERE nome = :velho"), 
                            {"novo": novo_nome_marca, "velho": marca_para_editar})
                conn.execute(text("UPDATE modelos_custom SET marca_nome = :novo WHERE marca_nome = :velho"), 
                            {"novo": novo_nome_marca, "velho": marca_para_editar})
                conn.commit()
            st.success("Marca e vínculos atualizados!")
            st.rerun()