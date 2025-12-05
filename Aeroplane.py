import streamlit as st
import random
import pandas as pd

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

# Initialize game state
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'players': {
            'red': {'planes': [0, 0, 0, 0], 'turn': True, 'score': 0},
            'blue': {'planes': [13, 13, 13, 13], 'turn': False, 'score': 0},
            'green': {'planes': [26, 26, 26, 26], 'turn': False, 'score': 0},
            'yellow': {'planes': [39, 39, 39, 39], 'turn': False, 'score': 0}
        },
        'current_player': 'red',
        'dice_roll': 0,
        'game_over': False,
        'winner': None
    }

# Game logic functions
def roll_dice():
    """Roll the dice (1-6)"""
    return random.randint(1, 6)

def move_plane(player, plane_idx, steps):
    """Move a player's plane by specified steps"""
    game = st.session_state.game_state
    current_pos = game['players'][player]['planes'][plane_idx]
    
    # Handle start rule (need 6 to move out of start)
    start_pos = BOARD_POSITIONS[f'start_{player}']
    home_pos = BOARD_POSITIONS[f'home_{player}']
    
    if current_pos == start_pos and steps != 6:
        return False  # Can't move out without rolling 6
    
    # Calculate new position
    if current_pos == start_pos and steps == 6:
        new_pos = start_pos + 1
    else:
        new_pos = current_pos + steps
    
    # Check for finish
    if new_pos >= BOARD_POSITIONS['finish']:
        new_pos = BOARD_POSITIONS['finish']
        game['players'][player]['score'] += 1
        
        # Check if player won
        if game['players'][player]['score'] == 4:
            game['game_over'] = True
            game['winner'] = player
    
    # Update position
    game['players'][player]['planes'][plane_idx] = new_pos
    return True

def switch_turn():
    """Switch to next player's turn"""
    game = st.session_state.game_state
    players = ['red', 'blue', 'green', 'yellow']
    current_idx = players.index(game['current_player'])
    next_idx = (current_idx + 1) % 4
    
    # Reset turn flags
    for p in players:
        game['players'][p]['turn'] = False
    
    game['current_player'] = players[next_idx]
    game['players'][game['current_player']]['turn'] = True
    game['dice_roll'] = 0

# UI Components
st.title("✈️ Aeroplane Chess (Flight Chess)")
st.subheader("Classic Chinese Aeroplane Chess Game")

# Game board visualization
def render_board():
    """Render the game board"""
    game = st.session_state.game_state
    
    # Create board grid (simplified representation)
    board_html = """
    <div style="display: grid; grid-template-columns: repeat(13, 40px); gap: 5px; margin: 20px 0;">
    """
    
    # Add board positions
    for i in range(52):
        # Check if any plane is on this position
        plane_html = ""
        for color, data in game['players'].items():
            if i in data['planes']:
                plane_html += f"""
                <div style="width: 30px; height: 30px; background-color: {PLAYER_COLORS[color]}; 
                           border-radius: 50%; margin: 2px; float: left;"></div>
                """
        
        # Add position number and planes
        board_html += f"""
        <div style="width: 40px; height: 40px; border: 1px solid #ccc; text-align: center; padding: 5px;">
            <small>{i}</small>
            {plane_html}
        </div>
        """
    
    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)

# Game controls
col1, col2 = st.columns([2, 1])

with col1:
    render_board()
    
    # Game status
    game = st.session_state.game_state
    st.write(f"**Current Player:** {game['current_player'].upper()} ({PLAYER_COLORS[game['current_player']]})")
    st.write(f"**Dice Roll:** {game['dice_roll'] if game['dice_roll'] > 0 else '🎲 Roll the dice!'}")
    
    # Score display
    score_data = {
        'Player': ['Red', 'Blue', 'Green', 'Yellow'],
        'Planes in Finish': [
            game['players']['red']['score'],
            game['players']['blue']['score'],
            game['players']['green']['score'],
            game['players']['yellow']['score']
        ]
    }
    st.dataframe(pd.DataFrame(score_data), use_container_width=True)

with col2:
    st.header("Game Controls")
    
    # Game over check
    if game['game_over']:
        st.success(f"🎉 {game['winner'].upper()} WINS! 🎉")
        if st.button("Start New Game"):
            # Reset game state
            st.session_state.game_state = {
                'players': {
                    'red': {'planes': [0, 0, 0, 0], 'turn': True, 'score': 0},
                    'blue': {'planes': [13, 13, 13, 13], 'turn': False, 'score': 0},
                    'green': {'planes': [26, 26, 26, 26], 'turn': False, 'score': 0},
                    'yellow': {'planes': [39, 39, 39, 39], 'turn': False, 'score': 0}
                },
                'current_player': 'red',
                'dice_roll': 0,
                'game_over': False,
                'winner': None
            }
            st.rerun()
    else:
        # Dice roll button
        if st.button("🎲 Roll Dice", disabled=game['dice_roll'] > 0):
            game['dice_roll'] = roll_dice()
            st.rerun()
        
        # Plane selection (only if dice rolled)
        if game['dice_roll'] > 0:
            st.subheader(f"Move a {game['current_player']} plane")
            current_player = game['current_player']
            planes = game['players'][current_player]['planes']
            
            # Show available planes
            for i, pos in enumerate(planes):
                plane_status = f"Position: {pos}"
                if pos == BOARD_POSITIONS['finish']:
                    plane_status = "✅ In Finish"
                
                if st.button(f"Plane {i+1}: {plane_status}", 
                           key=f"plane_{i}",
                           disabled=pos == BOARD_POSITIONS['finish']):
                    # Attempt to move the plane
                    move_success = move_plane(current_player, i, game['dice_roll'])
                    
                    if move_success:
                        # Switch turn (unless rolled 6, which gives another turn)
                        if game['dice_roll'] != 6:
                            switch_turn()
                    else:
                        st.error("❌ Can't move this plane (need 6 to move out of start!)")
                    
                    st.rerun()
            
            # Pass turn button (if needed)
            if st.button("➡️ Pass Turn", key="pass_turn"):
                switch_turn()
                st.rerun()

# Game instructions
with st.expander("📖 How to Play"):
    st.write("""
    ### Aeroplane Chess Rules (Simplified)
    1. **Objective**: Get all 4 of your planes to the finish position (52)
    2. **Starting**: You need to roll a 6 to move a plane out of your start position
    3. **Movement**: Roll the dice and move one of your planes by that number of steps
    4. **Extra Turn**: Rolling a 6 gives you an extra turn
    5. **Winning**: First player to get all 4 planes to finish wins!
    
    ### Start Positions:
    - Red: 0
    - Blue: 13
    - Green: 26
    - Yellow: 39
    """)

# Footer
st.markdown("""
---
### Publish This App
1. Save this code as `aeroplane_chess.py`
2. Install requirements: `pip install streamlit pandas`
3. Run locally: `streamlit run aeroplane_chess.py`
4. Deploy to Streamlit Community Cloud: 
   - Push to GitHub repository
   - Go to share.streamlit.io and connect your repo
""")
