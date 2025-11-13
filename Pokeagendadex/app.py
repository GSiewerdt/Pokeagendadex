#--------------------------------------------------------------------SETUP----------------------------------------------------------------#
import sqlite3
import re
import requests


#----------------------------------------------------------------------------------------------------------------------------------------#

#--------------------------------------------------------------------BANCO DE DADOS------------------------------------------------------#
def salvar(self):
    conexao = sqlite3.connect("treinadores.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treinador (
            id_treinador TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            insignias INTEGER,
            foto TEXT,
            cidade TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo TEXT,
            nivel INTEGER,
            local TEXT,
            treinador_id TEXT,
            FOREIGN KEY (treinador_id) REFERENCES treinador (id_treinador)
        )
    """)
    try:
        cursor.execute("""
            INSERT INTO treinador (id_treinador, nome, insignias, foto, cidade)
            VALUES (?, ?, ?, ?, ?)
        """, (self.id_treinador, self.nome, self.insignias, self.foto, self.cidade))
        conexao.commit()
        print(f"Treinador {self.nome} salvo com sucesso!")
    except sqlite3.IntegrityError:
        print("Treinador já cadastrado.")
    finally:
        conexao.close()


#----------------------------------------------------------------------------------------------------------------------------------------#


#----------------------------------------------------------INFORMAÇÕES DO TREINADOR------------------------------------------------------#
class Treinador:
    def __init__(self, nome, id_treinador, insignias=0, foto=None, cidade=None):
        if not re.fullmatch(r"\d{6}", str(id_treinador)):
            raise ValueError("O ID do treinador deve conter exatamente 6 dígitos numéricos.")
        self.nome = nome
        self.id_treinador = str(id_treinador)
        self.insignias = insignias
        self.foto = foto
        self.cidade = cidade

    def salvar(self):
        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treinador (
                id_treinador TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                insignias INTEGER,
                foto TEXT,
                cidade TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                tipo TEXT,
                nivel INTEGER,
                treinador_id TEXT,
                FOREIGN KEY (treinador_id) REFERENCES treinador (id_treinador)
            )
        """)
        try:
            cursor.execute("""
                INSERT INTO treinador (id_treinador, nome, insignias, foto, cidade)
                VALUES (?, ?, ?, ?, ?)
            """, (self.id_treinador, self.nome, self.insignias, self.foto, self.cidade))
            conexao.commit()
            print(f"Treinador {self.nome} salvo com sucesso!")
        except sqlite3.IntegrityError:
            print("Erro: Já existe um treinador com este ID.")
        finally:
            conexao.close()

    def capturar_pokemon(self, nome_pokemon, nivel=5):
        """Captura um Pokémon via PokeAPI e associa ao treinador"""
        url = f"https://pokeapi.co/api/v2/pokemon/{nome_pokemon.lower()}"
        resposta = requests.get(url)
        
        if resposta.status_code != 200:
            print("Pokémon não encontrado!")
            return
        
        dados = resposta.json()
        nome = dados["name"].capitalize()
        tipo = ", ".join([t["type"]["name"] for t in dados["types"]])

        pokemon = Pokemon(nome, tipo, nivel, self.id_treinador)
        pokemon.salvar()

        print(f"{self.nome} capturou {nome} (Tipo: {tipo})!")

    def listar_pokemons(self):
        """Lista os Pokémons associados a este treinador"""
        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, tipo, nivel FROM pokemon WHERE treinador_id = ?", (self.id_treinador,))
        resultados = cursor.fetchall()
        conexao.close()

        print(f"\nPokémons de {self.nome}:")
        if resultados:
            for nome, tipo, nivel in resultados:
                print(f"- {nome} (Tipo: {tipo}, Nível: {nivel})")
        else:
            print("Nenhum Pokémon capturado ainda.")

    # ------------------------
    # Contar Pokémons
    # ------------------------
    def contar_pokemons(self, local):
        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM pokemon
            WHERE treinador_id = ? AND local = ?
        """, (self.id_treinador, local))
        quantidade = cursor.fetchone()[0]
        conexao.close()
        return quantidade

    # ------------------------
    # Listar equipe e box
    # ------------------------
    def listar_equipe(self):
        self._listar_por_local("equipe")

    def listar_box(self):
        self._listar_por_local("box")

    def _listar_por_local(self, local):
        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome, tipo, nivel FROM pokemon
            WHERE treinador_id = ? AND local = ?
        """, (self.id_treinador, local))
        resultados = cursor.fetchall()
        conexao.close()

        titulo = "Equipe" if local == "equipe" else "Box"
        print(f"\n=== {titulo} de {self.nome} ===")
        if resultados:
            for r in resultados:
                print(f"[{r[0]}] {r[1]} (Tipo: {r[2]}, Nível: {r[3]})")
        else:
            print(f"Nenhum Pokémon na {titulo.lower()}.")

    # ------------------------
    # Gerenciar equipe / box
    # ------------------------
    def mover_pokemon(self, pokemon_id, destino):
        """Move um Pokémon entre equipe e box"""
        if destino not in ("equipe", "box"):
            print("Destino inválido. Use 'equipe' ou 'box'.")
            return

        if destino == "equipe" and self.contar_pokemons("equipe") >= 6:
            print("A equipe já tem 6 Pokémons! Libere espaço primeiro.")
            return

        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE pokemon SET local = ?
            WHERE id = ? AND treinador_id = ?
        """, (destino, pokemon_id, self.id_treinador))
        conexao.commit()

        if cursor.rowcount > 0:
            print(f"Pokémon movido para a {destino} com sucesso!")
        else:
            print("Pokémon não encontrado ou pertence a outro treinador.")
        conexao.close()

#----------------------------------------------------------------------------------------------------------------------------------------#

#--------------------------------------------------------------POKÉMON-------------------------------------------------------------------#
class Pokemon:
    def __init__(self, nome, tipo, nivel, treinador_id):
        self.nome = nome
        self.tipo = tipo
        self.nivel = nivel
        self.treinador_id = treinador_id

    def salvar(self):
        """Salva o Pokémon no banco de dados"""
        conexao = sqlite3.connect("treinadores.db")
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO pokemon (nome, tipo, nivel, treinador_id)
            VALUES (?, ?, ?, ?)
        """, (self.nome, self.tipo, self.nivel, self.treinador_id))
        conexao.commit()
        conexao.close()

