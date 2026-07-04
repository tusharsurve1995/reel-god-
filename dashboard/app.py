"""
REEL GOD — Dashboard Server
===========================
Flask + Socket.IO server providing a glassmorphic dashboard for managing the agent,
planning content, approving/rejecting ideas, and watching video compilation in real-time.
Includes custom authentication, voice speaking capabilities, and Instagram direct publishing.
"""

import os
import sys
import threading
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, emit
from rich.console import Console

# Adjust python path to find project modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import config
from brain.core import ReelGodBrain
from dashboard import auth

console = Console()

app = Flask(__name__)
app.config['SECRET_KEY'] = config.DASHBOARD_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure the accounts table exists and a bootstrap admin is seeded.
auth.init_db()

# Shared brain instance
brain_instance = None
brain_lock = threading.Lock()

def get_brain():
    global brain_instance
    with brain_lock:
        if brain_instance is None:
            brain_instance = ReelGodBrain()
            
            # Set up log callback to stream logs to web clients
            def socket_log_callback(msg):
                # Clean up rich formatting tags for HTML output
                clean_msg = msg
                tags = ["[bold green]", "[/bold green]", "[cyan]", "[/cyan]", "[dim]", "[/dim]", "[yellow]", "[/yellow]", "[red]", "[/red]", "[bold cyan]", "[/bold cyan]", "[bold]", "[/bold]"]
                for tag in tags:
                    clean_msg = clean_msg.replace(tag, "")
                socketio.emit('log_update', {'log': clean_msg})
                
            brain_instance.log_callback = socket_log_callback
            
        return brain_instance

def save_env_var(key: str, value: str):
    """Dynamically save key=value to local .env file."""
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        new_lines.append(f"{key}={value}\n")
        
    with open(env_path, "w") as f:
        f.writelines(new_lines)

