
import streamlit as st
import os
import asyncio
import edge_tts
import requests
from PIL import Image, ImageDraw
import tempfile
import time
import imageio
import numpy as np
import subprocess

# ========== KONFIGURACJA ==========
# ⚠️ WPISZ TU SWÓJ KLUCZ OPENROUTER:
OPENROUTER_KEY = "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"

st.set_page_config(
    page_title="🎬 FACELESS STORY GENERATOR",
    page_icon="📱",
    layout="wide"
)

# ========== STYLE ==========
st.markdown("""
<style>
    /* Reset i podstawowe czyszczenie */
    .main > div { padding: 0rem !important; }
    .stApp { background: #0a0a0a; }
    header { display: none !important; }
    footer { display: none !important; }

    /* Główny kontener imitujący iPhone */
    .phone-container {
        max-width: 400px;
        margin: 0 auto;
        background: #000000;
        border-radius: 40px;
        padding: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.9);
        border: 1px solid #2a2a2a;
    }

    /* Ekran iPhone z wycięciem */
    .phone-screen {
        background: #1a1a1a;
        border-radius: 30px;
        padding: 20px 10px;
        min-height: 700px;
        position: relative;
        border: 1px solid #333;
        background-image: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        box-shadow: inset 0 0 50px rgba(0,0,0,0.8);
    }

    /* Notch (wycięcie na kamerę) */
    .notch {
        background: #000;
        width: 150px;
        height: 30px;
        border-radius: 20px;
        margin: -5px auto 15px auto;
    }

    /* Wiadomości - styl jak w iOS */
    .msg-sent {
        background: #007aff;
        color: white;
        padding: 10px 14px;
        border-radius: 18px 18px 4px 18px;
        max-width: 85%;
        margin: 6px 0 6px auto;
        font-size: 15px;
        box-shadow: 0 2px 8px rgba(0,122,255,0.3);
        word-wrap: break-word;
        text-align: left;
    }
    .msg-received {
        background: #2c2c2e;
        color: white;
        padding: 10px 14px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        margin: 6px auto 6px 0;
        font-size: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        word-wrap: break-word;
        text-align: left;
    }
    .msg-time {
        color: #8e8e93;
        font-size: 11px;
        text-align: center;
        margin: 4px 0;
        font-weight: 300;
    }

    /* Input bar na dole */
    .input-bar {
        background: #1c1c1e;
        border-radius: 25px;
        padding: 6px 12px;
        margin-top: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #333;
    }
    .input-bar input {
        background: transparent;
        border: none;
        color: white;
        flex: 1;
        padding: 8px;
        font-size: 16px;
        outline: none;
    }
    .input-bar button {
        background: #007aff;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        color: white;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Przyciski w Streamlit */
    .stButton > button {
        width: 100%;
        padding: 14px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 30px;
        background: linear-gradient(90deg, #007aff, #5856d6);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(0,122,255,0.4);
        transition: 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background: linear-gradient(90deg, #0055cc, #4646b3);
        box-shadow: 0 6px 20px rgba(0,122,255,0.6);
    }

    /* Inne elementy */
    .stSelectbox > div > div {
        background: #1c1c1e !important;
        border-radius: 12px !important;
        border: 1px solid #333 !important;
        color: white !important;
    }
    .stTextArea > div > textarea {
        background: #1c1c1e !important;
        border-radius: 12px !important;
        border: 1px solid #333 !important;
        color: white !important;
        font-size: 15px !important;
    }
    h1 {
        color: white !important;
        text-align: center;
        font-weight: 800;
        text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }
    .stSubheader {
        color: #aaa !important;
    }
    .stCaption {
        color: #666 !important;
        text-align: center;
    }
    .stAlert {
        border-radius: 16px !important;
    }
    .stVideo {
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0,0,0,0.8);
    }
</style>
""", unsafe_allow_html=True)

# ========== STAN ==========
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ========== FUNKCJE ==========

