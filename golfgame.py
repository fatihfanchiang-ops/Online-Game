import streamlit as st
import streamlit.components.v1 as components
import random

# Set page config first (critical for Streamlit)
st.set_page_config(
    page_title="Drag & Drop Golf Game",
    page_icon="⛳",
    layout="wide"
)

# --------------------------
# Game State Management (Fixed initialization order)
# --------------------------
def init_session_state():
    default_state = {
        "score": 0,
        "strokes": 0,
        "level": 1,
        "ball_position": {"x": 100, "y": 400},
        "hole_position": {"x": random.randint(300, 700), "y": random.randint(100, 300)},
        "game_over": False,
        "level_complete": False  # New state for level transition
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize state before any operations
init_session_state()

# --------------------------
# Core Game Functions (Fixed logic)
# --------------------------
def reset_game():
    """Full game reset to level 1"""
    st.session_state.score = 0
    st.session_state.strokes = 0
    st.session_state.level = 1
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = {"x": random.randint(300, 700), "y": random.randint(100, 300)}
    st.session_state.game_over = False
    st.session_state.level_complete = False

def next_level():
    """Advance to next level (with max level check)"""
    if st.session_state.level >= 10:
        st.session_state.game_over = True
        return
    
    # Increment level and reset position/strokes
    st.session_state.level += 1
    st.session_state.strokes = 0
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = {
        "x": random.randint(400, 800),  # Harder positions for higher levels
        "y": random.randint(50, 350)
    }
    st.session_state.level_complete = False

def calculate_score(current_strokes, level):
    """Fixed scoring logic (par calculation)"""
    par = 3 + level  # Par increases with level
    score_gain = max(100 - ((current_strokes - par) * 20), 10)  # Min 10 points
    return score_gain

# --------------------------
# Auto Level Transition (Fixed trigger logic)
# --------------------------
if st.session_state.level_complete:
    # Auto-advance to next level after brief delay
    next_level()
    st.rerun()  # Critical for immediate UI update

# --------------------------
# HTML/JS Game Interface (Fixed critical bugs)
# --------------------------
golf_game_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        .golf-course {{
            position: relative;
            width: 900px;
            height: 500px;
            background: linear-gradient(135deg, #8BC34A 0%, #689F38 100%);
            border-radius: 10px;
            border: 5px solid #5D4037;
            overflow: hidden;
            cursor: grab;
        }}
        
        .golf-ball {{
            position: absolute;
            width: 25px;
            height: 25px;
            background: white;
            border-radius: 50%;
            border: 2px solid #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            z-index: 10;
            cursor: grab;
            transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        
        .golf-hole {{
            position: absolute;
            width: 40px;
            height: 40px;
            background: #212121;
            border-radius: 50%;
            border: 3px solid #795548;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.7);
            z-index: 5;
        }}
        
        .power-indicator {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 300px;
            height: 20px;
            background: #f5f5f5;
            border: 2px solid #333;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .power-bar {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #FF5722 0%, #FFC107 100%);
            transition: width 0.2s linear;
        }}
        
        .game-info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255,255,255,0.8);
            padding: 15px;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .obstacle {{
            position: absolute;
            background: #795548;
            border-radius: 5px;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        }}
        
        .aim-line {{
            position: absolute;
            height: 3px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 2px;
            z-index: 8;
            transform-origin: left center;
            pointer-events: none;
            box-shadow: 0 0 5px rgba(255, 255, 0, 0.8);
        }}
        
        .aim-dot {{
            position: absolute;
            width: 8px;
            height: 8px;
            background: rgba(255, 0, 0, 0.8);
            border-radius: 50%;
            z-index: 9;
            pointer-events: none;
        }}
        
        .hole-target {{
            position: absolute;
            width: 50px;
            height: 50px;
            border: 2px dashed rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            z-index: 4;
            transform: translate(-50%, -50%);
            left: {st.session_state.hole_position['x'] + 20}px;
            top: {st.session_state.hole_position['y'] + 20}px;
        }}
        
        /* Fixed level complete popup (z-index + animation) */
        .level-complete {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 40px 70px;
            border-radius: 20px;
            font-family: Arial, sans-serif;
            font-size: 28px;
            font-weight: bold;
            z-index: 9999;  /* Ensure it's on top */
            text-align: center;
            display: none;
            animation: fadeIn 0.5s ease-in-out;
            border: 3px solid #FFC107;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translate(-50%, -45%); }}
            to {{ opacity: 1; transform: translate(-50%, -50%); }}
        }}
    </style>
</head>
<body>
    <div class="golf-course" id="course">
        <div class="golf-ball" id="ball" style="left: {st.session_state.ball_position['x']}px; top: {st.session_state.ball_position['y']}px;"></div>
        <div class="golf-hole" id="hole" style="left: {st.session_state.hole_position['x']}px; top: {st.session_state.hole_position['y']}px;"></div>
        <div class="hole-target"></div>
        <div class="aim-line" id="aimLine"></div>
        <div class="aim-dot" id="aimDot"></div>
        
        <!-- Dynamic obstacles (1 per level, max 10) -->
        {''.join([
            f'<div class="obstacle" style="width: {50 + st.session_state.level * 8}px; height: {30 + st.session_state.level * 5}px; left: {random.randint(200, 800)}px; top: {random.randint(50, 450)}px;"></div>'
            for _ in range(min(st.session_state.level, 10))
        ])}
        
        <div class="power-indicator">
            <div class="power-bar" id="powerBar"></div>
        </div>
        
        <div class="game-info">
            Level: {st.session_state.level}<br>
            Strokes: {st.session_state.strokes}<br>
            Score: {st.session_state.score}
        </div>
        
        <!-- Fixed level complete popup -->
        <div class="level-complete" id="levelComplete">
            LEVEL {st.session_state.level} COMPLETE!<br>
            <span style="font-size: 18px; margin-top: 10px; display: block;">Next Level Loading...</span>
        </div>
    </div>

    <script>
        // Core elements (fixed selection)
        const ball = document.getElementById('ball');
        const hole = document.getElementById('hole');
        const course = document.getElementById('course');
        const powerBar = document.getElementById('powerBar');
        const aimLine = document.getElementById('aimLine');
        const aimDot = document.getElementById('aimDot');
        const levelCompletePopup = document.getElementById('levelComplete');
        
        // Game variables (fixed initialization)
        let isDragging = false;
        let startX, startY;
        let power = 0;
        const maxPower = 100;
        const friction = 0.98;
        let velocityX = 0;
        let velocityY = 0;
        let isMoving = false;
        
        // Hide aim line by default
        aimLine.style.display = 'none';
        aimDot.style.display = 'none';

        // --------------------------
        // Fixed Drag Controls (touch/mouse)
        // --------------------------
        ball.addEventListener('mousedown', startDrag);
        ball.addEventListener('touchstart', startDrag, {{passive: false}});  // Fixed passive: false for preventDefault
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, {{passive: false}});
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);

        function startDrag(e) {{
            if (isMoving) return;  // Prevent drag while ball is moving
            isDragging = true;
            
            // Fixed touch/mouse position detection
            const touch = e.touches ? e.touches[0] : null;
            startX = touch ? touch.clientX : e.clientX;
            startY = touch ? touch.clientY : e.clientY;
            
            power = 0;
            powerBar.style.width = '0%';
            aimLine.style.display = 'block';
            aimDot.style.display = 'block';
            
            e.preventDefault();  // Fixed text selection issue
        }}

        function drag(e) {{
            if (!isDragging || isMoving) return;
            
            const touch = e.touches ? e.touches[0] : null;
            const currentX = touch ? touch.clientX : e.clientX;
            const currentY = touch ? touch.clientY : e.clientY;
            
            const deltaX = startX - currentX;
            const deltaY = startY - currentY;
            const dragDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // Fixed power calculation (capped at maxPower)
            power = Math.min(Math.max(dragDistance, 0), maxPower);
            powerBar.style.width = (power / maxPower) * 100 + '%';
            
            updateAimLine(deltaX, deltaY, power);
            e.preventDefault();
        }}

        function updateAimLine(deltaX, deltaY, power) {{
            if (power === 0) {{
                aimLine.style.display = 'none';
                aimDot.style.display = 'none';
                return;
            }}
            
            // Fixed ball position calculation (relative to course)
            const ballRect = ball.getBoundingClientRect();
            const courseRect = course.getBoundingClientRect();
            const ballX = ballRect.left - courseRect.left + (ballRect.width / 2);
            const ballY = ballRect.top - courseRect.top + (ballRect.height / 2);
            
            const angle = Math.atan2(deltaY, deltaX);
            const lineLength = (power / maxPower) * 200;  // Fixed max line length
            const endX = ballX + Math.cos(angle) * lineLength;
            const endY = ballY + Math.sin(angle) * lineLength;
            
            // Fixed aim line positioning
            aimLine.style.left = ballX + 'px';
            aimLine.style.top = ballY + 'px';
            aimLine.style.width = lineLength + 'px';
            aimLine.style.transform = 'rotate(' + angle + 'rad)';
            
            // Fixed aim dot positioning (centered)
            aimDot.style.left = (endX - 4) + 'px';
            aimDot.style.top = (endY - 4) + 'px';
        }}

        function endDrag(e) {{
            if (!isDragging || isMoving) return;
            
            isDragging = false;
            powerBar.style.width = '0%';
            aimLine.style.display = 'none';
            aimDot.style.display = 'none';
            
            // Fixed direction calculation (opposite of drag)
            const touch = e.changedTouches ? e.changedTouches[0] : null;
            const endX = touch ? touch.clientX : e.clientX;
            const endY = touch ? touch.clientY : e.clientY;
            
            const deltaX = (startX - endX) / 10;  // Fixed speed multiplier
            const deltaY = (startY - endY) / 10;
            
            // Fixed velocity calculation
            const powerMultiplier = power / maxPower;
            velocityX = deltaX * powerMultiplier;
            velocityY = deltaY * powerMultiplier;
            
            // Start ball movement (fixed isMoving flag)
            if (!isMoving) {{
                isMoving = true;
                moveBall();
                // Send stroke count to Streamlit
                window.parent.postMessage({{type: 'STROKE'}}, '*');
            }}
        }}

        // --------------------------
        // Fixed Ball Physics & Collision
        // --------------------------
        function moveBall() {{
            // Stop movement when velocity is near zero
            if (Math.abs(velocityX) < 0.1 && Math.abs(velocityY) < 0.1) {{
                isMoving = false;
                
                // Fixed hole collision detection (center-to-center)
                const ballRect = ball.getBoundingClientRect();
                const holeRect = hole.getBoundingClientRect();
                
                const ballCenter = {{
                    x: ballRect.left + ballRect.width / 2,
                    y: ballRect.top + ballRect.height / 2
                }};
                
                const holeCenter = {{
                    x: holeRect.left + holeRect.width / 2,
                    y: holeRect.top + holeRect.height / 2
                }};
                
                // Fixed distance calculation (pythagorean theorem)
                const distanceToHole = Math.sqrt(
                    Math.pow(ballCenter.x - holeCenter.x, 2) +
                    Math.pow(ballCenter.y - holeCenter.y, 2)
                );
                
                // Ball is in hole (fixed threshold: 15px)
                if (distanceToHole < 15) {{
                    // Show level complete popup
                    levelCompletePopup.style.display = 'block';
                    
                    // Send hole-in event to Streamlit (fixed data format)
                    window.parent.postMessage({{
                        type: 'HOLE_IN',
                        level: {st.session_state.level}
                    }}, '*');
                    
                    // Auto-reload after 1.5s for next level
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 1500);
                    return;
                }}
                
                // Update ball position in Streamlit (fixed coordinates)
                const ballX = parseFloat(ball.style.left) || 0;
                const ballY = parseFloat(ball.style.top) || 0;
                window.parent.postMessage({{
                    type: 'POSITION',
                    x: ballX,
                    y: ballY
                }}, '*');
                return;
            }}
            
            // Apply friction (fixed physics)
            velocityX *= friction;
            velocityY *= friction;
            
            // Fixed current position calculation
            let currentX = parseFloat(ball.style.left) || 0;
            let currentY = parseFloat(ball.style.top) || 0;
            let newX = currentX + velocityX;
            let newY = currentY + velocityY;
            
            // Fixed boundary checks (keep ball in course)
            const courseRect = course.getBoundingClientRect();
            const ballRadius = ball.offsetWidth / 2;
            newX = Math.max(ballRadius, Math.min(courseRect.width - ballRadius, newX));
            newY = Math.max(ballRadius, Math.min(courseRect.height - ballRadius, newY));
            
            // Fixed obstacle collision (AABB)
            const obstacles = document.querySelectorAll('.obstacle');
            obstacles.forEach(obstacle => {{
                const obsRect = obstacle.getBoundingClientRect();
                const ballRect = {{
                    left: newX - ballRadius,
                    top: newY - ballRadius,
                    right: newX + ballRadius,
                    bottom: newY + ballRadius
                }};
                
                if (
                    ballRect.left < obsRect.right &&
                    ballRect.right > obsRect.left &&
                    ballRect.top < obsRect.bottom &&
                    ballRect.bottom > obsRect.top
                ) {{
                    // Fixed bounce physics (70% velocity retention)
                    velocityX *= -0.7;
                    velocityY *= -0.7;
                    newX = currentX + velocityX;
                    newY = currentY + velocityY;
                }}
            }});
            
            // Update ball position (fixed CSS units)
            ball.style.left = newX + 'px';
            ball.style.top = newY + 'px';
            
            // Continue animation (fixed requestAnimationFrame)
            requestAnimationFrame(moveBall);
        }}

        // Fixed reset handler
        window.addEventListener('message', (event) => {{
            if (event.data.type === 'RESET') {{
                ball.style.left = '100px';
                ball.style.top = '400px';
                hole.style.left = '{random.randint(300, 700)}px';
                hole.style.top = '{random.randint(100, 300)}px';
                
                // Update hole target position
                const holeTarget = document.querySelector('.hole-target');
                holeTarget.style.left = (parseInt(hole.style.left) + 20) + 'px';
                holeTarget.style.top = (parseInt(hole.style.top) + 20) + 'px';
                
                // Reset physics
                velocityX = 0;
                velocityY = 0;
                isMoving = false;
                levelCompletePopup.style.display = 'none';
            }}
        }});
    </script>
