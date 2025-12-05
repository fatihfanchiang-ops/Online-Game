import streamlit as st
import random
import pandas as pd
from datetime import datetime
import uuid
import math

# Set page config
st.set_page_config(
    page_title="3D Aeroplane Chess Simulator",
    page_icon="✈️",
    layout="wide"
)

# Game constants
BOARD_POSITIONS = {
    'start_red': 0, 'start_blue': 13, 'start_green': 26, 'start_yellow': 39,
    'home_red': 51, 'home_blue': 12, 'home_green': 25, 'home_yellow': 38,
    'finish': 52
}

PLAYER_COLORS = {
    'red': '#FF4444',
    'blue': '#3366FF',
    'green': '#00C851',
    'yellow': '#FFCC00'
}

PLAYER_NAMES = {
    'red': 'Red',
    'blue': 'Blue',
    'green': 'Green',
    'yellow': 'Yellow'
}

# Special plane types with 3D attributes
PLANE_TYPES = {
    'normal': {'name': 'Normal Plane', 'speed': 1, 'icon': '✈️', '3d_model': 'basic_jet', 'altitude': 10000},
    'jet': {'name': 'Jet Plane', 'speed': 2, 'icon': '✈️✈️', 'unlock_score': 1, '3d_model': 'supersonic_jet', 'altitude': 15000},
    'cargo': {'name': 'Cargo Plane', 'speed': 1, 'icon': '📦✈️', 'unlock_score': 2, '3d_model': 'cargo_jet', 'altitude': 8000},
    'supersonic': {'name': 'Supersonic Jet', 'speed': 3, 'icon': '🚀✈️', 'unlock_score': 3, '3d_model': 'hypersonic_jet', 'altitude': 20000}
}

# Initialize game state
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'players': {
            'red': {
                'planes': [0, 0, 0, 0],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': True, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                'flight_paths': [[], [], [], []]
            },
            'blue': {
                'planes': [13, 13, 13, 13],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                'flight_paths': [[], [], [], []]
            },
            'green': {
                'planes': [26, 26, 26, 26],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                'flight_paths': [[], [], [], []]
            },
            'yellow': {
                'planes': [39, 39, 39, 39],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                'flight_paths': [[], [], [], []]
            }
        },
        'current_player': 'red',
        'dice_roll': 0,
        'game_over': False,
        'winner': None,
        'last_move': None,
        'extra_turn': False,
        'cargo_carrying': None,
        '3d_camera': {'x': 0, 'y': -70, 'z': 20, 'rotation': 0},
        'weather_conditions': 'clear',
        'time_of_day': 'day',
        'animation_state': 'idle'
    }

# Initialize chat state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'player_nicknames' not in st.session_state:
    st.session_state.player_nicknames = {
        'red': 'Red Pilot',
        'blue': 'Blue Pilot',
        'green': 'Green Pilot',
        'yellow': 'Yellow Pilot'
    }

# Game logic functions
def roll_dice():
    return random.randint(1, 6)

def unlock_special_planes(player):
    game = st.session_state.game_state
    score = game['players'][player]['score']
    
    if score >= 1 and not game['players'][player]['special_planes_unlocked']['jet']:
        game['players'][player]['special_planes_unlocked']['jet'] = True
        add_chat_message(f"Unlocked Jet Plane! (2x speed, altitude: 15,000ft)", st.session_state.player_nicknames[player])
    
    if score >= 2 and not game['players'][player]['special_planes_unlocked']['cargo']:
        game['players'][player]['special_planes_unlocked']['cargo'] = True
        add_chat_message(f"Unlocked Cargo Plane! (Can carry other planes, altitude: 8,000ft)", st.session_state.player_nicknames[player])
    
    if score >= 3 and not game['players'][player]['special_planes_unlocked']['supersonic']:
        game['players'][player]['special_planes_unlocked']['supersonic'] = True
        add_chat_message(f"Unlocked Supersonic Jet! (3x speed, altitude: 20,000ft)", st.session_state.player_nicknames[player])

def convert_plane(player, plane_idx, new_type):
    game = st.session_state.game_state
    
    if plane_idx < 0 or plane_idx >= 4:
        return False
    
    if (game['players'][player]['plane_types'][plane_idx] == 'normal' and
        game['players'][player]['special_planes_unlocked'].get(new_type, False) and
        game['players'][player]['planes'][plane_idx] != BOARD_POSITIONS['finish']):
        
        game['players'][player]['plane_types'][plane_idx] = new_type
        altitude = PLANE_TYPES[new_type]['altitude']
        add_chat_message(f"Converted plane {plane_idx+1} to {PLANE_TYPES[new_type]['name']} (Altitude: {altitude}ft)", 
                       st.session_state.player_nicknames[player])
        return True
    return False

