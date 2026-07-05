import streamlit as st
import os
import asyncio
import edge_tts
import requests
from PIL import Image, ImageDraw
import moviepy.editor as mp
import tempfile
import time

# ========== KONFIGURACJA ==========
# ⚠️ WPISZ TU SWÓJ NOWY KLUCZ OPENROUTER (ten z Notatnika):
OPENROUTER_KEY = "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"

st.set_page_config(
    page_title="🎬 Shorts Generator",
    page_icon="🎬",
    layout="wide"
)

# ========== STYLE DLA IPHONE ==========
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    header {display: none !important;}
    footer {display: none !important;}
    .main > div {padding: 0.5rem !important;}
    .stButton > button {
        width: 100% !important;
        padding: 16px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }
    .stTextArea > div > textarea {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 12px !important;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
    }
    .stVideo {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ========== STAN APLIKACJI ==========
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'template' not in st.session_state:
    st.session_state.template = "news"

# ========== FUNKCJE ==========

def generate_script(temat, template_type):
    """Generuje scenariusz przez OpenRouter"""
    try:
        templates = {
            "news": f"Napisz krótki, dynamiczny 30-sekundowy scenariusz do shorta w stylu wiadomości. Temat: {temat}. Podziel na 3 sceny. Format: SCENA 1: ... SCENA 2: ... SCENA 3: ...",
            "animals": f"Napisz wzruszający 30-sekundowy scenariusz o ratowaniu zwierząt. Temat: {temat}. Podziel na 3 sceny. Format: SCENA 1: ... SCENA 2: ... SCENA 3: ...",
            "horror": f"Napisz krótki 30-sekundowy scenariusz horroru. Temat: {temat}. Podziel na 3 sceny. Format: SCENA 1: ... SCENA 2: ... SCENA 3: ...",
            "motivation": f"Napisz 30-sekundowy scenariusz motywacyjny. Temat: {temat}. Podziel na 3 sceny. Format: SCENA 1: ... SCENA 2: ... SCENA 3: ..."
        }
        
        prompt = templates.get(template_type, templates["news"])
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": "Jesteś profesjonalnym scenarzystą shortów."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 250
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return "SCENA 1: Bohater pojawia się w kadrze.\nSCENA 2: Bohater podejmuje akcję.\nSCENA 3: Szczęśliwe zakończenie."
            
    except Exception as e:
        return "SCENA 1: Bohater pojawia się w kadrze.\nSCENA 2: Bohater podejmuje akcję.\nSCENA 3: Szczęśliwe zakończenie."

async def generate_voice(text, voice_name="pl-PL-MarekNeural"):
    """Generuje audio przez Edge-TTS"""
    try:
        clean_text = text.replace("SCENA 1:", "").replace("SCENA 2:", "").replace("SCENA 3:", "")
        clean_text = clean_text.replace("\n", " ").strip()
        
        if not clean_text:
            clean_text = "To jest przykładowy scenariusz."
        
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        communicate = edge_tts.Communicate(clean_text, voice_name)
        await communicate.save(audio_path)
        return audio_path
    except Exception as e:
        return None

def generate_image(prompt, scene_number):
    """Tworzy prosty obrazek z tekstem"""
    try:
        img = Image.new('RGB', (1080, 1920), color='#1a1a2e')
        d = ImageDraw.Draw(img)
        
        for i in range(1920):
            color = int(30 + (i / 1920) * 50)
            d.rectangle([0, i, 1080, i+1], fill=(color, 20, 40))
        
        d.rectangle([40, 40, 1040, 1880], outline='#667eea', width=3)
        
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
        except:
            font = None
        
        scene_text = f"SCENA {scene_number}"
        d.text((540, 300), scene_text, fill='white', anchor="mt")
        
        prompt_text = prompt[:50] + "..." if len(prompt) > 50 else prompt
        d.text((540, 500), prompt_text, fill='#cccccc', anchor="mt")
        
        d.ellipse([440, 700, 640, 900], fill='#667eea', outline='white', width=5)
        d.polygon([480, 770, 480, 870, 600, 820], fill='white')
        
        d.text((540, 1700), "🎬 GENEROWANE PRZEZ AI", fill='#667eea', anchor="mt")
        
        img_path = tempfile.NamedTemporaryFile(delete=False, suffix=f"_scene_{scene_number}.png").name
        img.save(img_path)
        return img_path
        
    except Exception as e:
        img = Image.new('RGB', (1080, 1920), color='black')
        d = ImageDraw.Draw(img)
        d.text((100, 800), f"SCENA {scene_number}", fill='white')
        img_path = tempfile.NamedTemporaryFile(delete=False, suffix=f"_scene_{scene_number}.png").name
        img.save(img_path)
        return img_path

def create_video(scenes_texts, image_paths, audio_path, output_path):
    """Łączy obrazki i audio w film"""
    try:
        clip_duration = 4
        video_clips = []
        
        for img_path in image_paths:
            if os.path.exists(img_path):
                clip = mp.ImageClip(img_path, duration=clip_duration)
                video_clips.append(clip)
        
        if not video_clips:
            return False
        
        final_video = mp.concatenate_videoclips(video_clips, method="compose")
        
        if os.path.exists(audio_path):
            audio = mp.AudioFileClip(audio_path)
            if audio.duration > final_video.duration:
                final_video = final_video.set_duration(audio.duration)
            elif audio.duration < final_video.duration:
                final_video = final_video.subclip(0, audio.duration)
            final_video = final_video.set_audio(audio)
        
        final_video = final_video.resize(height=1920)
        final_video = final_video.crop(x_center=final_video.w/2, y_center=final_video.h/2, width=1080, height=1920)
        
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=2,
            verbose=False,
            logger=None
        )
        
        for clip in video_clips:
            clip.close()
        final_video.close()
        
        return True
        
    except Exception as e:
        return False

