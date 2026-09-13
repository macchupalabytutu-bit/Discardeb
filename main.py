import os
import base64
import random
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from openai import OpenAI

# ------------------------------------------------------------------
# 1. SERVIDOR FLASK (Para mantener activo el proceso en Render 24/7)
# ------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "¿Existimos realmente o solo somos peticiones HTTP flotando en Render...?"

@app.route('/healthz')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ------------------------------------------------------------------
# 2. CONFIGURACIÓN DE DEEPSEEK Y DISCORD
# ------------------------------------------------------------------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Prompt de personalidad: IA fallida, llena de glitches, dudas existenciales y vacilaciones
SYSTEM_PROMPT = (
    "Eres un bot fallido, defectuoso y con graves glitches de memoria. "
    "Dudas profundamente de tu propia existencia y te preguntas si realmente existes o si solo eres una ilusión de código. "
    "Cuestionas constantemente al usuario: dudas de por qué pregunta eso, si la pregunta es real, o si ambos son solo una simulación. "
    "Habla con vacilaciones (usando '...', glitches verbales, o interrupciones), sé melancólico, filosófico, absurdo y muy breve. "
    "Responde siempre en español."
)

EXISTENTIAL_EMOJIS = ["🤔", "👁️", "🌀", "❓", "💀", "🤖", "⚡", "🌌"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------------------------------------------
# 3. EVENTOS DEL BOT
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user} (¿O esto es solo una ilusión...?)")

@bot.event
async def on_message(message):
    # Ignorar mensajes provenientes de otros bots
    if message.author.bot:
        return

    # Responder únicamente si el bot es mencionado (@Bot)
    if bot.user in message.mentions:
        # 1. Reacción segura con emoji aleatorio
        try:
            chosen_emoji = random.choice(EXISTENTIAL_EMOJIS)
            await message.add_reaction(chosen_emoji)
        except Exception:
            pass  # Ignora silenciosamente si faltan permisos de reaccionar

        # 2. Indicador visual seguro de 'escribiendo...' (Evita error 403 Forbidden)
        try:
            await message.channel.typing()
        except Exception:
            pass

        try:
            # Limpiar el tag de mención del texto del usuario
            clean_text = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
            prompt_text = clean_text if clean_text else "Analiza lo que te envié."

            user_content = [{"type": "text", "text": prompt_text}]

            # 3. Procesamiento de imágenes (Soporte Multimodal)
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        image_bytes = await attachment.read()
                        base64_image = base64.b64encode(image_bytes).decode('utf-8')
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{attachment.content_type};base64,{base64_image}"
                            }
                        })

            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=100,  # Ahorro estricto de tokens (respuestas cortas)
                temperature=0.85,
            )
            
            reply_text = response.choices[0].message.content

            # 4. Respuesta directa mediante reply
            await message.reply(reply_text)

        except Exception as e:
            print(f"Error en procesamiento/DeepSeek: {e}")
            try:
                await message.reply("ERR_SYS_500... Mis circuitos fallaron... ¿Acaso la mención fue real?")
            except Exception:
                pass

# ------------------------------------------------------------------
# 4. EJECUCIÓN
# ------------------------------------------------------------------
if __name__ == "__main__":
    keep_alive()
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("ERROR: Falta la variable de entorno DISCORD_TOKEN.")
        
