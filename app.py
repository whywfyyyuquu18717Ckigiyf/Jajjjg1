from flask import Flask
from markupsafe import Markup

app = Flask(__name__)

html_content = Markup("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardcoded Watermark Player</title>
    <style>
        body, html {
            margin: 0; padding: 0; height: 100%;
            background-color: #141414;
            display: flex; justify-content: center; align-items: center;
            font-family: sans-serif;
        }

        .player-container {
            position: relative;
            width: 95%;
            max-width: 900px;
            background-color: #000;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
        }

        .player-container:-webkit-full-screen { width: 100%; height: 100%; }
        .player-container:-moz-full-screen { width: 100%; height: 100%; }
        .player-container:-ms-fullscreen { width: 100%; height: 100%; }
        .player-container:fullscreen { width: 100%; height: 100%; }

        video {
            width: 100%; height: 100%;
            display: block;
        }
        
        video::-webkit-media-controls-fullscreen-button {
            display: none;
        }

        .watermark {
            position: absolute;
            top: 15px; right: 15px;
            color: #FFFFFF;
            font-size: 18px; font-weight: bold;
            background-color: #E50914;
            padding: 6px 14px;
            border-radius: 5px;
            pointer-events: none;
            opacity: 0.9;
            z-index: 10;
        }
        
        .custom-fullscreen-btn {
            position: absolute;
            bottom: 12px;
            right: 15px;
            background: none;
            border: none;
            cursor: pointer;
            z-index: 10;
            opacity: 0.8;
            padding: 5px;
        }
        .custom-fullscreen-btn:hover {
            opacity: 1;
        }
    </style>
</head>
<body>

    <div id="player-container" class="player-container">
        <video id="my-video" controls preload="auto" controlslist="nodownload nofullscreen">
            <source src="https://surrit.com/984066a8-22ec-4678-ab62-f4c5465e1e7e/720p/video.m3u8" type="application/x-mpegURL">
            Your browser does not support the video tag.
        </video>
        
        <div class="watermark">From Netflix</div>

        <button id="fullscreen-btn" class="custom-fullscreen-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
            </svg>
        </button>
    </div>

    <script>
        const playerContainer = document.getElementById('player-container');
        const video = document.getElementById('my-video');
        const fullscreenBtn = document.getElementById('fullscreen-btn');

        fullscreenBtn.addEventListener('click', () => {
            const isFullscreen = document.fullscreenElement;
            if (!isFullscreen) {
                playerContainer.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });
    </script>

</body>
</html>
""")

@app.route('/')
def index():
    return html_content

# Render के लिए gunicorn सपोर्ट
if __name__ == '__main__':
    app.run()
