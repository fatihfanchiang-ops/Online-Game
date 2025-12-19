import streamlit as st
import streamlit.components.v1 as components
import random

# Set page config
st.set_page_config(
    page_title="Drag & Drop Golf Game",
    page_icon="⛳",
    layout="wide"
)

# Game state management
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'strokes' not in st.session_state:
    st.session_state.strokes = 0
if 'level' not in st.session_state:
    st.session_state.level = 1
if 'ball_position' not in st.session_state:
    st.session_state.ball_position = {"x": 100, "y": 400}
if 'hole_position' not in st.session_state:
    st.session_state.hole_position = {
        "x": random.randint(300, 700),
        "y": random.randint(100, 300)
    }

# Reset game function
def reset_game():
    st.session_state.score = 0
    st.session_state.strokes = 0
    st.session_state.level = 1
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = {
        "x": random.randint(300, 700),
        "y": random.randint(100, 300)
    }

# Next level function
def next_level():
    st.session_state.level += 1
    st.session_state.strokes = 0
    st.session_state.ball_position = {"x": 100, "y": 400}
    st.session_state.hole_position = {
        "x": random.randint(400, 800),
        "y": random.randint(50, 350)
    }

# HTML/CSS/JS for the golf game
golf_game_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drag & Drop Golf Game</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
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
    </style>
</head>
<body>
    <div class="golf-course" id="course">
        <div class="golf-ball" id="ball" style="left: {st.session_state.ball_position['x']}px; top: {st.session_state.ball_position['y']}px;"></div>
        <div class="golf-hole" id="hole" style="left: {st.session_state.hole_position['x']}px; top: {st.session_state.hole_position['y']}px;"></div>
        
        <!-- Obstacles (random for each level) -->
        <div class="obstacle" style="width: {50 + st.session_state.level * 10}px; height: {30 + st.session_state.level * 5}px; left: {random.randint(200, 600)}px; top: {random.randint(150, 350)}px;"></div>
        <div class="obstacle" style="width: {40 + st.session_state.level * 8}px; height: {40 + st.session_state.level * 6}px; left: {random.randint(300, 700)}px; top: {random.randint(100, 400)}px;"></div>
        
        <div class="power-indicator">
            <div class="power-bar" id="powerBar"></div>
        </div>
        
        <div class="game-info">
            Level: {st.session_state.level}<br>
            Strokes: {st.session_state.strokes}<br>
            Score: {st.session_state.score}
        </div>
    </div>

    <script>
        // Game elements
        const ball = document.getElementById('ball');
        const hole = document.getElementById('hole');
        const course = document.getElementById('course');
        const powerBar = document.getElementById('powerBar');
        
        // Game variables
        let isDragging = false;
        let startX, startY;
        let power = 0;
        let maxPower = 100;
        let dragDistance = 0;
        
        // Ball physics
        const friction = 0.98;
        let velocityX = 0;
        let velocityY = 0;
        let isMoving = false;
        
        // Start drag
        ball.addEventListener('mousedown', startDrag);
        ball.addEventListener('touchstart', startDrag, {passive: true});
        
        // Mouse move (document level for dragging outside ball)
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, {passive: true});
        
        // End drag
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        function startDrag(e) {{
            isDragging = true;
            // Get initial position
            startX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
            startY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
            
            // Reset power
            power = 0;
            powerBar.style.width = '0%';
            
            // Prevent text selection
            e.preventDefault();
        }}
        
        function drag(e) {{
            if (!isDragging) return;
            
            // Calculate drag distance
            const currentX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
            const currentY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
            
            const deltaX = startX - currentX;
            const deltaY = startY - currentY;
            
            // Calculate drag distance (hypotenuse)
            dragDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
            
            // Update power bar (capped at maxPower)
            power = Math.min(dragDistance, maxPower);
            powerBar.style.width = (power / maxPower) * 100 + '%';
        }}
        
        function endDrag(e) {{
            if (!isDragging) return;
            
            isDragging = false;
            powerBar.style.width = '0%';
            
            // Calculate direction (opposite of drag)
            const endX = e.type === 'touchend' ? e.changedTouches[0].clientX : e.clientX;
            const endY = e.type === 'touchend' ? e.changedTouches[0].clientY : e.clientY;
            
            const deltaX = (startX - endX) / 10; // Divide for speed control
            const deltaY = (startY - endY) / 10;
            
            // Set velocity based on drag distance and direction
            const powerMultiplier = power / maxPower;
            velocityX = deltaX * powerMultiplier;
            velocityY = deltaY * powerMultiplier;
            
            // Start ball movement
            if (!isMoving) {{
                isMoving = true;
                moveBall();
                // Increment strokes
                window.parent.postMessage({{type: 'STROKE'}}, '*');
            }}
        }}
        
        function moveBall() {{
            if (Math.abs(velocityX) < 0.1 && Math.abs(velocityY) < 0.1) {{
                isMoving = false;
                
                // Check if ball is in hole (collision detection)
                const ballRect = ball.getBoundingClientRect();
                const holeRect = hole.getBoundingClientRect();
                
                const ballCenterX = ballRect.left + ballRect.width / 2;
                const ballCenterY = ballRect.top + ballRect.height / 2;
                const holeCenterX = holeRect.left + holeRect.width / 2;
                const holeCenterY = holeRect.top + holeRect.height / 2;
                
                const distanceToHole = Math.sqrt(
                    Math.pow(ballCenterX - holeCenterX, 2) +
                    Math.pow(ballCenterY - holeCenterY, 2)
                );
                
                // If ball is in hole (distance < 15px)
                if (distanceToHole < 15) {{
                    // Calculate score (par is 3 + level)
                    const par = 3 + {st.session_state.level};
                    const scoreGain = Math.max(100 - ({st.session_state.strokes} - par) * 20, 10);
                    window.parent.postMessage({{
                        type: 'HOLE_IN',
                        score: scoreGain,
                        level: {st.session_state.level} + 1
                    }}, '*');
                }}
                
                // Update ball position in session state
                const ballX = parseFloat(ball.style.left) || 0;
                const ballY = parseFloat(ball.style.top) || 0;
                window.parent.postMessage({{
                    type: 'POSITION',
                    x: ballX,
                    y: ballY
                }}, '*');
                
                return;
            }}
            
            // Apply friction
            velocityX *= friction;
            velocityY *= friction;
            
            // Get current position
            let currentX = parseFloat(ball.style.left) || 0;
            let currentY = parseFloat(ball.style.top) || 0;
            
            // Calculate new position
            let newX = currentX + velocityX;
            let newY = currentY + velocityY;
            
            // Keep ball within course bounds
            const courseRect = course.getBoundingClientRect();
            const ballRadius = ball.offsetWidth / 2;
            
            newX = Math.max(ballRadius, Math.min(courseRect.width - ballRadius, newX));
            newY = Math.max(ballRadius, Math.min(courseRect.height - ballRadius, newY));
            
            // Check obstacle collision (simplified)
            const obstacles = document.querySelectorAll('.obstacle');
            obstacles.forEach(obstacle => {{
                const obsRect = obstacle.getBoundingClientRect();
                const ballRect = {{
                    left: newX - ballRadius,
                    top: newY - ballRadius,
                    right: newX + ballRadius,
                    bottom: newY + ballRadius
                }};
                
                // Simple AABB collision detection
                if (
                    ballRect.left < obsRect.right &&
                    ballRect.right > obsRect.left &&
                    ballRect.top < obsRect.bottom &&
                    ballRect.bottom > obsRect.top
                ) {{
                    // Reverse velocity on collision
                    velocityX *= -0.7;
                    velocityY *= -0.7;
                    newX = currentX + velocityX;
                    newY = currentY + velocityY;
                }}
            }});
            
            // Update ball position
            ball.style.left = newX + 'px';
            ball.style.top = newY + 'px';
            
            // Continue animation
            requestAnimationFrame(moveBall);
        }}
        
        // Listen for reset from Streamlit
        window.addEventListener('message', (event) => {{
            if (event.data.type === 'RESET') {{
                ball.style.left = '100px';
                ball.style.top = '400px';
                hole.style.left = '{random.randint(300, 700)}px';
                hole.style.top = '{random.randint(100, 300)}px';
                velocityX = 0;
                velocityY = 0;
                isMoving = false;
            }}
        }});
    </script>
