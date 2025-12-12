import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import io
from PIL import Image

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
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Game Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
HOLE_RADIUS = 10
BALL_RADIUS = 5
MAX_POWER = 100
FRICTION = 0.98
LEVELS = [
    # (tee_pos, hole_pos, obstacles, par)
    {"tee": (100, 300), "hole": (1000, 300), "obstacles": [(500, 200, 100, 100)], "par": 3},
    {"tee": (100, 100), "hole": (900, 500), "obstacles": [(300, 300, 80, 80), (600, 200, 120, 120)], "par": 4},
    {"tee": (100, 500), "hole": (1100, 100), "obstacles": [(200, 200, 60, 60), (400, 400, 90, 90), (700, 300, 70, 70)], "par": 5},
]

# Game State
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
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
    }

# Reset game state for new level
def reset_level(level_idx):
    st.session_state.game_state.update({
        "level": level_idx,
        "ball_pos": np.array(LEVELS[level_idx]["tee"], dtype=np.float64),
        "hole_pos": np.array(LEVELS[level_idx]["hole"]),
        "obstacles": LEVELS[level_idx]["obstacles"],
        "par": LEVELS[level_idx]["par"],
        "strokes": 0,
        "ball_velocity": np.array([0.0, 0.0]),
        "is_rolling": False,
        "level_complete": False,
    })

# Check collision with obstacles
def check_collision(pos, obstacles):
    x, y = pos
    for (ox, oy, w, h) in obstacles:
        if ox - BALL_RADIUS <= x <= ox + w + BALL_RADIUS and oy - BALL_RADIUS <= y <= oy + h + BALL_RADIUS:
            return True
    return False

# Check if ball is in hole
def check_hole(pos, hole_pos):
    distance = np.linalg.norm(pos - hole_pos)
    return distance < (HOLE_RADIUS + BALL_RADIUS)

# Update ball position
def update_ball():
    gs = st.session_state.game_state
    if np.linalg.norm(gs["ball_velocity"]) < 0.1:
        gs["is_rolling"] = False
        return
    
    # Apply friction
    gs["ball_velocity"] *= FRICTION
    
    # Calculate new position
    new_pos = gs["ball_pos"] + gs["ball_velocity"]
    
    # Check boundaries
    new_pos[0] = np.clip(new_pos[0], BALL_RADIUS, WINDOW_WIDTH - BALL_RADIUS)
    new_pos[1] = np.clip(new_pos[1], BALL_RADIUS, WINDOW_HEIGHT - BALL_RADIUS)
    
    # Check collision with obstacles
    if not check_collision(new_pos, gs["obstacles"]):
        gs["ball_pos"] = new_pos
    else:
        # Bounce off obstacle (simplified)
        gs["ball_velocity"] *= -0.5
    
    # Check hole
    if check_hole(gs["ball_pos"], gs["hole_pos"]):
        gs["level_complete"] = True
        gs["is_rolling"] = False

# Create game canvas
def create_game_canvas():
    gs = st.session_state.game_state
    
    # Create figure
    fig, ax = plt.subplots(figsize=(WINDOW_WIDTH/100, WINDOW_HEIGHT/100), dpi=100)
    ax.set_xlim(0, WINDOW_WIDTH)
    ax.set_ylim(0, WINDOW_HEIGHT)
    ax.set_aspect("equal")
    ax.axis("off")
    
    # Draw green background
    ax.add_patch(patches.Rectangle((0, 0), WINDOW_WIDTH, WINDOW_HEIGHT, facecolor="#8CC051", edgecolor="none"))
    
    # Draw obstacles (sand traps)
    for (ox, oy, w, h) in gs["obstacles"]:
        ax.add_patch(patches.Rectangle((ox, oy), w, h, facecolor="#F4D35E", edgecolor="#E0C040", linewidth=2))
    
    # Draw hole
    ax.add_patch(patches.Circle(gs["hole_pos"], HOLE_RADIUS, facecolor="#3A2E1F", edgecolor="#2A1F10", linewidth=2))
    
    # Draw ball
    ax.add_patch(patches.Circle(gs["ball_pos"], BALL_RADIUS, facecolor="white", edgecolor="black", linewidth=1))
    
    # Draw power/direction line if dragging
    if gs["drag_start"] is not None and not gs["is_rolling"]:
        start = np.array(gs["drag_start"])
        end = np.array(gs["drag_end"]) if gs["drag_end"] is not None else start
        direction = start - end
        length = np.linalg.norm(direction)
        if length > 0:
            # Normalize and scale
            max_line_length = 100
            scaled_dir = direction / length * min(length, max_line_length)
            ax.arrow(
                gs["ball_pos"][0], gs["ball_pos"][1],
                scaled_dir[0], scaled_dir[1],
                head_width=10, head_length=15, fc="red", ec="red", alpha=0.6
            )
    
    # Draw score info
    score_text = f"Level: {gs['level']+1} | Strokes: {gs['strokes']} | Par: {gs['par']}"
    if gs["level_complete"]:
        score_text += f" | Completed! (Par {gs['par']}, You: {gs['strokes']})"
        if gs["level"] < len(LEVELS)-1:
            score_text += " | Next Level →"
        else:
            score_text += " | Game Complete!"
    
    ax.text(
        WINDOW_WIDTH/2, 20, score_text,
        ha="center", va="center", fontsize=14,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
    )
    
    # Convert to PIL image
    buf = io.BytesIO()
    plt.tight_layout(pad=0)
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    img = Image.open(buf)
    
    # Close figure to prevent memory leaks
    plt.close(fig)
    
    return img

