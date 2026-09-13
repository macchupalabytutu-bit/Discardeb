import os
import random
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from groq import Groq

# ------------------------------------------------------------------
# 1. SERVIDOR FLASK (Hosting 24/7 en Render)
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
# 2. CONFIGURACIÓN DE GROQ Y DISCORD
# ------------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

groq_client = Groq(api_key=GROQ_API_KEY)

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
    print(f"Bot conectado como: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Responder únicamente si el bot es mencionado (@Bot)
    if bot.user in message.mentions:
        try:
            await message.add_reaction(random.choice(EXISTENTIAL_EMOJIS))
        except Exception:
            pass

        try:
            await message.channel.typing()
        except Exception:
            pass

        try:
            clean_text = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
            prompt_text = clean_text if clean_text else "..."

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=100,
                temperature=0.85,
            )
            
            reply_text = response.choices[0].message.content
            await message.reply(reply_text)

        except Exception as e:
            print(f"Error en la API: {e}")
            try:
                await message.reply(f"ERR_SYS_500... Mis circuitos fallaron... {e}")
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
        print("ERROR: Falta DISCORD_TOKEN")
        