# ── AUTHENTICATION DECORATOR ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ── ROUTES ────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if auth.verify_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = True
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Create a login. Open when there are no accounts yet (first-run setup);
    afterwards only a logged-in user can add more accounts (shared workspace)."""
    open_signup = auth.user_count() == 0
    if not open_signup and not session.get('logged_in'):
        return redirect(url_for('login'))

    message, ok = None, False
    if request.method == 'POST':
        username = request.form.get('username') or ''
        password = request.form.get('password') or ''
        ok, message = auth.create_user(username, password)
        if ok and open_signup:
            # First account created — log them straight in.
            session['logged_in'] = True
            session['username'] = username.strip()
            return redirect(url_for('index'))
    return render_template('register.html', open_signup=open_signup,
                           message=message, ok=ok)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# ── SETTINGS (API KEYS + ACCOUNTS) ─────────────────────────────────────
# User-editable API keys. Each is free; leaving one blank simply disables that
# feature (the app degrades gracefully).
SETTINGS_KEYS = [
    ("GEMINI_API_KEY", "Gemini (AI scripts & captions)", "https://aistudio.google.com/apikey"),
    ("PEXELS_API_KEY", "Pexels (royalty-free video/photos)", "https://www.pexels.com/api/"),
    ("PIXABAY_API_KEY", "Pixabay (royalty-free video/photos)", "https://pixabay.com/api/docs/"),
    ("JAMENDO_CLIENT_ID", "Jamendo (Creative-Commons music)", "https://devportal.jamendo.com"),
]


def _apply_setting(key: str, value: str) -> None:
    """Persist a key to .env, the live environment, and the config module so it
    takes effect immediately without a restart."""
    save_env_var(key, value)
    os.environ[key] = value
    if hasattr(config, key):
        setattr(config, key, value)


@app.route('/settings')
@login_required
def settings():
    key_status = []
    for key, label, url in SETTINGS_KEYS:
        current = os.environ.get(key) or getattr(config, key, "") or ""
        if current == "PASTE_YOUR_KEY_HERE":
            current = ""
        key_status.append({
            "key": key,
            "label": label,
            "url": url,
            "configured": bool(current),
            "masked": (current[:4] + "…" + current[-2:]) if len(current) > 8 else ("set" if current else ""),
        })
    return render_template(
        'settings.html',
        key_status=key_status,
        username=session.get('username', 'admin'),
        usernames=auth.list_usernames(),
    )


@app.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    data = request.json or {}
    saved = []
    valid_keys = {k for k, _, _ in SETTINGS_KEYS}
    for key, value in data.items():
        if key in valid_keys and isinstance(value, str) and value.strip():
            _apply_setting(key, value.strip())
            saved.append(key)
    return jsonify({"success": True, "saved": saved})


@app.route('/api/account/password', methods=['POST'])
@login_required
def api_change_password():
    data = request.json or {}
    ok, message = auth.change_password(
        session.get('username', ''),
        data.get('current_password', ''),
        data.get('new_password', ''),
    )
    return jsonify({"success": ok, "message": message}), (200 if ok else 400)


@app.route('/api/account/create', methods=['POST'])
@login_required
def api_create_account():
    data = request.json or {}
    ok, message = auth.create_user(data.get('username', ''), data.get('password', ''))
    return jsonify({"success": ok, "message": message}), (200 if ok else 400)

# ── PWA (installable web app) ──────────────────────────────────────────

@app.route('/manifest.webmanifest')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.webmanifest',
                               mimetype='application/manifest+json')


@app.route('/sw.js')
def service_worker():
    # Served from root so its scope covers the whole app.
    resp = send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/')
@login_required
def index():
    brain = get_brain()
    status = brain.get_status()
    pending_ideas = brain.memory.get_pending_ideas()
    
    # Get active content schedule from DB cache
    schedule_data = []
    try:
        active_slots = brain.memory.get_active_schedule()
        if active_slots:
            schedule_data = [{
                "day": s["day_name"],
                "date": s["date_str"],
                "style": s["style"],
                "theme": s["theme"],
                "post_time": s["post_time"]
            } for s in active_slots]
        else:
            schedule_data = brain.planner.generate_weekly_calendar().get("days", [])
    except Exception:
        pass
        
    # Get published posts
    recent_posts = brain.memory.get_recent_posts(limit=10)
    
    # Format style stats
    style_stats = brain.memory.get_style_stats()
    
    # Fetch active learned rules
    rules = brain.memory.get_active_rules()
    
    return render_template(
        'index.html',
        status=status,
        pending_ideas=pending_ideas,
        schedule=schedule_data,
        posts=recent_posts,
        style_stats=style_stats,
        rules=rules
    )

@app.route('/api/ideas/pending')
@login_required
def get_pending_ideas():
    brain = get_brain()
    ideas = brain.memory.get_pending_ideas()
    return jsonify(ideas)

@app.route('/api/idea/<int:idea_id>/approve', methods=['POST'])
@login_required
def approve_idea(idea_id):
    brain = get_brain()
    try:
        brain.memory.approve_idea(idea_id)
        return jsonify({"success": True, "message": f"Idea #{idea_id} approved."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/idea/<int:idea_id>/reject', methods=['POST'])
@login_required
def reject_idea(idea_id):
    brain = get_brain()
    data = request.json or {}
    reason = data.get("reason", "No reason provided")
    try:
        brain.memory.reject_idea(idea_id, reason)
        return jsonify({"success": True, "message": f"Idea #{idea_id} rejected."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/idea/<int:idea_id>/generate', methods=['POST'])
@login_required
def generate_content(idea_id):
    brain = get_brain()
    
    def run_generation():
        try:
            socketio.emit('generation_status', {'status': 'started', 'idea_id': idea_id})
            video_path = brain.generate_video_content(idea_id)
            socketio.emit('generation_status', {
                'status': 'completed',
                'idea_id': idea_id,
                'video_path': video_path,
                'filename': Path(video_path).name
            })
        except Exception as e:
            socketio.emit('generation_status', {
                'status': 'failed',
                'idea_id': idea_id,
                'error': str(e)
            })
            
    # Run compilation in a background thread so the HTTP request returns immediately
    thread = threading.Thread(target=run_generation)
    thread.start()
    return jsonify({"success": True, "message": "Generation started in background."})

# ── RULES & LEARNING API ─────────────────────────────────────────────

@app.route('/api/rules', methods=['GET', 'POST'])
@login_required
def manage_rules():
    brain = get_brain()
    if request.method == 'POST':
        data = request.json or {}
        rule = data.get("rule")
        category = data.get("category", "general")
        if rule:
            rule_id = brain.memory.save_rule(rule, category)
            brain.log(f"Commander added new rule: {rule}", style="green")
            return jsonify({"success": True, "id": rule_id})
        return jsonify({"success": False, "error": "No rule text provided."}), 400
        
    rules = brain.memory.get_active_rules()
    return jsonify(rules)

@app.route('/api/rule/<int:rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    brain = get_brain()
    try:
        brain.memory.delete_rule(rule_id)
        brain.log(f"Commander deactivated rule ID #{rule_id}", style="dim")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/gemini-live/config')
@login_required
def gemini_live_config():
    brain = get_brain()
    api_key = os.environ.get("GEMINI_API_KEY") or config.GEMINI_API_KEY
    system_instruction = brain._get_personality_with_rules()
    return jsonify({
        "api_key": api_key,
        "system_instruction": system_instruction,
        "model": "models/gemini-2.0-flash"
    })

@app.route('/api/voice-chat', methods=['POST'])
@login_required
def voice_chat():
    brain = get_brain()
    data = request.json or {}
    message = data.get("message", "")
    if not message:
        return jsonify({"success": False, "error": "Empty message."}), 400
        
    try:
        response = brain.respond_to_commander(message)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── INSTAGRAM INTEGRATION API ────────────────────────────────────────

@app.route('/api/instagram/status')
@login_required
def instagram_status():
    username = os.environ.get("INSTAGRAM_USERNAME") or getattr(config, "INSTAGRAM_USERNAME", None)
    password = os.environ.get("INSTAGRAM_PASSWORD") or getattr(config, "INSTAGRAM_PASSWORD", None)
    configured = bool(username and password)
    return jsonify({
        "configured": configured,
        "username": username or "None",
        "session_cached": Path("data/instagram_session.json").exists()
    })

@app.route('/api/instagram/save', methods=['POST'])
@login_required
def instagram_save():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required."}), 400
        
    try:
        save_env_var("INSTAGRAM_USERNAME", username)
        save_env_var("INSTAGRAM_PASSWORD", password)
        # Update run variables
        os.environ["INSTAGRAM_USERNAME"] = username
        os.environ["INSTAGRAM_PASSWORD"] = password
        
        # Test connection
        from instagram.publisher import InstagramPublisher
        publisher = InstagramPublisher()
        success = publisher.login()
        
        if success:
            get_brain().log(f"Instagram connected successfully: @{username}", style="green")
            return jsonify({"success": True, "message": "Instagram connected successfully."})
        else:
            return jsonify({"success": False, "error": "Credentials invalid or Instagram challenge occurred."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/instagram/publish', methods=['POST'])
@login_required
def instagram_publish():
    data = request.json or {}
    post_id = data.get("post_id")
    if not post_id:
        return jsonify({"success": False, "error": "Post ID required."}), 400
        
    brain = get_brain()
    # Fetch post from DB
    post = None
    with brain.memory._connect() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row:
            post = dict(row)
            
    if not post:
        return jsonify({"success": False, "error": f"Post #{post_id} not found."}), 404
        
    video_path = Path(post["video_path"])
    caption = post["caption"]
    
    def run_upload():
        try:
            socketio.emit('publish_status', {'status': 'started', 'post_id': post_id})
            brain.log(f"Initiating direct upload of Reel #{post_id} to Instagram...", style="cyan")
            
            from instagram.publisher import InstagramPublisher
            publisher = InstagramPublisher()
            media_id = publisher.publish_reel(video_path, caption)
            
            if media_id:
                # Update SQLite record
                with brain.memory._connect() as conn:
                    conn.execute(
                        "UPDATE posts SET instagram_id = ?, posted_at = datetime('now') WHERE id = ?",
                        (media_id, post_id)
                    )
                brain.log(f"Reel #{post_id} published successfully! Media ID: {media_id}", style="green")
                socketio.emit('publish_status', {
                    'status': 'completed',
                    'post_id': post_id,
                    'instagram_id': media_id
                })
            else:
                raise RuntimeError("Instagram failed to return media ID.")
        except Exception as e:
            brain.log(f"Instagram upload failed: {e}", style="red")
            socketio.emit('publish_status', {
                'status': 'failed',
                'post_id': post_id,
                'error': str(e)
            })
            
    thread = threading.Thread(target=run_upload)
    thread.start()
    return jsonify({"success": True, "message": "Reel upload process initiated."})

def _extract_keyframes(video_path: Path, temp_dir: Path) -> list:
    """Extract 4 keyframes from a video clip at even intervals."""
    from moviepy.editor import VideoFileClip
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up old keyframes
    for f in temp_dir.glob("frame_*.jpg"):
        try:
            f.unlink()
        except:
            pass
            
    clip = VideoFileClip(str(video_path))
    dur = clip.duration
    frames = []
    
    # Save frames at 15%, 40%, 65%, 85%
    intervals = [0.15, 0.40, 0.65, 0.85]
    for idx, pct in enumerate(intervals):
        out_jpg = temp_dir / f"frame_{idx}.jpg"
        clip.save_frame(str(out_jpg), t=dur * pct)
        if out_jpg.exists():
            frames.append(out_jpg)
            
    clip.close()
    return [str(f) for f in frames]

# ── VIDEO CO-PILOT API ────────────────────────────────────────────────

@app.route('/api/co-pilot/upload', methods=['POST'])
@login_required
def copilot_upload():
    """Receive uploaded video file and extract 4 keyframes locally."""
    if 'video' not in request.files:
        return jsonify({"success": False, "error": "No video file provided."}), 400
        
    file = request.files['video']
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename."}), 400
        
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = upload_dir / "temp_input.mp4"
    file.save(str(filepath))
    
    try:
        keyframes_dir = upload_dir / "keyframes"
        keyframes = _extract_keyframes(filepath, keyframes_dir)
        web_kf = [f"/uploads/keyframes/{Path(k).name}" for k in keyframes]
        
        return jsonify({
            "success": True, 
            "filepath": str(filepath), 
            "keyframes": web_kf
        })
    except Exception as e:
        console.print(f"[red]Keyframe extraction failed: {e}[/]")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/uploads/keyframes/<filename>')
@login_required
def serve_keyframe(filename):
    """Serve keyframe images for the UI dashboard."""
    return send_from_directory("data/uploads/keyframes", filename)

@app.route('/api/co-pilot/analyze', methods=['POST'])
@login_required
def copilot_analyze():
    """Call Gemini multimodal vision to analyze the extracted keyframes and user prompt."""
    data = request.json or {}
    filepath_str = data.get("filepath", "")
    instruction = data.get("instruction", "make a cinematic hype reel")
    
    if not filepath_str:
        return jsonify({"success": False, "error": "Video filepath missing."}), 400
        
    try:
        from google import genai as gai
        from PIL import Image
        import json, re
        
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({"success": False, "error": "GEMINI_API_KEY environment variable missing."}), 400
            
        client = gai.Client(api_key=api_key)
        
        upload_dir = Path("data/uploads")
        keyframes_dir = upload_dir / "keyframes"
        kfs = list(keyframes_dir.glob("frame_*.jpg"))
        kfs.sort()
        
        contents = [
            "You are REEL GOD's Multimodal Video Co-Pilot. Analyze these 4 sequential keyframes of a user's uploaded video."
        ]
        for k in kfs:
            contents.append(Image.open(k))
            
        prompt = f"""
