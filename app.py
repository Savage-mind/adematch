from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_session import Session
import json
import os

app = Flask(__name__)

# Use a secret key from the environment if available; fall back to a default for
# development. In production you should always set SECRET_KEY in your
# environment variables to a strong random value.
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')

# Configure session settings to enhance security. SESSION_COOKIE_SECURE
# ensures cookies are only sent over HTTPS, SESSION_COOKIE_HTTPONLY
# prevents client-side scripts from accessing the cookie, and
# SESSION_COOKIE_SAMESITE mitigates CSRF attacks.
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialise the session system
Session(app)

try:
    # Apply security headers such as Content-Security-Policy and HSTS. This
    # requires the flask-talisman package which can be installed via pip. If
    # flask-talisman is not available, this import will fail silently and the
    # application will continue without enforcing these headers.
    from flask_talisman import Talisman
    Talisman(app, force_https=True)
except Exception:
    # If flask-talisman is not installed, skip the Talisman configuration.
    pass


def load_events():
    """
    Load events from a JSON file. Events should be stored as a list of
    dictionaries with keys: name, date, venue and artists. The artists
    key should be a list of strings representing performing artists.
    """
    events_file = os.path.join(os.path.dirname(__file__), 'events.json')
    with open(events_file) as f:
        return json.load(f)


@app.route('/')
def index():
    """Home page where users can start the login process."""
    return render_template('index.html')


@app.route('/login')
def login():
    """
    Simulated login route. In a real application this would redirect
    users to Spotify's OAuth flow. For demonstration purposes we
    simply mark the user as logged in and assign a hardcoded list
    of favourite artists to the session.
    """
    # Mark the user as logged in
    session['logged_in'] = True
    # Hard-coded favourite artists for demonstration
    session['artists'] = [
        "Martin Garrix", "Armin van Buuren", "Charlotte de Witte", "Honey Dijon"
    ]
    return redirect(url_for('swipe'))


@app.route('/swipe')
def swipe():
    """
    Page where the user can swipe through events that match their
    favourite artists. If the user isn't logged in they are redirected
    to the home page.
    """
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    all_events = load_events()
    user_artists = session.get('artists', [])
    # Filter events containing at least one of the user's favourite artists
    matching = [
        event for event in all_events
        if any(artist in event.get('artists', []) for artist in user_artists)
    ]
    # Save remaining events and reset liked events
    session['remaining_events'] = matching
    session['liked_events'] = []
    return render_template('swipe.html')


@app.route('/api/next_event')
def api_next_event():
    """
    API endpoint returning the next event the user should see. If
    there are no more events left, returns null.
    """
    events = session.get('remaining_events', [])
    if events:
        return jsonify(events[0])
    return jsonify(None)


@app.route('/api/like_event', methods=['POST'])
def api_like_event():
    """
    API endpoint for recording a liked event. The liked event is
    appended to the liked_events list in the user's session. The
    current event is removed from the remaining_events list.
    """
    data = request.get_json(force=True)
    event = data.get('event')
    liked = session.get('liked_events', [])
    if event:
        liked.append(event)
        session['liked_events'] = liked
    # Remove the first event from the remaining list
    remaining = session.get('remaining_events', [])
    if remaining:
        remaining.pop(0)
        session['remaining_events'] = remaining
    return jsonify({'status': 'ok'})


@app.route('/api/dislike_event', methods=['POST'])
def api_dislike_event():
    """
    API endpoint for skipping an event. Simply removes the current
    event from the remaining_events list.
    """
    remaining = session.get('remaining_events', [])
    if remaining:
        remaining.pop(0)
        session['remaining_events'] = remaining
    return jsonify({'status': 'ok'})


@app.route('/results')
def results():
    """
    Show the list of events that the user has marked as liked. If
    there are no liked events the page displays a suitable message.
    """
    liked = session.get('liked_events', [])
    return render_template('results.html', liked_events=liked)


@app.route('/submit_event', methods=['GET', 'POST'])
def submit_event():
    """
    Allow users to submit a new event. On POST the event is appended to
    the events.json file and the user is redirected back to the swipe
    page. On GET the submission form is rendered.
    """
    if request.method == 'POST':
        event_name = request.form['event_name']
        date = request.form['date']
        venue = request.form['venue']
        artists_str = request.form['artists']
        artists = [a.strip() for a in artists_str.split(',') if a.strip()]
        events = load_events()
        new_event = {
            "name": event_name,
            "date": date,
            "venue": venue,
            "artists": artists
        }
        events.append(new_event)
        events_file = os.path.join(os.path.dirname(__file__), 'events.json')
        with open(events_file, 'w') as f:
            json.dump(events, f, indent=2)
        return redirect(url_for('swipe'))
    return render_template('submit_event.html')


if __name__ == '__main__':
    # Running the app in production; debug is off
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
