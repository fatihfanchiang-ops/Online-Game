import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from PIL import Image
import time

# Set page config for full-screen game
st.set_page_config(
    page_title="Golf Game",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit default elements
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding: 0 !important; margin: 0 !important;}
    canvas {border: none !important;}
    /* Optimize image rendering */
    img {image-rendering: pixelated; will-change: transform;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Game Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
HOLE_RADIUS = 10
BALL_RADIUS = 5
MAX_POWER = 100  # Maximum drag distance for full power
FRICTION = 0.98
UPDATE_INTERVAL = 0.016  # 60fps (16ms)
LEVELS = [
    {"tee": (100, 300), "hole": (1000, 300), "obstacles": [(500, 200, 100, 100)], "par": 3},
    {"tee": (100, 100), "hole": (900, 500), "obstacles": [(300, 300, 80, 80), (600, 200, 120, 120)], "par": 4},
    {"tee": (100, 500), "hole": (1100, 100), "obstacles": [(200, 200, 60, 60), (400, 400, 90, 90), (700, 300, 70, 70)], "par": 5},
]

# Power Meter Constants (Optimized)
POWER_METER_WIDTH = 300
POWER_METER_HEIGHT = 30
POWER_METER_POS = (WINDOW_WIDTH/2 - POWER_METER_WIDTH/2, WINDOW_HEIGHT - 50)
POWER_COLORS = {
    0: "#3498db",    # Blue (low)
    50: "#f1c40f",   # Yellow (medium)
    80: "#e74c3c",   # Red (high)
    100: "#c0392b"   # Dark red (max)
}

# Game State (Optimized for fast access)
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "level": 0,
        "ball_pos": np.array(LEVELS[0]["tee"], dtype=np.float64),
        "hole_pos": np.array(LEVELS[0]["hole"]),
        "obstacles": LEVELS[0]["obstacles"],
        "par": LEVELS[0]["par"],
        "strokes": 0,
        "drag_start": None,
        "drag_end": None,
        "current_power": 0.0,
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
        "last_update": time.time(),  # For frame timing
        "image_size": (WINDOW_WIDTH, WINDOW_HEIGHT),  # Cache image size
    }

# Reset game state
def reset_level(level_idx):
    gs = st.session_state.game_state
    gs.update({
        "level": level_idx,
        "ball_pos": np.array(LEVELS[level_idx]["tee"], dtype=np.float64),
        "hole_pos": np.array(LEVELS[level_idx]["hole"]),
        "obstacles": LEVELS[level_idx]["obstacles"],
        "par": LEVELS[level_idx]["par"],
        "strokes": 0,
        "current_power": 0.0,
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
    })

# Fast color interpolation (vectorized)
def get_power_color(power_percent):
    power_percent = np.clip(power_percent, 0, 100)
    sorted_stops = sorted(POWER_COLORS.items())
    
    # Find color range
    for i, (stop, color) in enumerate(sorted_stops[:-1]):
        next_stop, next_color = sorted_stops[i+1]
        if stop <= power_percent <= next_stop:
            # Fast RGB interpolation
            ratio = (power_percent - stop) / (next_stop - stop)
            r1, g1, b1 = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
            r2, g2, b2 = int(next_color[1:3],16), int(next_color[3:5],16), int(next_color[5:7],16)
            
            r = int(r1 + ratio * (r2 - r1))
            g = int(g1 + ratio * (g2 - g1))
            b = int(b1 + ratio * (b2 - b1))
            return f"#{r:02x}{g:02x}{b:02x}"
    return POWER_COLORS[100]

# Optimized collision check
def check_collision(pos, obstacles):
    x, y = pos
    for (ox, oy, w, h) in obstacles:
        if (ox - BALL_RADIUS <= x <= ox + w + BALL_RADIUS and 
            oy - BALL_RADIUS <= y <= oy + h + BALL_RADIUS):
            return True
    return False

# Optimized hole check
def check_hole(pos, hole_pos):
    return np.linalg.norm(pos - hole_pos) < (HOLE_RADIUS + BALL_RADIUS)

