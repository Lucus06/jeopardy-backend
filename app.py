from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

game_state = {
    "is_locked": True,
    "winner": None,
    "max_players": 4, # Default, overwritten by host
    "team_counts": {"Team A": 0, "Team B": 0, "Team C": 0, "Team D": 0}
}

@app.route('/')
def index():
    return "Jeopardy Backend is running!"

@socketio.on('setup_game')
def handle_setup(data):
    game_state['max_players'] = data.get('max_players', 4)
    # Reset team counts for a fresh game
    game_state['team_counts'] = {"Team A": 0, "Team B": 0, "Team C": 0, "Team D": 0}
    print(f"Host initialized game. Max players per team: {game_state['max_players']}")

@socketio.on('join_team')
def handle_join(data):
    team_name = data.get('team')
    
    # Check if team exists and is under capacity
    if team_name in game_state['team_counts']:
        if game_state['team_counts'][team_name] < game_state['max_players']:
            game_state['team_counts'][team_name] += 1
            emit('join_status', {'success': True, 'team': team_name})
            print(f"Player joined {team_name}. Count: {game_state['team_counts'][team_name]}")
        else:
            emit('join_status', {'success': False, 'message': 'Team is full!'})
    else:
        emit('join_status', {'success': False, 'message': 'Invalid Team'})

@socketio.on('host_unlock')
def handle_unlock():
    game_state['is_locked'] = False
    game_state['winner'] = None
    emit('buzzer_unlocked', broadcast=True)

@socketio.on('host_lock')
def handle_lock():
    game_state['is_locked'] = True
    emit('buzzer_locked', broadcast=True)

@socketio.on('player_buzz')
def handle_buzz(data):
    team_name = data.get('team')
    if not game_state['is_locked'] and game_state['winner'] is None:
        game_state['is_locked'] = True
        game_state['winner'] = team_name
        emit('buzz_winner', {'team': team_name}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