def generate_story(temat, template_type):
    """Generuje historię przez OpenRouter"""
    try:
        templates = {
            "horror": f"Napisz przerażającą historię w formie rozmowy na iMessage między dwiema osobami (Kuba i Olivia) na temat: {temat}. Format: Kuba: ... Olivia: ... Maksymalnie 10 wiadomości.",
            "love": f"Napisz romantyczną historię w formie rozmowy na iMessage między dwiema osobami (Kuba i Olivia) na temat: {temat}. Format: Kuba: ... Olivia: ... Maksymalnie 10 wiadomości.",
            "mystery": f"Napisz tajemniczą historię w formie rozmowy na iMessage między dwiema osobami (Kuba i Olivia) na temat: {temat}. Format: Kuba: ... Olivia: ... Maksymalnie 10 wiadomości.",
            "drama": f"Napisz dramatyczną historię w formie rozmowy na iMessage między dwiema osobami (Kuba i Olivia) na temat: {temat}. Format: Kuba: ... Olivia: ... Maksymalnie 10 wiadomości.",
            "random": f"Wygeneruj ciekawą historię w formie rozmowy na iMessage między dwiema osobami (Kuba i Olivia) na temat: {temat}. Format: Kuba: ... Olivia: ... Maksymalnie 10 wiadomości."
        }
        
        prompt = templates.get(template_type, templates["random"])
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": "Jesteś pisarzem tworzącym historie w formie rozmów na iMessage. Twórz krótkie, wciągające dialogi."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9,
                "max_tokens": 400
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return "Kuba: Hej, jesteś tam?\nOlivia: Tak, słucham.\nKuba: Muszę ci coś powiedzieć..."
            
    except Exception as e:
        return "Kuba: Hej, jesteś tam?\nOlivia: Tak, słucham.\nKuba: Muszę ci coś powiedzieć..."

async def generate_voice(text, voice_name):
    """Generuje audio dla pojedynczej wiadomości"""
    try:
        if not text or len(text.strip()) < 2:
            return None
            
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(audio_path)
        return audio_path
    except Exception as e:
        return None

def create_imessage_image(messages):
    """Generuje obrazek z konwersacją w stylu iMessage"""
    try:
        # Rozmiar: 1080x1920 (Shorts)
        img = Image.new('RGB', (1080, 1920), color='#0a0a0a')
        d = ImageDraw.Draw(img)
        
        # Tło - gradient w stylu iOS
        for i in range(1920):
            r = int(20 + (i / 1920) * 30)
            g = int(20 + (i / 1920) * 25)
            b = int(30 + (i / 1920) * 40)
            d.rectangle([0, i, 1080, i+1], fill=(r, g, b))
        
        # Status bar (pasek na górze)
        d.rectangle([0, 0, 1080, 60], fill='#000000')
        d.text((30, 20), "9:41", fill='white', font=ImageFont.load_default())
        d.text((980, 20), "📶 🔋", fill='white', font=ImageFont.load_default())
        
        # Pasek nawigacji
        d.rectangle([0, 60, 1080, 110], fill='#1c1c1e')
        d.text((540, 85), "iMessage", fill='white', anchor="mt", font=ImageFont.load_default())
        
        # Wiadomości
        y = 140
        for msg in messages[:10]:  # max 10 wiadomości
            text = msg.get('text', '')
            sender = msg.get('sender', '')
            
            if not text:
                continue
                
            # Oblicz szerokość tekstu (w przybliżeniu)
            text_width = len(text) * 18
            max_width = 750
            
            if text_width > max_width:
                # Podziel na linie
                lines = []
                current_line = ""
                for word in text.split():
                    if len(current_line) + len(word) < 40:
                        current_line += word + " "
                    else:
                        lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())
                
                line_height = 30
                total_height = len(lines) * line_height + 20
            else:
                lines = [text]
                total_height = 50
            
            if sender.lower() == 'kuba':
                # Wiadomość wysłana (po prawej)
                x_start = 1080 - text_width - 60 if text_width < max_width else 1080 - max_width - 60
                x_start = max(250, x_start)
                
                # Tło wiadomości
                d.rounded_rectangle([x_start, y, 1060, y + total_height],
                                  radius=20, fill='#007aff')
                
                # Tekst
                y_text = y + 20
                for line in lines:
                    d.text((x_start + 20, y_text), line, fill='white', font=ImageFont.load_default())
                    y_text += line_height
                
                y += total_height + 15
            else:
                # Wiadomość otrzymana (po lewej)
                x_start = 20
                max_width = 750
                
                # Tło wiadomości
                d.rounded_rectangle([x_start, y, x_start + max(100, min(text_width + 40, max_width)), y + total_height],
                                  radius=20, fill='#2c2c2e')
                
                # Tekst
                y_text = y + 20
                for line in lines:
                    d.text((x_start + 20, y_text), line, fill='white', font=ImageFont.load_default())
                    y_text += line_height
                
                y += total_height + 15
            
            if y > 1750:
                break
        
        # Pasek input na dole
        d.rectangle([0, 1820, 1080, 1920], fill='#1c1c1e')
        d.rounded_rectangle([30, 1835, 950, 1885], radius=25, fill='#2c2c2e')
        d.text((50, 1860), "iMessage", fill='#8e8e93', font=ImageFont.load_default())
        d.ellipse([980, 1845, 1030, 1895], fill='#007aff')
        d.polygon([995, 1860, 1015, 1860, 1005, 1875], fill='white')
        
        # Zapisz obrazek
        img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img.save(img_path)
        return img_path
        
    except Exception as e:
        # Prosty fallback
        img = Image.new('RGB', (1080, 1920), color='black')
        d = ImageDraw.Draw(img)
        d.text((100, 800), "ERROR: " + str(e)[:50], fill='white')
        img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img.save(img_path)
        return img_path