# Fast ball update (minimal calculations)
def update_ball():
    gs = st.session_state.game_state
    if np.linalg.norm(gs["ball_velocity"]) < 0.1:
        gs["is_rolling"] = False
        return
    
    # Apply friction and update position (vectorized)
    gs["ball_velocity"] *= FRICTION
    new_pos = gs["ball_pos"] + gs["ball_velocity"]
    
    # Boundary check (fast clip)
    new_pos[0] = np.clip(new_pos[0], BALL_RADIUS, WINDOW_WIDTH - BALL_RADIUS)
    new_pos[1] = np.clip(new_pos[1], BALL_RADIUS, WINDOW_HEIGHT - BALL_RADIUS)
    
    # Collision check (early exit if collision)
    if not check_collision(new_pos, gs["obstacles"]):
        gs["ball_pos"] = new_pos
    else:
        gs["ball_velocity"] *= -0.5
    
    # Hole check (early exit if complete)
    if check_hole(gs["ball_pos"], gs["hole_pos"]):
        gs["level_complete"] = True
        gs["is_rolling"] = False

# Optimized canvas rendering (cached figure setup)
@st.cache_data(show_spinner=False)
def create_blank_figure(width, height):
    """Cache blank figure to avoid reinitializing"""
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax

def create_game_canvas():
    gs = st.session_state.game_state
    
    # Use cached figure (major performance boost)
    fig, ax = create_blank_figure(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Draw background (single patch)
    ax.add_patch(patches.Rectangle((0, 0), WINDOW_WIDTH, WINDOW_HEIGHT, 
                                  facecolor="#8CC051", edgecolor="none"))
    
    # Draw obstacles (vectorized where possible)
    for (ox, oy, w, h) in gs["obstacles"]:
        ax.add_patch(patches.Rectangle((ox, oy), w, h, 
                                      facecolor="#F4D35E", edgecolor="#E0C040", linewidth=2))
    
    # Draw hole and ball (minimal elements)
    ax.add_patch(patches.Circle(gs["hole_pos"], HOLE_RADIUS, 
                               facecolor="#3A2E1F", edgecolor="#2A1F10", linewidth=2))
    ax.add_patch(patches.Circle(gs["ball_pos"], BALL_RADIUS, 
                               facecolor="white", edgecolor="black", linewidth=1))
    
    # Draw direction arrow (only if dragging)
    if gs["drag_start"] is not None and not gs["is_rolling"]:
        start = np.array(gs["drag_start"])
        end = np.array(gs["drag_end"]) if gs["drag_end"] is not None else start
        direction = start - end
        length = np.linalg.norm(direction)
        
        if length > 0:
            scaled_dir = direction / length * min(length, 100)
            ax.arrow(gs["ball_pos"][0], gs["ball_pos"][1],
                    scaled_dir[0], scaled_dir[1],
                    head_width=10, head_length=15, fc="red", ec="red", alpha=0.6)
    
    # Draw POWER METER (hyper-responsive)
    if not gs["is_rolling"] and not gs["level_complete"]:
        # Meter background
        ax.add_patch(patches.Rectangle(POWER_METER_POS, POWER_METER_WIDTH, POWER_METER_HEIGHT,
                                      facecolor="#ecf0f1", edgecolor="#bdc3c7", linewidth=2))
        
        # Power fill (instant update)
        power_width = (gs["current_power"] / 100) * POWER_METER_WIDTH
        power_color = get_power_color(gs["current_power"])
        ax.add_patch(patches.Rectangle(POWER_METER_POS, power_width, POWER_METER_HEIGHT,
                                      facecolor=power_color, edgecolor="none"))
        
        # Power text (high contrast)
        text_color = "black" if gs["current_power"] < 70 else "white"
        ax.text(POWER_METER_POS[0] + POWER_METER_WIDTH/2,
               POWER_METER_POS[1] + POWER_METER_HEIGHT/2,
               f"Power: {int(gs['current_power'])}%",
               ha="center", va="center", fontsize=12, fontweight="bold",
               color=text_color, zorder=10)  # Z-order ensures text is on top
    
    # Score text (minimal bbox)
    score_text = f"Level: {gs['level']+1} | Strokes: {gs['strokes']} | Par: {gs['par']}"
    if gs["level_complete"]:
        score_text += f" | Completed! (Par {gs['par']}, You: {gs['strokes']})"
        if gs["level"] < len(LEVELS)-1:
            score_text += " | Next Level →"
        else:
            score_text += " | Game Complete!"
    
    ax.text(WINDOW_WIDTH/2, 20, score_text,
           ha="center", va="center", fontsize=14,
           bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, pad=0.5))
    
    # Fast image conversion (no unnecessary padding)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, 
                dpi=100, facecolor="#8CC051", edgecolor="none")
    buf.seek(0)
    img = Image.open(buf)
    
    # Cache image size for fast coordinate mapping
    st.session_state.game_state["image_size"] = (img.width, img.height)
    
    # Clean up (prevent memory leaks)
    plt.close(fig)
    return img

