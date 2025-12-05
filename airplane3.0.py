import streamlit as st
import random
import pandas as pd
from datetime import datetime
import uuid

# Set page config
st.set_page_config(
    page_title="Aeroplane Chess",
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

# Special plane types
PLANE_TYPES = {
    'normal': {'name': 'Normal Plane', 'speed': 1, 'icon': '✈️'},
    'jet': {'name': 'Jet Plane', 'speed': 2, 'icon': '✈️✈️', 'unlock_score': 1},  # 2x speed
    'cargo': {'name': 'Cargo Plane', 'speed': 1, 'icon': '📦✈️', 'unlock_score': 2},  # Can carry other planes
    'supersonic': {'name': 'Supersonic Jet', 'speed': 3, 'icon': '🚀✈️', 'unlock_score': 3}  # 3x speed
}

# Initialize game state with proper defaults
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'players': {
            'red': {
                'planes': [0, 0, 0, 0],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': True, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
            },
            'blue': {
                'planes': [13, 13, 13, 13],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
            },
            'green': {
                'planes': [26, 26, 26, 26],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
            },
            'yellow': {
                'planes': [39, 39, 39, 39],
                'plane_types': ['normal', 'normal', 'normal', 'normal'],
                'turn': False, 
                'score': 0,
                'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
            }
        },
        'current_player': 'red',
        'dice_roll': 0,
        'game_over': False,
        'winner': None,
        'last_move': None,
        'extra_turn': False,
        'cargo_carrying': None  # Track cargo plane carrying other planes
    }

# Initialize chat state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'player_nicknames' not in st.session_state:
    st.session_state.player_nicknames = {
        'red': 'Red Player',
        'blue': 'Blue Player',
        'green': 'Green Player',
        'yellow': 'Yellow Player'
    }

# Game logic functions
def roll_dice():
    """Roll the dice (1-6)"""
    return random.randint(1, 6)

def unlock_special_planes(player):
    """Unlock special planes based on score"""
    game = st.session_state.game_state
    score = game['players'][player]['score']
    
    # Unlock jet plane at 1 plane in finish
    if score >= 1 and not game['players'][player]['special_planes_unlocked']['jet']:
        game['players'][player]['special_planes_unlocked']['jet'] = True
        add_chat_message(f"Unlocked Jet Plane! (2x speed)", st.session_state.player_nicknames[player])
    
    # Unlock cargo plane at 2 planes in finish
    if score >= 2 and not game['players'][player]['special_planes_unlocked']['cargo']:
        game['players'][player]['special_planes_unlocked']['cargo'] = True
        add_chat_message(f"Unlocked Cargo Plane! (Can carry other planes)", st.session_state.player_nicknames[player])
    
    # Unlock supersonic jet at 3 planes in finish
    if score >= 3 and not game['players'][player]['special_planes_unlocked']['supersonic']:
        game['players'][player]['special_planes_unlocked']['supersonic'] = True
        add_chat_message(f"Unlocked Supersonic Jet! (3x speed)", st.session_state.player_nicknames[player])

def convert_plane(player, plane_idx, new_type):
    """Convert a normal plane to a special plane"""
    game = st.session_state.game_state
    
    # Validate inputs
    if plane_idx < 0 or plane_idx >= 4:
        return False
    
    # Check if plane is normal and new type is unlocked
    if (game['players'][player]['plane_types'][plane_idx] == 'normal' and
        game['players'][player]['special_planes_unlocked'].get(new_type, False) and
        game['players'][player]['planes'][plane_idx] != BOARD_POSITIONS['finish']):
        
        game['players'][player]['plane_types'][plane_idx] = new_type
        add_chat_message(f"Converted plane {plane_idx+1} to {PLANE_TYPES[new_type]['name']}", 
                       st.session_state.player_nicknames[player])
        return True
    return False

