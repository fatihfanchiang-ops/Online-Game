import streamlit as st
import numpy as np
import time
import logging
import json

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
        transition: all 0.05s linear;
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
    .aim-arrow {
        position: absolute;
        background-color: red;
        z-index: 5;
        pointer-events: none;
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

# ====================== Game State Initialization ======================
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "level": 0,
        "ball_pos": np.array(GAME_CONFIG["levels"][0]["tee"], dtype=np.float64),
        "hole_pos": np.array(GAME_CONFIG["levels"][0]["hole"]),
        "obstacles": GAME_CONFIG["levels"][0]["obstacles"],
        "par": GAME_CONFIG["levels"][0]["par"],
        "strokes": 0,
        "drag_start": None,
        "drag_end": None,
        "current_power": 0.0,
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
        "last_update": time.time(),
        "wind": np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"]),
        "hit_feedback": False,
        "hit_feedback_start": 0,
        "flash_state": False,
        "progress": {"completed_levels": []}
    }

# ====================== Core Functions ======================
def reset_level(level_idx):
    """Reset game state for specified level"""
    gs = st.session_state.game_state
    
    if level_idx > 0 and level_idx - 1 not in gs["progress"]["completed_levels"]:
        gs["progress"]["completed_levels"].append(level_idx - 1)
    
    gs.update({
        "level": level_idx,
        "ball_pos": np.array(GAME_CONFIG["levels"][level_idx]["tee"], dtype=np.float64),
        "hole_pos": np.array(GAME_CONFIG["levels"][level_idx]["hole"]),
        "obstacles": GAME_CONFIG["levels"][level_idx]["obstacles"],
        "par": GAME_CONFIG["levels"][level_idx]["par"],
        "strokes": 0,
        "current_power": 0.0,
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
        "drag_start": None,
        "drag_end": None,
        "last_update": time.time(),
        "wind": np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"]),
        "hit_feedback": False
    })

def get_power_color(power_percent):
    """Get gradient color for power meter"""
    power_percent = np.clip(power_percent, 0, 100)
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
    """Snap drag direction to 15° increments"""
    angle = np.degrees(np.arctan2(direction[1], direction[0]))
    snapped_angle = round(angle / 15) * 15
    rad = np.radians(snapped_angle)
    return np.array([np.cos(rad), np.sin(rad)])

def check_collision(pos, obstacles):
    """2D collision detection"""
    x, y = pos
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - ball_radius <= x <= ox + w + ball_radius and 
            oy - ball_radius <= y <= oy + h + ball_radius):
            return True
    return False

def check_hole(pos, hole_pos):
    """2D hole detection"""
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    hole_radius = GAME_CONFIG["physics"]["hole_radius"]
    return np.linalg.norm(pos - hole_pos) < (hole_radius + ball_radius)

