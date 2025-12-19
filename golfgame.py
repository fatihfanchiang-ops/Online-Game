import streamlit as st
import streamlit.components.v1 as components
import random
import math

# Set page config
st.set_page_config(
    page_title="Progressive Golf Game",
    page_icon="⛳",
    layout="wide"
)

# --------------------------
# Session State Initialization
# --------------------------
def init_session_state():
    default_state = {
        "score": 0,
        "strokes": 0,
        "level": 1,
        "ball_position": {"x": 100, "y": 400},
        "hole_position": {"x": random.randint(300, 700), "y": random.randint(100, 300)},
        "game_over": False,
        "level_complete": False,
        # Difficulty progression variables
        "obstacle_count": 1,
        "obstacle_size_multiplier": 1.0,
        "friction": 0.98,
        "aim_line_max_length": 200,
        "power_multiplier": 10,
        "hole_min_distance": 200
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --------------------------
# Progressive Difficulty Logic
# --------------------------
def calculate_difficulty(level):
    """Calculate progressive difficulty based on current level"""
    # Exponential difficulty scaling
    difficulty_factor = math.pow(1.2, level - 1)
    
    # Update difficulty parameters
    st.session_state.obstacle_count = min(1 + (level - 1) * 2, 15)  # 1,3,5... up to 15 obstacles
    st.session_state.obstacle_size_multiplier = 1.0 + (level - 1) * 0.15  # 1x → 2.5x at lvl 10
    st.session_state.friction = max(0.90, 0.98 - (level - 1) * 0.008)  # 0.98 → 0.90 (faster ball stop)
    st.session_state.aim_line_max_length = max(80, 200 - (level - 1) * 12)  # 200px → 80px (harder aim)
    st.session_state.power_multiplier = max(8, 10 - (level - 1) * 0.2)  # 10 → 8 (less power control)
    st.session_state.hole_min_distance = 200 + (level - 1) * 50  # Min distance from start → 200→700px

def generate_harder_hole_position(level):
    """Generate increasingly difficult hole positions (farther, more edge positions)"""
    # Higher levels → hole closer to edges and farther from start
    edge_bias = min(0.8, (level - 1) * 0.1)  # 0 → 0.8 (more edge positions)
    
    # Random position with edge bias
    if random.random() < edge_bias:
        # Edge position (top/bottom/left/right)
        edge_choice = random.choice(['top', 'bottom', 'left', 'right'])
        if edge_choice == 'top':
            x = random.randint(100, 800)
            y = random.randint(50, 150)
        elif edge_choice == 'bottom':
            x = random.randint(100, 800)
            y = random.randint(350, 450)
        elif edge_choice == 'left':
            x = random.randint(100, 200)
            y = random.randint(50, 450)
        else:  # right
            x = random.randint(700, 800)
            y = random.randint(50, 450)
    else:
        # Regular position but farther from start
        x = random.randint(
            int(st.session_state.hole_min_distance), 
            800
        )
        y = random.randint(50, 450)
    
    return {"x": x, "y": y}

def reset_game():
    """Full reset to level 1 (easy difficulty)"""
    st.session_state.score = 0
    st.session_state.strokes = 0
    st.session_state.level = 1
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = generate_harder_hole_position(1)
    st.session_state.game_over = False
    st.session_state.level_complete = False
    # Reset difficulty parameters
    calculate_difficulty(1)

def next_level():
    """Advance to next level with increased difficulty"""
    if st.session_state.level >= 20:  # Max level (20) → game complete
        st.session_state.game_over = True
        return
    
    # Increment level
    st.session_state.level += 1
    st.session_state.strokes = 0
    st.session_state.ball_position = {"x": 100, "y": 400}
    
    # Generate harder hole position
    st.session_state.hole_position = generate_harder_hole_position(st.session_state.level)
    
    # Update difficulty for new level
    calculate_difficulty(st.session_state.level)
    st.session_state.level_complete = False

def calculate_score(current_strokes, level):
    """Score with bonus for fewer strokes on harder levels"""
    par = 3 + math.ceil(level * 0.7)  # Par increases faster (3→17 at lvl20)
    base_score = max(100 - ((current_strokes - par) * 25), 10)  # Higher penalty for extra strokes
    # Difficulty bonus (higher levels = more points)
    difficulty_bonus = level * 10
    total_score = base_score + difficulty_bonus
    return total_score

# Auto-advance to next level if complete
if st.session_state.level_complete:
    next_level()
    st.rerun()

# Calculate current difficulty
calculate_difficulty(st.session_state.level)

# --------------------------
# Game HTML/JS with Progressive Difficulty
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
        
        .difficulty-meter {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 15px;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 15;
        }}
        
        .obstacle {{
            position: absolute;
            background: #795548;
            border-radius: 5px;
            box-shadow: 0 3px 8px rgba(0,0,0,0.5);  /* Darker shadows for higher levels */
            opacity: {min(0.95, 0.7 + (st.session_state.level * 0.01))};  /* More opaque obstacles */
        }}
        
        .aim-line {{
            position: absolute;
            height: 3px;
            background: rgba(255, 255, 255, {max(0.5, 0.7 - (st.session_state.level * 0.01))});  /* Fainter aim line */
            border-radius: 2px;
            z-index: 8;
            transform-origin: left center;
            pointer-events: none;
            box-shadow: 0 0 5px rgba(255, 255, 0, {max(0.5, 0.8 - (st.session_state.level * 0.02))});
        }}
        
        .aim-dot {{
            position: absolute;
            width: {max(4, 8 - (st.session_state.level * 0.2))}px;  /* Smaller aim dot */
            height: {max(4, 8 - (st.session_state.level * 0.2))}px;
            background: rgba(255, 0, 0, {max(0.6, 0.8 - (st.session_state.level * 0.01))});
            border-radius: 50%;
            z-index: 9;
            pointer-events: none;
        }}
        
        .hole-target {{
            position: absolute;
            width: {max(30, 50 - (st.session_state.level * 1.5))}px;  /* Smaller target marker */
            height: {max(30, 50 - (st.session_state.level * 1.5))}px;
            border: 2px dashed rgba(255, 255, 255, {max(0.4, 0.6 - (st.session_state.level * 0.015))});
            border-radius: 50%;
            z-index: 4;
            transform: translate(-50%, -50%);
            left: {st.session_state.hole_position['x'] + 20}px;
            top: {st.session_state.hole_position['y'] + 20}px;
        }}
        
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
            z-index: 9999;
            text-align: center;
            display: none;
            animation: fadeIn 0.5s ease-in-out;
            border: 3px solid #FFC107;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translate(-50%, -45%); }}
            to {{ opacity: 1; transform: translate(-50%, -50%); }}
        }}
        
        /* Difficulty visual indicator */
        .difficulty-bar {{
            width: 100%;
            height: 5px;
            background: #ddd;
            border-radius: 3px;
            margin-top: 5px;
            overflow: hidden;
        }}
        
        .difficulty-fill {{
            height: 100%;
            width: {min(100, st.session_state.level * 5)}%;
            background: linear-gradient(90deg, #4CAF50, #FF9800, #F44336);
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
        
        <!-- Progressive obstacles (more and larger with higher levels) -->
        {''.join([
            f'<div class="obstacle" style="width: {50 * st.session_state.obstacle_size_multiplier + random.randint(-10, 20)}px; height: {30 * st.session_state.obstacle_size_multiplier + random.randint(-5, 15)}px; left: {random.randint(150, 850)}px; top: {random.randint(50, 450)}px;"></div>'
            for _ in range(st.session_state.obstacle_count)
        ])}
        
        <div class="power-indicator">
            <div class="power-bar" id="powerBar"></div>
        </div>
        
        <div class="game-info">
            Level: {st.session_state.level}<br>
            Strokes: {st.session_state.strokes}<br>
            Score: {st.session_state.score}
        </div>
        
        <!-- Difficulty meter -->
        <div class="difficulty-meter">
            Difficulty: {st.session_state.level}/20
            <div class="difficulty-bar">
                <div class="difficulty-fill"></div>
            </div>
            <small>Obstacles: {st.session_state.obstacle_count}</small>
        </div>
        
        <div class="level-complete" id="levelComplete">
            LEVEL {st.session_state.level} COMPLETE!<br>
            <span style="font-size: 18px; margin-top: 10px; display: block;">
                Next Level ({st.session_state.level + 1}) - Harder!
            </span>
        </div>
    </div>

    <script>
        // Game elements
        const ball = document.getElementById('ball');
        const hole = document.getElementById('hole');
        const course = document.getElementById('course');
        const powerBar = document.getElementById('powerBar');
        const aimLine = document.getElementById('aimLine');
        const aimDot = document.getElementById('aimDot');
        const levelCompletePopup = document.getElementById('levelComplete');
        
        // Progressive difficulty parameters (from Python)
        const friction = {st.session_state.friction};
        const aimLineMaxLength = {st.session_state.aim_line_max_length};
        const powerMultiplier = {st.session_state.power_multiplier};
        const maxPower = 100;
        
        // Game variables
        let isDragging = false;
        let startX, startY;
        let power = 0;
        let velocityX = 0;
        let velocityY = 0;
        let isMoving = false;
        
        // Hide aim line by default
        aimLine.style.display = 'none';
        aimDot.style.display = 'none';

        // Drag controls
        ball.addEventListener('mousedown', startDrag);
        ball.addEventListener('touchstart', startDrag, {{passive: false}});
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, {{passive: false}});
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);

        function startDrag(e) {{
            if (isMoving) return;
            isDragging = true;
            
            const touch = e.touches ? e.touches[0] : null;
            startX = touch ? touch.clientX : e.clientX;
            startY = touch ? touch.clientY : e.clientY;
            
            power = 0;
            powerBar.style.width = '0%';
            aimLine.style.display = 'block';
            aimDot.style.display = 'block';
            
            e.preventDefault();
        }}

        function drag(e) {{
            if (!isDragging || isMoving) return;
            
            const touch = e.touches ? e.touches[0] : null;
            const currentX = touch ? touch.clientX : e.clientX;
            const currentY = touch ? touch.clientY : e.clientY;
            
            const deltaX = startX - currentX;
            const deltaY = startY - currentY;
            const dragDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // More sensitive power control (harder to get perfect power)
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
            
            const ballRect = ball.getBoundingClientRect();
            const courseRect = course.getBoundingClientRect();
            const ballX = ballRect.left - courseRect.left + (ballRect.width / 2);
            const ballY = ballRect.top - courseRect.top + (ballRect.height / 2);
            
            const angle = Math.atan2(deltaY, deltaX);
            const lineLength = (power / maxPower) * aimLineMaxLength;  // Shorter aim line for higher levels
            const endX = ballX + Math.cos(angle) * lineLength;
            const endY = ballY + Math.sin(angle) * lineLength;
            
            aimLine.style.left = ballX + 'px';
            aimLine.style.top = ballY + 'px';
            aimLine.style.width = lineLength + 'px';
            aimLine.style.transform = 'rotate(' + angle + 'rad)';
            
            aimDot.style.left = (endX - (aimDot.offsetWidth / 2)) + 'px';
            aimDot.style.top = (endY - (aimDot.offsetHeight / 2)) + 'px';
        }}

        function endDrag(e) {{
            if (!isDragging || isMoving) return;
            
            isDragging = false;
            powerBar.style.width = '0%';
            aimLine.style.display = 'none';
            aimDot.style.display = 'none';
            
            const touch = e.changedTouches ? e.changedTouches[0] : null;
            const endX = touch ? touch.clientX : e.clientX;
            const endY = touch ? touch.clientY : e.clientY;
            
            const deltaX = (startX - endX) / powerMultiplier;  // Less power control
            const deltaY = (startY - endY) / powerMultiplier;
            
            // More unpredictable ball movement for higher levels
            const randomVariance = {min(0.15, 0.02 + (st.session_state.level * 0.007))};  // Random drift
            const driftX = (Math.random() - 0.5) * randomVariance;
            const driftY = (Math.random() - 0.5) * randomVariance;
            
            const powerMultiplierVal = power / maxPower;
            velocityX = (deltaX + driftX) * powerMultiplierVal;
            velocityY = (deltaY + driftY) * powerMultiplierVal;
            
            if (!isMoving) {{
                isMoving = true;
                moveBall();
                window.parent.postMessage({{type: 'STROKE'}}, '*');
            }}
        }}

        function moveBall() {{
            if (Math.abs(velocityX) < 0.08 && Math.abs(velocityY) < 0.08) {{  // Harder to stop perfectly
                isMoving = false;
                
                // Hole collision detection
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
                
                const distanceToHole = Math.sqrt(
                    Math.pow(ballCenter.x - holeCenter.x, 2) +
                    Math.pow(ballCenter.y - holeCenter.y, 2)
                );
                
                // Narrower hole detection for higher levels
                const holeThreshold = {max(12, 15 - (st.session_state.level * 0.15))};  // 15px → 12px
                if (distanceToHole < holeThreshold) {{
                    levelCompletePopup.style.display = 'block';
                    
                    window.parent.postMessage({{
                        type: 'HOLE_IN',
                        level: {st.session_state.level}
                    }}, '*');
                    
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 2000);  // Longer delay for harder levels
                    return;
                }}
                
                // Update ball position
                const ballX = parseFloat(ball.style.left) || 0;
                const ballY = parseFloat(ball.style.top) || 0;
                window.parent.postMessage({{
                    type: 'POSITION',
                    x: ballX,
                    y: ballY
                }}, '*');
                return;
            }}
            
            // Apply friction (less friction = ball stops faster)
            velocityX *= friction;
            velocityY *= friction;
            
            let currentX = parseFloat(ball.style.left) || 0;
            let currentY = parseFloat(ball.style.top) || 0;
            let newX = currentX + velocityX;
            let newY = currentY + velocityY;
            
            // Boundary checks
            const courseRect = course.getBoundingClientRect();
            const ballRadius = ball.offsetWidth / 2;
            newX = Math.max(ballRadius, Math.min(courseRect.width - ballRadius, newX));
            newY = Math.max(ballRadius, Math.min(courseRect.height - ballRadius, newY));
            
            // Obstacle collision (harder collisions for higher levels)
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
                    // More unpredictable bounce for higher levels
                    const bounceVariance = {min(0.3, 0.1 + (st.session_state.level * 0.01))};
                    const randomBounceX = (Math.random() - 0.5) * bounceVariance;
                    const randomBounceY = (Math.random() - 0.5) * bounceVariance;
                    
                    velocityX = (velocityX * -0.7) + randomBounceX;  // Less predictable bounce
                    velocityY = (velocityY * -0.7) + randomBounceY;
                    newX = currentX + velocityX;
                    newY = currentY + velocityY;
                }}
            }});
            
            ball.style.left = newX + 'px';
            ball.style.top = newY + 'px';
            
            requestAnimationFrame(moveBall);
        }}

        // Reset handler
        window.addEventListener('message', (event) => {{
            if (event.data.type === 'RESET') {{
                ball.style.left = '100px';
                ball.style.top = '400px';
                hole.style.left = '{random.randint(300, 700)}px';
                hole.style.top = '{random.randint(100, 300)}px';
                
                const holeTarget = document.querySelector('.hole-target');
                holeTarget.style.left = (parseInt(hole.style.left) + 20) + 'px';
                holeTarget.style.top = (parseInt(hole.style.top) + 20) + 'px';
                
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
# Streamlit UI
# --------------------------
st.title("⛳ Progressive Golf Game (Harder Levels)")

# Game Over Screen
if st.session_state.game_over:
    st.success(f"""
        🎉 Congratulations! You completed all 20 levels!
        Final Score: {st.session_state.score}
        You mastered the hardest difficulty!
    """)
    if st.button("Play Again", type="primary"):
        reset_game()
        st.rerun()

# Active Game Screen
else:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        components.html(golf_game_html, height=580, width=950)
    
    with col2:
        st.header("Game Stats")
        st.metric("Current Level", st.session_state.level)
        st.metric("Strokes This Level", st.session_state.strokes)
        st.metric("Total Score", st.session_state.score)
        
        # Difficulty info
        st.subheader("Current Difficulty")
        st.write(f"🔹 Obstacles: {st.session_state.obstacle_count} (Level {st.session_state.level}: {st.session_state.obstacle_count}x)")
        st.write(f"🔹 Friction: {st.session_state.friction:.2f} (Lower = faster stop)")
        st.write(f"🔹 Aim Line Length: {st.session_state.aim_line_max_length}px (Shorter = harder aim)")
        st.write(f"🔹 Hole Min Distance: {st.session_state.hole_min_distance}px (Farther = harder)")
        
        # Controls
        st.subheader("Controls")
        if st.button("Reset Game", type="primary"):
            reset_game()
            st.rerun()
        
        if st.button("Skip to Next Level", disabled=st.session_state.level >= 20):
            next_level()
            st.rerun()

# --------------------------
# Message Handler
# --------------------------
components.html(f"""
<script>
    let isProcessing = false;
    
    window.addEventListener('message', async (event) => {{
        if (isProcessing) return;
        isProcessing = true;
        
        try {{
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
            
            else if (event.data.type === 'HOLE_IN') {{
                // Calculate score with difficulty bonus
                const currentStrokes = {st.session_state.strokes};
                const currentLevel = {st.session_state.level};
                const par = 3 + Math.ceil(currentLevel * 0.7);
                const baseScore = Math.max(100 - ((currentStrokes - par) * 25), 10);
                const difficultyBonus = currentLevel * 10;
                const totalScore = baseScore + difficultyBonus;
                
                // Update score
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['score', {st.session_state.score} + totalScore],
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
            console.error('Error:', error);
        }} 
        finally {{
            isProcessing = false;
        }}
    }});
</script>
""", height=0, width=0)