User's editing intent/instruction: "{instruction}"

Based on the visuals and instruction, generate a world-class creative editing structure:
1. Identify the core theme, content, and emotional mood of the clip.
2. Recommend a layout format: "9:16" (Reel/Story) or "1:1" (Square Feed Post).
3. Recommend a specific music search query (e.g. dramatic violin epic, sad acoustic piano, upbeat bollywood energetic).
4. Write a 5-step progressive narrative subtitle script that builds deep tension and delivers a high-impact climax. Keep each subtitle short (max 7 words). The sum of all durations MUST equal 25.0 seconds.

Return ONLY valid JSON:
{{
  "theme": "Identified theme of the footage",
  "aspect_ratio": "9:16 or 1:1",
  "music_query": "Music search query",
  "title": "Creative video title",
  "caption": "Viral Instagram caption with emojis and hashtags",
  "narrative": [
    {{"text": "Short emotional hook...", "duration": 4.5}},
    {{"text": "Rising tension line...", "duration": 5.0}},
    {{"text": "The turning point...", "duration": 5.0}},
    {{"text": "CLIMAX LINE IN CAPS...", "duration": 5.5}},
    {{"text": "Ending resolution punchline...", "duration": 5.0}}
  ]
}}
"""
        contents.append(prompt)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        
        txt = re.sub(r'^```[a-z]*\n?', '', resp.text.strip())
        txt = re.sub(r'```$', '', txt).strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        
        if m:
            analysis = json.loads(m.group(0))
            return jsonify({"success": True, "analysis": analysis})
        else:
            raise RuntimeError("Gemini did not return valid JSON block.")
            
    except Exception as e:
        console.print(f"[red]Co-pilot analysis failed: {e}[/]")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/co-pilot/compile', methods=['POST'])
@login_required
def copilot_compile():
    """Trigger the editor to compile the user video with recommended music and subtitles."""
    data = request.json or {}
    filepath_str = data.get("filepath", "")
    analysis = data.get("analysis", {})
    
    if not filepath_str or not analysis:
        return jsonify({"success": False, "error": "Missing video path or analysis data."}), 400
        
    def run_copilot_compilation():
        try:
            socketio.emit('copilot_status', {'status': 'started'})
            
            from generator.reel_composer import ReelComposer
            from music.music_fetcher import MusicFetcher
            
            composer = ReelComposer()
            music_fx = MusicFetcher()
            
            music_query = analysis.get("music_query", "cinematic theme no copyright")
            get_brain().log(f"Co-Pilot: Sourcing music for query '{music_query}'...", style="cyan")
            socketio.emit('copilot_progress', {'percent': 15, 'stage': 'Sourcing recommended music track...'})
            
            music_path = music_fx._download_audio(music_query, "copilot")
            socketio.emit('copilot_progress', {'percent': 30, 'stage': 'Music sourced. Synthesizing montage edits...'})
            
            get_brain().log(f"Co-Pilot: Synthesizing multi-cut edits & narrative overlays...", style="cyan")
            reel_meta = {
                "anime": "uploaded_video",
                "style": "custom",
                "title": analysis.get("title", "My Masterpiece"),
                "caption": analysis.get("caption", "My custom video"),
                "aspect_ratio": analysis.get("aspect_ratio", "9:16"),
                "narrative": analysis.get("narrative", [])
            }
            
            # Progress callback for the video composer
            def progress_handler(percent, stage):
                socketio.emit('copilot_progress', {'percent': percent, 'stage': stage})

            output_name = f"copilot_{int(time.time())}.mp4"
            final_path = composer.compose_reel(Path(filepath_str), music_path, reel_meta, output_name, progress_cb=progress_handler)
            
            if final_path:
                post_id = None
                with get_brain().memory._connect() as conn:
                    cursor = conn.execute(
                        "INSERT INTO posts (idea_id, title, style, caption, video_path, posted_at) VALUES (NULL, ?, ?, ?, ?, datetime('now'))",
                        (reel_meta["title"], reel_meta.get("style", "custom"), reel_meta["caption"], str(final_path))
                    )
                    post_id = cursor.lastrowid
                
                get_brain().log(f"Co-Pilot: Production complete! Generated Reel #{post_id}", style="green")
                socketio.emit('copilot_status', {
                    'status': 'completed',
                    'post_id': post_id,
                    'filename': final_path.name
                })
            else:
                raise RuntimeError("Composer failed to render video.")
                
        except Exception as e:
            get_brain().log(f"Co-Pilot compilation failed: {e}", style="red")
            socketio.emit('copilot_status', {'status': 'failed', 'error': str(e)})
            
    import time
    thread = threading.Thread(target=run_copilot_compilation)
    thread.start()
    return jsonify({"success": True, "message": "Co-pilot synthesis started in background."})

# ── INSTAGRAM REEL CREATOR API ─────────────────────────────────────────
# Unified creator: build a Reel / Post / Story from anime (internet) or an
# uploaded photo/video, with any music genre. Powered by generator.reel_studio.

CREATOR_STYLES = [
    "epic_action", "emotional", "romance", "dark_cinematic",
    "motivational", "mystical",
]
CREATOR_FORMATS = ["reel", "post", "story"]
CREATOR_GENRES = [
    "auto", "bollywood", "hollywood", "pop",
    "instrumental", "action", "romantic", "worldwide",
]

@app.route('/api/creator/options')
@login_required
def creator_options():
    """Dropdown options for the Reel Creator UI."""
    from generator.anime_fetcher import ANIME_SEARCHES
    animes = [{"key": k, "label": k.replace("_", " ").title()} for k in sorted(ANIME_SEARCHES.keys())]
    return jsonify({
        "animes": animes,
        "styles": CREATOR_STYLES,
        "formats": CREATOR_FORMATS,
        "genres": CREATOR_GENRES,
        "stock_sources": config.stock_sources_available(),
    })

@app.route('/api/creator/stock', methods=['POST'])
@login_required
def creator_stock():
    """Create a Reel/Post/Story from royalty-free stock footage (Pexels/Pixabay)."""
    if not config.stock_sources_available():
        return jsonify({
            "success": False,
            "error": "No royalty-free stock source configured. Add a free "
                     "PEXELS_API_KEY or PIXABAY_API_KEY, then restart.",
        }), 400
    data = request.json or {}
    kwargs = {
        "source": "stock",
        "style": data.get("style", "epic_action"),
        "fmt": data.get("format", "reel"),
        "genre": data.get("genre", "auto"),
        "instruction": data.get("instruction", ""),
    }
    threading.Thread(target=_run_creator_job, args=(kwargs,), daemon=True).start()
    return jsonify({"success": True, "message": "Creating from royalty-free stock in background."})

def _run_creator_job(kwargs: dict):
    """Background worker that runs reel_studio.create_reel and streams progress."""
    from generator import reel_studio
    def progress_handler(percent, stage):
        socketio.emit('creator_progress', {'percent': percent, 'stage': stage})
    try:
        socketio.emit('creator_status', {'status': 'started'})
        result = reel_studio.create_reel(get_brain(), progress_cb=progress_handler, **kwargs)
        socketio.emit('creator_status', {
            'status': 'completed',
            'post_id': result.get('post_id'),
            'filename': result.get('filename'),
            'title': result.get('title'),
            'format': result.get('format'),
        })
    except Exception as e:
        get_brain().log(f"Reel Creator failed: {e}", style="red")
        socketio.emit('creator_status', {'status': 'failed', 'error': str(e)})

@app.route('/api/creator/anime', methods=['POST'])
@login_required
def creator_anime():
    """Create a Reel/Post/Story from an anime source fetched off the internet."""
    data = request.json or {}
    anime = (data.get("anime") or "").strip() or None  # None → agent picks
    kwargs = {
        "source": "anime",
        "anime": anime,
        "style": data.get("style", "epic_action"),
        "fmt": data.get("format", "reel"),
        "genre": data.get("genre", "auto"),
        "instruction": data.get("instruction", ""),
    }
    threading.Thread(target=_run_creator_job, args=(kwargs,), daemon=True).start()
    return jsonify({"success": True, "message": "Creating from anime in background."})

@app.route('/api/creator/upload', methods=['POST'])
@login_required
def creator_upload():
    """Receive an uploaded photo OR video for conversion into a Reel/Post/Story."""
    import time
    file = request.files.get('media') or request.files.get('video')
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No media file provided."}), 400

    ext = Path(file.filename).suffix.lower()
    from generator.reel_studio import IMAGE_EXTS, VIDEO_EXTS
    if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
        return jsonify({"success": False, "error": f"Unsupported file type '{ext}'."}), 400

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / f"creator_{int(time.time())}{ext}"
    file.save(str(filepath))
    kind = "image" if ext in IMAGE_EXTS else "video"
    return jsonify({"success": True, "filepath": str(filepath), "kind": kind})

@app.route('/api/creator/compile-upload', methods=['POST'])
@login_required
def creator_compile_upload():
    """Turn an uploaded photo/video into a Reel/Post/Story."""
    data = request.json or {}
    filepath_str = (data.get("filepath") or "").strip()
    if not filepath_str or not Path(filepath_str).exists():
        return jsonify({"success": False, "error": "Uploaded media not found."}), 400
    kwargs = {
        "source": "upload",
        "media_path": Path(filepath_str),
        "style": data.get("style", "epic_action"),
        "fmt": data.get("format", "reel"),
        "genre": data.get("genre", "auto"),
        "instruction": data.get("instruction", ""),
    }
    threading.Thread(target=_run_creator_job, args=(kwargs,), daemon=True).start()
    return jsonify({"success": True, "message": "Converting upload in background."})

# Serve generated videos
@app.route('/videos/<filename>')
@login_required
def serve_video(filename):
    return send_from_directory(config.CONTENT_DIR, filename)

# Serve generated images/thumbnails
@app.route('/thumbnails/<filename>')
@login_required
def serve_thumbnail(filename):
    return send_from_directory(config.COMFYUI_OUTPUT_DIR, filename)

# ── SOCKET EVENTS ──────────────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    if not session.get('logged_in'):
        return False
    emit('status_update', {'status': 'connected'})

def get_local_ip():
    """Auto-detect local network IP address for mobile access."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable, just triggers OS interface lookup
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# ── START SERVER ──────────────────────────────────────────────────────

def start_dashboard():
    """Start Flask + Socket.IO server."""
    get_brain()

    # Hosting platforms (Render/Railway/etc.) inject the port to bind via $PORT.
    port = int(os.environ.get("PORT", config.DASHBOARD_PORT))
    local_ip = get_local_ip()
    from rich.panel import Panel

    console.print(Panel(
        f"[bold green]✓ Dashboard Server Active & Network-Accessible[/bold green]\n\n"
        f"🖥️  [bold]On your PC:[/]       [cyan]http://127.0.0.1:{port}[/cyan]\n"
        f"📱 [bold]On your Mobile:[/]   [cyan]http://{local_ip}:{port}[/cyan]\n\n"
        f"[dim]Note: Ensure both your PC and Mobile are on the same Wi-Fi network![/dim]",
        title="🚀 REEL GOD COMMAND DASHBOARD",
        border_style="green"
    ))

    socketio.run(
        app,
        host=config.DASHBOARD_HOST,
        port=port,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )

if __name__ == '__main__':
    start_dashboard()