def move_plane(player, plane_idx, steps):
    """Move a player's plane by specified steps with special plane abilities"""
    game = st.session_state.game_state
    
    # Validate inputs
    if plane_idx < 0 or plane_idx >= 4:
        return False
    
    current_pos = game['players'][player]['planes'][plane_idx]
    plane_type = game['players'][player]['plane_types'][plane_idx]
    
    # Skip if plane is already in finish
    if current_pos == BOARD_POSITIONS['finish']:
        return False
    
    # Handle start rule (need 6 to move out of start)
    start_pos = BOARD_POSITIONS[f'start_{player}']
    
    if current_pos == start_pos and steps != 6:
        return False  # Can't move out without rolling 6
    
    # Apply special plane speed multipliers
    speed_multiplier = PLANE_TYPES[plane_type]['speed']
    actual_steps = steps * speed_multiplier
    
    # Calculate new position
    if current_pos == start_pos and steps == 6:
        new_pos = start_pos + 1
    else:
        new_pos = current_pos + actual_steps
    
    # Handle cargo plane carrying
    carried_planes_info = ""
    if plane_type == 'cargo' and game['cargo_carrying'] is None:
        # Find other planes at the same position to carry
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
    
    # Check for finish (exact position or beyond)
    finish_pos = BOARD_POSITIONS['finish']
    move_description = f"{PLANE_TYPES[plane_type]['icon']} {PLAYER_NAMES[player]} {PLANE_TYPES[plane_type]['name']} {plane_idx+1}"
    
    if new_pos >= finish_pos:
        # Only move to finish if exact or beyond
        new_pos = finish_pos
        game['players'][player]['score'] += 1
        game['last_move'] = f"{move_description} reached finish! (Moved {actual_steps} steps with {speed_multiplier}x speed){carried_planes_info}"
        
        # Unlock special planes based on new score
        unlock_special_planes(player)
        
        # Check if player won
        if game['players'][player]['score'] == 4:
            game['game_over'] = True
            game['winner'] = player
            # Add game end message to chat
            add_chat_message(f"Game Over! {st.session_state.player_nicknames[player]} ({PLAYER_NAMES[player]}) wins!", "System")
    else:
        game['last_move'] = f"{move_description} moved from {current_pos} to {new_pos} (Rolled {steps}, moved {actual_steps} steps with {speed_multiplier}x speed){carried_planes_info}"
        
        # Move carried planes with cargo plane
        if game['cargo_carrying'] and game['cargo_carrying'][0] == plane_idx:
            for carried_idx in game['cargo_carrying'][1]:
                if game['players'][player]['planes'][carried_idx] != BOARD_POSITIONS['finish']:
                    game['players'][player]['planes'][carried_idx] = new_pos
            game['cargo_carrying'] = None
    
    # Update position
    game['players'][player]['planes'][plane_idx] = new_pos
    return True

def switch_turn():
    """Switch to next player's turn"""
    game = st.session_state.game_state
    
    # Reset cargo carrying when turn ends
    game['cargo_carrying'] = None
    
    # If rolled 6, get extra turn
    if game['dice_roll'] == 6 and not game['game_over']:
        game['extra_turn'] = True
        game['last_move'] += " (Extra turn for rolling 6!)"
        game['dice_roll'] = 0  # Reset dice for next roll
        return
    
    # Normal turn switch
    game['extra_turn'] = False
    players = ['red', 'blue', 'green', 'yellow']
    current_idx = players.index(game['current_player'])
    next_idx = (current_idx + 1) % 4
    
    # Reset turn flags
    for p in players:
        game['players'][p]['turn'] = False
    
    game['current_player'] = players[next_idx]
    game['players'][game['current_player']]['turn'] = True
    game['dice_roll'] = 0
    
    # Notify chat about turn change
    add_chat_message(f"It's now {st.session_state.player_nicknames[game['current_player']]}'s turn ({PLAYER_NAMES[game['current_player']]})", "System")

def add_chat_message(message, sender, is_system=False):
    """Add a message to the chat with validation"""
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
    
    # Keep only last 50 messages to prevent memory issues
    if len(st.session_state.chat_messages) > 50:
        st.session_state.chat_messages = st.session_state.chat_messages[-50:]

