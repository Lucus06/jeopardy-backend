from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS so GitHub Pages can talk to this Render server
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO with eventlet and allow cross-origin requests
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global game state variables
game_state = {
    "is_locked": True,  # Buzzers are locked by default
    "winner": None      # Stores the team that buzzed first
}

@app.route('/')
def index():
    return "Jeopardy Backend is running!"

# --- HOST COMMANDS ---

@socketio.on('host_unlock')
def handle_unlock():
    game_state['is_locked'] = False
    game_state['winner'] = None
    # Tell all connected players the buzzers are live
    emit('buzzer_unlocked', broadcast=True)
    print("Host unlocked the buzzers.")

@socketio.on('host_lock')
def handle_lock():
    game_state['is_locked'] = True
    emit('buzzer_locked', broadcast=True)
    print("Host locked the buzzers.")

@socketio.on('host_reset')
def handle_reset():
    game_state['is_locked'] = True
    game_state['winner'] = None
    emit('game_reset', broadcast=True)
    print("Host reset the round.")

# --- PLAYER COMMANDS ---

@socketio.on('player_buzz')
def handle_buzz(data):
    team_name = data.get('team')
    
    # Check if the buzzer is unlocked and no one has won yet
    if not game_state['is_locked'] and game_state['winner'] is None:
        # We have a winner! Lock the system immediately.
        game_state['is_locked'] = True
        game_state['winner'] = team_name
        
        # Broadcast the winner to everyone (Host and all players)
        emit('buzz_winner', {'team': team_name}, broadcast=True)
        print(f"Team {team_name} buzzed first!")

if __name__ == '__main__':
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000)
