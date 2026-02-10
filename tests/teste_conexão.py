import sqlalchemy

# ATENÇÃO: Do seu computador para o Docker, ainda usamos 'localhost'
engine = sqlalchemy.create_engine("postgresql://user_fipe:password_fipe@localhost:5432/fipe_db")

try:
    with engine.connect() as conn:
        print("✅ Python e Docker estão conversando!")
except Exception as e:
    print(f"❌ Erro: {e}")