def move_plane(player, plane_idx, steps):
    game = st.session_state.game_state
    
    if plane_idx < 0 or plane_idx >= 4:
        return False
    
    current_pos = game['players'][player]['planes'][plane_idx]
    plane_type = game['players'][player]['plane_types'][plane_idx]
    
    if current_pos == BOARD_POSITIONS['finish']:
        return False
    
    start_pos = BOARD_POSITIONS[f'start_{player}']
    
    if current_pos == start_pos and steps != 6:
        return False
    
    speed_multiplier = PLANE_TYPES[plane_type]['speed']
    actual_steps = steps * speed_multiplier
    
    if current_pos == start_pos and steps == 6:
        new_pos = start_pos + 1
    else:
        new_pos = current_pos + actual_steps
    
    # Record flight path for animation
    game['players'][player]['flight_paths'][plane_idx].append({
        'from': current_pos,
        'to': new_pos,
        'timestamp': datetime.now(),
        'speed': actual_steps * 100,
        'altitude': PLANE_TYPES[plane_type]['altitude']
    })
    
    game['animation_state'] = 'flying'
    
    carried_planes_info = ""
    if plane_type == 'cargo' and game['cargo_carrying'] is None:
        carried_planes = []
        for i, pos in enumerate(game['players'][player]['planes']):
            if (i != plane_idx and 
                pos == current_pos and 
                pos != start_pos and 
                pos != BOARD_POSITIONS['finish']):
                carried_planes.append(i)
        
        if carried_planes:
            game['cargo_carrying'] = (plane_idx, carried_planes)
            carried_planes_info = f" (Carrying planes {[p+1 for p in carried_planes]})"
            add_chat_message(f"Cargo plane carrying planes {[p+1 for p in carried_planes]}", 
                           st.session_state.player_nicknames[player])
    
    finish_pos = BOARD_POSITIONS['finish']
    plane_model = PLANE_TYPES[plane_type]['3d_model']
    move_description = f"{PLANE_TYPES[plane_type]['icon']} {PLAYER_NAMES[player]} {PLANE_TYPES[plane_type]['name']} (3D: {plane_model}) {plane_idx+1}"
    
    if new_pos >= finish_pos:
        new_pos = finish_pos
        game['players'][player]['score'] += 1
        altitude = PLANE_TYPES[plane_type]['altitude']
        game['last_move'] = f"{move_description} reached finish! (Moved {actual_steps} steps at {altitude}ft with {speed_multiplier}x speed){carried_planes_info}"
        
        unlock_special_planes(player)
        
        if game['players'][player]['score'] == 4:
            game['game_over'] = True
            game['winner'] = player
            game['animation_state'] = 'landed'
            add_chat_message(f"Game Over! {st.session_state.player_nicknames[player]} ({PLAYER_NAMES[player]}) wins! All planes landed safely at destination!", "System")
    else:
        altitude = PLANE_TYPES[plane_type]['altitude']
        game['last_move'] = f"{move_description} flew from {current_pos} to {new_pos} (Rolled {steps}, speed: {actual_steps*100} km/h at {altitude}ft with {speed_multiplier}x speed){carried_planes_info}"
        
        if game['cargo_carrying'] and game['cargo_carrying'][0] == plane_idx:
            for carried_idx in game['cargo_carrying'][1]:
                if game['players'][player]['planes'][carried_idx] != BOARD_POSITIONS['finish']:
                    game['players'][player]['planes'][carried_idx] = new_pos
                    game['players'][player]['flight_paths'][carried_idx].append({
                        'from': current_pos,
                        'to': new_pos,
                        'timestamp': datetime.now(),
                        'speed': actual_steps * 100,
                        'altitude': PLANE_TYPES['cargo']['altitude'],
                        'carried': True
                    })
            game['cargo_carrying'] = None
    
    game['players'][player]['planes'][plane_idx] = new_pos
    return True

def switch_turn():
    game = st.session_state.game_state
    
    game['cargo_carrying'] = None
    game['animation_state'] = 'idle'
    
    if game['dice_roll'] == 6 and not game['game_over']:
        game['extra_turn'] = True
        game['last_move'] += " (Extra flight segment granted for perfect roll!)"
        game['dice_roll'] = 0
        return
    
    game['extra_turn'] = False
    players = ['red', 'blue', 'green', 'yellow']
    current_idx = players.index(game['current_player'])
    next_idx = (current_idx + 1) % 4
    
    for p in players:
        game['players'][p]['turn'] = False
    
    game['current_player'] = players[next_idx]
    game['players'][game['current_player']]['turn'] = True
    game['dice_roll'] = 0
    
    add_chat_message(f"Flight control: Now passing to {st.session_state.player_nicknames[game['current_player']]} ({PLAYER_NAMES[game['current_player']]} squadron)", "System")

def add_chat_message(message, sender, is_system=False):
    if not message or not sender:
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    message_id = str(uuid.uuid4())
    
    st.session_state.chat_messages.append({
        'id': message_id,
        'text': message,
        'sender': sender,
        'timestamp': timestamp,
        'is_system': is_system
    })
    
    if len(st.session_state.chat_messages) > 50:
        st.session_state.chat_messages = st.session_state.chat_messages[-50:]

def lighten_color(color, factor=0.3):
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

# Main HTML 3D Canvas
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<style>
/* 3D Scene Styles */
#scene-container {
    position: relative;
    width: 100%;
    height: 500px;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

/* 3D Aircraft Animation */
.aircraft {
    transition: all 1.5s ease-in-out;
    transform-origin: center;
}

.aircraft-flying {
    animation: flyPath 2s ease-in-out;
}

@keyframes flyPath {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.05) rotate(5deg); opacity: 0.9; }
    100% { transform: scale(1); opacity: 1; }
}

/* Cockpit Instrument Panel */
.instrument-panel {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin: 20px 0;
}

.instrument {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border-radius: 10px;
    padding: 15px;
    color: #00ff00;
    text-align: center;
    border: 2px solid #333;
    box-shadow: inset 0 0 10px rgba(0,255,0,0.3);
}

