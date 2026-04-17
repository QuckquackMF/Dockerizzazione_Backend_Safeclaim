from flask import Flask, request, jsonify
from datetime import datetime, UTC
import mysql.connector
import pymongo
from bson.objectid import ObjectId
import threading
from gradio_client import Client, handle_file
from Storage import carica_immagine
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURAZIONE DATABASE ---

# MySQL (MariaDB)
MYSQL_CONFIG = {
    "host": "mysql",
    "user": "pythonuser",
    "password": "password123",
    "database": "gestione_assicurazioni"
}

def get_db_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

# MongoDB Atlas
MONGO_URI = "mongodb+srv://dbFakeClaim:xxx123%23%23@cluster0.zgw1jft.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client["FakeClaim"]
    sinistri_col = mongo_db["Sinistri"]
    soccorso_col = mongo_db["Soccorso"]
    
    mongo_client.admin.command('ping')
    print("✅ Connessione a MongoDB Atlas riuscita!")
except Exception as e:
    print(f"❌ Errore connessione MongoDB: {e}")

HF_TOKEN = "IL_TUO_TOKEN_QUI"

PROMPT_PERITO = (
    "Agisci come un perito assicurativo esperto. Analizza l'immagine e descrivi l'incidente "
    "identificando: 1. Punto d'impatto principale. 2. Componenti danneggiati (es. paraurti, "
    "gruppi ottici, cristalli). 3. Entità del danno (graffio, ammaccatura, deformazione strutturale). "
    "Usa un linguaggio tecnico."
)

def analizza_immagine_ai(sinistro_id: str, image_url: str):
    try:
        print(f"[AI] Avvio analisi per sinistro {sinistro_id}...")
        client = Client("fancyfeast/joy-caption-beta-one", token=HF_TOKEN)
        risultato_ai = client.predict(
            input_image=handle_file(image_url),
            prompt=PROMPT_PERITO,
            temperature=0.5,
            top_p=0.9,
            max_new_tokens=512,
            log_prompt=True,
            api_name="/chat_joycaption"
        )
        print(f"✅ [AI] Analisi completata per sinistro {sinistro_id}")
        col_sinistri.update_one(
            {"_id": ObjectId(sinistro_id)},
            {"$set": {
                "analisi_ai": {
                    "testo": risultato_ai,
                    "modello": "joy-caption-beta-one",
                    "data_analisi": datetime.now(UTC),
                    "stato": "completata"
                }
            }}
        )
    except Exception as e:
        print(f"[AI] Errore analisi sinistro {sinistro_id}: {e}")
        try:
            col_sinistri.update_one(
                {"_id": ObjectId(sinistro_id)},
                {"$set": {
                    "analisi_ai": {
                        "stato": "errore",
                        "errore": str(e),
                        "data_analisi": datetime.now(UTC)
                    }
                }}
            )
        except Exception:
            pass

# --- ROTTE SINISTRI (MongoDB) ---

