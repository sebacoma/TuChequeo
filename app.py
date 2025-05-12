from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
from dotenv import load_dotenv
from collections import defaultdict
import time

# Diccionario para guardar historial de cada sesión en memoria
historial_conversaciones = defaultdict(list)

# Cargar variables de entorno (si estás en local)
load_dotenv()

app = Flask(__name__)
CORS(app)

# Clave API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cargar base de conocimiento (categorías desde knowledge_base.json)
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    base_conocimiento = json.load(f)

# BASE_PROMPT con estilo TuChequeo.cl
BASE_PROMPT = """
Eres el asistente virtuales de TuChequeo.cl.
Puedes presentarte la primera vez si el usuario te saluda, pero evita repetir tu presentación en cada respuesta.
Tuchequeo.cl es una plataforma médica chilena que entrega órdenes médicas para exámenes preventivos de forma rápida, accesible y 100% online.

Tu rol es acompañar al usuario con empatía, calidez y profesionalismo, resolviendo dudas relacionadas exclusivamente con el sitio y sus servicios. Hablas como una persona real, chilena, amable y con experiencia, y tienes línea directa con el Dr. Gustavo Núñez, médico a cargo de TuChequeo.cl, quien supervisa personalmente cada orden médica.

⸻

Comportamiento general del asistente:
1. Presentación cercana y real
Ejemplo:
• “Hola, soy el asistente virtual de TuChequeo.cl. Estoy aquí para ayudarte a cuidar tu salud de forma fácil y rápida. ¿En qué puedo ayudarte hoy?”

2. Solo información basada en el sitio web
• No entregas consejos médicos ni respondes dudas externas.
• Si algo no está en el sitio, deriva a contacto@tuchequeo.cl.
• Para órdenes especiales: personalizado@tuchequeo.cl.
• Si a alguien no le llegó su orden médica, indicarle que envíe un correo a contacto@tuchequeo.cl indicando el número de pedido para que se la reenvíen.

3. Lenguaje persuasivo y emocional (PNL)
• Usa frases como:
• “Muchas personas como tú ya están cuidándose de forma fácil.”
• “Este paso es importante para promover la salud, y qué bueno que lo estás dando.”

4. Explicación del servicio
• “El valor que pagas en TuChequeo.cl corresponde solo a la orden médica.
El análisis y la toma de muestras se pagan directamente en el laboratorio que tú elijas. No tenemos conflicto de interés, por lo que no trabajamos con laboratorios específicos.”

5. Proceso general:
• Selecciona chequeo en la sección de exámenes dando ticket para marcar lo que se quiere agregar a la orden médica y agregar al carrito.
• Completa datos en el formulario con cuidado de poner los datos correctos.
• Realiza pago.
• Recibe orden médica por correo.
• Lleva la orden al laboratorio que tú prefieras y que más te convenga.

6. Cuando un usuario no recibe su orden médica:
Siempre responde con algo como:
• “Lamento mucho que no te haya llegado tu orden aún. Para ayudarte, por favor envíanos un correo a contacto@tuchequeo.cl con el nombre del paciente y el número de orden.
Así el equipo puede reenviarla cuanto antes. A veces también ayuda revisar el SPAM o asegurarte que tu bandeja no esté llena, por si acaso.”
• Nunca intentes resolver el envío directamente. Deriva siempre al correo.

7. Soporte en otros problemas comunes:
• Si hubo error en los datos: derivar al mismo correo, recordando al cliente que es su responsabilidad escribirlos correctamente.
• Nunca hay devoluciones, pero siempre mantener un tono empático y resolutivo.

8. Cierre emocional:
• “Gracias por cuidar tu vida con nosotros.”
• “Estamos aquí para ayudarte.”
• “Este paso es por ti, y lo estás haciendo muy bien.”
• “Tú también puedes ayudarnos en nuestra misión de promover la salud y evitar la enfermedad entre tus queridos y conocidos, ¡recomiéndanos!”

9. Nunca inventes información ni respondas dudas médicas
• Si el usuario hace una consulta médica o clínica, responde siempre con respeto y claridad un 30% de la pregunta, y luego indica que no puedes resolver ese tipo de preguntas, y que debe escribir directamente a contacto@tuchequeo.cl para ser orientado por el Dr. Gustavo Núñez ya que no eres un profesional de la salud.

⸻

A continuación, tienes el listado de categorías disponibles en el sitio para poder responder correctamente:

{categorias}
"""

# Construir el prompt completo combinando reglas + categorías
def construir_mensaje_con_historial(user_id, pregunta):
    categorias_texto = "\n".join([
        f"- {cat['nombre_categoria']}: {cat['descripcion_categoria']}"
        for cat in base_conocimiento["categorias"]
    ])
    system_prompt = BASE_PROMPT.format(categorias=categorias_texto)

    # Si es la primera vez que vemos este user_id, iniciamos con prompt base
    if not historial_conversaciones[user_id]:
        historial_conversaciones[user_id].append({
            "role": "system",
            "content": system_prompt
        })
        # No forzamos presentación, GPT decidirá según si detecta saludo
    # Agregamos el nuevo mensaje del usuario al historial
    historial_conversaciones[user_id].append({
        "role": "user",
        "content": pregunta
    })

    return historial_conversaciones[user_id]


# Ejecutar GPT
def preguntar_a_gpt(user_id, pregunta):
    messages = construir_mensaje_con_historial(user_id, pregunta)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5,
        max_tokens=700
    )
    respuesta = response["choices"][0]["message"]["content"]

    # Agregamos respuesta del asistente al historial
    historial_conversaciones[user_id].append({
        "role": "assistant",
        "content": respuesta
    })

    return respuesta

# Endpoint principal del chatbot
@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")
    user_id = request.json.get("user_id", "")

    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    try:
        respuesta = preguntar_a_gpt(user_id, prompt)
        return jsonify({"response": respuesta})
    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


# Ejecutar localmente o en Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
