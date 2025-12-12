import streamlit as st
import numpy as np
import time
import json

# ====================== Custom JSON Encoder for Numpy Types ======================
class NumpyEncoder(json.JSONEncoder):
    """Custom encoder to handle numpy types for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        return super(NumpyEncoder, self).default(obj)

# ====================== Configuration (2D Only) ======================
GAME_CONFIG = {
    "window": {"width": 1200, "height": 600},
    "physics": {
        "friction": 0.98,
        "max_power": 100,
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-3, 3)
    },
    "visuals": {
        "colors": {
            "green": "#8CC051",
            "sand": "#F4D35E",
            "sand_border": "#E0C040",
            "hole": "#3A2E1F",
            "hole_border": "#2A1F10",
            "ball": "white",
            "ball_border": "black",
            "power_meter": {0: "#3498db", 50: "#f1c40f", 80: "#e74c3c", 100: "#c0392b"}
        },
        "power_meter": {"width": 300, "height": 30, "y_pos": 50},
        "hit_feedback": {"scale": 1.2, "color": "#ffdd00", "duration": 0.1}
    },
    "levels": [
        {"tee": (100, 300), "hole": (1000, 300), "obstacles": [(500, 200, 100, 100)], "par": 3},
        {"tee": (100, 100), "hole": (900, 500), "obstacles": [(300, 300, 80, 80), (600, 200, 120, 120)], "par": 4},
        {"tee": (100, 500), "hole": (1100, 100), "obstacles": [(200, 200, 60, 60), (400, 400, 90, 90), (700, 300, 70, 70)], "par": 5},
    ]
}

# ====================== Initial Setup ======================
st.set_page_config(
    page_title="2D Golf Game",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide default Streamlit UI
hide_st_style = """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 1rem !important;}
    .game-container {
        position: relative;
        width: 100%;
        height: 600px;
        background-color: #8CC051;
        border: 1px solid #6A9030;
        overflow: hidden;
    }
    .obstacle {
        position: absolute;
        background-color: #F4D35E;
        border: 2px solid #E0C040;
    }
    .hole {
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #3A2E1F;
        border: 2px solid #2A1F10;
        transform: translate(-50%, -50%);
    }
    .ball {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: white;
        border: 1px solid black;
        transform: translate(-50%, -50%);
        z-index: 10;
    }
    .ball-feedback {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ffdd00;
        border: 1px solid black;
        transform: translate(-50%, -50%);
        z-index: 10;
    }
    .power-meter {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 30px;
        background-color: #ecf0f1;
        border: 2px solid #bdc3c7;
        border-radius: 5px;
        overflow: hidden;
    }
    .power-fill {
        height: 100%;
        width: 0%;
        transition: width 0.1s linear;
    }
    .power-text {
        position: absolute;
        bottom: 25px;
        left: 50%;
        transform: translateX(-50%);
        color: black;
        font-weight: bold;
        font-size: 14px;
        z-index: 15;
    }
    .game-info {
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        z-index: 20;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# ====================== Game State Initialization (Use Python Lists Instead of Numpy Arrays) ======================
if "game_state" not in st.session_state:
    # Use standard Python lists instead of numpy arrays for JSON compatibility
    st.session_state.game_state = {
        "level": 0,
        "ball_pos": list(GAME_CONFIG["levels"][0]["tee"]),  # [x, y] as list
        "hole_pos": list(GAME_CONFIG["levels"][0]["hole"]),  # [x, y] as list
        "obstacles": GAME_CONFIG["levels"][0]["obstacles"],
        "par": GAME_CONFIG["levels"][0]["par"],
        "strokes": 0,
        "drag_start": None,
        "drag_end": None,
        "current_power": 0.0,
        "ball_velocity": [0.0, 0.0],  # [x, y] velocity as list
        "is_rolling": False,
        "level_complete": False,
        "last_update": time.time(),
        "wind": float(np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"])),
        "hit_feedback": False,
        "hit_feedback_start": 0.0,
        "flash_state": False,
        "progress": {"completed_levels": []}
    }

# ====================== Core Functions ======================
def reset_level(level_idx):
    """Reset game state for specified level"""
    gs = st.session_state.game_state
    
    if level_idx > 0 and level_idx - 1 not in gs["progress"]["completed_levels"]:
        gs["progress"]["completed_levels"].append(level_idx - 1)
    
    # Use lists instead of numpy arrays for JSON compatibility
    gs.update({
        "level": level_idx,
        "ball_pos": list(GAME_CONFIG["levels"][level_idx]["tee"]),
        "hole_pos": list(GAME_CONFIG["levels"][level_idx]["hole"]),
        "obstacles": GAME_CONFIG["levels"][level_idx]["obstacles"],
        "par": GAME_CONFIG["levels"][level_idx]["par"],
        "strokes": 0,
        "current_power": 0.0,
        "ball_velocity": [0.0, 0.0],
        "is_rolling": False,
        "level_complete": False,
        "drag_start": None,
        "drag_end": None,
        "last_update": time.time(),
        "wind": float(np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"])),
        "hit_feedback": False
    })

def get_power_color(power_percent):
    """Get gradient color for power meter"""
    power_percent = max(0.0, min(100.0, power_percent))
    colors = GAME_CONFIG["visuals"]["colors"]["power_meter"]
    sorted_stops = sorted(colors.items())
    
    if power_percent == 100:
        return colors[100]
    if power_percent == 0:
        return colors[0]
    
    for i, (stop, color) in enumerate(sorted_stops[:-1]):
        next_stop, next_color = sorted_stops[i+1]
        if stop <= power_percent < next_stop:
            ratio = (power_percent - stop) / (next_stop - stop)
            r1, g1, b1 = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
            r2, g2, b2 = int(next_color[1:3],16), int(next_color[3:5],16), int(next_color[5:7],16)
            
            r = int(r1 + ratio * (r2 - r1))
            g = int(g1 + ratio * (g2 - g1))
            b = int(b1 + ratio * (b2 - b1))
            return f"#{r:02x}{g:02x}{b:02x}"
    return colors[100]

def snap_to_angle(direction):
    """Snap drag direction to 15° increments (using lists instead of numpy)"""
    dx, dy = direction
    angle = np.degrees(np.arctan2(dy, dx))
    snapped_angle = round(angle / 15) * 15
    rad = np.radians(snapped_angle)
    return [np.cos(rad), np.sin(rad)]

def calculate_distance(pos1, pos2):
    """Calculate distance between two points (list format)"""
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def check_collision(pos, obstacles):
    """2D collision detection (using lists)"""
    x, y = pos
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - ball_radius <= x <= ox + w + ball_radius and 
            oy - ball_radius <= y <= oy + h + ball_radius):
            return True
    return False

def check_hole(pos, hole_pos):
    """2D hole detection (using lists)"""
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    hole_radius = GAME_CONFIG["physics"]["hole_radius"]
    return calculate_distance(pos, hole_pos) < (hole_radius + ball_radius)

def update_ball():
    """Update ball position with 2D physics (using lists instead of numpy arrays)"""
    gs = st.session_state.game_state
    
    # Check if ball has stopped rolling
    velocity_magnitude = calculate_distance(gs["ball_velocity"], [0, 0])
    if velocity_magnitude < 0.1:
        gs["is_rolling"] = False
        return
    
    # Apply friction
    gs["ball_velocity"][0] *= GAME_CONFIG["physics"]["friction"]
    gs["ball_velocity"][1] *= GAME_CONFIG["physics"]["friction"]
    
    # Apply wind (horizontal only)
    gs["ball_velocity"][0] += gs["wind"] * 0.05
    
    # Calculate new position
    new_pos = [
        gs["ball_pos"][0] + gs["ball_velocity"][0],
        gs["ball_pos"][1] + gs["ball_velocity"][1]
    ]
    
    # Boundary limits
    new_pos[0] = max(GAME_CONFIG["physics"]["ball_radius"], 
                    min(new_pos[0], GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"]))
    new_pos[1] = max(GAME_CONFIG["physics"]["ball_radius"], 
                    min(new_pos[1], GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"]))
    
    # Collision handling
    if not check_collision(new_pos, gs["obstacles"]):
        gs["ball_pos"] = new_pos
    else:
        # Reverse velocity on collision
        gs["ball_velocity"][0] *= -0.5
        gs["ball_velocity"][1] *= -0.5
    
    # Hole detection
    if check_hole(gs["ball_pos"], gs["hole_pos"]):
        gs["level_complete"] = True
        gs["is_rolling"] = False

# ====================== Main Game Rendering ======================
def render_game():
    """Render game using native Streamlit/HTML (no matplotlib)"""
    gs = st.session_state.game_state
    
    # Game container
    st.markdown('<div class="game-container" id="game-container">', unsafe_allow_html=True)
    
    # Render obstacles
    for i, (ox, oy, w, h) in enumerate(gs["obstacles"]):
        st.markdown(
            f'<div class="obstacle" style="left: {ox}px; top: {oy}px; width: {w}px; height: {h}px;"></div>',
            unsafe_allow_html=True
        )
    
    # Render hole
    hole_x, hole_y = gs["hole_pos"]
    st.markdown(
        f'<div class="hole" style="left: {hole_x}px; top: {hole_y}px;"></div>',
        unsafe_allow_html=True
    )
    
    # Render ball (with feedback effect)
    ball_x, ball_y = gs["ball_pos"]
    if gs["hit_feedback"]:
        # Check if feedback duration expired
        if time.time() - gs["hit_feedback_start"] > GAME_CONFIG["visuals"]["hit_feedback"]["duration"]:
            gs["hit_feedback"] = False
            # Normal ball
            st.markdown(
                f'<div class="ball" style="left: {ball_x}px; top: {ball_y}px;"></div>',
                unsafe_allow_html=True
            )
        else:
            # Feedback ball
            st.markdown(
                f'<div class="ball-feedback" style="left: {ball_x}px; top: {ball_y}px;"></div>',
                unsafe_allow_html=True
            )
    else:
        # Normal ball
        st.markdown(
            f'<div class="ball" style="left: {ball_x}px; top: {ball_y}px;"></div>',
            unsafe_allow_html=True
        )
    
    # Render power meter
    power_color = "#ff0000" if (gs["current_power"] > 90 and gs["flash_state"]) else get_power_color(gs["current_power"])
    st.markdown(
        f'''
        <div class="power-meter">
            <div class="power-fill" style="width: {gs['current_power']}%; background-color: {power_color};"></div>
        </div>
        <div class="power-text">Power: {int(gs['current_power'])}%</div>
        ''',
        unsafe_allow_html=True
    )
    
    # Game info text
    info_text = []
    info_text.append(f"Level: {gs['level']+1} | Strokes: {gs['strokes']} | Par: {gs['par']}")
    info_text.append(f"Wind: {gs['wind']:.1f} m/s")
    info_text.append(f"Completed Levels: {len(gs['progress']['completed_levels'])}")
    
    if gs["level_complete"]:
        info_text[0] += f" | Completed! (Par {gs['par']}, You: {gs['strokes']})"
        info_text[0] += " | Next Level →" if gs["level"] < len(GAME_CONFIG["levels"])-1 else " | Game Complete!"
    
    st.markdown(
        f'<div class="game-info">{" | ".join(info_text)}</div>',
        unsafe_allow_html=True
    )
    
    # Close game container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Safe JSON serialization (using our custom encoder)
    game_state_serialized = json.dumps(gs, cls=NumpyEncoder)
    
    # JavaScript for game interaction (simplified for Streamlit compatibility)
    js_code = f"""
    <script>
    const gameContainer = document.getElementById('game-container');
    let isDragging = false;
    let dragStart = {{x: 0, y: 0}};
    
    // Game state (safely serialized)
    const gameState = {game_state_serialized};
    const UPDATE_INTERVAL = {1/60 * 1000};
    
    // Get ball element
    function getBallElement() {{
        return document.querySelector('.ball') || document.querySelector('.ball-feedback');
    }}
    
    // Handle mouse down/touch start
    gameContainer.addEventListener('mousedown', function(e) {{
        if (gameState.is_rolling || gameState.level_complete) return;
        
        isDragging = true;
        const rect = gameContainer.getBoundingClientRect();
        dragStart = {{
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        }};
        
        // Send drag start to Streamlit (via rerun)
        window.parent.postMessage({{
            type: 'drag_start',
            x: dragStart.x,
            y: dragStart.y
        }}, '*');
    }});
    
    // Handle mouse move/touch move
    gameContainer.addEventListener('mousemove', function(e) {{
        if (!isDragging || gameState.is_rolling || gameState.level_complete) return;
        
        const rect = gameContainer.getBoundingClientRect();
        const currentPos = {{
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        }};
        
        // Calculate drag distance for power
        const dx = dragStart.x - currentPos.x;
        const dy = dragStart.y - currentPos.y;
        const distance = Math.sqrt(dx*dx + dy*dy);
        const power = Math.min(distance / {GAME_CONFIG["physics"]["max_power"]} * 100, 100);
        
        // Update power meter visually
        const powerFill = document.querySelector('.power-fill');
        const powerText = document.querySelector('.power-text');
        if (powerFill && powerText) {{
            powerFill.style.width = power + '%';
            powerText.textContent = `Power: ${{Math.round(power)}}%`;
            
            // Update color
            if (power > 90) {{
                powerFill.style.backgroundColor = gameState.flash_state ? '#ff0000' : '{get_power_color(gs['current_power'])}';
            }} else {{
                powerFill.style.backgroundColor = '{get_power_color(gs['current_power'])}';
            }}
        }}
        
        // Send drag move to Streamlit
        window.parent.postMessage({{
            type: 'drag_move',
            x: currentPos.x,
            y: currentPos.y,
            power: power
        }}, '*');
    }});
    
    // Handle mouse up/touch end
    gameContainer.addEventListener('mouseup', function(e) {{
        if (!isDragging || gameState.is_rolling || gameState.level_complete) return;
        
        isDragging = false;
        const rect = gameContainer.getBoundingClientRect();
        const endPos = {{
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        }};
        
        // Calculate shot power and direction
        const dx = dragStart.x - endPos.x;
        const dy = dragStart.y - endPos.y;
        const distance = Math.sqrt(dx*dx + dy*dy);
        const power = Math.min(distance / {GAME_CONFIG["physics"]["max_power"]} * 10, 10);
        
        // Send shot command to Streamlit
        window.parent.postMessage({{
            type: 'shot',
            dx: dx,
            dy: dy,
            power: power
        }}, '*');
        
        // Reset power meter
        const powerFill = document.querySelector('.power-fill');
        const powerText = document.querySelector('.power-text');
        if (powerFill && powerText) {{
            powerFill.style.width = '0%';
            powerText.textContent = 'Power: 0%';
        }}
    }});
    
    // Update game state periodically
    setInterval(() => {{
        window.parent.postMessage({{type: 'game_update'}}, '*');
    }}, UPDATE_INTERVAL);
    </script>
    """
    st.components.v1.html(js_code, height=0)

# ====================== Main Game Logic ======================
def main():
    gs = st.session_state.game_state
    current_time = time.time()
    
    # Game update loop (60fps)
    UPDATE_INTERVAL = 1 / 60
    if current_time - gs["last_update"] >= UPDATE_INTERVAL:
        # Update ball physics if rolling
        if gs["is_rolling"]:
            update_ball()
        
        # Toggle flash state for power meter
        if gs["current_power"] > 90:
            gs["flash_state"] = not gs["flash_state"]
        
        gs["last_update"] = current_time
    
    # Render game
    render_game()
    
    # Handle shot from user input (simplified for Streamlit)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Manual shot control (works around Streamlit's interaction model)
        if not gs["is_rolling"] and not gs["level_complete"]:
            st.markdown("### Take a Shot")
            power = st.slider("Power", 0, 100, 50, key=f"power_slider_{gs['strokes']}")
            direction_x = st.slider("Direction X", -10, 10, 5, key=f"dir_x_{gs['strokes']}")
            direction_y = st.slider("Direction Y", -10, 10, 0, key=f"dir_y_{gs['strokes']}")
            
            if st.button("Hit Ball", use_container_width=True):
                # Calculate velocity based on power and direction
                power_scaled = power / 100 * 10
                gs["ball_velocity"] = [
                    direction_x * power_scaled / 10,
                    direction_y * power_scaled / 10
                ]
                gs["is_rolling"] = True
                gs["strokes"] += 1
                gs["hit_feedback"] = True
                gs["hit_feedback_start"] = time.time()
        
        # Level completion handling
        if gs["level_complete"]:
            st.success(f"Level {gs['level']+1} Complete!")
            if gs["level"] < len(GAME_CONFIG["levels"])-1:
                if st.button("Next Level", use_container_width=True):
                    reset_level(gs["level"] + 1)
            else:
                st.balloons()
                st.success("Congratulations! You completed all levels!")
                if st.button("Play Again", use_container_width=True):
                    reset_level(0)
        
        # Game controls
        st.markdown("### Game Controls")
        st.write("• Use sliders to set power and direction")
        st.write("• Click 'Hit Ball' to shoot")
        st.write("• Wind affects ball horizontally")
        st.write("• Avoid sand traps!")
        
        # Reset button
        if st.button("Reset Ball to Tee", use_container_width=True):
            gs["ball_pos"] = list(GAME_CONFIG["levels"][gs["level"]]["tee"])
            gs["ball_velocity"] = [0.0, 0.0]
            gs["is_rolling"] = False
    
    # Auto-rerun to update game state
    st.experimental_rerun()

# ====================== Run Game ======================
if __name__ == "__main__":
    main()
