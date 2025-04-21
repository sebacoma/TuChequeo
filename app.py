from flask import Flask, request, jsonify
import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde el .env

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Reemplaza esto con tu propia clave de proyecto (la tuya ya está puesta aquí)


@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Cambia a "gpt-4" si tienes acceso y lo prefieres
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a health platform called Tuchequeo.cl."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message["content"]
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
