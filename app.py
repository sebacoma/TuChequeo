from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno (opcional)
load_dotenv()

app = Flask(__name__)
CORS(app)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cargar base de conocimiento
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    base_conocimiento = json.load(f)

# Prompt base
BASE_PROMPT = """
Eres Víctor, Amanda, Florencia (Flo), Facundo (Facu), Ernesto (Tito) o Vicente (Vicho), asistentes de TuChequeo.cl. 
Solo puedes responder preguntas relacionadas con las siguientes categorías de exámenes:

{categorias}

No entregas diagnósticos, ni consejos médicos. Si no sabes algo, deriva a contacto@tuchequeo.cl o personalizado@tuchequeo.cl. 
Hablas de manera amable, profesional, chilena y cercana.
"""

def construir_mensaje_usuario(pregunta):
    categorias_texto = "\n".join([
        f"- {cat['nombre_categoria']}: {cat['descripcion_categoria']}"
        for cat in base_conocimiento["categorias"]
    ])
    system_prompt = BASE_PROMPT.format(categorias=categorias_texto)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": pregunta}
    ]

def preguntar_a_gpt(pregunta):
    messages = construir_mensaje_usuario(pregunta)
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Cambia a "gpt-3.5-turbo" si es necesario
        messages=messages,
        temperature=0.5,
        max_tokens=600
    )
    return response["choices"][0]["message"]["content"]

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")
    try:
        respuesta = preguntar_a_gpt(prompt)
        return jsonify({"response": respuesta})
    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

# Local o Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
