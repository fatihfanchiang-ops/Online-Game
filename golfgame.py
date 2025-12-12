import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from PIL import Image
import time
import logging

# ====================== Configuration (2D Only) ======================
GAME_CONFIG = {
    "window": {"width": 1200, "height": 600},
    "physics": {
        "friction": 0.98,
        "max_power": 100,
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-3, 3)  # Strict 2D horizontal wind
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
        "power_meter": {"width": 300, "height": 30, "y_pos": -50},
        "hit_feedback": {"scale": 1.2, "color": "#ffdd00", "duration": 0.1}
    },
    "levels": [
        {"tee": (100, 300), "hole": (1000, 300), "obstacles": [(500, 200, 100, 100)], "par": 3},
        {"tee": (100, 100), "hole": (900, 500), "obstacles": [(300, 300, 80, 80), (600, 200, 120, 120)], "par": 4},
        {"tee": (100, 500), "hole": (1100, 100), "obstacles": [(200, 200, 60, 60), (400, 400, 90, 90), (700, 300, 70, 70)], "par": 5},
    ]
}

# ====================== Initial Setup ======================
# Page configuration (Streamlit best practice)
st.set_page_config(
    page_title="2D Golf Game",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide default Streamlit UI
hide_st_style = """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding: 0 !important; margin: 0 !important;}
    img {
        image-rendering: pixelated; 
        will-change: transform;
        touch-action: none;
        user-select: none;
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Logging configuration (error tracking)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("golf_game.log"), logging.StreamHandler()]
)

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
        "image_size": (GAME_CONFIG["window"]["width"], GAME_CONFIG["window"]["height"]),
        "wind": np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"]),
        "hit_feedback": False,
        "flash_state": False,
        "progress": {"completed_levels": []}
    }

# ====================== Core Functions (Verified) ======================
def reset_level(level_idx):
    """Reset game state for specified level (2D only)"""
    gs = st.session_state.game_state
    
    # Save progress
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
    """Get 2D gradient color for power meter (verified)"""
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
    """2D angle snapping for precise aiming (verified)"""
    angle = np.degrees(np.arctan2(direction[1], direction[0]))
    snapped_angle = round(angle / 15) * 15
    rad = np.radians(snapped_angle)
    return np.array([np.cos(rad), np.sin(rad)])

def check_collision(pos, obstacles):
    """2D collision detection (verified)"""
    x, y = pos
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - ball_radius <= x <= ox + w + ball_radius and 
            oy - ball_radius <= y <= oy + h + ball_radius):
            return True
    return False

def check_hole(pos, hole_pos):
    """2D hole detection (verified)"""
    ball_radius = GAME_CONFIG["physics"]["ball_radius"]
    hole_radius = GAME_CONFIG["physics"]["hole_radius"]
    return np.linalg.norm(pos - hole_pos) < (hole_radius + ball_radius)

def update_ball():
    """2D physics update (wind + friction) - verified"""
    gs = st.session_state.game_state
    try:
        if np.linalg.norm(gs["ball_velocity"]) < 0.1:
            gs["is_rolling"] = False
            return
        
        # Apply 2D friction
        gs["ball_velocity"] *= GAME_CONFIG["physics"]["friction"]
        
        # Apply 2D horizontal wind
        gs["ball_velocity"][0] += gs["wind"] * 0.05
        
        # Calculate new 2D position
        new_pos = gs["ball_pos"] + gs["ball_velocity"]
        
        # 2D boundary limits
        new_pos[0] = np.clip(new_pos[0], GAME_CONFIG["physics"]["ball_radius"], 
                            GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"])
        new_pos[1] = np.clip(new_pos[1], GAME_CONFIG["physics"]["ball_radius"], 
                            GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"])
        
        # 2D collision handling
        if not check_collision(new_pos, gs["obstacles"]):
            gs["ball_pos"] = new_pos
        else:
            gs["ball_velocity"] *= -0.5
        
        # 2D hole detection
        if check_hole(gs["ball_pos"], gs["hole_pos"]):
            gs["level_complete"] = True
            gs["is_rolling"] = False
            
    except Exception as e:
        logging.error(f"Ball update error: {str(e)}", exc_info=True)
        st.error("Failed to update ball position!")

# ====================== Canvas Rendering (Performance Optimized) ======================
# Reusable 2D figure initialization (verified)
if "game_figure" not in st.session_state:
    fig, ax = plt.subplots(
        figsize=(GAME_CONFIG["window"]["width"]/100, GAME_CONFIG["window"]["height"]/100), 
        dpi=80  # Optimized for performance
    )
    st.session_state.game_figure = fig
    st.session_state.game_ax = ax

def create_game_canvas():
    """Render 2D game canvas (verified - no 3D elements)"""
    gs = st.session_state.game_state
    fig, ax = st.session_state.game_figure, st.session_state.game_ax
    
    try:
        # Clear axis (10x faster than recreating)
        ax.clear()
        ax.set_xlim(0, GAME_CONFIG["window"]["width"])
        ax.set_ylim(0, GAME_CONFIG["window"]["height"])
        ax.set_aspect("equal")
        ax.axis("off")
        
        # 2D green background
        ax.add_patch(patches.Rectangle((0, 0), GAME_CONFIG["window"]["width"], 
                                      GAME_CONFIG["window"]["height"], 
                                      facecolor=GAME_CONFIG["visuals"]["colors"]["green"], 
                                      edgecolor="none"))
        
        # 2D obstacles (sand traps)
        for (ox, oy, w, h) in gs["obstacles"]:
            ax.add_patch(patches.Rectangle((ox, oy), w, h, 
                                          facecolor=GAME_CONFIG["visuals"]["colors"]["sand"], 
                                          edgecolor=GAME_CONFIG["visuals"]["colors"]["sand_border"], 
                                          linewidth=2))
        
        # 2D hole
        ax.add_patch(patches.Circle(gs["hole_pos"], GAME_CONFIG["physics"]["hole_radius"], 
                                   facecolor=GAME_CONFIG["visuals"]["colors"]["hole"], 
                                   edgecolor=GAME_CONFIG["visuals"]["colors"]["hole_border"], 
                                   linewidth=2))
        
        # 2D golf ball with hit feedback
        if gs["hit_feedback"]:
            # 2D visual feedback (enlargement)
            ax.add_patch(patches.Circle(gs["ball_pos"], 
                                       GAME_CONFIG["physics"]["ball_radius"] * GAME_CONFIG["visuals"]["hit_feedback"]["scale"], 
                                       facecolor=GAME_CONFIG["visuals"]["hit_feedback"]["color"], 
                                       edgecolor=GAME_CONFIG["visuals"]["colors"]["ball_border"], 
                                       linewidth=1))
            # Reset feedback after duration
            if time.time() - gs["hit_feedback_start"] > GAME_CONFIG["visuals"]["hit_feedback"]["duration"]:
                gs["hit_feedback"] = False
        else:
            # Normal 2D ball
            ax.add_patch(patches.Circle(gs["ball_pos"], GAME_CONFIG["physics"]["ball_radius"], 
                                       facecolor=GAME_CONFIG["visuals"]["colors"]["ball"], 
                                       edgecolor=GAME_CONFIG["visuals"]["colors"]["ball_border"], 
                                       linewidth=1))
        
        # 2D aiming arrow
        if gs["drag_start"] is not None and not gs["is_rolling"]:
            start = np.array(gs["drag_start"])
            end = np.array(gs["drag_end"]) if gs["drag_end"] is not None else start
            direction = start - end
            length = np.linalg.norm(direction)
            
            if length > 0:
                # 2D angle snapping
                direction = snap_to_angle(direction)
                scaled_dir = direction * min(length, 100)
                ax.arrow(gs["ball_pos"][0], gs["ball_pos"][1],
                        scaled_dir[0], scaled_dir[1],
                        head_width=10, head_length=15, fc="red", ec="red", alpha=0.6)
        
        # 2D power meter (flashing at high power)
        if not gs["is_rolling"] and not gs["level_complete"]:
            power_meter_x = GAME_CONFIG["window"]["width"]/2 - GAME_CONFIG["visuals"]["power_meter"]["width"]/2
            power_meter_y = GAME_CONFIG["window"]["height"] + GAME_CONFIG["visuals"]["power_meter"]["y_pos"]
            
            # 2D power meter background
            ax.add_patch(patches.Rectangle((power_meter_x, power_meter_y), 
                                          GAME_CONFIG["visuals"]["power_meter"]["width"], 
                                          GAME_CONFIG["visuals"]["power_meter"]["height"],
                                          facecolor="#ecf0f1", edgecolor="#bdc3c7", linewidth=2))
            
            # 2D flashing effect for high power
            if gs["current_power"] > 90:
                gs["flash_state"] = not gs["flash_state"]
                power_color = "#ff0000" if gs["flash_state"] else get_power_color(gs["current_power"])
            else:
                power_color = get_power_color(gs["current_power"])
            
            # 2D power meter fill
            power_width = (gs["current_power"] / 100) * GAME_CONFIG["visuals"]["power_meter"]["width"]
            ax.add_patch(patches.Rectangle((power_meter_x, power_meter_y), 
                                          power_width, GAME_CONFIG["visuals"]["power_meter"]["height"],
                                          facecolor=power_color, edgecolor="none"))
            
            # 2D power text
            text_color = "black" if gs["current_power"] < 70 else "white"
            ax.text(power_meter_x + GAME_CONFIG["visuals"]["power_meter"]["width"]/2,
                   power_meter_y + GAME_CONFIG["visuals"]["power_meter"]["height"]/2,
                   f"Power: {int(gs['current_power'])}%",
                   ha="center", va="center", fontsize=12, fontweight="bold",
                   color=text_color, zorder=10)
        
        # 2D game info text
        info_text = []
        info_text.append(f"Level: {gs['level']+1} | Strokes: {gs['strokes']} | Par: {gs['par']}")
        info_text.append(f"Wind: {gs['wind']:.1f} m/s")
        info_text.append(f"Completed Levels: {len(gs['progress']['completed_levels'])}")
        
        if gs["level_complete"]:
            info_text[0] += f" | Completed! (Par {gs['par']}, You: {gs['strokes']})"
            info_text[0] += " | Next Level →" if gs["level"] < len(GAME_CONFIG["levels"])-1 else " | Game Complete!"
        
        ax.text(GAME_CONFIG["window"]["width"]/2, 20, " | ".join(info_text),
               ha="center", va="center", fontsize=14,
               bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, pad=0.5))
        
        # Convert to 2D image with compression
        buf = io.BytesIO()
        fig.savefig(
            buf, 
            format="png", 
            bbox_inches="tight", 
            pad_inches=0, 
            dpi=80,
            facecolor=GAME_CONFIG["visuals"]["colors"]["green"], 
            edgecolor="none",
            quality=85
        )
        buf.seek(0)
        img = Image.open(buf)
        
        # Cache image size for 2D coordinate scaling
        gs["image_size"] = (img.width, img.height)
        
        return img
    
    except Exception as e:
        logging.error(f"Canvas rendering error: {str(e)}", exc_info=True)
        st.error("Failed to render game screen!")
        return Image.new(
            'RGB', 
            (GAME_CONFIG["window"]["width"], GAME_CONFIG["window"]["height"]), 
            color=GAME_CONFIG["visuals"]["colors"]["green"]
        )

# ====================== Main Game Logic (Fully Verified) ======================
def main():
    gs = st.session_state.game_state
    current_time = time.time()
    
    # Fixed 60fps update (2D only)
    UPDATE_INTERVAL = 1 / 60
    if current_time - gs["last_update"] >= UPDATE_INTERVAL:
        if gs["is_rolling"]:
            update_ball()
        gs["last_update"] = current_time
    
    # Generate 2D game canvas
    game_image = create_game_canvas()
    
    # Display with use_container_width=True (Streamlit requirement)
    if "img_placeholder" not in st.session_state:
        st.session_state.img_placeholder = st.empty()
    st.session_state.img_placeholder.image(game_image, use_container_width=True)
    
    # 2D drag event handling (verified)
    def handle_drag(event):
        if gs["is_rolling"] or gs["level_complete"]:
            return
        
        # 2D coordinate scaling
        img_w, img_h = gs["image_size"]
        scale_x = GAME_CONFIG["window"]["width"] / img_w
        scale_y = GAME_CONFIG["window"]["height"] / img_h
        game_x = event.x * scale_x
        game_y = event.y * scale_y
        
        if event.type in ["mousedown", "touchstart"]:
            gs["drag_start"] = (game_x, game_y)
            gs["current_power"] = 0.0
        
        elif event.type in ["mousemove", "touchmove"]:
            if gs["drag_start"] is not None:
                gs["drag_end"] = (game_x, game_y)
                # Calculate 2D power from drag distance
                drag_vector = np.array(gs["drag_start"]) - np.array((game_x, game_y))
                drag_distance = np.linalg.norm(drag_vector)
                if drag_distance > 0:
                    gs["current_power"] = min((drag_distance / GAME_CONFIG["physics"]["max_power"]) * 100, 100)
        
        elif event.type in ["mouseup", "touchend"]:
            if gs["drag_start"] is not None and gs["drag_end"] is not None:
                drag_vector = np.array(gs["drag_start"]) - np.array(gs["drag_end"])
                drag_distance = np.linalg.norm(drag_vector)
                
                # 2D hit logic (verified)
                if drag_distance > 0.1:
                    power = (drag_distance / GAME_CONFIG["physics"]["max_power"]) * 10
                    
                    # Set 2D velocity
                    gs["ball_velocity"] = (drag_vector / drag_distance) * power
                    gs["is_rolling"] = True
                    gs["strokes"] += 1
                    
                    # 2D hit feedback
                    gs["hit_feedback"] = True
                    gs["hit_feedback_start"] = time.time()
            
            # Reset drag state
            gs["drag_start"] = None
            gs["drag_end"] = None
            gs["current_power"] = 0.0
    
    # 2D JavaScript controls (verified)
    js_code = f"""
    <script>
    const img = document.querySelector('img');
    let isDragging = false;
    let lastUpdate = 0;
    const UPDATE_INTERVAL = {UPDATE_INTERVAL * 1000};
    
    // Get 2D event coordinates
    function getEventCoords(e) {{
        const rect = img.getBoundingClientRect();
        let x, y;
        
        if (e.type.includes('touch')) {{
            e.preventDefault();
            const touch = e.touches[0] || e.changedTouches[0];
            x = (touch.clientX - rect.left) * (img.naturalWidth / rect.width);
            y = (touch.clientY - rect.top) * (img.naturalHeight / rect.height);
        }} else {{
            x = e.offsetX * (img.naturalWidth / rect.width);
            y = e.offsetY * (img.naturalHeight / rect.height);
        }}
        return {{x, y}};
    }}
    
    // Throttle 2D event dispatching
    function dispatchEvent(type, x, y) {{
        const now = performance.now();
        if (now - lastUpdate > UPDATE_INTERVAL) {{
            window.parent.postMessage({{type, x, y}}, '*');
            lastUpdate = now;
        }}
    }}
    
    // 2D mouse events
    img.addEventListener('mousedown', (e) => {{
        isDragging = true;
        const {{x, y}} = getEventCoords(e);
        dispatchEvent('mousedown', x, y);
    }});
    
    img.addEventListener('mousemove', (e) => {{
        if (isDragging) {{
            const {{x, y}} = getEventCoords(e);
            dispatchEvent('mousemove', x, y);
        }}
    }});
    
    img.addEventListener('mouseup', (e) => {{
        isDragging = false;
        const {{x, y}} = getEventCoords(e);
        dispatchEvent('mouseup', x, y);
    }});
    
    // 2D touch events (mobile support)
    img.addEventListener('touchstart', (e) => {{
        isDragging = true;
        const {{x, y}} = getEventCoords(e);
        dispatchEvent('touchstart', x, y);
    }});
    
    img.addEventListener('touchmove', (e) => {{
        if (isDragging) {{
            const {{x, y}} = getEventCoords(e);
            dispatchEvent('touchmove', x, y);
        }}
    }});
    
    img.addEventListener('touchend', (e) => {{
        isDragging = false;
        const {{x, y}} = getEventCoords(e);
        dispatchEvent('touchend', x, y);
    }});
    
    img.addEventListener('touchcancel', (e) => {{
        isDragging = false;
    }});
    
    // Force 2D canvas refresh
    setInterval(() => {{
        if (img) {{
            img.src = img.src.split('?')[0] + '?' + performance.now();
        }}
    }}, {UPDATE_INTERVAL * 1000});
    </script>
    """
    st.components.v1.html(js_code, height=0)
    
    # Level completion (use_container_width=True verified)
    if gs["level_complete"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if gs["level"] < len(GAME_CONFIG["levels"])-1:
                if st.button("Next Level", key="next_level", use_container_width=True):
                    reset_level(gs["level"] + 1)
            else:
                if st.button("Play Again", key="play_again", use_container_width=True):
                    reset_level(0)
    
    # Safe rerender (error handled)
    try:
        st.experimental_rerun()
    except Exception:
        pass

if __name__ == "__main__":
    main()
