import streamlit as st
import streamlit.components.v1 as components
import random
import math

# Set page config
st.set_page_config(
    page_title="Auto-Skip Golf Game",
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
        # Auto-level variables
        "auto_advance": False,
        "advance_delay": 2000,  # 2 second delay before auto-skipping
        # Difficulty progression
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
# Auto-Level Progression (No manual input needed)
# --------------------------
def calculate_difficulty(level):
    """Calculate progressive difficulty based on current level"""
    difficulty_factor = math.pow(1.2, level - 1)
    
    st.session_state.obstacle_count = min(1 + (level - 1) * 2, 15)
    st.session_state.obstacle_size_multiplier = 1.0 + (level - 1) * 0.15
    st.session_state.friction = max(0.90, 0.98 - (level - 1) * 0.008)
    st.session_state.aim_line_max_length = max(80, 200 - (level - 1) * 12)
    st.session_state.power_multiplier = max(8, 10 - (level - 1) * 0.2)
    st.session_state.hole_min_distance = 200 + (level - 1) * 50

def generate_harder_hole_position(level):
    """Generate increasingly difficult hole positions"""
    edge_bias = min(0.8, (level - 1) * 0.1)
    
    if random.random() < edge_bias:
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
        else:
            x = random.randint(700, 800)
            y = random.randint(50, 450)
    else:
        x = random.randint(int(st.session_state.hole_min_distance), 800)
        y = random.randint(50, 450)
    
    return {"x": x, "y": y}

# AUTOMATIC LEVEL ADVANCE (CORE FEATURE)
def auto_advance_level():
    """Automatically advance to next level with no user input"""
    if st.session_state.auto_advance:
        if st.session_state.level >= 20:
            st.session_state.game_over = True
        else:
            # Increment level and reset state
            st.session_state.level += 1
            st.session_state.strokes = 0
            st.session_state.ball_position = {"x": 100, "y": 400}
            
            # Generate harder hole position
            st.session_state.hole_position = generate_harder_hole_position(st.session_state.level)
            
            # Update difficulty
            calculate_difficulty(st.session_state.level)
        
        # Reset auto-advance flag
        st.session_state.auto_advance = False
        st.rerun()

# Trigger auto-advance if flag is set
if st.session_state.auto_advance:
    auto_advance_level()

def reset_game():
    """Full reset to level 1"""
    st.session_state.score = 0
    st.session_state.strokes = 0
    st.session_state.level = 1
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = generate_harder_hole_position(1)
    st.session_state.game_over = False
    st.session_state.auto_advance = False
    calculate_difficulty(1)

def calculate_score(current_strokes, level):
    """Score with difficulty bonus"""
    par = 3 + math.ceil(level * 0.7)
    base_score = max(100 - ((current_strokes - par) * 25), 10)
    difficulty_bonus = level * 10
    return base_score + difficulty_bonus

# Calculate current difficulty
calculate_difficulty(st.session_state.level)

# --------------------------
# Game HTML/JS with Full Auto-Skip
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
            box-shadow: 0 3px 8px rgba(0,0,0,0.5);
            opacity: {min(0.95, 0.7 + (st.session_state.level * 0.01))};
        }}
        
        .aim-line {{
            position: absolute;
            height: 3px;
            background: rgba(255, 255, 255, {max(0.5, 0.7 - (st.session_state.level * 0.01))});
            border-radius: 2px;
            z-index: 8;
            transform-origin: left center;
            pointer-events: none;
            box-shadow: 0 0 5px rgba(255, 255, 0, {max(0.5, 0.8 - (st.session_state.level * 0.02))});
        }}
        
        .aim-dot {{
            position: absolute;
            width: {max(4, 8 - (st.session_state.level * 0.2))}px;
            height: {max(4, 8 - (st.session_state.level * 0.2))}px;
            background: rgba(255, 0, 0, {max(0.6, 0.8 - (st.session_state.level * 0.01))});
            border-radius: 50%;
            z-index: 9;
            pointer-events: none;
        }}
        
        .hole-target {{
            position: absolute;
            width: {max(30, 50 - (st.session_state.level * 1.5))}px;
            height: {max(30, 50 - (st.session_state.level * 1.5))}px;
            border: 2px dashed rgba(255, 255, 255, {max(0.4, 0.6 - (st.session_state.level * 0.015))});
            border-radius: 50%;
            z-index: 4;
            transform: translate(-50%, -50%);
            left: {st.session_state.hole_position['x'] + 20}px;
            top: {st.session_state.hole_position['y'] + 20}px;
        }}
        
        /* Auto-level transition animation */
        .level-transition {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease;
            font-family: Arial, sans-serif;
        }}
        
        .level-transition.active {{
            opacity: 1;
            pointer-events: all;
        }}
        
        .level-transition h1 {{
            font-size: 48px;
            margin-bottom: 20px;
            color: #FFC107;
        }}
        
        .level-transition p {{
            font-size: 24px;
            margin-bottom: 30px;
        }}
        
        .progress-bar {{
            width: 50%;
            height: 10px;
            background: #333;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 20px;
        }}
        
        .progress-fill {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #4CAF50, #FFC107);
            transition: width {st.session_state.advance_delay / 1000}s linear;
        }}
        
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
        
        <!-- Progressive obstacles -->
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
        
        <div class="difficulty-meter">
            Difficulty: {st.session_state.level}/20
            <div class="difficulty-bar">
                <div class="difficulty-fill"></div>
            </div>
            <small>Obstacles: {st.session_state.obstacle_count}</small>
        </div>
        
        <!-- Auto-level transition screen (no manual button) -->
        <div class="level-transition" id="levelTransition">
            <h1>LEVEL {st.session_state.level} COMPLETE!</h1>
            <p>Auto-advancing to Level {st.session_state.level + 1}...</p>
            <p style="font-size: 18px; color: #ccc;">Difficulty increased!</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
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
        const levelTransition = document.getElementById('levelTransition');
        const progressFill = document.getElementById('progressFill');
        
        // Progressive difficulty parameters
        const friction = {st.session_state.friction};
        const aimLineMaxLength = {st.session_state.aim_line_max_length};
        const powerMultiplier = {st.session_state.power_multiplier};
        const maxPower = 100;
        const advanceDelay = {st.session_state.advance_delay};  // Auto-skip delay (ms)
        
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
            const lineLength = (power / maxPower) * aimLineMaxLength;
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
            
            const deltaX = (startX - endX) / powerMultiplier;
            const deltaY = (startY - endY) / powerMultiplier;
            
            // Random variance for harder levels
            const randomVariance = {min(0.15, 0.02 + (st.session_state.level * 0.007))};
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
            if (Math.abs(velocityX) < 0.08 && Math.abs(velocityY) < 0.08) {{
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
                
                // Narrower threshold for harder levels
                const holeThreshold = {max(12, 15 - (st.session_state.level * 0.15))};
                if (distanceToHole < holeThreshold) {{
                    // Trigger auto-level transition (NO MANUAL INPUT NEEDED)
                    triggerAutoLevelAdvance();
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
            
            // Physics
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
            
            // Obstacle collision with random bounce
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
                    const bounceVariance = {min(0.3, 0.1 + (st.session_state.level * 0.01))};
                    const randomBounceX = (Math.random() - 0.5) * bounceVariance;
                    const randomBounceY = (Math.random() - 0.5) * bounceVariance;
                    
                    velocityX = (velocityX * -0.7) + randomBounceX;
                    velocityY = (velocityY * -0.7) + randomBounceY;
                    newX = currentX + velocityX;
                    newY = currentY + velocityY;
                }}
            }});
            
            ball.style.left = newX + 'px';
            ball.style.top = newY + 'px';
            
            requestAnimationFrame(moveBall);
        }}

        // --------------------------
        // AUTO-LEVEL ADVANCE (NO MANUAL INPUT)
        // --------------------------
        function triggerAutoLevelAdvance() {{
            // Show transition screen
            levelTransition.classList.add('active');
            
            // Animate progress bar
            progressFill.style.width = '100%';
            
            // Calculate score and send to Streamlit
            const currentStrokes = {st.session_state.strokes};
            const currentLevel = {st.session_state.level};
            const par = 3 + Math.ceil(currentLevel * 0.7);
            const baseScore = Math.max(100 - ((currentStrokes - par) * 25), 10);
            const difficultyBonus = currentLevel * 10;
            const totalScore = baseScore + difficultyBonus;
            
            // Send hole-in event to trigger auto-advance
            window.parent.postMessage({{
                type: 'HOLE_IN',
                score: totalScore,
                level: currentLevel
            }}, '*');
            
            // Auto-reload after delay (triggers next level)
            setTimeout(() => {{
                window.location.reload();
            }}, advanceDelay);
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
                levelTransition.classList.remove('active');
                progressFill.style.width = '0%';
            }}
        }});
    </script>