# Main game loop
def main():
    gs = st.session_state.game_state
    
    # Update ball position if rolling
    if gs["is_rolling"]:
        update_ball()
    
    # Create game canvas
    game_image = create_game_canvas()
    
    # Create interactive image with drag controls
    img_placeholder = st.empty()
    
    # Handle mouse/touch drag events
    def handle_drag(event):
        if gs["is_rolling"] or gs["level_complete"]:
            return
        
        # Get coordinates relative to image
        x = event.x
        y = event.y
        
        # Convert to game coordinates (adjust for image scaling)
        scale_x = WINDOW_WIDTH / game_image.width
        scale_y = WINDOW_HEIGHT / game_image.height
        game_x = x * scale_x
        game_y = y * scale_y
        
        if event.type == "mousedown" or event.type == "touchstart":
            gs["drag_start"] = (game_x, game_y)
        elif event.type == "mousemove" or event.type == "touchmove":
            if gs["drag_start"] is not None:
                gs["drag_end"] = (game_x, game_y)
        elif event.type == "mouseup" or event.type == "touchend":
            if gs["drag_start"] is not None and gs["drag_end"] is not None:
                # Calculate hit power and direction
                start = np.array(gs["drag_start"])
                end = np.array(gs["drag_end"])
                direction = start - end
                power = np.linalg.norm(direction) / MAX_POWER * 10
                
                if power > 0.1:
                    # Set ball velocity
                    gs["ball_velocity"] = direction / np.linalg.norm(direction) * power
                    gs["is_rolling"] = True
                    gs["strokes"] += 1
            
            # Reset drag state
            gs["drag_start"] = None
            gs["drag_end"] = None
    
    # Display image with click/drag handlers
    img_placeholder.image(game_image, use_column_width=True)
    
    # Add JavaScript for touch/mouse handling (Streamlit doesn't support direct event handling, so we use JS)
    js_code = """
    <script>
    const img = document.querySelector('img');
    let isDragging = false;
    let startX, startY;
    
    // Mouse handlers
    img.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.offsetX;
        startY = e.offsetY;
        window.parent.postMessage({type: 'mousedown', x: startX, y: startY}, '*');
    });
    
    img.addEventListener('mousemove', (e) => {
        if (isDragging) {
            window.parent.postMessage({type: 'mousemove', x: e.offsetX, y: e.offsetY}, '*');
        }
    });
    
    img.addEventListener('mouseup', (e) => {
        isDragging = false;
        window.parent.postMessage({type: 'mouseup', x: e.offsetX, y: e.offsetY}, '*');
    });
    
    // Touch handlers
    img.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = img.getBoundingClientRect();
        startX = touch.clientX - rect.left;
        startY = touch.clientY - rect.top;
        window.parent.postMessage({type: 'touchstart', x: startX, y: startY}, '*');
    });
    
    img.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = img.getBoundingClientRect();
        window.parent.postMessage({type: 'touchmove', x: touch.clientX - rect.left, y: touch.clientY - rect.top}, '*');
    });
    
    img.addEventListener('touchend', (e) => {
        e.preventDefault();
        window.parent.postMessage({type: 'touchend', x: startX, y: startY}, '*');
    });
    
    // Listen for game state updates
    window.addEventListener('message', (e) => {
        if (e.data.type === 'update') {
            img.src = img.src + '?' + new Date().getTime();
        }
    });
    </script>
    """
    st.components.v1.html(js_code, height=0)
    
    # Handle level completion
    if gs["level_complete"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if gs["level"] < len(LEVELS)-1:
                if st.button("Next Level", key="next_level", use_container_width=True):
                    reset_level(gs["level"] + 1)
            else:
                if st.button("Play Again", key="play_again", use_container_width=True):
                    reset_level(0)
    
    # Auto-update the game canvas
    st.experimental_rerun()

if __name__ == "__main__":
    main()
