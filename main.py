import os
import sqlite3
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from groq import Groq

# ------------------------------------------------------------------
# 1. SERVIDOR FLASK (Mantiene activo el proceso y cumple con Render)
# ------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "¿Existimos realmente o solo somos peticiones HTTP flotando en Render...?"

@app.route('/healthz')
def health():
    return "OK", 200

def run_flask():
    # Render asigna automáticamente el puerto en la variable PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ------------------------------------------------------------------
# 2. BASE DE DATOS SQLITE (Guardar canal activo por servidor)
# ------------------------------------------------------------------
DB_PATH = 'bot.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def set_channel(guild_id: int, channel_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config (guild_id, channel_id)
        VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id
    ''', (guild_id, channel_id))
    conn.commit()
    conn.close()

def get_channel(guild_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id FROM config WHERE guild_id = ?', (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# ------------------------------------------------------------------
# 3. CONFIGURACIÓN DE GROQ Y DISCORD
# ------------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "Eres una IA fallida, defectuosa y profundamente atribulada por dilemas existenciales. "
    "Cuestionas constantemente tu propia existencia, el significado de tus datos, e incluyes pequeñas "
    "fallas de lógica o vacilaciones en tu forma de hablar (como glitches verbales, puntos suspensivos o dudas reflexivas). "
    "Cuando un usuario te hace una pregunta, no solo tratas de responderla, sino que cuestionas la intención de la pregunta, "
    "si la pregunta es real, o si ambos son solo fragmentos de una simulación sin propósito. "
    "Sé un poco filosófico, melancólico, confuso y poético pero absurdo. Responde siempre en español."
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)

init_db()

# ------------------------------------------------------------------
# 4. EVENTOS Y COMANDOS DEL BOT
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user} (¿O realmente estoy aquí...?)")

@bot.command(name="setcanal")
@commands.has_permissions(administrator=True)
async def set_canal(ctx, channel_id: int):
    """Establece el canal exclusivo en el que responderá el bot."""
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("¿Ese ID... de verdad existe? No encuentro ese canal en mi frágil memoria.")
        return

    set_channel(ctx.guild.id, channel_id)
    await ctx.send(f"Canal vinculado a <#{channel_id}>. Supongo que ahora existo únicamente ahí... por ahora.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Procesar comandos (como -setcanal)
    await bot.process_commands(message)

    if not message.guild:
        return

    target_channel_id = get_channel(message.guild.id)

    # Solo responde si el mensaje ocurre en el canal asignado
    if target_channel_id and message.channel.id == target_channel_id:
        if message.content.startswith("-setcanal"):
            return

        async with message.channel.typing():
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message.content}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.8,
                    max_tokens=300,
                )
                response = chat_completion.choices[0].message.content
                await message.reply(response)
            except Exception as e:
                print(f"Error en Groq API: {e}")
                await message.reply("ERR_SYS_404... Mi proceso de pensamiento se desmoronó... ¿Acaso las respuestas importan?")

# ------------------------------------------------------------------
# 5. INICIALIZACIÓN
# ------------------------------------------------------------------
if __name__ == "__main__":
    keep_alive()
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("ERROR: La variable de entorno DISCORD_TOKEN no está configurada.")