# Main game loop (optimized for responsiveness)
def main():
    gs = st.session_state.game_state
    current_time = time.time()
    
    # Throttle updates to 60fps (prevents overloading)
    if current_time - gs["last_update"] >= UPDATE_INTERVAL:
        # Update ball only if rolling (minimal calculations)
        if gs["is_rolling"]:
            update_ball()
        gs["last_update"] = current_time
    
    # Create canvas (optimized rendering)
    game_image = create_game_canvas()
    
    # Use single placeholder (no reinitialization)
    if "img_placeholder" not in st.session_state:
        st.session_state.img_placeholder = st.empty()
    st.session_state.img_placeholder.image(game_image, use_column_width=True)
    
    # Ultra-fast drag handler (direct coordinate mapping)
    def handle_drag(event):
        if gs["is_rolling"] or gs["level_complete"]:
            return
        
        # Get image dimensions (cached)
        img_w, img_h = gs["image_size"]
        
        # Direct coordinate conversion (no scaling lag)
        scale_x = WINDOW_WIDTH / img_w
        scale_y = WINDOW_HEIGHT / img_h
        game_x = event.x * scale_x
        game_y = event.y * scale_y
        
        # Instant state updates (no delays)
        if event.type in ["mousedown", "touchstart"]:
            gs["drag_start"] = (game_x, game_y)
            gs["current_power"] = 0.0  # Instant reset
        
        elif event.type in ["mousemove", "touchmove"]:
            if gs["drag_start"] is not None:
                gs["drag_end"] = (game_x, game_y)
                # Fast power calculation (vectorized)
                drag_vector = np.array(gs["drag_start"]) - np.array((game_x, game_y))
                drag_distance = np.linalg.norm(drag_vector)
                # Instant power update (capped at 100%)
                gs["current_power"] = min((drag_distance / MAX_POWER) * 100, 100)
        
        elif event.type in ["mouseup", "touchend"]:
            if gs["drag_start"] is not None and gs["drag_end"] is not None:
                # Fast velocity calculation
                drag_vector = np.array(gs["drag_start"]) - np.array(gs["drag_end"])
                drag_distance = np.linalg.norm(drag_vector)
                
                if drag_distance > 0.1:
                    power = (drag_distance / MAX_POWER) * 10
                    gs["ball_velocity"] = (drag_vector / drag_distance) * power
                    gs["is_rolling"] = True
                    gs["strokes"] += 1
            
            # Instant reset (no lag)
            gs["drag_start"] = None
            gs["drag_end"] = None
            gs["current_power"] = 0.0
    
    # Hyper-responsive JavaScript (60fps update)
    js_code = f"""
    <script>
    const img = document.querySelector('img');
    let isDragging = false;
    let lastUpdate = 0;
    const UPDATE_INTERVAL = {UPDATE_INTERVAL * 1000}; // Convert to ms
    
    // Prevent default touch actions (reduces latency)
    img.style.touchAction = 'none';
    img.style.userSelect = 'none';
    
    // Fast coordinate extraction
    function getEventCoords(e) {{
        const rect = img.getBoundingClientRect();
        let x, y;
        
        if (e.type.includes('touch')) {{
            e.preventDefault();
            const touch = e.touches[0] || e.changedTouches[0];
            x = touch.clientX - rect.left;
            y = touch.clientY - rect.top;
        }} else {{
            x = e.offsetX;
            y = e.offsetY;
        }}
        
        return {{x, y}};
    }}
    
    // Fast event dispatch (no unnecessary processing)
    function dispatchEvent(type, x, y) {{
        const now = performance.now();
        // Throttle to 60fps (prevents browser overload)
        if (now - lastUpdate > UPDATE_INTERVAL) {{
            window.parent.postMessage({{type, x, y}}, '*');
            lastUpdate = now;
        }}
    }}
    
    // Mouse handlers (instant response)
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
    
    // Touch handlers (zero latency)
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
    
    // Force canvas refresh (16ms interval)
    setInterval(() => {{
        img.src = img.src.split('?')[0] + '?' + performance.now();
    }}, {UPDATE_INTERVAL * 1000});
    </script>
    """
    st.components.v1.html(js_code, height=0)
    
    # Level completion handling (minimal UI updates)
    if gs["level_complete"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if gs["level"] < len(LEVELS)-1:
                if st.button("Next Level", key="next_level", use_container_width=True):
                    reset_level(gs["level"] + 1)
            else:
                if st.button("Play Again", key="play_again", use_container_width=True):
                    reset_level(0)
    
    # Instant rerun (no delay)
    st.experimental_rerun()

if __name__ == "__main__":
    main()
