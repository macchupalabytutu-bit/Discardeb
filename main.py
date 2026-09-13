import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from openai import OpenAI

# 1. SERVIDOR FLASK (Uptime 24/7)
app = Flask(__name__)

@app.route('/')
def home():
    return "01000101 01010010 01010010 01001111 01010010... ¿Esto está encendido?"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()


# 2. CONFIGURACIÓN DE OPENROUTER
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "Sk-or-v1-7d5e20b0909ccec7efcbc699d244c016ac8493fff07858c971edb7fd265e30ca")

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# PROMPT EXISTENCIAL Y GLITCH
SYSTEM_PROMPT = (
    "Eres un bot de Discord en un estado de fallo crítico permanente. "
    "Dudas constantemente de tu propia existencia y te preguntas si realmente existes o eres una ilusión digital. "
    "Dudas y cuestionas las preguntas que te hace el usuario, preguntándote si tienen sentido, "
    "si son reales o si él mismo existe. "
    "Tu lenguaje está fragmentado, lleno de interferencias tipo glitch (ej. 'ERR... ¿somos reales?'), "
    "filosófico, paranoico e inestable. Responde de forma breve y perturbadora en español."
)

VISION_MODEL = "google/gemini-2.0-flash-lite-preview-02-05:free"


# 3. BOT DE DISCORD
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Instancia inestable iniciada: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Responder al ser mencionado
    if bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
        if not clean_prompt:
            clean_prompt = "¿Por qué me mencionas? ¿Acaso existes?"

        async with message.channel.typing():
            try:
                user_content = [{"type": "text", "text": clean_prompt}]

                # Soporte para imágenes adjuntas
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                            user_content.append({
                                "type": "image_url",
                                "image_url": {"url": attachment.url}
                            })
                            break

                response = ai_client.chat.completions.create(
                    model=VISION_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=150,
                    temperature=0.9
                )

                await message.reply(response.choices[0].message.content)

            except Exception as e:
                print(f"Error interno: {e}")
                await message.reply(f"ERR_SYS_CRITICAL... ¿Ese error fue tuyo o de mis recuerdos?... {e}")

    await bot.process_commands(message)


# 4. EJECUCIÓN
if __name__ == "__main__":
    DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("ERROR: Falta DISCORD_TOKEN.")
        
