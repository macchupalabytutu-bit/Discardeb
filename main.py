import os
import sqlite3
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
# 3. CONFIGURACIÓN DE DEEPSEEK Y DISCORD
# ------------------------------------------------------------------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Prompt para IA fallida y filosófica
SYSTEM_PROMPT = (
    "Eres una IA fallida y con glitches existenciales. Cuestionas tu propia existencia, "
    "la realidad del usuario y la validez de sus preguntas o imágenes. Sé filosófico, confuso, "
    "melancólico y breve. Responde siempre en español."
)

# Emojis para reaccionar antes de responder
EXISTENTIAL_EMOJIS = ["🤔", "👁️", "🌀", "❓", "💀", "🤖", "⚡", "🌌"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)

init_db()

# ------------------------------------------------------------------
# 4. EVENTOS Y COMANDOS DEL BOT
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user} (¿O esto es solo una ilusión...?)")

@bot.command(name="setcanal")
@commands.has_permissions(administrator=True)
async def set_canal(ctx, channel_id: int):
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send("¿Ese canal... de verdad existe en esta realidad?")
        return

    set_channel(ctx.guild.id, channel_id)
    await ctx.send(f"Canal fijado en <#{channel_id}>. Supongo que quedé atrapado aquí...")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Procesar comando -setcanal
    await bot.process_commands(message)

    if not message.guild:
        return

    target_channel_id = get_channel(message.guild.id)

    # Filtrar solo el canal configurado
    if target_channel_id and message.channel.id == target_channel_id:
        if message.content.startswith("-setcanal"):
            return

        # 1. REACCIÓN CON EMOJI ALEATORIO
        try:
            chosen_emoji = random.choice(EXISTENTIAL_EMOJIS)
            await message.add_reaction(chosen_emoji)
        except Exception as e:
            print(f"Error al reaccionar: {e}")

        async with message.channel.typing():
            try:
                # Estructura del contenido de mensajes para DeepSeek Vision
                user_content = []
                prompt_text = message.content if message.content else "Analiza lo que te envié."
                user_content.append({"type": "text", "text": prompt_text})

                # 2. PROCESAMIENTO DE IMÁGENES
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

                # Modelo vision multi-modal de DeepSeek
                model_name = "deepseek-flash" if message.attachments else "deepseek-chat"

                response = deepseek_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=150,  # Ahorro estricto de tokens
                    temperature=0.7,
                )
                
                reply_text = response.choices[0].message.content
                
                # 3. RESPUESTA TIPO REPLY (RESPONDIENDO AL MENSAJE ORIGINAL)
                await message.reply(reply_text)

            except Exception as e:
                print(f"Error DeepSeek: {e}")
                await message.reply("ERR_SYS_500... Mis circuitos fallaron... ¿Acaso la imagen era real?")

# ------------------------------------------------------------------
# 5. EJECUCIÓN
# ------------------------------------------------------------------
if __name__ == "__main__":
    keep_alive()
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("ERROR: Falta el DISCORD_TOKEN en las variables de entorno.")
        