/* Weather Effects */
.weather-clear { background: linear-gradient(135deg, #87CEEB 0%, #B0E0E6 100%); }
.weather-cloudy { background: linear-gradient(135deg, #B0C4DE 0%, #778899 100%); }
.weather-rainy { background: linear-gradient(135deg, #4682B4 0%, #5F9EA0 100%); }
.weather-foggy { background: linear-gradient(135deg, #D3D3D3 0%, #F5F5F5 100%); }

/* Time of Day Themes */
.time-day { filter: brightness(1); }
.time-dusk { filter: sepia(0.5) brightness(0.8); }
.time-night { filter: brightness(0.4) hue-rotate(200deg); }

/* Chat Messages */
.chat-message {
    margin: 8px 0;
    padding: 10px 15px;
    border-radius: 10px;
    border-left: 4px solid #007bff;
    background: #f8f9fa;
}

.chat-system {
    background: #e9ecef;
    border-left: 4px solid #6c757d;
    font-style: italic;
}

/* 3D Button Styles */
.btn-3d {
    position: relative;
    display: inline-block;
    padding: 10px 20px;
    margin: 5px;
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 5px 0 #004085;
    transition: all 0.2s ease;
}

.btn-3d:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 0 #004085;
}

.btn-3d:active {
    transform: translateY(3px);
    box-shadow: 0 2px 0 #004085;
}

/* Flight Path Visualization */
.flight-path {
    position: absolute;
    width: 400px;
    height: 400px;
    border: 2px dashed #00ff00;
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.flight-marker {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transform: translate(-50%, -50%);
}

.aircraft-marker {
    position: absolute;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 12px;
    transform: translate(-50%, -50%);
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    transition: all 1s ease;
}

/* Animation Keyframes */
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); }
}

.pulse {
    animation: pulse 1.5s infinite;
}

/* Dashboard Styles */
.dashboard {
    background: linear-gradient(135deg, #1a2a6c 0%, #2c3e50 100%);
    border-radius: 20px;
    padding: 20px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# Main UI
st.title("✈️ 3D Aeroplane Chess Simulator")
st.subheader("Immersive 3D Flight Chess with Realistic Aircraft Simulation")

# Main layout
main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    # 3D Scene Container with HTML Canvas
    game = st.session_state.game_state
    current_player = game['current_player']
    current_color = PLAYER_COLORS[current_player]
    current_nickname = st.session_state.player_nicknames[current_player]
    
    # Generate 3D scene HTML
    scene_html = f"""
    <div class="dashboard">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: {current_color};">{current_nickname}'s Cockpit</h3>
                <p style="margin: 5px 0; opacity: 0.8;">{PLAYER_NAMES[current_player]} Squadron | Flight Control</p>
            </div>
            <div style="background: rgba(0,0,0,0.3); padding: 10px 15px; border-radius: 10px;">
                <span style="font-size: 24px; font-weight: bold;">{game['time_of_day'].upper()}</span>
                <span style="margin-left: 15px; background: {get_weather_color(game['weather_conditions'])}; 
                          padding: 5px 10px; border-radius: 5px; font-size: 12px;">
                    {game['weather_conditions'].upper()}
                </span>
            </div>
        </div>
        
        <div class="instrument-panel">
            <!-- Altimeter -->
            <div class="instrument">
                <div style="font-size: 12px; opacity: 0.7;">ALTITUDE</div>
                <div style="font-size: 28px; font-weight: bold;">{get_current_altitude()} FT</div>
            </div>
            
            <!-- Airspeed -->
            <div class="instrument">
                <div style="font-size: 12px; opacity: 0.7;">AIRSPEED</div>
                <div style="font-size: 28px; font-weight: bold;">{get_current_airspeed()} KM/H</div>
            </div>
            
            <!-- Position -->
            <div class="instrument">
                <div style="font-size: 12px; opacity: 0.7;">FLIGHT POSITION</div>
                <div style="font-size: 28px; font-weight: bold;">{get_average_position()}</div>
            </div>
            
            <!-- Status -->
            <div class="instrument">
                <div style="font-size: 12px; opacity: 0.7;">FLIGHT STATUS</div>
                <div style="font-size: 28px; font-weight: bold;">{get_flight_status()}</div>
            </div>
        </div>
    </div>
    
    <!-- 3D Flight Scene -->
    <div id="scene-container" class="weather-{game['weather_conditions']} time-{game['time_of_day']}">
        <!-- Flight Path Circle -->
        <div class="flight-path"></div>
        
        <!-- Flight Markers -->
        {render_flight_markers_html()}
        
        <!-- Aircraft Positions -->
        {render_aircraft_positions_html()}
        
        <!-- Finish Line -->
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 420px; height: 420px;">
            <div style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%);
                       background: #FFC107; color: black; padding: 5px 15px; border-radius: 20px;
                       font-weight: bold;">FINISH ZONE</div>
        </div>
        
        <!-- Camera Controls Overlay -->
        <div style="position: absolute; bottom: 20px; right: 20px; 
                   background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 10px;">
            <div style="font-size: 12px;">3D View: X={game['3d_camera']['x']:.1f}, Y={game['3d_camera']['y']:.1f}, Z={game['3d_camera']['z']:.1f}</div>
            <div style="font-size: 12px;">Rotation: {game['3d_camera']['rotation']}°</div>
        </div>
    </div>
    
    <!-- 3D Camera Controls -->
    <div style="margin: 20px 0;">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div>
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">Camera Rotation</label>
                <input type="range" min="0" max="360" value="{game['3d_camera']['rotation']}" 
                       oninput="document.getElementById('rot-value').textContent = this.value">
                <span id="rot-value">{game['3d_camera']['rotation']}</span>°
            </div>
            <div>
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">Camera Height</label>
                <input type="range" min="0" max="50" value="{game['3d_camera']['z']}"
                       oninput="document.getElementById('height-value').textContent = this.value">
                <span id="height-value">{game['3d_camera']['z']}</span> units
            </div>
            <div>
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">Weather Conditions</label>
                <select id="weather-select" onchange="updateWeather(this.value)">
                    <option value="clear" {'selected' if game['weather_conditions'] == 'clear' else ''}>Clear Sky</option>
                    <option value="cloudy" {'selected' if game['weather_conditions'] == 'cloudy' else ''}>Cloudy</option>
                    <option value="rainy" {'selected' if game['weather_conditions'] == 'rainy' else ''}>Rainy</option>
                    <option value="foggy" {'selected' if game['weather_conditions'] == 'foggy' else ''}>Foggy</option>
                </select>
            </div>
            <div>
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">Time of Day</label>
                <select id="time-select" onchange="updateTime(this.value)">
                    <option value="day" {'selected' if game['time_of_day'] == 'day' else ''}>Day</option>
                    <option value="dusk" {'selected' if game['time_of_day'] == 'dusk' else ''}>Dusk</option>
                    <option value="night" {'selected' if game['time_of_day'] == 'night' else ''}>Night</option>
                </select>
            </div>
        </div>
    </div>
    """
    
    st.markdown(scene_html, unsafe_allow_html=True)
    
    # Game Status
    st.markdown("---")
    st.subheader("Flight Control Status")
    
    # Status badges
    status_badges = []
    if game['extra_turn']:
        status_badges.append("🏅 Extra Flight Segment")
    if game['cargo_carrying']:
        status_badges.append("📦 Carrying Aircraft")
    if game['game_over']:
        status_badges.append("🎮 Mission Complete")
    
    status_text = " | ".join(status_badges) if status_badges else "In Flight"
    
    st.markdown(f"""
    <div style="padding: 15px; background: linear-gradient(135deg, {current_color} 0%, {lighten_color(current_color)} 100%); 
               color: white; border-radius: 12px; font-size: 18px; font-weight: bold; margin-bottom: 15px;
               box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        {current_nickname} ({PLAYER_NAMES[game['current_player']].upper()} SQUADRON)
        <span style="font-size: 12px; font-weight: normal; margin-left: 10px;">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Dice Roll and Last Move
    col_dice, col_last_move = st.columns(2)
    
    with col_dice:
        if game['dice_roll'] > 0:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f2f6 0%, #e8f4f8 100%); 
                       border-radius: 15px; padding: 25px; text-align: center;
                       box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 70px; line-height: 1; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);">🎲</div>
                <div style="font-size: 40px; font-weight: bold; color: #262730; margin: 10px 0;">{game['dice_roll']}</div>
                <div style="font-size: 14px; color: #666; text-transform: uppercase;">Flight Distance</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f0f2f6 0%, #e8f4f8 100%); 
                       border-radius: 15px; padding: 25px; text-align: center;
                       box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 50px; line-height: 1; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);">🎲</div>
                <div style="font-size: 18px; color: #666; margin-top: 15px;">Click to set flight path!</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_last_move:
        if game['last_move']:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e8f4f8 0%, #f0f8fb 100%); 
                       border-radius: 15px; padding: 20px; height: 100%;
                       box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; color: #2d3748; font-weight: bold; margin-bottom: 8px;">
                    Last Flight Operation
                </div>
                <div style="font-size: 13px; color: #4a5568; font-style: italic; line-height: 1.4;">
                    {game['last_move']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f5f5f5 0%, #f8f8f8 100%); 
                       border-radius: 15px; padding: 20px; height: 100%;
                       box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="font-size: 15px; color: #718096; text-align: center; line-height: 1.5;">
                    No flight operations yet<br>Roll the dice to begin your mission!
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Flight Dashboard
    st.subheader("Flight Operations Dashboard")
    
    # Create flight data
    score_data = []
    for color in ['red', 'blue', 'green', 'yellow']:
        unlocked = []
        if game['players'][color]['special_planes_unlocked']['jet']:
            unlocked.append("✈️✈️ Jet (15,000ft)")
        if game['players'][color]['special_planes_unlocked']['cargo']:
            unlocked.append("📦✈️ Cargo (8,000ft)")
        if game['players'][color]['special_planes_unlocked']['supersonic']:
            unlocked.append("🚀✈️ Supersonic (20,000ft)")
        
        total_distance = sum(game['players'][color]['planes'])
        avg_altitude = sum(PLANE_TYPES[pt]['altitude'] for pt in game['players'][color]['plane_types']) // 4
        
        status = "🏆 Mission Complete!" if game['winner'] == color else "🟢 In Flight" if not game['game_over'] else "🔴 Mission Failed"
        
        score_data.append({
            'Pilot': f"<span style='color: {PLAYER_COLORS[color]}; font-weight: bold;'>{st.session_state.player_nicknames[color]}</span>",
            'Squadron': f"<span style='color: {PLAYER_COLORS[color]};'>{PLAYER_NAMES[color]}</span>",
            'Aircraft Landed': game['players'][color]['score'],
            'Total Flight Distance': total_distance,
            'Avg Altitude (ft)': avg_altitude,
            'Unlocked Aircraft': ', '.join(unlocked) if unlocked else 'None',
            'Status': status
        })
    
    st.markdown(pd.DataFrame(score_data).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Game Controls
    st.markdown("---")
    st.subheader("🎮 Flight Controls")
    
    if game['game_over']:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                   padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0;
                   border: 3px solid #28a745; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <h2 style="color: #155724; margin-bottom: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">🎉 MISSION COMPLETE 🎉</h2>
            <h3 style="color: #155724; font-size: 24px;">{st.session_state.player_nicknames[game['winner']]} ({PLAYER_NAMES[game['winner']]} SQUADRON) WINS!</h3>
            <p style="font-size: 18px; color: #2d3748; margin-top: 20px; line-height: 1.6;">
                All 4 aircraft have successfully landed at the destination airport!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Start New Mission", type="primary", use_container_width=True):
            # Reset game state
            st.session_state.game_state = {
                'players': {
                    'red': {
                        'planes': [0, 0, 0, 0],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': True, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                        'flight_paths': [[], [], [], []]
                    },
                    'blue': {
                        'planes': [13, 13, 13, 13],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                        'flight_paths': [[], [], [], []]
                    },
                    'green': {
                        'planes': [26, 26, 26, 26],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                        'flight_paths': [[], [], [], []]
                    },
                    'yellow': {
                        'planes': [39, 39, 39, 39],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False},
                        'flight_paths': [[], [], [], []]
                    }
                },
                'current_player': 'red',
                'dice_roll': 0,
                'game_over': False,
                'winner': None,
                'last_move': None,
                'extra_turn': False,
                'cargo_carrying': None,
                '3d_camera': {'x': 0, 'y': -70, 'z': 20, 'rotation': 0},
                'weather_conditions': 'clear',
                'time_of_day': 'day',
                'animation_state': 'idle'
            }
            add_chat_message("A new flight mission has begun! All aircraft ready for takeoff.", "System", is_system=True)
            st.rerun()
    else:
        # Game controls
        control_cols = st.columns(2)
        
        with control_cols[0]:
            if st.button("🎲 Set Flight Path (Roll Dice)", type="primary", 
                       disabled=game['dice_roll'] > 0, use_container_width=True):
                game['dice_roll'] = roll_dice()
                game['last_move'] = f"{current_nickname} set flight path with distance {game['dice_roll']}"
                add_chat_message(f"Set flight path distance: {game['dice_roll']} units", current_nickname)
                st.rerun()
        
        with control_cols[1]:
            reset_confirm = st.checkbox("Confirm Mission Reset", key="reset_check")
            if st.button("🔄 Reset Mission", type="secondary", 
                       disabled=not reset_confirm, use_container_width=True):
                # Reset game state
                st.session_state.game_state = {
                    'players': {
                        'red': {'planes': [0,0,0,0], 'plane_types': ['normal']*4, 'turn': True, 'score':0, 'special_planes_unlocked':{'jet':False,'cargo':False,'supersonic':False}, 'flight_paths':[[],[],[],[]]},
                        'blue': {'planes': [13,13,13,13], 'plane_types': ['normal']*4, 'turn': False, 'score':0, 'special_planes_unlocked':{'jet':False,'cargo':False,'supersonic':False}, 'flight_paths':[[],[],[],[]]},
                        'green': {'planes': [26,26,26,26], 'plane_types': ['normal']*4, 'turn': False, 'score':0, 'special_planes_unlocked':{'jet':False,'cargo':False,'supersonic':False}, 'flight_paths':[[],[],[],[]]},
                        'yellow': {'planes': [39,39,39,39], 'plane_types': ['normal']*4, 'turn': False, 'score':0, 'special_planes_unlocked':{'jet':False,'cargo':False,'supersonic':False}, 'flight_paths':[[],[],[],[]]}
                    },
                    'current_player': 'red',
                    'dice_roll': 0,
                    'game_over': False,
                    'winner': None,
                    'last_move': "Mission reset - all aircraft returned to base",
                    'extra_turn': False,
                    'cargo_carrying': None,
                    '3d_camera': {'x': 0, 'y': -70, 'z': 20, 'rotation': 0},
                    'weather_conditions': 'clear',
                    'time_of_day': 'day',
                    'animation_state': 'idle'
                }
                add_chat_message("Mission reset - all aircraft returned to base!", "System", is_system=True)
                st.rerun()
        
        # Aircraft upgrade section
        if game['players'][current_player]['score'] >= 1:
            st.markdown("---")
            st.subheader("✈️ Upgrade Aircraft Type")
            
            normal_planes = []
            for i in range(4):
                if (game['players'][current_player]['plane_types'][i] == 'normal' and 
                    game['players'][current_player]['planes'][i] != BOARD_POSITIONS['finish']):
                    normal_planes.append(i)
            
            if normal_planes:
                convert_cols = st.columns([3, 2, 1])
                
                with convert_cols[0]:
                    plane_options = []
                    for i in normal_planes:
                        pos = game['players'][current_player]['planes'][i]
                        altitude = PLANE_TYPES['normal']['altitude']
                        plane_options.append(f"Aircraft {i+1} - Position: {pos}, Altitude: {altitude}ft")
                    
                    selected_plane = st.selectbox(
                        "Select aircraft to upgrade:",
                        options=plane_options,
                        key="convert_plane_select"
                    )
                
                with convert_cols[1]:
                    available_types = []
                    if game['players'][current_player]['special_planes_unlocked']['jet']:
                        available_types.append('jet')
                    if game['players'][current_player]['special_planes_unlocked']['cargo']:
                        available_types.append('cargo')
                    if game['players'][current_player]['special_planes_unlocked']['supersonic']:
                        available_types.append('supersonic')
                    
                    if available_types:
                        type_options = [f"{PLANE_TYPES[t]['icon']} {PLANE_TYPES[t]['name']} ({PLANE_TYPES[t]['altitude']}ft)" for t in available_types]
                        selected_type = st.selectbox(
                            "Upgrade to:",
                            options=type_options,
                            key="new_plane_type"
                        )
                    else:
                        st.selectbox("Upgrade to:", options=["No aircraft unlocked yet"], disabled=True, key="no_type")
                        selected_type = None
                
                with convert_cols[2]:
                    convert_btn_disabled = (not selected_plane or not selected_type)
                    if st.button("🔄 Upgrade", type="secondary", 
                               disabled=convert_btn_disabled, use_container_width=True):
                        plane_idx = int(selected_plane.split()[1]) - 1
                        
                        type_key = None
                        if selected_type:
                            if "Jet Plane" in selected_type:
                                type_key = 'jet'
                            elif "Cargo Plane" in selected_type:
                                type_key = 'cargo'
                            elif "Supersonic Jet" in selected_type:
                                type_key = 'supersonic'
                        
                        if type_key and convert_plane(current_player, plane_idx, type_key):
                            st.success(f"✅ Upgraded to {PLANE_TYPES[type_key]['name']}! Altitude: {PLANE_TYPES[type_key]['altitude']}ft")
                            st.rerun()
                        else:
                            st.error("❌ Could not upgrade aircraft!")
            else:
                st.info("ℹ️ No standard aircraft available for upgrade (all are special aircraft or have landed)")
        
        # Plane selection
        if game['dice_roll'] > 0:
            st.markdown("---")
            st.subheader(f"✈️ Execute Flight Plan - {current_nickname}")
            
            planes = game['players'][current_player]['planes']
            plane_types = game['players'][current_player]['plane_types']
            
            plane_cols = st.columns(2)
            
            for i, (pos, ptype) in enumerate(zip(planes, plane_types)):
                with plane_cols[i % 2]:
                    plane_icon = PLANE_TYPES[ptype]['icon']
                    speed_multiplier = PLANE_TYPES[ptype]['speed']
                    actual_steps = game['dice_roll'] * speed_multiplier
                    altitude = PLANE_TYPES[ptype]['altitude']
                    airspeed = actual_steps * 100
                    
                    if pos == BOARD_POSITIONS['finish']:
                        plane_status = f"{plane_icon} Aircraft {i+1}: ✅ Landed at Destination"
                        disabled = True
                    elif pos == BOARD_POSITIONS[f'start_{current_player}'] and game['dice_roll'] != 6:
                        plane_status = f"{plane_icon} Aircraft {i+1}: 📍 At Base (Need 6 for takeoff)"
                        disabled = True
                    else:
                        new_pos = pos + actual_steps if pos != BOARD_POSITIONS[f'start_{current_player}'] else pos + 1
                        finish_note = " (Final Approach!)" if new_pos >= BOARD_POSITIONS['finish'] else ""
                        plane_status = f"{plane_icon} Aircraft {i+1}: {pos} → {new_pos} (Speed: {airspeed} km/h, Altitude: {altitude}ft){finish_note}"
                        disabled = False
                    
                    if st.button(plane_status, key=f"plane_{i}", disabled=disabled, use_container_width=True):
                        move_success = move_plane(current_player, i, game['dice_roll'])
                        
                        if move_success:
                            add_chat_message(
                                f"Executed flight plan for {PLANE_TYPES[ptype]['name']} {i+1} (speed: {airspeed} km/h, altitude: {altitude}ft)", 
                                current_nickname
                            )
                            switch_turn()
                        else:
                            st.error("❌ Flight plan execution failed!")
                            add_chat_message(
                                f"Flight plan failed for {PLANE_TYPES[ptype]['name']} {i+1}", 
                                current_nickname
                            )
                        
                        st.rerun()
            
            if not game['extra_turn']:
                if st.button("➡️ Transfer Flight Control", key="pass_turn", 
                           use_container_width=True, type="secondary"):
                    game['last_move'] = f"{current_nickname} transferred flight control to next squadron"
                    add_chat_message("Transferred flight control to next squadron", current_nickname)
                    switch_turn()
                    st.rerun()

with main_col2:
    # Chat and Settings Tabs
    tab1, tab2, tab3 = st.tabs(["💬 Flight Communications", "👨‍✈️ Pilot Settings", "✈️ Aircraft Info"])
    
    with tab1:
        st.subheader("Flight Communication System")
        
        # Chat Container
        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.chat_messages:
                st.markdown("""
                <div style="height: 100%; display: flex; align-items: center; justify-content: center;
                           color: #6c757d; font-style: italic; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                           border-radius: 10px; padding: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 40px; margin-bottom: 15px;">📡</div>
                        <div>Flight communication channel open</div>
                        <div style="font-size: 12px; margin-top: 5px;">Send your first transmission!</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_messages:
                    if msg['is_system']:
                        st.markdown(f"""
                        <div class="chat-message chat-system">
                            <small>[{msg['timestamp']}] <strong style="color: #0288D1;">ATC Control:</strong> {msg['text']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        player_color = "#6c757d"
                        for color, nickname in st.session_state.player_nicknames.items():
                            if nickname == msg['sender']:
                                player_color = PLAYER_COLORS[color]
                                break
                        
                        st.markdown(f"""
                        <div class="chat-message" style="border-left-color: {player_color};">
                            <small>[{msg['timestamp']}] <strong style="color: {player_color};">{msg['sender']}:</strong> {msg['text']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Chat Input
        st.markdown("---")
        st.subheader("Transmit Message")
        
        selected_player = st.selectbox(
            "Transmit as:",
            options=list(st.session_state.player_nicknames.values()),
            index=list(st.session_state.player_nicknames.keys()).index(st.session_state.game_state['current_player'])
        )
        
        with st.form(key='chat_form', clear_on_submit=True):
            msg_text = st.text_input("Enter transmission...", key="chat_input", 
                                   placeholder="Flight status update, coordinates, or communication...")
            submit_btn = st.form_submit_button("📤 Send Transmission", type="primary", use_container_width=True)
            
            if submit_btn and msg_text.strip():
                add_chat_message(msg_text.strip(), selected_player)
        
        if st.button("🗑️ Clear Communication Log", type="secondary", use_container_width=True):
            if st.checkbox("Confirm clear communication log?"):
                st.session_state.chat_messages = []
                st.rerun()
    
    with tab2:
        st.subheader("Pilot Identification")
        
        st.markdown("### Customize Pilot Call Signs")
        
        for color in ['red', 'blue', 'green', 'yellow']:
            col_color, col_input = st.columns([1, 4])
            with col_color:
                st.markdown(f"""
                <div style="width: 40px; height: 40px; background: linear-gradient(135deg, {PLAYER_COLORS[color]} 0%, {lighten_color(PLAYER_COLORS[color])} 100%); 
                           border-radius: 50%; margin: 8px auto; display: flex; align-items: center; justify-content: center;
                           box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                    <span style="color: white; font-weight: bold;">{PLAYER_NAMES[color][0]}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_input:
                new_nickname = st.text_input(
                    f"{PLAYER_NAMES[color]} Squadron Pilot",
                    value=st.session_state.player_nicknames[color],
                    key=f"nickname_{color}"
                )
                if new_nickname and new_nickname != st.session_state.player_nicknames[color]:
                    old_name = st.session_state.player_nicknames[color]
                    st.session_state.player_nicknames[color] = new_nickname
                    add_chat_message(f"Pilot call sign changed: {old_name} → {new_nickname}", "ATC Control", is_system=True)
        
        st.markdown("---")
        st.subheader("Flight Data Management")
        
        if st.button("📥 Export Flight Logs", use_container_width=True):
            if st.session_state.chat_messages:
                flight_log = f"3D Aeroplane Chess Flight Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                flight_log += "="*60 + "\n\n"
                
                game = st.session_state.game_state
                flight_log += "CURRENT MISSION STATUS:\n"
                flight_log += f"Current Pilot: {st.session_state.player_nicknames[game['current_player']]}\n"
                flight_log += f"Weather: {game['weather_conditions'].title()}\n"
                flight_log += f"Time of Day: {game['time_of_day'].title()}\n"
                flight_log += f"Game Over: {game['game_over']}\n"
                if game['winner']:
                    flight_log += f"Winner: {st.session_state.player_nicknames[game['winner']]}\n"
                flight_log += "\n"
                
                flight_log += "AIRCRAFT POSITIONS:\n"
                for color in ['red', 'blue', 'green', 'yellow']:
                    flight_log += f"{PLAYER_NAMES[color]} Squadron: {st.session_state.player_nicknames[color]}\n"
                    flight_log += f"  Planes in Finish: {game['players'][color]['score']}\n"
                    flight_log += f"  Positions: {game['players'][color]['planes']}\n"
                    flight_log += f"  Aircraft Types: {game['players'][color]['plane_types']}\n\n"
                
                flight_log += "COMMUNICATION LOG:\n"
                for msg in st.session_state.chat_messages:
                    flight_log += f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}\n"
                
                st.download_button(
                    label="Download Complete Flight Log",
                    data=flight_log,
                    file_name=f"aeroplane_chess_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("No flight logs to export!")
        
        st.markdown("---")
        st.subheader("Mission Control Reset")
        
        if st.button("🔄 Reset All Mission Settings", type="secondary", use_container_width=True):
            if st.checkbox("Reset pilot call signs and communication logs?"):
                st.session_state.player_nicknames = {
                    'red': 'Red Pilot',
                    'blue': 'Blue Pilot',
                    'green': 'Green Pilot',
                    'yellow': 'Yellow Pilot'
                }
                st.session_state.chat_messages = []
                add_chat_message("All mission settings reset to default", "ATC Control", is_system=True)
                st.rerun()
    
    with tab3:
        st.subheader("✈️ Aircraft Specifications")
        
        aircraft_specs = {
            'Aircraft Type': ['✈️ Standard Jet', '✈️✈️ High-Speed Jet', '📦✈️ Cargo Aircraft', '🚀✈️ Supersonic Jet'],
            'Max Speed': ['1× dice roll', '2× dice roll', '1× dice roll', '3× dice roll'],
            'Cruise Altitude': ['10,000 ft', '15,000 ft', '8,000 ft', '20,000 ft'],
            '3D Model': ['Basic Commercial Jet', 'Military Supersonic Jet', 'Heavy Cargo Transport', 'Hypersonic Experimental Jet'],
            'Special Ability': [
                'Standard flight characteristics',
                'Double speed, increased maneuverability',
                'Can carry other aircraft at same position',
                'Triple speed, maximum altitude capability'
            ],
            'Unlock Requirement': [
                'Available at mission start',
                '1 aircraft successfully landed',
                '2 aircraft successfully landed',
                '3 aircraft successfully landed'
            ]
        }
        
        st.dataframe(pd.DataFrame(aircraft_specs), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🎯 3D Flight Strategy Tips")
        
        flight_tips = [
            "🔹 Unlock High-Speed Jet first for rapid transit across the flight map",
            "🔹 Adjust camera angle (0-360°) to get better visibility of all aircraft positions",
            "🔹 Use Cargo Aircraft to move multiple aircraft together and conserve fuel",
            "🔹 Supersonic Jet is ideal for final approach to the destination airport",
            "🔹 Changing weather conditions affect visibility - adjust your strategy accordingly",
            "🔹 Higher altitude aircraft (Supersonic Jet) have priority in flight path selection",
            "🔹 Time of day affects navigation - night flights require more careful planning",
            "🔹 Extra flight segments (rolling 6) can be used to gain strategic advantage"
        ]
        
        for tip in flight_tips:
            st.markdown(f"""
            <div style='padding: 12px; margin: 6px 0; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 100%); 
                       border-radius: 8px; border-left: 3px solid #4FC3F7;'>
                {tip}
            </div>
            """, unsafe_allow_html=True)

# Helper functions for HTML rendering
def get_weather_color(weather):
    colors = {
        'clear': '#4FC3F7',
        'cloudy': '#90A4AE',
        'rainy': '#5C6BC0',
        'foggy': '#B0BEC5'
    }
    return colors.get(weather, '#4FC3F7')

def get_current_altitude():
    game = st.session_state.game_state
    current_player = game['current_player']
    total_altitude = 0
    plane_count = 0
    
    for i, plane_type in enumerate(game['players'][current_player]['plane_types']):
        if game['players'][current_player]['planes'][i] != BOARD_POSITIONS['finish']:
            total_altitude += PLANE_TYPES[plane_type]['altitude']
            plane_count += 1
    
    return total_altitude // plane_count if plane_count > 0 else 10000

def get_current_airspeed():
    game = st.session_state.game_state
    if game['dice_roll'] > 0:
        return game['dice_roll'] * 100
    return 0

def get_average_position():
    game = st.session_state.game_state
    current_player = game['current_player']
    total_pos = 0
    plane_count = 0
    
    for pos in game['players'][current_player]['planes']:
        if pos != BOARD_POSITIONS['finish']:
            total_pos += pos
            plane_count += 1
    
    return total_pos // plane_count if plane_count > 0 else 0

def get_flight_status():
    game = st.session_state.game_state
    if game['game_over']:
        return "LANDED"
    elif game['extra_turn']:
        return "EXTRA FLIGHT"
    elif game['dice_roll'] > 0:
        return "READY"
    else:
        return "STANDBY"

def render_flight_markers_html():
    markers = []
    for i in range(0, 52, 4):
        angle = (i / 52) * 360
        x = 200 + 180 * math.cos(math.radians(angle))
        y = 200 + 180 * math.sin(math.radians(angle))
        
        color = "#90CAF9"
        if i == BOARD_POSITIONS['start_red']: color = "#FF4444"
        elif i == BOARD_POSITIONS['start_blue']: color = "#3366FF"
        elif i == BOARD_POSITIONS['start_green']: color = "#00C851"
        elif i == BOARD_POSITIONS['start_yellow']: color = "#FFCC00"
        
        markers.append(f"""
        <div class="flight-marker" style="left: {x}px; top: {y}px; background-color: {color};">
            <div style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%);
                       font-size: 10px; font-weight: bold; color: white; text-shadow: 1px 1px 2px black;">
                {i}
            </div>
        </div>
        """)
    
    return "\n".join(markers)

def render_aircraft_positions_html():
    game = st.session_state.game_state
    aircraft_html = []
    
    for color, player_data in game['players'].items():
        for plane_idx, pos in enumerate(player_data['planes']):
            if pos == BOARD_POSITIONS['finish']:
                angle = plane_idx * 90
                x = 200 + 200 * math.cos(math.radians(angle))
                y = 200 + 200 * math.sin(math.radians(angle))
            else:
                angle = (pos / 52) * 360
                x = 200 + 180 * math.cos(math.radians(angle))
                y = 200 + 180 * math.sin(math.radians(angle))
            
            plane_type = player_data['plane_types'][plane_idx]
            plane_icon = PLANE_TYPES[plane_type]['icon']
            plane_color = PLAYER_COLORS[color]
            
            size = 25
            if plane_type == 'supersonic': size = 30
            elif plane_type == 'cargo': size = 35
            
            rotation = angle + 90
            
            # Animation class based on game state
            animation_class = ""
            if game['animation_state'] == 'flying' and game['current_player'] == color:
                animation_class = "aircraft-flying"
            
            aircraft_html.append(f"""
            <div class="aircraft-marker {animation_class}" 
                 style="left: {x}px; top: {y}px; width: {size}px; height: {size}px;
                        background-color: {plane_color}; transform: translate(-50%, -50%) rotate({rotation}deg);
                        z-index: {100 + plane_idx};">
                {plane_icon}
                <span style="position: absolute; bottom: -20px; font-size: 8px; transform: rotate(-{rotation}deg);">
                    {plane_idx+1}
                </span>
            </div>
            """)
    
    return "\n".join(aircraft_html)

# JavaScript for 3D interactions
st.markdown("""
<script>
// Update weather conditions
function updateWeather(weather) {
    const scene = document.getElementById('scene-container');
    scene.className = `weather-${weather} time-${document.getElementById('time-select').value}`;
    
    // In a real app, we would update the game state here
    console.log('Weather changed to:', weather);
}

// Update time of day
function updateTime(time) {
    const scene = document.getElementById('scene-container');
    scene.className = `weather-${document.getElementById('weather-select').value} time-${time}`;
    
    // In a real app, we would update the game state here
    console.log('Time changed to:', time);
}

// 3D Camera rotation animation
let rotation = {st.session_state.game_state['3d_camera']['rotation']};
function animateCamera() {
    rotation += 0.5;
    if (rotation > 360) rotation = 0;
    
    // Update flight markers rotation (demo only)
    document.querySelectorAll('.flight-marker').forEach(marker => {
        const currentLeft = parseFloat(marker.style.left);
        const currentTop = parseFloat(marker.style.top);
        const centerX = 200;
        const centerY = 200;
        
        const angle = Math.atan2(currentTop - centerY, currentLeft - centerX) * 180 / Math.PI;
        const newAngle = angle + 0.5;
        const distance = Math.sqrt(Math.pow(currentLeft - centerX, 2) + Math.pow(currentTop - centerY, 2));
        
        marker.style.left = `${centerX + distance * Math.cos(newAngle * Math.PI / 180)}px`;
        marker.style.top = `${centerY + distance * Math.sin(newAngle * Math.PI / 180)}px`;
    });
    
    requestAnimationFrame(animateCamera);
}

// Start camera animation
animateCamera();

// Add aircraft animation on click
document.querySelectorAll('.aircraft-marker').forEach(aircraft => {
    aircraft.addEventListener('click', () => {
        aircraft.classList.add('aircraft-flying');
        setTimeout(() => {
            aircraft.classList.remove('aircraft-flying');
        }, 2000);
    });
});
</script>
""", unsafe_allow_html=True)

# Game Instructions
with st.expander("📖 3D Flight Operations Manual", expanded=False):
    st.markdown("""
    ## 🎯 Mission Objective
    Be the first pilot to successfully land all 4 of your aircraft at the destination airport (position 52).

    ## 🎮 3D Flight Controls
    ### Starting the Mission
    - Each squadron has 4 aircraft at their departure airport
    - Red Squadron: Position 0 | Blue Squadron: Position 13 | Green Squadron: Position 26 | Yellow Squadron: Position 39
    - You need to roll a **6** to authorize takeoff from the departure airport
    - Squadrons take turns clockwise (Red → Blue → Green → Yellow)

    ### Flight Navigation Rules
    - Roll the dice (1-6) to set your flight distance
    - You can only navigate one aircraft per flight segment
    - Rolling a 6 grants an extra flight segment
    - Aircraft fly along a 3D spiral flight path (positions increase numerically)
    - Any flight that reaches or exceeds position 52 lands at the destination airport

    ## ✈️ Advanced Aircraft Systems
    ### High-Speed Jet (2× Speed)
    - Unlocked when 1 aircraft lands at destination
    - Flies at twice the set flight distance (e.g., roll 3 = 6 units)
    - Cruise altitude: 15,000ft
    - 3D Model: Military Supersonic Jet

    ### Cargo Aircraft
    - Unlocked when 2 aircraft land at destination
    - Can carry other aircraft at the same flight position
    - All carried aircraft move with the cargo aircraft
    - Cruise altitude: 8,000ft
    - 3D Model: Heavy Cargo Transport

    ### Supersonic Jet (3× Speed)
    - Unlocked when 3 aircraft land at destination
    - Flies at three times the set flight distance (e.g., roll 2 = 6 units)
    - Cruise altitude: 20,000ft
    - 3D Model: Hypersonic Experimental Jet

    ## 📡 3D Visualization Features
    ### Camera Controls
    - Adjust camera rotation (0-360°) to view the flight map from any angle
    - Change camera height to zoom in/out of the 3D flight space
    - Weather conditions affect visibility and flight characteristics
    - Time of day changes the visual appearance of the flight map

    ### Flight Instruments
    - Altimeter shows current cruise altitude (feet)
    - Airspeed indicator shows current velocity (km/h)
    - Flight position display shows average squadron position
    - Status indicator shows current mission status
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px 0;">
    <p>✈️ 3D Aeroplane Chess Simulator | Built with Streamlit + HTML/CSS/JavaScript</p>
    <p style="font-size: 12px;">To run locally: <code>streamlit run aeroplane_chess_3d.py</code></p>
</div>
""", unsafe_allow_html=True)
