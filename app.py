import uuid
from flask import Flask, request, render_template_string, url_for, abort

# Initialize the Flask application
app = Flask(__name__)

# This dictionary acts as a simple in-memory database.
# For a real application, you would use a proper database like SQLite or PostgreSQL.
url_mappings = {}

# --- HTML & CSS & JavaScript Templates ---

# This is the main page template where users will paste their links.
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Page Generator</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 600px;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }
        p {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        .link-box {
            display: flex;
            margin-bottom: 10px;
        }
        input[type="url"], input[type="text"] {
            flex-grow: 1;
            padding: 12px;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            font-size: 16px;
        }
        button {
            display: block;
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button[type="submit"] {
            background-color: #3498db;
            color: white;
            margin-top: 15px;
        }
        button[type="submit"]:hover {
            background-color: #2980b9;
        }
        button[type="button"] {
            background-color: #ecf0f1;
            color: #34495e;
            margin-top: 10px;
            font-weight: normal;
        }
        button[type="button"]:hover {
            background-color: #dadedf;
        }
        #result {
            margin-top: 30px;
            padding: 20px;
            background-color: #e8f6f3;
            border-left: 5px solid #1abc9c;
            border-radius: 6px;
        }
        .copy-container {
            display: flex;
            gap: 10px;
        }
        .copy-container button {
            width: auto;
            padding: 0 20px;
            background-color: #1abc9c;
            color: white;
        }
         .copy-container button:hover {
            background-color: #16a085;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Generate a Sharable Video Page 🎬</h1>
        <p>Paste your direct cloud video links below. A unique page will be created to display them all.</p>

        <form method="post">
            <div id="link-boxes-container">
                <div class="link-box">
                    <input type="url" name="urls" placeholder="https://example.com/your-video.mp4" required>
                </div>
            </div>
            <button type="button" onclick="addLinkBox()">+ Add Another Link</button>
            <button type="submit">Generate Page</button>
        </form>

        {% if generated_link %}
        <div id="result">
            <h2>Your unique page is ready!</h2>
            <div class="copy-container">
                <input type="text" value="{{ generated_link }}" id="generatedUrl" readonly>
                <button onclick="copyLink()">Copy</button>
            </div>
            <p id="copy-success" style="display:none; color: green; text-align: left; margin-top: 10px;">Copied!</p>
        </div>
        {% endif %}
    </div>

    <script>
        function addLinkBox() {
            const container = document.getElementById('link-boxes-container');
            const newDiv = document.createElement('div');
            newDiv.className = 'link-box';
            newDiv.innerHTML = '<input type="url" name="urls" placeholder="https://example.com/another-video.mp4">';
            container.appendChild(newDiv);
        }

        function copyLink() {
            const urlInput = document.getElementById('generatedUrl');
            navigator.clipboard.writeText(urlInput.value).then(() => {
                const successMsg = document.getElementById('copy-success');
                successMsg.style.display = 'block';
                setTimeout(() => {
                    successMsg.style.display = 'none';
                }, 2000); // Hide message after 2 seconds
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        }
    </script>
</body>
</html>
"""

# This is the template for the generated page that embeds and plays the videos.
VIDEO_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Video Playlist</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #2c3e50;
            color: #ecf0f1;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        .video-wrapper {
            margin-bottom: 40px;
            background-color: #34495e;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        video {
            width: 100%;
            border-radius: 6px;
            display: block;
        }
        .error {
            text-align: center;
            font-size: 1.5em;
            color: #e74c3c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Video Playlist</h1>
        {% if video_urls %}
            {% for video_url in video_urls %}
                <div class="video-wrapper">
                    <video controls preload="metadata">
                        <source src="{{ video_url }}" type="video/mp4">
                        Your browser does not support the video tag. Please try a different browser.
                    </video>
                </div>
            {% endfor %}
        {% else %}
            <p class="error">😥 No videos found for this link or the link has expired.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Handles the main page.
    GET: Displays the form to submit URLs.
    POST: Processes the submitted URLs, generates a unique link, and displays it.
    """
    if request.method == 'POST':
        # Get all submitted URLs from the form, which have name="urls"
        urls = request.form.getlist('urls')
        
        # Filter out any empty strings that might be submitted
        valid_urls = [url for url in urls if url.strip()]
        
        if not valid_urls:
            # If no valid URLs were submitted, just show the page again.
            return render_template_string(HOME_PAGE_TEMPLATE)

        # Generate a short, unique ID (e.g., 'a1b2c3')
        unique_id = uuid.uuid4().hex[:6]
        
        # Store the list of URLs with the unique ID in our "database"
        url_mappings[unique_id] = valid_urls
        
        # Create the full, shareable link
        generated_link = url_for('view_videos', unique_id=unique_id, _external=True)
        
        # Render the home page again, but this time show the generated link
        return render_template_string(HOME_PAGE_TEMPLATE, generated_link=generated_link)

    # For a GET request, just show the standard home page
    return render_template_string(HOME_PAGE_TEMPLATE)

@app.route('/view/<unique_id>')
def view_videos(unique_id):
    """
    Displays the page with the embedded videos for a given unique ID.
    """
    # Look up the unique ID in our "database". If not found, it returns None.
    video_urls = url_mappings.get(unique_id)
    
    if not video_urls:
        # If the ID is invalid or doesn't exist, show a 404 Not Found error.
        abort(404)
        
    # If found, render the video player page with the list of video URLs
    return render_template_string(VIDEO_VIEW_TEMPLATE, video_urls=video_urls)

# Custom error handler for 404 Not Found
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 - Not Found</h1><p>Sorry, the page you are looking for does not exist or the link may have expired.</p>", 404

# This block allows you to run the app directly from the Python script
if __name__ == '__main__':
    app.run()