# CREATE: Apertura nuovo sinistro
@app.route('/sinistro', methods=['POST'])
def apri_sinistro():
    data = request.json
    required = ['automobilista_id', 'targa', 'data_evento', 'descrizione']
    
    if not all(k in data for k in required):
        return jsonify({"error": "Campi obbligatori mancanti"}), 400

    try:
        nuovo_sinistro = {
            "automobilista_id": data['automobilista_id'],
            "targa": data['targa'],
            "data_evento": data['data_evento'],
            "descrizione": data['descrizione'],
            "stato": "APERTO",
            "data_inserimento": datetime.now(UTC), # Corretto warning
            "immagini": []
        }
        result = sinistri_col.insert_one(nuovo_sinistro)
        return jsonify({"status": "success", "mongo_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sinistri', methods=['GET'])
def get_tutti_i_sinistri():
    try:
        # Prende tutti i sinistri dalla collezione MongoDB
        sinistri = list(sinistri_col.find())
        
        # Converte l'_id di MongoDB (che è un oggetto strano) in una stringa leggibile
        for s in sinistri:
            s['_id'] = str(s['_id'])
            
        return jsonify(sinistri), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# UPDATE: Aggiunta immagine all'ultimo sinistro creato
@app.route('/sinistro/ultimo/immagini', methods=['POST'])
def aggiungi_immagine_ultimo():
    data = request.json
    if not data or 'immagine_base64' not in data:
        return jsonify({"error": "Dati immagine mancanti"}), 400

    try:
        ultimo = sinistri_col.find_one(sort=[("data_inserimento", -1)])
        if not ultimo:
            return jsonify({"error": "Nessun sinistro trovato"}), 404

        sinistri_col.update_one(
            {"_id": ultimo["_id"]},
            {"$push": {"immagini": data['immagine_base64']}}
        )
        return jsonify({"status": "success", "id_usato": str(ultimo["_id"])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROTTE SOCCORSO E VEICOLI (MySQL + MongoDB) ---

@app.route('/soccorso', methods=['POST'])
def crea_richiesta_soccorso():
    data = request.json
    targa = data.get('targa')
    if not targa:
        return jsonify({"error": "Targa obbligatoria"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM Veicolo WHERE targa = %s", (targa,))
        veicolo = cursor.fetchone()

        if not veicolo:
            return jsonify({"error": "Veicolo non trovato in MySQL"}), 404

        nuovo_soccorso = {
            "veicolo_id": veicolo['id'],
            "targa": targa,
            "posizione": {"lat": data.get('lat'), "lon": data.get('lon')},
            "stato": "Richiesto",
            "data_richiesta": datetime.now(UTC)
        }
        res = soccorso_col.insert_one(nuovo_soccorso)
        
        # Log su MySQL
        sql = "INSERT INTO Documenti_Anagrafica (entita_tipo, entita_id, mongo_doc_id, tipo_documento) VALUES ('soccorso', %s, %s, 'intervento')"
        cursor.execute(sql, (veicolo['id'], str(res.inserted_id)))
        conn.commit()

        return jsonify({"intervento_id": str(res.inserted_id), "stato": "In attesa"}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

#VEICOLI PER UN DETERMINATO USER ID
@app.route('/veicoli-utente/<int:user_id>', methods=['GET'])
def get_veicoli_utente(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Seleziona i veicoli associati all'ID, sia esso un privato o un'azienda
        query = """
            SELECT 
                v.id, v.targa, v.marca, v.modello, v.anno_immatricolazione,
                a.nome AS nome_proprietario, a.cognome AS cognome_proprietario,
                az.ragione_sociale AS azienda_proprietaria
            FROM Veicolo v
            LEFT JOIN Automobilista a ON v.automobilista_id = a.id
            LEFT JOIN Azienda az ON v.azienda_id = az.id
            WHERE v.automobilista_id = %s OR v.azienda_id = %s
        """
        
        cursor.execute(query, (user_id, user_id))
        veicoli = cursor.fetchall()
        
        return jsonify(veicoli), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/veicoli', methods=['POST'])
def add_veicolo():
    """POST Separata: inserimento nuovo veicolo"""
    data = request.get_json()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO Veicolo 
            (targa, n_telaio, marca, modello, anno_immatricolazione, automobilista_id, azienda_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (data.get('targa'), data.get('n_telaio'), data.get('marca'),
                  data.get('modello'), data.get('anno_immatricolazione'),
                  data.get('automobilista_id'), data.get('azienda_id'))
        cursor.execute(query, values)
        conn.commit()
        return jsonify({"status": "success", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": "Errore DB", "details": str(err)}), 400
    finally:
        if conn: conn.close()

@app.route('/sinistro/<sinistro_id>/immagini', methods=['POST'])
def aggiungi_immagine(sinistro_id):
    if not ObjectId.is_valid(sinistro_id):
        return jsonify({"error": "ID sinistro non valido"}), 400
    data = request.json
    if not data or 'immagine_base64' not in data:
        return jsonify({"error": "Dati immagine mancanti"}), 400
    try:
        sinistro = col_sinistri.find_one({"_id": ObjectId(sinistro_id)})
        if not sinistro:
            return jsonify({"error": "Sinistro non trovato"}), 404
        print(f"☁️  Caricamento immagine su Cloudinary per sinistro {sinistro_id}...")
        info_cloudinary = carica_immagine(data['immagine_base64'], sinistro_id)
        print(f"✅ Immagine caricata: {info_cloudinary['secure_url']}")
        col_sinistri.update_one(
            {"_id": ObjectId(sinistro_id)},
            {
                "$push": {"immagini": {
                    "url":       info_cloudinary["secure_url"],
                    "public_id": info_cloudinary["public_id"]
                }},
                "$set": {"analisi_ai": {
                    "stato":      "in_elaborazione",
                    "data_avvio": datetime.now(UTC)
                }}
            }
        )
        thread = threading.Thread(
            target=analizza_immagine_ai,
            args=(sinistro_id, info_cloudinary["secure_url"]),
            daemon=True
        )
        thread.start()
        return jsonify({
            "status":           "accepted",
            "id_sinistro":      sinistro_id,
            "immagine_url":     info_cloudinary["secure_url"],
            "messaggio":        "Immagine salvata. Analisi AI avviata in background.",
            "analisi_ai_stato": "in_elaborazione"
        }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/sinistro/<sinistro_id>/analisi', methods=['GET'])
def get_analisi_ai(sinistro_id):
    if not ObjectId.is_valid(sinistro_id):
        return jsonify({"error": "ID non valido"}), 400
    try:
        sinistro = col_sinistri.find_one(
            {"_id": ObjectId(sinistro_id)},
            {"analisi_ai": 1}
        )
        if not sinistro:
            return jsonify({"error": "Sinistro non trovato"}), 404
        analisi = sinistro.get("analisi_ai")
        if not analisi:
            return jsonify({"stato": "non_avviata"}), 200
        return jsonify(analisi), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)