# UI Components
st.title("✈️ Aeroplane Chess (Flight Chess) with Special Planes")
st.subheader("Classic Chinese Aeroplane Chess Game with Jet, Cargo, and Supersonic Planes")

# Main layout: game board/controls and chat
main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    # Game board visualization with improved styling
    def render_board():
        """Render the game board with better visualization"""
        game = st.session_state.game_state
        
        # Create a more intuitive board layout (4 quadrants)
        st.markdown("### Game Board")
        
        # Create a styled board with better plane visualization
        board_container = st.container()
        with board_container:
            # Create a grid layout (13 columns for the board)
            cols = st.columns(13)
            
            # Add board positions in a more logical layout
            for i in range(52):
                with cols[i % 13]:
                    # Determine position type for display
                    pos_type = ""
                    if i == BOARD_POSITIONS['start_red']: 
                        pos_type = " 🟥"
                    elif i == BOARD_POSITIONS['start_blue']: 
                        pos_type = " 🟦"
                    elif i == BOARD_POSITIONS['start_green']: 
                        pos_type = " 🟩"
                    elif i == BOARD_POSITIONS['start_yellow']: 
                        pos_type = " 🟨"
                    elif i == BOARD_POSITIONS['finish'] - 1: 
                        pos_type = " 🏆"
                    
                    # Get plane info for this position
                    plane_html = ""
                    plane_count = 0
                    
                    # Collect all planes at this position
                    planes_at_pos = []
                    for color, data in game['players'].items():
                        for idx, pos in enumerate(data['planes']):
                            if pos == i and pos != BOARD_POSITIONS['finish']:
                                planes_at_pos.append((color, idx, data['plane_types'][idx]))
                                plane_count += 1
                    
                    # Create plane icons
                    for color, idx, ptype in planes_at_pos[:4]:  # Limit to 4 planes per position
                        plane_color = PLAYER_COLORS[color]
                        plane_icon = PLANE_TYPES[ptype]['icon']
                        plane_html += f"""
                        <div style="width: 25px; height: 25px; background-color: {plane_color}; 
                                   border-radius: 50%; margin: 1px auto; display: flex;
                                   align-items: center; justify-content: center; color: white;
                                   font-size: 8px;">
                            {plane_icon}
                        </div>
                        """
                    
                    # Display position with planes
                    st.markdown(f"""
                    <div style="width: 50px; height: 50px; border: 2px solid #ccc; 
                               border-radius: 8px; text-align: center; padding: 5px;
                               margin: 5px; background-color: #f8f9fa;">
                        <strong style="font-size: 12px;">{i}</strong>{pos_type}
                        <div style="margin-top: 2px; font-size: 8px; line-height: 1;">{plane_html}</div>
                        {f"<small>({plane_count})</small>" if plane_count > 0 else ""}
                    </div>
                    """, unsafe_allow_html=True)
    
    render_board()
    
    # Game status section
    game = st.session_state.game_state
    st.markdown("---")
    st.subheader("Game Status")
    
    # Current player indicator with color
    current_color = PLAYER_COLORS[game['current_player']]
    current_nickname = st.session_state.player_nicknames[game['current_player']]
    
    # Status badges
    status_badges = []
    if game['extra_turn']:
        status_badges.append("🏅 Extra Turn")
    if game['cargo_carrying']:
        status_badges.append("📦 Carrying Planes")
    if game['game_over']:
        status_badges.append("🎮 Game Over")
    
    status_text = " | ".join(status_badges) if status_badges else "Playing"
    
    st.markdown(f"""
    <div style="padding: 12px; background-color: {current_color}; color: white; 
               border-radius: 8px; font-size: 18px; font-weight: bold; margin-bottom: 10px;">
        {current_nickname} ({PLAYER_NAMES[game['current_player']].upper()})
        <span style="font-size: 12px; font-weight: normal; margin-left: 10px;">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Dice roll and last move
    col_dice, col_last_move = st.columns(2)
    
    with col_dice:
        if game['dice_roll'] > 0:
            # Stylish dice display
            st.markdown(f"""
            <div style="background-color: #f0f2f6; border-radius: 10px; padding: 20px; text-align: center;">
                <div style="font-size: 60px; line-height: 1;">🎲</div>
                <div style="font-size: 36px; font-weight: bold; color: #262730;">{game['dice_roll']}</div>
                <div style="font-size: 12px; color: #666;">Current Roll</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #f0f2f6; border-radius: 10px; padding: 20px; text-align: center;">
                <div style="font-size: 40px; line-height: 1;">🎲</div>
                <div style="font-size: 16px; color: #666;">Click to roll!</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_last_move:
        if game['last_move']:
            st.markdown(f"""
            <div style="background-color: #e8f4f8; border-radius: 10px; padding: 15px; height: 100%;">
                <div style="font-size: 14px; color: #2d3748; font-weight: bold; margin-bottom: 5px;">
                    Last Move
                </div>
                <div style="font-size: 12px; color: #4a5568; font-style: italic;">
                    {game['last_move']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #f5f5f5; border-radius: 10px; padding: 15px; height: 100%;">
                <div style="font-size: 14px; color: #718096; text-align: center;">
                    No moves yet<br>Roll the dice to start!
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Score display with better styling
    st.subheader("Score Board & Special Planes")
    
    # Create enhanced score data
    score_data = []
    for color in ['red', 'blue', 'green', 'yellow']:
        unlocked = []
        if game['players'][color]['special_planes_unlocked']['jet']:
            unlocked.append("✈️✈️ Jet")
        if game['players'][color]['special_planes_unlocked']['cargo']:
            unlocked.append("📦✈️ Cargo")
        if game['players'][color]['special_planes_unlocked']['supersonic']:
            unlocked.append("🚀✈️ Supersonic")
        
        # Player status
        status = "🏆 Winner!" if game['winner'] == color else "🟢 Playing" if not game['game_over'] else "🔴 Lost"
        
        score_data.append({
            'Player': f"<span style='color: {PLAYER_COLORS[color]}; font-weight: bold;'>{st.session_state.player_nicknames[color]}</span>",
            'Color': f"<span style='color: {PLAYER_COLORS[color]};'>{PLAYER_NAMES[color]}</span>",
            'Planes in Finish': game['players'][color]['score'],
            'Unlocked Planes': ', '.join(unlocked) if unlocked else 'None',
            'Status': status
        })
    
    # Display score table
    score_df = pd.DataFrame(score_data)
    st.markdown(score_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Game controls
    st.markdown("---")
    st.subheader("🎮 Game Controls")
    
    # Game over check
    if game['game_over']:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                   padding: 25px; border-radius: 15px; text-align: center; margin: 20px 0;
                   border: 2px solid #28a745;">
            <h2 style="color: #155724; margin-bottom: 15px;">🎉 GAME OVER 🎉</h2>
            <h3 style="color: #155724;">{st.session_state.player_nicknames[game['winner']]} ({PLAYER_NAMES[game['winner']]}) WINS!</h3>
            <p style="font-size: 16px; color: #2d3748; margin-top: 15px;">
                All 4 planes reached the finish line!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Start New Game", type="primary", use_container_width=True):
            # Reset game state completely
            st.session_state.game_state = {
                'players': {
                    'red': {
                        'planes': [0, 0, 0, 0],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': True, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                    },
                    'blue': {
                        'planes': [13, 13, 13, 13],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                    },
                    'green': {
                        'planes': [26, 26, 26, 26],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                    },
                    'yellow': {
                        'planes': [39, 39, 39, 39],
                        'plane_types': ['normal', 'normal', 'normal', 'normal'],
                        'turn': False, 
                        'score': 0,
                        'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                    }
                },
                'current_player': 'red',
                'dice_roll': 0,
                'game_over': False,
                'winner': None,
                'last_move': None,
                'extra_turn': False,
                'cargo_carrying': None
            }
            # Add system message to chat
            add_chat_message("A new game has started!", "System", is_system=True)
            st.rerun()
    else:
        # Main game controls
        control_cols = st.columns(2)
        
        with control_cols[0]:
            if st.button("🎲 Roll Dice", type="primary", 
                       disabled=game['dice_roll'] > 0, use_container_width=True):
                game['dice_roll'] = roll_dice()
                game['last_move'] = f"{current_nickname} rolled a {game['dice_roll']}"
                # Add to chat
                add_chat_message(f"Rolled a {game['dice_roll']}", current_nickname)
                st.rerun()
        
        with control_cols[1]:
            # Reset game with confirmation
            reset_confirm = st.checkbox("Confirm Reset", key="reset_check")
            if st.button("🔄 Reset Game", type="secondary", 
                       disabled=not reset_confirm, use_container_width=True):
                # Full game reset
                st.session_state.game_state = {
                    'players': {
                        'red': {
                            'planes': [0, 0, 0, 0],
                            'plane_types': ['normal', 'normal', 'normal', 'normal'],
                            'turn': True, 
                            'score': 0,
                            'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                        },
                        'blue': {
                            'planes': [13, 13, 13, 13],
                            'plane_types': ['normal', 'normal', 'normal', 'normal'],
                            'turn': False, 
                            'score': 0,
                            'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                        },
                        'green': {
                            'planes': [26, 26, 26, 26],
                            'plane_types': ['normal', 'normal', 'normal', 'normal'],
                            'turn': False, 
                            'score': 0,
                            'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                        },
                        'yellow': {
                            'planes': [39, 39, 39, 39],
                            'plane_types': ['normal', 'normal', 'normal', 'normal'],
                            'turn': False, 
                            'score': 0,
                            'special_planes_unlocked': {'jet': False, 'cargo': False, 'supersonic': False}
                        }
                    },
                    'current_player': 'red',
                    'dice_roll': 0,
                    'game_over': False,
                    'winner': None,
                    'last_move': "Game reset",
                    'extra_turn': False,
                    'cargo_carrying': None
                }
                add_chat_message("Game has been reset!", "System", is_system=True)
                st.rerun()
        
        # Special plane conversion section
        current_player = game['current_player']
        if game['players'][current_player]['score'] >= 1:
            st.markdown("---")
            st.subheader("✈️ Convert to Special Plane")
            
            # Get normal planes available for conversion
            normal_planes = []
            for i in range(4):
                if (game['players'][current_player]['plane_types'][i] == 'normal' and 
                    game['players'][current_player]['planes'][i] != BOARD_POSITIONS['finish']):
                    normal_planes.append(i)
            
            if normal_planes:
                # Show conversion options
                convert_cols = st.columns([3, 2, 1])
                
                with convert_cols[0]:
                    plane_options = []
                    for i in normal_planes:
                        pos = game['players'][current_player]['planes'][i]
                        plane_options.append(f"Plane {i+1} - Position: {pos}")
                    
                    selected_plane = st.selectbox(
                        "Select plane to convert:",
                        options=plane_options,
                        key="convert_plane_select"
                    )
                
                with convert_cols[1]:
                    # Get available special plane types
                    available_types = []
                    if game['players'][current_player]['special_planes_unlocked']['jet']:
                        available_types.append('jet')
                    if game['players'][current_player]['special_planes_unlocked']['cargo']:
                        available_types.append('cargo')
                    if game['players'][current_player]['special_planes_unlocked']['supersonic']:
                        available_types.append('supersonic')
                    
                    if available_types:
                        type_options = [f"{PLANE_TYPES[t]['icon']} {PLANE_TYPES[t]['name']}" for t in available_types]
                        selected_type = st.selectbox(
                            "Convert to:",
                            options=type_options,
                            key="new_plane_type"
                        )
                    else:
                        st.selectbox("Convert to:", options=["No planes unlocked yet"], disabled=True, key="no_type")
                        selected_type = None
                
                with convert_cols[2]:
                    convert_btn_disabled = (not selected_plane or not selected_type)
                    if st.button("🔄 Convert", type="secondary", 
                               disabled=convert_btn_disabled, use_container_width=True):
                        # Extract plane index
                        plane_idx = int(selected_plane.split()[1]) - 1
                        
                        # Extract plane type key
                        type_key = None
                        if selected_type:
                            if "Jet Plane" in selected_type:
                                type_key = 'jet'
                            elif "Cargo Plane" in selected_type:
                                type_key = 'cargo'
                            elif "Supersonic Jet" in selected_type:
                                type_key = 'supersonic'
                        
                        if type_key and convert_plane(current_player, plane_idx, type_key):
                            st.success(f"✅ Converted to {PLANE_TYPES[type_key]['name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Could not convert plane!")
            else:
                st.info("ℹ️ No normal planes available for conversion (all are special planes or in finish)")
        
        # Plane selection (only if dice rolled)
        if game['dice_roll'] > 0:
            st.markdown("---")
            st.subheader(f"✈️ Move {current_nickname}'s Plane")
            
            planes = game['players'][current_player]['planes']
            plane_types = game['players'][current_player]['plane_types']
            
            # Show available planes in a grid
            plane_cols = st.columns(2)
            
            for i, (pos, ptype) in enumerate(zip(planes, plane_types)):
                with plane_cols[i % 2]:
                    # Get plane info
                    plane_icon = PLANE_TYPES[ptype]['icon']
                    speed_multiplier = PLANE_TYPES[ptype]['speed']
                    actual_steps = game['dice_roll'] * speed_multiplier
                    
                    # Determine plane status
                    if pos == BOARD_POSITIONS['finish']:
                        plane_status = f"{plane_icon} Plane {i+1}: ✅ In Finish"
                        disabled = True
                    elif pos == BOARD_POSITIONS[f'start_{current_player}'] and game['dice_roll'] != 6:
                        plane_status = f"{plane_icon} Plane {i+1}: 📍 Start (Need 6 to move)"
                        disabled = True
                    else:
                        new_pos = pos + actual_steps if pos != BOARD_POSITIONS[f'start_{current_player}'] else pos + 1
                        finish_note = " (Finish!)" if new_pos >= BOARD_POSITIONS['finish'] else ""
                        plane_status = f"{plane_icon} Plane {i+1}: {pos} → {new_pos} (x{speed_multiplier} speed){finish_note}"
                        disabled = False
                    
                    # Plane button with color
                    if st.button(plane_status, key=f"plane_{i}", disabled=disabled, use_container_width=True):
                        # Attempt to move the plane
                        move_success = move_plane(current_player, i, game['dice_roll'])
                        
                        if move_success:
                            # Add to chat
                            add_chat_message(
                                f"Moved {PLANE_TYPES[ptype]['name']} plane {i+1} (rolled {game['dice_roll']}, moved {actual_steps} steps)", 
                                current_nickname
                            )
                            # Switch turn (handles extra turn for 6)
                            switch_turn()
                        else:
                            st.error("❌ Can't move this plane!")
                            add_chat_message(
                                f"Tried to move {PLANE_TYPES[ptype]['name']} plane {i+1} but failed", 
                                current_nickname
                            )
                        
                        st.rerun()
            
            # Pass turn button (only if not extra turn)
            if not game['extra_turn']:
                if st.button("➡️ Pass Turn", key="pass_turn", 
                           use_container_width=True, type="secondary"):
                    game['last_move'] = f"{current_nickname} passed their turn"
                    add_chat_message("Passed their turn", current_nickname)
                    switch_turn()
                    st.rerun()

with main_col2:
    # Chat and player settings
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "👤 Player Settings", "✈️ Plane Info"])
    
    with tab1:
        st.subheader("Game Chat")
        
        # Chat history with better styling
        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.chat_messages:
                st.markdown("""
                <div style="height: 100%; display: flex; align-items: center; justify-content: center;
                           color: #6c757d; font-style: italic;">
                    No messages yet. Start the conversation!
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_messages:
                    if msg['is_system']:
                        # System message styling
                        st.markdown(f"""
                        <div style="background-color: #e9ecef; padding: 8px 12px; border-radius: 8px; margin: 5px 0;
                                   font-style: italic; color: #495057;">
                            <small>[{msg['timestamp']}] <strong>System:</strong> {msg['text']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Find player color for this message
                        player_color = "#6c757d"  # Default gray
                        for color, nickname in st.session_state.player_nicknames.items():
                            if nickname == msg['sender']:
                                player_color = PLAYER_COLORS[color]
                                break
                        
                        # User message styling
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 10px 15px; border-radius: 10px; margin: 5px 0;
                                   border-left: 4px solid {player_color};">
                            <small>[{msg['timestamp']}] <strong style="color: {player_color};">{msg['sender']}:</strong> {msg['text']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Chat input
        st.markdown("---")
        st.subheader("Send Message")
        
        # Select which player is sending the message
        selected_player = st.selectbox(
            "Send as:",
            options=list(st.session_state.player_nicknames.values()),
            index=list(st.session_state.player_nicknames.keys()).index(st.session_state.game_state['current_player'])
        )
        
        # Message input with form to prevent rerun on enter
        with st.form(key='chat_form', clear_on_submit=True):
            msg_text = st.text_input("Type your message...", key="chat_input")
            submit_btn = st.form_submit_button("📤 Send Message", type="primary", use_container_width=True)
            
            if submit_btn and msg_text.strip():
                add_chat_message(msg_text.strip(), selected_player)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
            if st.checkbox("Confirm clear chat?"):
                st.session_state.chat_messages = []
                st.rerun()
    
    with tab2:
        st.subheader("Player Nicknames")
        
        # Allow setting nicknames for each player
        st.markdown("### Customize Player Names")
        
        for color in ['red', 'blue', 'green', 'yellow']:
            col_color, col_input = st.columns([1, 4])
            with col_color:
                st.markdown(f"""
                <div style="width: 30px; height: 30px; background-color: {PLAYER_COLORS[color]}; 
                           border-radius: 50%; margin: 8px auto;"></div>
                """, unsafe_allow_html=True)
            with col_input:
                new_nickname = st.text_input(
                    f"{PLAYER_NAMES[color]} Player",
                    value=st.session_state.player_nicknames[color],
                    key=f"nickname_{color}"
                )
                # Update nickname if changed
                if new_nickname and new_nickname != st.session_state.player_nicknames[color]:
                    old_name = st.session_state.player_nicknames[color]
                    st.session_state.player_nicknames[color] = new_nickname
                    add_chat_message(f"{old_name} is now known as {new_nickname}", "System", is_system=True)
        
        # Chat settings
        st.markdown("---")
        st.subheader("Chat Settings")
        
        # Export chat history
        if st.button("📥 Export Chat History", use_container_width=True):
            if st.session_state.chat_messages:
                chat_text = "\n".join([
                    f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}" 
                    for msg in st.session_state.chat_messages
                ])
                st.download_button(
                    label="Download Chat File",
                    data=chat_text,
                    file_name=f"aeroplane_chess_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("No chat history to export!")
        
        # Reset all settings
        st.markdown("---")
        st.subheader("Reset Settings")
        
        if st.button("🔄 Reset All Settings", type="secondary", use_container_width=True):
            if st.checkbox("Reset nicknames and chat?"):
                st.session_state.player_nicknames = {
                    'red': 'Red Player',
                    'blue': 'Blue Player',
                    'green': 'Green Player',
                    'yellow': 'Yellow Player'
                }
                st.session_state.chat_messages = []
                add_chat_message("All chat settings have been reset", "System", is_system=True)
                st.rerun()
    
    with tab3:
        st.subheader("✈️ Special Plane Information")
        
        # Plane info table with better formatting
        st.markdown("### Plane Types & Abilities")
        
        plane_info = {
            'Plane Type': ['✈️ Normal Plane', '✈️✈️ Jet Plane', '📦✈️ Cargo Plane', '🚀✈️ Supersonic Jet'],
            'Speed': ['1×', '2×', '1×', '3×'],
            'Special Ability': [
                'Standard movement',
                'Moves twice the dice roll',
                'Carries other planes at the same position',
                'Moves three times the dice roll'
            ],
            'Unlock Requirement': [
                'Starts with all planes',
                '1 plane in finish zone',
                '2 planes in finish zone',
                '3 planes in finish zone'
            ]
        }
        
        st.dataframe(pd.DataFrame(plane_info), use_container_width=True)
        
        # Game tips
        st.markdown("---")
        st.subheader("🎯 Game Strategy Tips")
        
        tips = [
            "🔹 Unlock Jet Plane first for faster movement across the board",
            "🔹 Use Cargo Plane to move multiple planes together and save turns",
            "🔹 Save Supersonic Jet for the final stretch to the finish line",
            "🔹 Rolling a 6 gives you an extra turn - use it strategically",
            "🔹 Convert planes based on your current game position",
            "🔹 Focus on getting one plane to finish first to unlock special planes",
            "🔹 Cargo Plane works best when multiple planes are at the same position"
        ]
        
        for tip in tips:
            st.markdown(f"<div style='padding: 8px; margin: 4px 0; background-color: #f8f9fa; border-radius: 6px;'>{tip}</div>", 
                       unsafe_allow_html=True)

# Game instructions with better formatting
with st.expander("📖 Complete Game Rules", expanded=False):
    st.markdown("""
    ## 🎯 Game Objective
    Be the first player to move all 4 of your planes to the finish position (52).

    ## 🎲 Basic Rules
    ### Starting the Game
    - Each player has 4 planes at their starting position
    - Red: Position 0 | Blue: Position 13 | Green: Position 26 | Yellow: Position 39
    - You need to roll a **6** to move a plane out of the starting position
    - Players take turns clockwise (Red → Blue → Green → Yellow)

    ### Movement Rules
    - Roll the dice (1-6) to determine how many steps to move
    - You can only move one plane per turn
    - Rolling a 6 gives you an extra turn
    - Planes move forward only (positions increase numerically)
    - Any move that reaches or exceeds position 52 sends the plane to finish

    ## ✈️ Special Plane Rules
    ### Jet Plane (2× Speed)
    - Unlocked when 1 plane reaches finish
    - Moves twice the dice roll (e.g., roll 3 = move 6 steps)
    - Great for quickly moving across the board

    ### Cargo Plane
    - Unlocked when 2 planes reach finish
    - Can carry other planes at the same position
    - All carried planes move with the cargo plane
    - Saves turns by moving multiple planes at once

    ### Supersonic Jet (3× Speed)
    - Unlocked when 3 planes reach finish
    - Moves three times the dice roll (e.g., roll 2 = move 6 steps)
    - Perfect for the final sprint to the finish line

    ### Plane Conversion
    - Convert normal planes to special planes in the controls section
    - Only normal planes not in finish can be converted
    - Converted planes retain their special abilities permanently

    ## 💬 Chat Features
    - Send messages as any player
    - Customize player nicknames
    - Export chat history to text file
    - System messages track game events automatically
    """)

# Custom styling
st.markdown("""
<style>
    /* General styling */
    .stButton>button {
        border-radius: 8px;
        height: 3em;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 16px;
        font-weight: bold;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Chat styling */
    div[data-testid="stVerticalBlock"] > div[style*="height: 400px"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
    }
    
    /* Improve mobile responsiveness */
    @media (max-width: 768px) {
        .stColumns {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px 0;">
    <p>✈️ Aeroplane Chess with Special Planes | Built with Streamlit</p>
    <p style="font-size: 12px;">To run locally: <code>streamlit run aeroplane_chess.py</code></p>
</div>
""", unsafe_allow_html=True)
