import pandas as pd
from sqlalchemy import create_engine, text

# Conexão via Docker (localhost para o seu Python)
DB_URL = "postgresql://user_fipe:password_fipe@localhost:5432/fipe_db"
engine = create_engine(DB_URL)

def init_db():
    """Cria as tabelas iniciais se não existirem."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buscas_log (
                id SERIAL PRIMARY KEY,
                marca VARCHAR(100),
                modelo VARCHAR(100),
                ano VARCHAR(20),
                preco VARCHAR(50),
                data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

def salvar_consulta(dados):
    """Abstração para registrar logs de uso no banco."""
    df = pd.DataFrame([dados])
    df.to_sql('buscas_log', engine, if_exists='append', index=False)