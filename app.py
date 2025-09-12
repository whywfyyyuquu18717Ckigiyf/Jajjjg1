import uuid
from flask import Flask, request, render_template_string, url_for, abort, redirect
import re

# Flask app ko initialize karein
app = Flask(__name__)

# Video links ko store karne ke liye in-memory dictionary
# Production ke liye database ka istemal karna behtar hoga
video_links_db = {}

# ==============================================================================
# HTML TEMPLATES
# Inhe alag file mein bhi rakh sakte hain, lekin single-file ke liye yahi theek hai
# ==============================================================================

# Home Page ka Template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Link Embedder</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f0f2f5;
            color: #1c1e21;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 90%;
            max-width: 500px;
        }
        h1 {
            color: #0d6efd;
            margin-bottom: 1.5rem;
        }
        p {
            color: #606770;
            margin-bottom: 2rem;
        }
        .url-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #dddfe2;
            border-radius: 8px;
            font-size: 1rem;
            margin-bottom: 1rem;
            box-sizing: border-box;
        }
        .submit-btn {
            background-color: #0d6efd;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
            width: 100%;
        }
        .submit-btn:hover {
            background-color: #0b5ed7;
        }
        .generated-link-container {
            margin-top: 2rem;
            background-color: #e7f3ff;
            padding: 1rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .generated-link {
            font-family: monospace;
            color: #0b5ed7;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-right: 1rem;
        }
        .copy-btn {
            background-color: #198754;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .copy-btn:hover {
            background-color: #157347;
        }
        .error {
            color: #dc3545;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Link Embedder</h1>
        <p>Apna video link (jaise .../360p/video.m3u8) yahan paste karein.</p>
        <form method="POST">
            <input type="url" name="video_url" class="url-input" placeholder="https://surrit.com/.../360p/video.m3u8" required>
            <button type="submit" class="submit-btn">Generate Link</button>
        </form>
        
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if generated_url %}
            <div class="generated-link-container">
                <span id="new-link" class="generated-link">{{ generated_url }}</span>
                <button onclick="copyLink()" class="copy-btn">Copy</button>
            </div>
        {% endif %}
    </div>

    <script>
        function copyLink() {
            const linkElement = document.getElementById('new-link');
            const linkText = linkElement.innerText;
            navigator.clipboard.writeText(linkText).then(() => {
                const copyButton = document.querySelector('.copy-btn');
                copyButton.innerText = 'Copied!';
                setTimeout(() => {
                    copyButton.innerText = 'Copy';
                }, 2000);
            }).catch(err => {
                console.error('Copy karne mein error aaya: ', err);
            });
        }
    </script>
</body>
</html>
"""

# Video Display Page ka Template
VIDEO_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Embedded Videos</title>
    <!-- HLS.js library for playing m3u8 files -->
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #121212;
            color: #e0e0e0;
            margin: 0;
            padding: 1.5rem;
        }
        h1 {
            text-align: center;
            color: #ffffff;
            border-bottom: 2px solid #0d6efd;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        .video-container {
            background-color: #1e1e1e;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }
        .video-player {
            width: 100%;
            height: auto;
            background-color: #000;
        }
        h2 {
            font-size: 1.2rem;
            color: #0d6efd;
            padding: 0.8rem 1rem;
            margin: 0;
            background-color: #2a2a2a;
        }
    </style>
</head>
<body>
    <h1>Video Player</h1>
    <div class="video-grid">
        {% for video in videos %}
        <div class="video-container">
            <h2>{{ video.quality }}</h2>
            <video id="video-{{ loop.index }}" class="video-player" data-src="{{ video.url }}" controls></video>
        </div>
        {% endfor %}
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const videoElements = document.querySelectorAll('.video-player');
            videoElements.forEach(videoEl => {
                const videoSrc = videoEl.getAttribute('data-src');
                if (Hls.isSupported()) {
                    const hls = new Hls();
                    hls.loadSource(videoSrc);
                    hls.attachMedia(videoEl);
                    hls.on(Hls.Events.MANIFEST_PARSED, () => {
                        // Aap chahein to yahan auto-play kar sakte hain
                        // videoEl.play();
                    });
                } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
                    // Native HLS support (jaise Safari mein)
                    videoEl.src = videoSrc;
                }
            });
        });
    </script>
</body>
</html>
"""

# ==============================================================================
# FLASK ROUTES
# ==============================================================================

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = request.form.get('video_url')
        if not original_url:
            return render_template_string(HOME_TEMPLATE, error="URL daalna zaroori hai.")

        # URL ka base part nikalne ke liye regex ka istemal
        # Yeh '.../quality/video.m3u8' pattern ko match karega
        match = re.match(r'^(.*\/)[^\/]+\/video\.m3u8$', original_url)
        
        if not match:
            return render_template_string(HOME_TEMPLATE, error="Link ka format sahi nahi hai. Aakhri mein '/quality/video.m3u8' hona chahiye.")

        base_url = match.group(1)
        
        # Ek unique ID generate karein
        video_id = uuid.uuid4().hex[:8]
        
        # ID aur base URL ko store karein
        video_links_db[video_id] = base_url
        
        # Naya URL banayein
        generated_url = url_for('show_videos', video_id=video_id, _external=True)
        
        return render_template_string(HOME_TEMPLATE, generated_url=generated_url)

    return render_template_string(HOME_TEMPLATE)

@app.route('/v/<string:video_id>')
def show_videos(video_id):
    # Diye gaye ID se base URL dhundein
    base_url = video_links_db.get(video_id)
    
    if not base_url:
        # Agar ID nahi mila to 404 error
        abort(404, description="Video link nahi mila.")
        
    qualities = ['1080p', '720p', '480p', '360p']
    videos_to_render = []
    
    for quality in qualities:
        videos_to_render.append({
            'quality': f'Quality: {quality}',
            'url': f'{base_url}{quality}/video.m3u8'
        })
        
    return render_template_string(VIDEO_PAGE_TEMPLATE, videos=videos_to_render)


# ==============================================================================
# APP KO RUN KAREIN
# ==============================================================================
if __name__ == '__main__':
    # '0.0.0.0' use karne se yeh aapke network par bhi accessible hoga
    app.run(host='0.0.0.0', port=5000, debug=True)