</body>
</html>
"""

# Streamlit UI
st.title("⛳ Drag & Drop Golf Game")
st.markdown("### How to Play:")
st.markdown("1. Drag the golf ball backward to aim (the farther you drag, the more power)")
st.markdown("2. Release to hit the ball toward the hole")
st.markdown("3. Avoid obstacles and get the ball in the hole with as few strokes as possible")
st.markdown("4. Each level gets harder with more obstacles!")

# Create two columns for game and controls
col1, col2 = st.columns([3, 1])

with col1:
    # Render the golf game HTML
    components.html(golf_game_html, height=550, width=950)

with col2:
    st.header("Game Controls")
    st.metric("Current Level", st.session_state.level)
    st.metric("Strokes", st.session_state.strokes)
    st.metric("Total Score", st.session_state.score)
    
    # Buttons
    if st.button("Reset Game", type="primary"):
        reset_game()
        st.rerun()
    
    if st.button("Next Level (Cheat)", disabled=st.session_state.level >= 5):
        next_level()
        st.rerun()
    
    st.info("🏆 Score more points by getting the ball in the hole with fewer strokes!")
    st.warning("⚠️ Obstacles will bounce your ball - aim carefully!")

# JavaScript to handle messages from the game
components.html("""
<script>
    // Listen for messages from the game iframe
    window.addEventListener('message', (event) => {
        if (event.data.type === 'STROKE') {
            // Increment strokes in Streamlit
            fetch('/_stcore/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'method': 'set_item',
                    'args': ['strokes', %s + 1],
                    'kwargs': {}
                })
            }).then(() => window.location.reload());
        }
        
        if (event.data.type === 'HOLE_IN') {
            // Update score and level
            fetch('/_stcore/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'method': 'set_item',
                    'args': ['score', %s + event.data.score],
                    'kwargs': {}
                })
            }).then(() => {
                fetch('/_stcore/stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        'method': 'set_item',
                        'args': ['level', event.data.level],
                        'kwargs': {}
                    })
                }).then(() => {
                    fetch('/_stcore/stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            'method': 'set_item',
                            'args': ['strokes', 0],
                            'kwargs': {}
                        })
                    }).then(() => window.location.reload());
                });
            });
        }
        
        if (event.data.type === 'POSITION') {
            // Update ball position
            fetch('/_stcore/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'method': 'set_item',
                    'args': ['ball_position', {x: event.data.x, y: event.data.y}],
                    'kwargs': {}
                })
            });
        }
    });
</script>
""" % (st.session_state.strokes, st.session_state.score), height=0, width=0)

# Game instructions
st.markdown("---")
st.subheader("Game Rules")
st.markdown("""
- **Par**: Each level has a par (3 + level number) - try to get the ball in the hole in par or fewer strokes for maximum points
- **Power**: The farther you drag the ball back, the more power your shot has
- **Obstacles**: Trees (brown rectangles) will bounce your ball - plan your shots around them
- **Scoring**: 100 points for par, 80 points for 1 over par, 60 for 2 over, etc. (minimum 10 points)
""")