def create_video(image_path, audio_paths, output_path):
    """Łączy obrazek z audio w film"""
    try:
        # Jeśli brak audio, stwórz cichy film
        if not audio_paths or all(a is None for a in audio_paths):
            # 10 sekund ciszy
            subprocess.run([
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_path,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', '10',
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
                output_path
            ], capture_output=True)
            return True
        
        # Złącz wszystkie audio w jedno
        valid_audio = [a for a in audio_paths if a and os.path.exists(a)]
        if not valid_audio:
            return False
            
        # Stwórz plik z listą audio
        list_path = tempfile.NamedTemporaryFile(delete=False, suffix=".txt").name
        with open(list_path, 'w') as f:
            for audio in valid_audio:
                f.write(f"file '{audio}'\n")
        
        # Złącz audio
        combined_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_path,
            '-c:a', 'copy',
            combined_audio
        ], capture_output=True)
        
        # Stwórz film z obrazkiem i audio
        subprocess.run([
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-i', combined_audio,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
            output_path
        ], capture_output=True)
        
        # Sprzątanie
        try: os.unlink(list_path)
        except: pass
        try: os.unlink(combined_audio)
        except: pass
        
        return True
        
    except Exception as e:
        return False

# ========== INTERFEJS ==========

st.markdown("<h1>📱 Faceless Stories</h1>", unsafe_allow_html=True)
st.caption("Twórz wiralowe historie w stylu iMessage")

# Wybór szablonu
st.markdown("---")
st.subheader("📁 Wybierz klimat")

cols = st.columns(5)
templates = [
    ("horror", "👻", "Horror"),
    ("love", "❤️", "Romans"),
    ("mystery", "🔍", "Tajemnica"),
    ("drama", "🎭", "Dramat"),
    ("random", "🎲", "Losowe")
]

for idx, (key, icon, name) in enumerate(templates):
    with cols[idx]:
        if st.button(f"{icon}", use_container_width=True):
            st.session_state.template = key
            st.rerun()

# Wybór głosów
st.subheader("🎤 Głosy")

col1, col2 = st.columns(2)
with col1:
    voice1 = st.selectbox(
        "Głos Kuby:",
        ["pl-PL-MarekNeural", "pl-PL-ZofiaNeural", "en-US-ChristopherNeural"],
        format_func=lambda x: {
            "pl-PL-MarekNeural": "👨 Męski (PL)",
            "pl-PL-ZofiaNeural": "👩 Żeński (PL)",
            "en-US-ChristopherNeural": "👨 Męski (EN)"
        }[x]
    )