</body>
</html>
"""

# --------------------------
# Streamlit UI (No manual level buttons needed)
# --------------------------
st.title("⛳ Auto-Skip Golf Game (Progressive Difficulty)")

# Game Over Screen (after level 20)
if st.session_state.game_over:
    st.success(f"""
        🎉 CONGRATULATIONS!
        You completed all 20 levels of progressive difficulty!
        
        Final Score: {st.session_state.score}
        You mastered the hardest challenges!
    """)
    if st.button("Play Again", type="primary"):
        reset_game()
        st.rerun()

# Active Game Screen (no manual level buttons)
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
        st.write(f"🔹 Obstacles: {st.session_state.obstacle_count}")
        st.write(f"🔹 Friction: {st.session_state.friction:.2f} (Faster stop)")
        st.write(f"🔹 Aim Line Length: {st.session_state.aim_line_max_length}px")
        st.write(f"🔹 Auto-Skip Delay: {st.session_state.advance_delay / 1000}s")
        
        # Only reset button (no skip level button)
        st.subheader("Controls")
        if st.button("Reset Game", type="primary"):
            reset_game()
            st.rerun()

# --------------------------
# Auto-Level Message Handler
# --------------------------
components.html(f"""
<script>
    let isProcessing = false;
    
    window.addEventListener('message', async (event) => {{
        if (isProcessing) return;
        isProcessing = true;
        
        try {{
            if (event.data.type === 'STROKE') {{
                // Increment strokes
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
                // Update score
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['score', {st.session_state.score} + event.data.score],
                        kwargs: {{}}
                    }})
                }});
                
                // Set auto-advance flag (triggers next level automatically)
                await fetch('/_stcore/stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        method: 'set_item',
                        args: ['auto_advance', true],
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
