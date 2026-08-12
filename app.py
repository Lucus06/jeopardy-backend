from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import random
import string

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# Global game state
game_state = {
    "is_locked": True,
    "is_active": False, # Tracks if the host has launched the game
    "room_code": None,  # The 5-character join code
    "winner": None,
    "max_players": 4,
    "team_counts": {}
}

@app.route('/')
def index():
    return "Jeopardy Backend is running!"

@socketio.on('setup_game')
def handle_setup(data):
    teams = data.get('teams', [])
    game_state['max_players'] = data.get('max_players', 4)
    game_state['is_active'] = True
    game_state['room_code'] = generate_code()
    # Reset team counts based on the teams the host actually created
    game_state['team_counts'] = {team: 0 for team in teams}
    
    print(f"Game launched! Code: {game_state['room_code']}")
    # Send the code back to the host to display
    emit('game_launched', {'room_code': game_state['room_code']})

@socketio.on('join_team')
def handle_join(data):
    team_name = data.get('team')
    room_code = data.get('room_code', '').upper()
    
    # 1. Check if host launched the game
    if not game_state['is_active']:
        emit('join_status', {'success': False, 'message': 'The host has not launched the game yet!'})
        return
        
    # 2. Check if the code is correct
    if room_code != game_state['room_code']:
        emit('join_status', {'success': False, 'message': 'Invalid Game Code!'})
        return

    # 3. Check if the team exists and isn't full
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