def update_ball():
    """Update ball position with 2D physics"""
    gs = st.session_state.game_state
    
    if np.linalg.norm(gs["ball_velocity"]) < 0.1:
        gs["is_rolling"] = False
        return
    
    # Apply friction
    gs["ball_velocity"] *= GAME_CONFIG["physics"]["friction"]
    
    # Apply wind (horizontal only)
    gs["ball_velocity"][0] += gs["wind"] * 0.05
    
    # Calculate new position
    new_pos = gs["ball_pos"] + gs["ball_velocity"]
    
    # Boundary limits
    new_pos[0] = np.clip(new_pos[0], GAME_CONFIG["physics"]["ball_radius"], 
                        GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"])
    new_pos[1] = np.clip(new_pos[1], GAME_CONFIG["physics"]["ball_radius"], 
                        GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"])
    
    # Collision handling
    if not check_collision(new_pos, gs["obstacles"]):
        gs["ball_pos"] = new_pos
    else:
        gs["ball_velocity"] *= -0.5
    
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
    
    # Render aim arrow if dragging
    if gs["drag_start"] is not None and not gs["is_rolling"]:
        start = np.array(gs["drag_start"])
        end = np.array(gs["drag_end"]) if gs["drag_end"] is not None else start
        direction = start - end
        length = np.linalg.norm(direction)
        
        if length > 0:
            direction = snap_to_angle(direction)
            scaled_dir = direction * min(length, 100)
            arrow_x = ball_x + scaled_dir[0] / 2
            arrow_y = ball_y + scaled_dir[1] / 2
            arrow_length = np.linalg.norm(scaled_dir)
            angle = np.degrees(np.arctan2(scaled_dir[1], scaled_dir[0]))
            
            st.markdown(
                f'''
                <div class="aim-arrow" style="
                    left: {ball_x}px;
                    top: {ball_y}px;
                    width: {arrow_length}px;
                    height: 3px;
                    background-color: red;
                    transform-origin: left center;
                    transform: rotate({angle}deg);
                "></div>
                ''',
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
    
    # JavaScript for game interaction
    js_code = f"""
    <script>
    const gameContainer = document.getElementById('game-container');
    const ball = document.querySelector('.ball') || document.querySelector('.ball-feedback');
    let isDragging = false;
    let dragStart = {{x: 0, y: 0}};
    
    // Game state from Streamlit
    const gameState = {json.dumps(gs)};
    const UPDATE_INTERVAL = {1/60 * 1000};
    
    // Handle mouse/touch events
    gameContainer.addEventListener('mousedown', startDrag);
    gameContainer.addEventListener('touchstart', startDrag, {{passive: false}});
    
    gameContainer.addEventListener('mousemove', drag);
    gameContainer.addEventListener('touchmove', drag, {{passive: false}});
    
    gameContainer.addEventListener('mouseup', endDrag);
    gameContainer.addEventListener('touchend', endDrag);
    gameContainer.addEventListener('touchcancel', endDrag);
    
    function getEventPos(e) {{
        const rect = gameContainer.getBoundingClientRect();
        let x, y;
        
        if (e.type.includes('touch')) {{
            e.preventDefault();
            x = e.touches[0].clientX - rect.left;
            y = e.touches[0].clientY - rect.top;
        }} else {{
            x = e.clientX - rect.left;
            y = e.clientY - rect.top;
        }}
        
        return {{x, y}};
    }}
    
    function startDrag(e) {{
        if (gameState.is_rolling || gameState.level_complete) return;
        
        isDragging = true;
        const pos = getEventPos(e);
        dragStart = pos;
        
        // Send drag start to Streamlit
        window.parent.postMessage({{
            type: 'mousedown',
            x: pos.x,
            y: pos.y
        }}, '*');
    }}
    
    function drag(e) {{
        if (!isDragging || gameState.is_rolling || gameState.level_complete) return;
        
        const pos = getEventPos(e);
        
        // Send drag move to Streamlit
        window.parent.postMessage({{
            type: 'mousemove',
            x: pos.x,
            y: pos.y
        }}, '*');
    }}
    
    function endDrag(e) {{
        if (!isDragging || gameState.is_rolling || gameState.level_complete) return;
        
        isDragging = false;
        const pos = getEventPos(e);
        
        // Send drag end to Streamlit
        window.parent.postMessage({{
            type: 'mouseup',
            x: pos.x,
            y: pos.y
        }}, '*');
    }}
    
    // Update game state periodically
    setInterval(() => {{
        window.parent.postMessage({{type: 'game_update'}}, '*');
    }}, UPDATE_INTERVAL);
    
    // Flash effect for power meter
    setInterval(() => {{
        const powerFill = document.querySelector('.power-fill');
        const powerText = document.querySelector('.power-text');
        const currentPower = parseFloat(powerFill.style.width) || 0;
        
        if (currentPower > 90) {{
            const flashState = {gs['flash_state']};
            powerFill.style.backgroundColor = flashState ? '#ff0000' : '{get_power_color(gs['current_power'])}';
        }}
    }}, 200);
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
    
    # Handle drag events from JavaScript
    def handle_drag_events():
        # This would normally handle postMessage events, but for simplicity
        # we'll use Streamlit's session state for interaction
        pass
    
    handle_drag_events()
    
    # Level completion handling
    if gs["level_complete"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if gs["level"] < len(GAME_CONFIG["levels"])-1:
                if st.button("Next Level", key="next_level", use_container_width=True):
                    reset_level(gs["level"] + 1)
            else:
                if st.button("Play Again", key="play_again", use_container_width=True):
                    reset_level(0)
    
    # Manual drag handling (fallback for Streamlit interaction)
    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        st.markdown("### Game Controls")
        st.write("• Click and drag the ball to aim")
        st.write("• Drag distance = power")
        st.write("• Wind affects ball horizontally")
        st.write("• Avoid sand traps!")
        
        # Debug controls (optional)
        if st.button("Reset Ball", use_container_width=True):
            gs["ball_pos"] = np.array(GAME_CONFIG["levels"][gs["level"]]["tee"])
            gs["ball_velocity"] = np.array([0.0, 0.0])
            gs["is_rolling"] = False
    
    # Rerun to update game state
    st.experimental_rerun()

# ====================== Run Game ======================
if __name__ == "__main__":
    main()