if __name__ == "__main__":
    ash = Treinador("Ash Ketchum", 123456, insignias=8, cidade="Pallet Town")
    ash.salvar()

    ash.capturar_pokemon("pikachu", nivel=25)
    ash.capturar_pokemon("charizard", nivel=50)
    ash.listar_pokemons()



#----------------------------------------------------------------------------------------------------------------------------------------#

#--------------------------------------------------------------POKÉDEX-------------------------------------------------------------------#

def buscar_pokemon(nome):
    url = f"https://pokeapi.co/api/v2/pokemon/{nome.lower()}"
    resposta = requests.get(url)
    
    if resposta.status_code != 200:
        print("Pokémon não encontrado!")
        return
    
    pokemon = resposta.json()
    
    print(f"\n=== {pokemon['name'].capitalize()} ===")
    print(f"ID: {pokemon['id']}")
    
    tipos = [t['type']['name'] for t in pokemon['types']]
    print("Tipos:", ", ".join(tipos))
    
    habilidades = [a['ability']['name'] for a in pokemon['abilities']]
    print("Habilidades:", ", ".join(habilidades))
    
    print(f"Altura: {pokemon['height'] / 10} m")
    print(f"Peso: {pokemon['weight'] / 10} kg")
    
    print("Sprites (imagens):", pokemon['sprites']['front_default'])




#----------------------------------------------------------------------------------------------------------------------------------------#


