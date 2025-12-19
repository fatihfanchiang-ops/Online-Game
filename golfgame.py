import streamlit as st
import numpy as np
import time
import json

# ====================== 游戏配置 ======================
GAME_CONFIG = {
    "window": {"width": 750, "height": 450},
    "physics": {
        "friction": 0.975,
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-2.5, 2.5),
        "power_scale": 0.2,       # 力度缩放（增大让拖拽更明显）
        "max_drag_distance": 100  # 最大拖拽距离（对应100%力度）
    },
    "levels": [
        {"tee": (80, 225), "hole": (670, 225), "obstacles": [(350, 200, 70, 50)], "par": 3},
        {"tee": (80, 100), "hole": (650, 350), "obstacles": [(230, 160, 55, 55), (480, 260, 90, 50)], "par": 4},
        {"tee": (80, 350), "hole": (660, 120), "obstacles": [(180, 230, 65, 65), (380, 130, 75, 75), (530, 280, 65, 65)], "par": 5},
    ]
}

# ====================== 页面设置 ======================
st.set_page_config(
    page_title="2D Golf Game",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🏌️"
)

# 拖拽操作+力度进度条专用CSS
st.markdown("""
    <style>
    /* 隐藏默认元素 */
    #MainMenu, footer, header {visibility: hidden !important;}
    
    /* 主容器 */
    .block-container {
        padding: 1rem !important;
        max-width: 850px !important;
        margin: 0 auto !important;
    }
    
    /* 游戏区域 - 支持拖拽操作 */
    .game-area {
        position: relative;
        width: 100%;
        max-width: 750px;
        height: 450px;
        background-color: #8CC051;
        border: 2px solid #6A9030;
        border-radius: 8px;
        margin: 20px auto;
        overflow: hidden;
        touch-action: none;
        box-sizing: border-box;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        cursor: grab;
    }
    
    .game-area:active {
        cursor: grabbing;
    }
    
    /* 障碍物 */
    .obstacle {
        position: absolute;
        background: #F4D35E;
        border: 1.5px solid #E0C040;
        border-radius: 3px;
        box-sizing: border-box;
    }
    
    /* 球洞 */
    .hole {
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #2A1F10;
        border: 2px solid #1A1208;
        transform: translate(-50%, -50%);
        box-shadow: inset 0 0 4px rgba(0,0,0,0.6);
        z-index: 5;
    }
    
    /* 高尔夫球 - 拖拽操作优化 */
    .ball {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #FFFFFF;
        border: 1px solid #333333;
        transform: translate(-50%, -50%);
        z-index: 10;
        box-shadow: 0 1px 2px rgba(0,0,0,0.4);
        transition: transform 0.1s ease;
    }
    
    .ball.dragging {
        transform: translate(-50%, -50%) scale(1.3);
        box-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }
    
    /* 拖拽轨迹线 */
    .drag-line {
        position: absolute;
        border: 2px solid #ff6b6b;
        z-index: 8;
        pointer-events: none;
        opacity: 0.8;
    }
    
    /* 力度进度条容器 */
    .power-meter-container {
        position: absolute;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 250px;
        height: 20px;
        background-color: #e9ecef;
        border-radius: 10px;
        border: 2px solid #ced4da;
        overflow: hidden;
        z-index: 15;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        display: none;
    }
    
    .power-meter-container.visible {
        display: block;
    }
    
    /* 力度进度条 */
    .power-meter-fill {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #4CAF50, #FFEB3B, #F44336);
        border-radius: 8px;
        transition: width 0.05s linear;
    }
    
    /* 力度数值显示 */
    .power-value {
        position: absolute;
        bottom: 55px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.7);
        color: white;
        padding: 3px 10px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        z-index: 16;
        display: none;
    }
    
    .power-value.visible {
        display: block;
    }
    
    /* 力度刻度标记 */
    .power-markers {
        position: absolute;
        bottom: 58px;
        left: 50%;
        transform: translateX(-50%);
        width: 250px;
        height: 10px;
        z-index: 15;
        display: none;
    }
    
    .power-markers.visible {
        display: block;
    }
    
    .power-marker {
        position: absolute;
        width: 1px;
        height: 8px;
        background-color: #666;
        top: 0;
    }
    
    .power-marker-label {
        position: absolute;
        font-size: 10px;
        color: #666;
        transform: translateX(-50%);
        top: 10px;
    }
    
    /* 信息框 */
    .info-box {
        position: absolute;
        top: 8px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255,255,255,0.95);
        padding: 6px 20px;
        border-radius: 18px;
        font-size: 13px;
        font-weight: 600;
        z-index: 20;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        max-width: 90%;
    }
    
    /* 操作提示 */
    .control-tip {
        text-align: center;
        color: #333;
        font-size: 15px;
        margin: 10px 0;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        margin: 5px auto !important;
        display: block !important;
        width: 200px !important;
    }
    
    h1 {
        text-align: center;
        margin-bottom: 10px !important;
    }
    
    h2 {
        font-size: 1.2rem !important;
        text-align: center;
        margin: 15px 0 5px 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== 初始化游戏状态 ======================
if "golf_game" not in st.session_state:
    st.session_state.golf_game = {
        "level": 0,
        "ball_x": GAME_CONFIG["levels"][0]["tee"][0],
        "ball_y": GAME_CONFIG["levels"][0]["tee"][1],
        "hole_x": GAME_CONFIG["levels"][0]["hole"][0],
        "hole_y": GAME_CONFIG["levels"][0]["hole"][1],
        "obstacles": GAME_CONFIG["levels"][0]["obstacles"],
        "par": GAME_CONFIG["levels"][0]["par"],
        "strokes": 0,
        "vel_x": 0.0,
        "vel_y": 0.0,
        "is_rolling": False,
        "level_complete": False,
        "wind": float(np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"])),
        "last_update": time.time(),
        "load_count": 0,
        # 拖拽相关状态
        "drag_start_x": 0,
        "drag_start_y": 0,
        "is_dragging": False,
        "drag_power": 0,
        "drag_distance": 0
    }

# ====================== 核心函数 ======================
def reset_level(level_idx):
    """重置关卡"""
    game = st.session_state.golf_game
    level = GAME_CONFIG["levels"][level_idx]
    
    try:
        game.update({
            "level": level_idx,
            "ball_x": float(level["tee"][0]),
            "ball_y": float(level["tee"][1]),
            "hole_x": float(level["hole"][0]),
            "hole_y": float(level["hole"][1]),
            "obstacles": level["obstacles"].copy(),
            "par": int(level["par"]),
            "strokes": 0,
            "vel_x": 0.0,
            "vel_y": 0.0,
            "is_rolling": False,
            "level_complete": False,
            "wind": float(np.random.uniform(*GAME_CONFIG["physics"]["wind_strength"])),
            "last_update": time.time(),
            # 重置拖拽状态
            "drag_start_x": 0,
            "drag_start_y": 0,
            "is_dragging": False,
            "drag_power": 0,
            "drag_distance": 0
        })
    except Exception:
        st.session_state.golf_game = {
            "level": level_idx,
            "ball_x": float(level["tee"][0]),
            "ball_y": float(level["tee"][1]),
            "hole_x": float(level["hole"][0]),
            "hole_y": float(level["hole"][1]),
            "obstacles": level["obstacles"],
            "par": int(level["par"]),
            "strokes": 0,
            "vel_x": 0.0,
            "vel_y": 0.0,
            "is_rolling": False,
            "level_complete": False,
            "wind": 0.0,
            "last_update": time.time(),
            "load_count": 1,
            "drag_start_x": 0,
            "drag_start_y": 0,
            "is_dragging": False,
            "drag_power": 0,
            "drag_distance": 0
        }

def calculate_distance(x1, y1, x2, y2):
    """计算两点之间的距离"""
    return np.hypot(x1 - x2, y1 - y2)

def check_collision(x, y, obstacles):
    """检测碰撞"""
    radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - radius <= x <= ox + w + radius) and (oy - radius <= y <= oy + h + radius):
            return True
    return False

def update_ball_position():
    """更新球的位置"""
    game = st.session_state.golf_game
    
    if abs(game["vel_x"]) < 0.08 and abs(game["vel_y"]) < 0.08:
        game["is_rolling"] = False
        return
    
    game["vel_x"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_y"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_x"] += game["wind"] * 0.04
    
    new_x = game["ball_x"] + game["vel_x"]
    new_y = game["ball_y"] + game["vel_y"]
    
    # 边界限制
    new_x = np.clip(
        new_x,
        GAME_CONFIG["physics"]["ball_radius"],
        GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"]
    )
    new_y = np.clip(
        new_y,
        GAME_CONFIG["physics"]["ball_radius"],
        GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"]
    )
    
    if not check_collision(new_x, new_y, game["obstacles"]):
        game["ball_x"] = float(new_x)
        game["ball_y"] = float(new_y)
    else:
        game["vel_x"] *= -0.45
        game["vel_y"] *= -0.45
    
    if calculate_distance(game["ball_x"], game["ball_y"], game["hole_x"], game["hole_y"]) < 14:
        game["level_complete"] = True
        game["is_rolling"] = False

# ====================== 渲染游戏界面（支持拖拽+力度进度条） ======================
def render_game():
    """渲染游戏 - 支持拖拽操作和力度进度条"""
    game = st.session_state.golf_game
    
    # 游戏区域容器
    game_html = '<div class="game-area" id="gameArea">'
    
    # 绘制障碍物
    for (ox, oy, w, h) in game["obstacles"]:
        game_html += f'<div class="obstacle" style="left:{ox}px;top:{oy}px;width:{w}px;height:{h}px;"></div>'
    
    # 绘制球洞
    hole_x = np.clip(game["hole_x"], 10, GAME_CONFIG["window"]["width"] - 10)
    hole_y = np.clip(game["hole_y"], 10, GAME_CONFIG["window"]["height"] - 10)
    game_html += f'<div class="hole" style="left:{hole_x}px;top:{hole_y}px;"></div>'
    
    # 绘制拖拽轨迹线（如果正在拖拽）
    if game["is_dragging"] and game["drag_start_x"] and game["drag_start_y"]:
        ball_x = np.clip(game["ball_x"], 5, GAME_CONFIG["window"]["width"] - 5)
        ball_y = np.clip(game["ball_y"], 5, GAME_CONFIG["window"]["height"] - 5)
        
        # 计算轨迹线参数
        drag_distance = calculate_distance(game["drag_start_x"], game["drag_start_y"], ball_x, ball_y)
        # 限制最大拖拽距离
        drag_distance = min(drag_distance, GAME_CONFIG["physics"]["max_drag_distance"])
        angle = np.arctan2(game["drag_start_y"] - ball_y, game["drag_start_x"] - ball_x)
        
        # 轨迹线（长度随拖拽距离变化）
        game_html += f'''
        <div class="drag-line" style="
            width: {drag_distance}px;
            height: 0;
            left: {ball_x}px;
            top: {ball_y}px;
            transform-origin: 0% 50%;
            transform: rotate({np.degrees(angle)}deg);
            opacity: {0.5 + min(game["drag_power"], 100)/200};
        "></div>
        '''
    
    # 绘制高尔夫球（添加拖拽状态）
    ball_x = np.clip(game["ball_x"], 5, GAME_CONFIG["window"]["width"] - 5)
    ball_y = np.clip(game["ball_y"], 5, GAME_CONFIG["window"]["height"] - 5)
    drag_class = "dragging" if game["is_dragging"] else ""
    game_html += f'<div class="ball {drag_class}" style="left:{ball_x}px;top:{ball_y}px;"></div>'
    
    # 信息框
    if game["level_complete"]:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} (Par: {game['par']}) | Completed!"
    else:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} | Wind: {game['wind']:.1f} m/s"
    
    game_html += f'<div class="info-box">{info_text}</div>'
    
    # 力度进度条容器
    power_visible = "visible" if game["is_dragging"] else ""
    power_percentage = min(int(game["drag_power"]), 100)
    
    # 力度刻度标记
    markers_html = ""
    for i in range(0, 101, 20):  # 每20%一个刻度
        markers_html += f'''
        <div class="power-marker" style="left: {i}%;"></div>
        <div class="power-marker-label" style="left: {i}%;">{i}%</div>
        '''
    
    # 添加力度进度条
    game_html += f'''
    <!-- 力度刻度 -->
    <div class="power-markers {power_visible}">
        {markers_html}
    </div>
    
    <!-- 力度数值 -->
    <div class="power-value {power_visible}">
        {power_percentage}% Power
    </div>
    
    <!-- 力度进度条 -->
    <div class="power-meter-container {power_visible}">
        <div class="power-meter-fill" style="width: {power_percentage}%;"></div>
    </div>
    '''
    
    # 关闭容器
    game_html += '</div>'
    
    # 添加拖拽交互的JavaScript（优化力度计算）
    drag_js = f"""
    <script>
    // 获取游戏状态
    const gameState = {json.dumps(game)};
    const maxDragDistance = {GAME_CONFIG["physics"]["max_drag_distance"]};
    const powerScale = {GAME_CONFIG["physics"]["power_scale"]};
    const gameArea = document.getElementById('gameArea');
    let isDragging = false;
    let startX, startY;
    let ballX = {game["ball_x"]};
    let ballY = {game["ball_y"]};
    
    // 拖拽开始
    gameArea.addEventListener('mousedown', startDrag);
    gameArea.addEventListener('touchstart', handleTouchStart, {{passive: true}});
    
    // 拖拽移动
    gameArea.addEventListener('mousemove', dragMove);
    gameArea.addEventListener('touchmove', handleTouchMove, {{passive: true}});
    
    // 拖拽结束
    gameArea.addEventListener('mouseup', endDrag);
    gameArea.addEventListener('mouseleave', endDrag);
    gameArea.addEventListener('touchend', endDrag);
    
    function getPosition(e) {{
        const rect = gameArea.getBoundingClientRect();
        let clientX, clientY;
        
        if (e.touches) {{
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }} else {{
            clientX = e.clientX;
            clientY = e.clientY;
        }}
        
        return {{
            x: clientX - rect.left,
            y: clientY - rect.top
        }};
    }}
    
    function startDrag(e) {{
        // 只有球不滚动时才能拖拽
        if (gameState.is_rolling || gameState.level_complete) return;
        
        const pos = getPosition(e);
        
        // 检查是否点击在球上（15px范围内）
        const distance = Math.hypot(pos.x - ballX, pos.y - ballY);
        if (distance < 15) {{
            isDragging = true;
            startX = pos.x;
            startY = pos.y;
            
            // 更新拖拽状态
            window.parent.postMessage({{
                type: 'drag_start',
                x: startX,
                y: startY
            }}, '*');
        }}
    }}
    
    function handleTouchStart(e) {{
        startDrag(e);
    }}
    
    function dragMove(e) {{
        if (!isDragging) return;
        
        const pos = getPosition(e);
        
        // 计算拖拽距离（从球的位置到拖拽点）
        const dx = startX - pos.x;
        const dy = startY - pos.y;
        const dragDistance = Math.hypot(dx, dy);
        
        // 限制最大拖拽距离
        const clampedDistance = Math.min(dragDistance, maxDragDistance);
        
        // 计算力度百分比（拖拽距离越长，力度越大）
        const powerPercentage = (clampedDistance / maxDragDistance) * 100;
        
        // 更新拖拽状态
        window.parent.postMessage({{
            type: 'drag_move',
            x: pos.x,
            y: pos.y,
            power: powerPercentage,
            distance: clampedDistance
        }}, '*');
    }}
    
    function handleTouchMove(e) {{
        dragMove(e);
    }}
    
    function endDrag(e) {{
        if (!isDragging) return;
        
        isDragging = false;
        const pos = getPosition(e);
        
        // 计算击球力度和方向
        const dx = startX - pos.x;
        const dy = startY - pos.y;
        const dragDistance = Math.hypot(dx, dy);
        
        // 只有拖拽距离大于5px才击球
        if (dragDistance > 5) {{
            // 限制最大力度
            const clampedDistance = Math.min(dragDistance, maxDragDistance);
            const scaleFactor = (clampedDistance / maxDragDistance) * powerScale;
            
            // 发送击球指令（力度与拖拽距离成正比）
            window.parent.postMessage({{
                type: 'shot',
                dx: dx * scaleFactor,
                dy: dy * scaleFactor,
                power: (clampedDistance / maxDragDistance) * 100,
                distance: clampedDistance
            }}, '*');
        }}
        
        // 重置拖拽状态
        window.parent.postMessage({{
            type: 'drag_end'
        }}, '*');
    }}
    </script>
    """
    
    # 渲染游戏和拖拽脚本
    st.markdown(game_html + drag_js, unsafe_allow_html=True)

# ====================== 主游戏逻辑 ======================
def main():
    """主游戏函数 - 支持拖拽操作和力度进度条"""
    st.title("🏌️ 2D Golf Game")
    
    game = st.session_state.golf_game
    
    # 操作提示（强调拖拽长度=力度）
    st.markdown("""
        <div class="control-tip">
            🎮 操作方式：按住小球向后拖拽，拖拽越长，击球力度越大<br>
            📏 力度范围：0-100%（进度条实时显示）| 💨 风力影响：±2.5 m/s
        </div>
    """, unsafe_allow_html=True)
    
    # 首次加载初始化
    if game["load_count"] == 0:
        reset_level(0)
        game["load_count"] = 1
    
    # 处理拖拽消息
    query_params = st.query_params
    if "drag_type" in query_params:
        drag_type = query_params["drag_type"]
        
        if drag_type == "start":
            game["is_dragging"] = True
            game["drag_start_x"] = float(query_params.get("x", 0))
            game["drag_start_y"] = float(query_params.get("y", 0))
        
        elif drag_type == "move":
            if game["is_dragging"]:
                game["drag_power"] = float(query_params.get("power", 0))
                game["drag_distance"] = float(query_params.get("distance", 0))
        
        elif drag_type == "end":
            game["is_dragging"] = False
            game["drag_start_x"] = 0
            game["drag_start_y"] = 0
            game["drag_power"] = 0
            game["drag_distance"] = 0
        
        elif drag_type == "shot":
            # 执行击球（力度与拖拽距离成正比）
            game["strokes"] += 1
            game["vel_x"] = float(query_params.get("dx", 0))
            game["vel_y"] = float(query_params.get("dy", 0))
            game["is_rolling"] = True
            game["is_dragging"] = False
            game["drag_power"] = 0
            game["drag_distance"] = 0
    
    # 更新游戏状态
    current_time = time.time()
    if current_time - game["last_update"] >= 0.02:
        if game["is_rolling"] and not game["level_complete"]:
            update_ball_position()
        game["last_update"] = current_time
    
    # 渲染游戏（支持拖拽+力度进度条）
    render_game()
    
    # 简单的控制按钮（重置/关卡选择）
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Game Controls")
        if st.button("🔄 Reset Ball to Tee", use_container_width=True):
            reset_level(game["level"])
    
    with col2:
        st.subheader("Level Selection")
        # 关卡选择
        level_options = [f"Level {i+1}" for i in range(len(GAME_CONFIG["levels"]))]
        selected_level = st.selectbox("Select Level", level_options, index=game["level"])
        
        if st.button("Go to Selected Level", use_container_width=True):
            try:
                new_level = int(selected_level.split()[1]) - 1
                reset_level(new_level)
            except:
                reset_level(0)
    
    # 关卡完成处理
    if game["level_complete"]:
        st.success("🎉 Hole In! Congratulations! 🎉")
        
        col_buttons = st.columns([1, 1])
        with col_buttons[0]:
            if game["level"] < len(GAME_CONFIG["levels"]) - 1:
                if st.button("▶️ Next Level", use_container_width=True):
                    reset_level(game["level"] + 1)
            else:
                st.balloons()
                st.success("🏆 You Completed All Levels! 🏆")
        
        with col_buttons[1]:
            if st.button("🔁 Play Again", use_container_width=True):
                reset_level(0)

# ====================== 运行游戏 ======================
if __name__ == "__main__":
    try:
        main()
        # 自动刷新
        if not st.session_state.golf_game["level_complete"]:
            st.experimental_rerun()
    except Exception as e:
        st.error("🔄 Game refreshed - minor issue resolved")
        st.session_state.golf_game = {"load_count": 0}
        st.experimental_rerun()