</body>
</html>
"""

# --------------------------
# Streamlit UI (Fixed flow)
# --------------------------
st.title("⛳ Drag & Drop Golf Game")

# Game Over Screen (fixed logic)
if st.session_state.game_over:
    st.success(f"🎉 Congratulations! You completed all 10 levels with a total score of {st.session_state.score}!")
    if st.button("Play Again", type="primary"):
        reset_game()
        st.rerun()

# Active Game Screen
else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Fixed component rendering (height/width)
        components.html(golf_game_html, height=550, width=950)
    
    with col2:
        st.header("Controls")
        st.metric("Level", st.session_state.level)
        st.metric("Strokes", st.session_state.strokes)
        st.metric("Score", st.session_state.score)
        
        # Fixed button actions
        if st.button("Reset Game", type="primary"):
            reset_game()
            st.rerun()
        
        if st.button("Skip Level", disabled=st.session_state.level >= 10):
            next_level()
            st.rerun()

# --------------------------
# Fixed Message Handler (Critical for state sync)
# --------------------------
components.html(f"""
<script>
    // Fixed message listener (prevent duplicate requests)
    let isProcessing = false;
    
    window.addEventListener('message', async (event) => {{
        if (isProcessing) return;
        isProcessing = true;
        
        try {{
            // Fixed stroke counting
            if (event.data.type === 'STROKE') {{
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['strokes', {st.session_state.strokes} + 1],
                        kwargs: {{}}
                    }})
                }});
                window.location.reload();
            }}
            
            // Fixed hole-in handling (score + level)
            else if (event.data.type === 'HOLE_IN') {{
                // Calculate and update score
                const currentStrokes = {st.session_state.strokes};
                const currentLevel = {st.session_state.level};
                const par = 3 + currentLevel;
                const scoreGain = Math.max(100 - ((currentStrokes - par) * 20), 10);
                
                // Update score first
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['score', {st.session_state.score} + scoreGain],
                        kwargs: {{}}
                    }})
                }});
                
                // Mark level as complete
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['level_complete', true],
                        kwargs: {{}}
                    }})
                }});
            }}
            
            // Fixed ball position update
            else if (event.data.type === 'POSITION') {{
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['ball_position', {{x: event.data.x, y: event.data.y}}],
                        kwargs: {{}}
                    }})
                }});
            }}
        }} 
        catch (error) {{
            console.error('Error processing game event:', error);
        }} 
        finally {{
            isProcessing = false;
        }}
    }});
</script>
""", height=0, width=0)