with col2:
    voice2 = st.selectbox(
        "Głos Olivii:",
        ["pl-PL-ZofiaNeural", "pl-PL-MarekNeural", "en-US-JennyNeural"],
        format_func=lambda x: {
            "pl-PL-ZofiaNeural": "👩 Żeński (PL)",
            "pl-PL-MarekNeural": "👨 Męski (PL)",
            "en-US-JennyNeural": "👩 Żeński (EN)"
        }[x]
    )

# Temat
st.subheader("📝 Temat historii")
temat = st.text_area(
    "",
    placeholder="Np. Przeklęty dom, nocna rozmowa, tajemniczy telefon...",
    height=60,
    label_visibility="collapsed"
)

# Przycisk
if st.button("🔥 GENERUJ HISTORIĘ", use_container_width=True):
    if not temat:
        st.error("❌ Wpisz temat!")
    elif not OPENROUTER_KEY or OPENROUTER_KEY == "wpisz-tutaj-swoj-klucz":
        st.error("❌ Wpisz swój klucz OpenRouter w kodzie!")
    else:
        with st.spinner("🎬 Tworzę historię... (może chwilę potrwać)"):
            try:
                # 1. Generuj historię
                story_text = generate_story(temat, st.session_state.template)
                st.session_state.story = story_text
                
                # Parsuj wiadomości
                messages = []
                for line in story_text.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            sender = parts[0].strip()
                            text = parts[1].strip()
                            if sender.lower() in ['kuba', 'olivia']:
                                messages.append({'sender': sender, 'text': text})
                
                if not messages:
                    messages = [
                        {'sender': 'Kuba', 'text': 'Hej, jesteś tam?'},
                        {'sender': 'Olivia', 'text': 'Tak, słucham.'},
                        {'sender': 'Kuba', 'text': 'Muszę ci coś powiedzieć...'}
                    ]
                
                st.session_state.messages = messages
                
                # Podgląd konwersacji
                with st.expander("📱 Podgląd konwersacji"):
                    st.markdown('<div class="phone-container"><div class="phone-screen"><div class="notch"></div>', unsafe_allow_html=True)
                    for msg in messages:
                        if msg['sender'].lower() == 'kuba':
                            st.markdown(f'<div class="msg-sent">{msg["text"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="msg-received">{msg["text"]}</div>', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)
                
                # 2. Generuj głosy
                audio_paths = []
                progress = st.progress(0)
                for i, msg in enumerate(messages):
                    voice = voice1 if msg['sender'].lower() == 'kuba' else voice2
                    audio = asyncio.run(generate_voice(msg['text'], voice))
                    if audio:
                        audio_paths.append(audio)
                    progress.progress((i + 1) / len(messages))
                
                # 3. Generuj obrazek
                img_path = create_imessage_image(messages)
                
                # 4. Twórz film
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                if create_video(img_path, audio_paths, output_path):
                    st.session_state.video_path = output_path
                    st.session_state.generated = True
                    st.success("✅ Gotowe! Ściągaj poniżej.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Błąd tworzenia filmu")
                    
            except Exception as e:
                st.error(f"❌ Coś się jebło: {str(e)[:100]}")

# Podgląd i pobieranie
if st.session_state.generated and st.session_state.video_path:
    if os.path.exists(st.session_state.video_path):
        st.markdown("---")
        st.subheader("📱 Twój film")
        st.video(st.session_state.video_path)
        
        with open(st.session_state.video_path, "rb") as f:
            video_bytes = f.read()
        st.download_button(
            label="⬇️ Pobierz na iPhone",
            data=video_bytes,
            file_name=f"story_{int(time.time())}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
    else:
        st.session_state.generated = False

# Stopka
st.markdown("---")
st.caption("🔹 Działa na iPhone · 100% darmowe · Dodaj do ekranu głównego")
