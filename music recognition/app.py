import streamlit as st
import requests
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os
import io

# Page setup
st.set_page_config(
    page_title="Song Recognizer - AudD API",
    page_icon="🎵",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(90deg, #FF4B4B, #FF8C42);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
    }
    .success-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎵 Song Recognition with AudD API")
st.markdown("### Play any song from your mobile → Get instant results!")

# Your API Key
YOUR_API_KEY = "4465b59e3a86186e7809929f13a6622b"

# Sidebar
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key = st.text_input("AudD API Key:", value=YOUR_API_KEY, type="password")
    
    # Test API
    if st.button("Test API Connection"):
        try:
            # Simple test request
            test_response = requests.get(f"https://api.audd.io/?api_token={api_key}")
            if test_response.status_code == 200:
                st.success("✅ API Key is valid!")
            else:
                st.error("❌ API Key invalid")
        except:
            st.error("❌ Connection failed")
    
    st.markdown("---")
    st.header("⚙️ Settings")
    record_duration = st.slider("Recording Time (seconds)", 5, 20, 10)
    
    # Microphone info
    try:
        devices = sd.query_devices()
        st.info(f"📢 Found {len([d for d in devices if d['max_input_channels'] > 0])} microphone(s)")
    except:
        st.warning("Could not detect microphones")

# **FIXED: Correct AudD API function**
def recognize_song_audd(audio_file_path, api_token):
    """
    CORRECT implementation for AudD API
    """
    url = "https://api.audd.io/"
    
    try:
        # Read the audio file
        with open(audio_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        
        # Create proper multipart form data
        files = {
            'file': ('audio.wav', audio_bytes, 'audio/wav')
        }
        
        data = {
            'api_token': api_token,
            'return': 'apple_music,spotify,youtube',
        }
        
        # Make POST request with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        # Log for debugging
        st.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"HTTP Error: {response.status_code}")
            st.error(f"Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# **ALTERNATIVE: Using requests_toolbelt for better multipart**
def recognize_song_audd_alternative(audio_file_path, api_token):
    """Alternative method using proper multipart encoding"""
    try:
        from requests_toolbelt.multipart.encoder import MultipartEncoder
        
        # Read file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Create multipart encoder
        mp_encoder = MultipartEncoder(
            fields={
                'file': ('audio.wav', audio_data, 'audio/wav'),
                'api_token': api_token,
                'return': 'spotify,apple_music'
            }
        )
        
        headers = {
            'Content-Type': mp_encoder.content_type,
            'User-Agent': 'SongRecognizer/1.0'
        }
        
        response = requests.post(
            'https://api.audd.io/',
            data=mp_encoder,
            headers=headers,
            timeout=30
        )
        
        return response.json()
        
    except ImportError:
        st.info("Installing requests-toolbelt for better performance...")
        os.system("pip install requests-toolbelt")
        return recognize_song_audd_alternative(audio_file_path, api_token)
    except Exception as e:
        st.error(f"Alternative method failed: {e}")
        return None

# **SIMPLEST: Direct file upload method**
def recognize_song_simple(audio_file_path, api_token):
    """Simplest working method"""
    import base64
    
    try:
        # Read and encode file
        with open(audio_file_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Send as POST with JSON
        payload = {
            'api_token': api_token,
            'audio': audio_base64,
            'return': 'spotify'
        }
        
        response = requests.post(
            'https://api.audd.io/',
            json=payload,
            timeout=30
        )
        
        return response.json()
        
    except Exception as e:
        st.error(f"Simple method error: {e}")
        return None

# Record audio function
def record_audio(duration=10):
    """Record audio from microphone"""
    try:
        st.info(f"🎤 Recording for {duration} seconds...")
        st.info("▶️ Play your song NOW and hold phone near microphone!")
        
        # Record audio
        recording = sd.rec(
            int(duration * 44100),
            samplerate=44100,
            channels=1,
            dtype='float32'
        )
        
        # Show progress
        progress_bar = st.progress(0)
        for i in range(duration):
            time.sleep(1)
            progress_bar.progress((i + 1) / duration)
        
        sd.wait()
        st.success("✅ Recording complete!")
        
        return recording, 44100
        
    except Exception as e:
        st.error(f"Recording failed: {e}")
        return None, None

# Display results
def display_song_info(result):
    """Display song information"""
    if not result:
        return
    
    if result.get('status') == 'success' and result.get('result'):
        song = result['result']
        
        # Display in nice format
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Album art
            album_art = None
            if 'spotify' in song:
                album_art = song['spotify']['album']['images'][0]['url']
            elif 'apple_music' in song:
                album_art = song['apple_music']['artwork']['url']
            
            if album_art:
                st.image(album_art, width=150)
            else:
                st.image("https://via.placeholder.com/150x150/667eea/ffffff?text=Album+Art", 
                        width=150)
        
        with col2:
            # Song info
            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')
            
            st.markdown(f"# 🎶 **{title}**")
            st.markdown(f"### 👨‍🎤 **{artist}**")
            
            if 'album' in song:
                st.markdown(f"💿 **Album:** {song['album']}")
            
            if 'release_date' in song:
                st.markdown(f"📅 **Released:** {song['release_date']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Streaming links
        st.markdown("### 🔊 Listen on:")
        
        cols = st.columns(3)
        
        if 'spotify' in song:
            with cols[0]:
                st.markdown(f"[![Spotify](https://img.shields.io/badge/Spotify-1DB954?logo=spotify&logoColor=white)]({song['spotify']['external_urls']['spotify']})")
        
        if 'apple_music' in song:
            with cols[1]:
                st.markdown(f"[![Apple Music](https://img.shields.io/badge/Apple_Music-FA243C?logo=apple-music&logoColor=white)]({song['apple_music']['url']})")
        
        if 'youtube' in song:
            with cols[2]:
                youtube_url = f"https://youtube.com/watch?v={song['youtube']['vid']}"
                st.markdown(f"[![YouTube](https://img.shields.io/badge/YouTube-FF0000?logo=youtube&logoColor=white)]({youtube_url})")
    
    elif result.get('status') == 'success' and not result.get('result'):
        st.warning("""
        ### 🎵 No song detected!
        
        **Possible reasons:**
        - Song was too quiet
        - Recording too short
        - Background noise
        - Song not in database
        
        **Try:**
        1. Play song louder
        2. Record 10+ seconds
        3. Use popular English song
        4. Reduce background noise
        """)
    else:
        st.error(f"API Error: {result}")

# **MAIN APP**
def main():
    st.header("🎤 Record from Mobile")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🎵 START RECORDING & RECOGNIZE", type="primary", use_container_width=True):
            
            # Validate API key
            if not api_key:
                st.error("Please enter API key")
                return
            
            # Record audio
            audio_data, sr = record_audio(record_duration)
            
            if audio_data is not None:
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    sf.write(tmp_file.name, audio_data, sr)
                    
                    # Play recording
                    st.audio(tmp_file.name, format='audio/wav')
                    
                    # Try different methods
                    st.info("🔄 Sending to AudD API...")
                    
                    # Method 1: Simple base64 method (most reliable)
                    with st.spinner("Method 1: Base64 encoding..."):
                        result = recognize_song_simple(tmp_file.name, api_key)
                        
                        if result and result.get('status') == 'success':
                            display_song_info(result)
                        else:
                            # Method 2: Multipart form
                            st.info("Trying Method 2: Multipart form...")
                            result = recognize_song_audd(tmp_file.name, api_key)
                            display_song_info(result)
                    
                    # Cleanup
                    os.unlink(tmp_file.name)
    
    with col2:
        st.markdown("""
        ### 💡 Quick Tips:
        
        1. **Play song loudly** (70%+ volume)
        2. **Hold phone near** computer mic
        3. **Record 10 seconds** minimum
        4. **Use popular songs** for best results
        5. **Quiet environment**
        
        ### 🎯 Test Songs:
        - Shape of You - Ed Sheeran
        - Blinding Lights - The Weeknd
        - Dance Monkey - Tones and I
        """)
    
    # Upload option
    st.markdown("---")
    st.header("📁 Or Upload Audio File")
    
    uploaded_file = st.file_uploader("Choose audio file", type=['mp3', 'wav', 'm4a'])
    
    if uploaded_file is not None:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            
            st.audio(uploaded_file)
            
            if st.button("🔍 Identify Uploaded Song", type="secondary"):
                with st.spinner("Analyzing..."):
                    result = recognize_song_simple(tmp_file.name, api_key)
                    display_song_info(result)
                
                os.unlink(tmp_file.name)
    
    # Test section
    st.markdown("---")
    st.header("🧪 Quick API Test")
    
    if st.button("Test with Sample Audio"):
        # Create a simple test audio
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, test_audio, 44100)
            
            # Test API
            test_result = recognize_song_simple(tmp_file.name, api_key)
            
            if test_result:
                st.json(test_result)
            
            os.unlink(tmp_file.name)

# Run app
if __name__ == "__main__":
    main()