# ========== INTERFEJS ==========

st.title("🎬 Shorts Generator")
st.caption("Twórz filmy na iPhone za darmo")

# Wybór szablonu
st.subheader("📁 Wybierz szablon")

cols = st.columns(4)
templates = [
    ("news", "📰", "Wiadomości"),
    ("animals", "🐾", "Zwierzęta"),
    ("horror", "👻", "Horror"),
    ("motivation", "💪", "Motywacja")
]

for idx, (key, icon, name) in enumerate(templates):
    with cols[idx]:
        if st.button(f"{icon}\n{name}", use_container_width=True):
            st.session_state.template = key
            st.rerun()

# Wybór głosu
st.subheader("🎤 Wybierz głos")
voice = st.selectbox(
    "Lektor:",
    ["pl-PL-MarekNeural", "pl-PL-ZofiaNeural", "en-US-ChristopherNeural", "en-US-JennyNeural"],
    format_func=lambda x: {
        "pl-PL-MarekNeural": "👨 Męski (PL)",
        "pl-PL-ZofiaNeural": "👩 Żeński (PL)",
        "en-US-ChristopherNeural": "👨 Męski (EN)",
        "en-US-JennyNeural": "👩 Żeński (EN)"
    }[x]
)

# Temat
st.subheader("✏️ Temat shorta")
temat = st.text_area(
    "",
    placeholder="Np. Pies który uratował dziecko z pożaru",
    height=80,
    label_visibility="collapsed"
)

# Przycisk generowania
if st.button("🚀 GENERUJ SHORTA", use_container_width=True):
    if not temat:
        st.error("❌ Wpisz temat!")
    else:
        with st.spinner("🎬 Tworzę shorta... (2-3 minuty)"):
            try:
                # 1. Scenariusz
                st.info("📝 Piszę scenariusz...")
                script = generate_script(temat, st.session_state.template)
                st.session_state.script = script
                
                with st.expander("📜 Zobacz scenariusz"):
                    st.code(script)
                
                # 2. Głos
                st.info("🎤 Nagrywam lektora...")
                audio_path = asyncio.run(generate_voice(script, voice))
                
                # 3. Obrazki
                st.info("🖼️ Tworzę obrazki...")
                scenes = [s.strip() for s in script.split("\n") if s.strip() and "SCENA" in s]
                if len(scenes) < 3:
                    while len(scenes) < 3:
                        scenes.append(f"SCENA {len(scenes)+1}: {temat}")
                
                image_paths = []
                progress = st.progress(0)
                for i, scene in enumerate(scenes[:3]):
                    prompt = scene.replace(f"SCENA {i+1}:", "").strip()
                    img_path = generate_image(prompt, i+1)
                    image_paths.append(img_path)
                    progress.progress((i+1)/3)
                
                # 4. Film
                st.info("🎬 Montuję film...")
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                
                if create_video(scenes, image_paths, audio_path, output_path):
                    st.session_state.video_path = output_path
                    st.session_state.generated = True
                    st.success("✅ Gotowe!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Błąd montażu")
                    
                for path in image_paths:
                    try: os.unlink(path)
                    except: pass
                try: os.unlink(audio_path)
                except: pass
                
            except Exception as e:
                st.error(f"❌ Błąd: {str(e)[:200]}")

# Podgląd
if st.session_state.generated and st.session_state.video_path:
    if os.path.exists(st.session_state.video_path):
        st.subheader("📱 Twój short")
        st.video(st.session_state.video_path)
        
        with open(st.session_state.video_path, "rb") as f:
            video_bytes = f.read()
        st.download_button(
            label="⬇️ Pobierz na iPhone",
            data=video_bytes,
            file_name=f"short_{int(time.time())}.mp4",
            mime="video/mp4",
            use_container_width=True
        )
    else:
        st.session_state.generated = False

st.divider()
st.caption("Made with ❤️ · Działa na iPhone · 100% darmowe")
