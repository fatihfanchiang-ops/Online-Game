import streamlit as st
import numpy as np
import time
import json

# ====================== Configuration (2D Only) ======================
GAME_CONFIG = {
    "window": {"width": 800, "height": 500},  # Optimized for Streamlit display
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
        "power_meter": {"width": 200, "height": 25, "y_pos": 30},
        "hit_feedback": {"scale": 1.2, "color": "#ffdd00", "duration": 0.1}
    },
    "levels": [
        {"tee": (80, 250), "hole": (700, 250), "obstacles": [(400, 200, 80, 80)], "par": 3},
        {"tee": (80, 100), "hole": (700, 400), "obstacles": [(250, 150, 60, 60), (500, 250, 100, 60)], "par": 4},
        {"tee": (80, 400), "hole": (700, 100), "obstacles": [(200, 200, 70, 70), (400, 100, 80, 80), (550, 300, 70, 70)], "par": 5},
    ]
}

# ====================== Initial Setup ======================
st.set_page_config(
    page_title="2D Golf Game",
    layout="centered",  # Changed from wide to centered for better display
    initial_sidebar_state="collapsed",
)

# Custom CSS for perfect screen display
hide_st_style = """
    <style>
    /* Hide default Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Main container styling */
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    
    /* Game container - responsive and properly sized */
    .game-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        height: 500px;
        background-color: #8CC051;
        border: 3px solid #6A9030;
        border-radius: 10px;
        overflow: hidden;
        margin: 0 auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Obstacles (sand traps) */
    .obstacle {
        position: absolute;
        background-color: #F4D35E;
        border: 2px solid #E0C040;
        border-radius: 4px;
    }
    
    /* Hole */
    .hole {
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #3A2E1F;
        border: 2px solid #2A1F10;
        transform: translate(-50%, -50%);
        box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
    }
    
    /* Golf ball */
    .ball {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: white;
        border: 1px solid black;
        transform: translate(-50%, -50%);
        z-index: 10;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Ball hit feedback */
    .ball-feedback {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ffdd00;
        border: 1px solid black;
        transform: translate(-50%, -50%);
        z-index: 10;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Power meter */
    .power-meter {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 200px;
        height: 25px;
        background-color: #ecf0f1;
        border: 2px solid #bdc3c7;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .power-fill {
        height: 100%;
        width: 0%;
        transition: width 0.1s linear;
        border-radius: 13px;
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
        background-color: rgba(255,255,255,0.8);
        padding: 2px 10px;
        border-radius: 10px;
    }
    
    /* Game info display */
    .game-info {
        position: absolute;
        top: 15px;
        left: 50%;
        transform: translateX(-50%);
        background-color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        z-index: 20;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        text-align: center;
    }
    
    /* Responsive adjustments for mobile */
    @media (max-width: 768px) {{
        .game-container {{
            height: 400px;
            border-radius: 8px;
        }}
        .game-info {{
            font-size: 12px;
            padding: 6px 15px;
            top: 10px;
        }}
        .power-meter {{
            width: 180px;
            height: 20px;
        }}
        .power-text {{
            font-size: 12px;
        }}
    }}
    
    @media (max-width: 480px) {{
        .game-container {{
            height: 300px;
        }}
        .game-info {{
            font-size: 11px;
            padding: 5px 10px;
            width: 90%;
        }}
        .power-meter {{
            width: 150px;
        }}
    }}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# ====================== Game State Initialization ======================
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "level": 0,
        "ball_pos": list(GAME_CONFIG["levels"][0]["tee"]),
        "hole_pos": list(GAME_CONFIG["levels"][0]["hole"]),
        "obstacles": GAME_CONFIG["levels"][0]["obstacles"],
        "par": GAME_CONFIG["levels"][0]["par"],
        "strokes": 0,
        "current_power": 0.0,
        "ball_velocity": [0.0, 0.0],
        "is_rolling": False,
        "level_complete": False,
        "last_update": time.time(),
        "wind": float(np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"])),
        "hit_feedback": False,
        "hit_feedback_start": 0.0,
        "flash_state": False,
        "progress": {"completed_levels": []}
    }

# ====================== Core Game Functions ======================
def reset_level(level_idx):
    """Reset game state for specified level"""
    gs = st.session_state.game_state
    
    if level_idx > 0 and level_idx - 1 not in gs["progress"]["completed_levels"]:
        gs["progress"]["completed_levels"].append(level_idx - 1)
    
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

def calculate_distance(pos1, pos2):
    """Calculate distance between two points"""
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

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
    return calculate_distance(pos, hole_pos) < (hole_radius + ball_radius)

def update_ball():
    """Update ball position with 2D physics"""
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

# ====================== Game Rendering ======================
def render_game():
    """Render game with perfect screen display"""
    gs = st.session_state.game_state
    
    # Main game container
    st.markdown('<div class="game-container" id="game-container">', unsafe_allow_html=True)
    
    # Render obstacles (sand traps)
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
    
    # Render ball with hit feedback
    ball_x, ball_y = gs["ball_pos"]
    if gs["hit_feedback"]:
        if time.time() - gs["hit_feedback_start"] > GAME_CONFIG["visuals"]["hit_feedback"]["duration"]:
            gs["hit_feedback"] = False
            st.markdown(
                f'<div class="ball" style="left: {ball_x}px; top: {ball_y}px;"></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="ball-feedback" style="left: {ball_x}px; top: {ball_y}px;"></div>',
                unsafe_allow_html=True
            )
    else:
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
    
    # Game info display
    info_text = []
    info_text.append(f"Level: {gs['level']+1} | Strokes: {gs['strokes']} | Par: {gs['par']}")
    info_text.append(f"Wind: {gs['wind']:.1f} m/s")
    
    if gs["level_complete"]:
        info_text[0] = f"Level {gs['level']+1} Complete! | Strokes: {gs['strokes']} (Par: {gs['par']})"
        info_text.append("🎉 Hole in! 🎉")
    
    st.markdown(
        f'<div class="game-info">{" | ".join(info_text)}</div>',
        unsafe_allow_html=True
    )
    
    # Close game container
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== Main Game Logic ======================
def main():
    # Set page title
    st.title("🏌️ 2D Golf Game")
    
    gs = st.session_state.game_state
    current_time = time.time()
    
    # Game update loop (60fps)
    UPDATE_INTERVAL = 1 / 60
    if current_time - gs["last_update"] >= UPDATE_INTERVAL:
        if gs["is_rolling"]:
            update_ball()
        
        # Flash effect for high power
        if gs["current_power"] > 90:
            gs["flash_state"] = not gs["flash_state"]
        
        gs["last_update"] = current_time
    
    # Render the game with perfect screen layout
    render_game()
    
    # Game controls in a clean layout
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Game Controls")
        st.write("Adjust the sliders to aim and set power for your shot!")
        
        # Game control sliders (responsive)
        if not gs["is_rolling"] and not gs["level_complete"]:
            col_slider1, col_slider2 = st.columns(2)
            
            with col_slider1:
                power = st.slider("Shot Power", 0, 100, 50, key="power", 
                                 help="0 = soft, 100 = maximum power")
                direction_x = st.slider("Horizontal Direction", -10, 10, 5, key="dir_x",
                                       help="-10 = left, 10 = right")
            
            with col_slider2:
                direction_y = st.slider("Vertical Direction", -10, 10, 0, key="dir_y",
                                       help="-10 = up, 10 = down")
                wind_info = st.info(f"Current Wind: {gs['wind']:.1f} m/s (affects horizontal movement)")
            
            # Hit ball button
            if st.button("⛳ Hit Ball", use_container_width=True, type="primary"):
                gs["current_power"] = power
                power_scaled = power / 100 * 10
                gs["ball_velocity"] = [
                    direction_x * power_scaled / 10,
                    direction_y * power_scaled / 10
                ]
                gs["is_rolling"] = True
                gs["strokes"] += 1
                gs["hit_feedback"] = True
                gs["hit_feedback_start"] = time.time()
        
        # Level completion
        if gs["level_complete"]:
            st.success(f"🏆 Level {gs['level']+1} Completed!")
            st.write(f"You took {gs['strokes']} strokes (Par: {gs['par']})")
            
            col_buttons = st.columns(2)
            with col_buttons[0]:
                if gs["level"] < len(GAME_CONFIG["levels"])-1:
                    if st.button("▶️ Next Level", use_container_width=True):
                        reset_level(gs["level"] + 1)
                else:
                    st.balloons()
                    st.success("🎊 Congratulations! You completed all levels! 🎊")
            
            with col_buttons[1]:
                if st.button("🔄 Play Again", use_container_width=True):
                    reset_level(0)
    
    with col2:
        # Game info and actions
        st.subheader("Game Actions")
        
        # Reset ball button
        if st.button("🔙 Reset Ball to Tee", use_container_width=True):
            gs["ball_pos"] = list(GAME_CONFIG["levels"][gs["level"]]["tee"])
            gs["ball_velocity"] = [0.0, 0.0]
            gs["is_rolling"] = False
        
        # Level selector
        st.subheader("Level Selector")
        level_options = [f"Level {i+1}" for i in range(len(GAME_CONFIG["levels"]))]
        selected_level = st.selectbox("Jump to Level", level_options, index=gs["level"])
        
        if st.button("Go to Level", use_container_width=True):
            new_level = int(selected_level.split()[1]) - 1
            reset_level(new_level)
        
        # Game stats
        st.subheader("Game Stats")
        st.write(f"Completed Levels: {len(gs['progress']['completed_levels'])}/{len(GAME_CONFIG['levels'])}")
        st.write(f"Total Strokes: {gs['strokes']}")
        
    # Auto-rerun to update game state
    st.experimental_rerun()

# ====================== Run Game ======================
if __name__ == "__main__":
    main()
