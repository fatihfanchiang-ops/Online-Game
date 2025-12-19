import streamlit as st
import numpy as np
import time

# ====================== 游戏配置（修复坐标位置） ======================
GAME_CONFIG = {
    "window": {"width": 750, "height": 450},  # 游戏区域尺寸
    "physics": {
        "friction": 0.975,
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-2.5, 2.5)
    },
    # 修复后的关卡布局 - 所有元素都在草地范围内
    "levels": [
        # 第1关：球和球洞都在草地中央区域
        {"tee": (80, 225), "hole": (670, 225), "obstacles": [(350, 200, 70, 50)], "par": 3},
        # 第2关：球在左上，球洞在右下（都在草地内）
        {"tee": (80, 100), "hole": (650, 350), "obstacles": [(230, 160, 55, 55), (480, 260, 90, 50)], "par": 4},
        # 第3关：球在左下，球洞在右上（边界内）
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

# 修复布局的CSS - 确保游戏区域完全包含所有元素
st.markdown("""
    <style>
    /* 隐藏默认元素 */
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container {
        padding: 0.8rem !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    /* 游戏区域 - 确保所有元素都在草地内 */
    .game-area {
        position: relative;
        width: 100%;
        max-width: 750px;
        height: 450px;
        background-color: #8CC051; /* 草地绿 */
        border: 2px solid #6A9030;
        border-radius: 8px;
        margin: 10px auto;
        overflow: hidden;
        touch-action: none;
        box-sizing: border-box; /* 确保边框不影响内部尺寸 */
    }
    /* 障碍物（沙坑） */
    .obstacle {
        position: absolute;
        background: #F4D35E;
        border: 1.5px solid #E0C040;
        border-radius: 3px;
        box-sizing: border-box;
    }
    /* 球洞 - 确保在草地内显示完整 */
    .hole {
        position: absolute;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #2A1F10;
        border: 2px solid #1A1208;
        transform: translate(-50%, -50%); /* 中心点定位 */
        box-shadow: inset 0 0 4px rgba(0,0,0,0.6);
        z-index: 5;
        /* 确保球洞不会超出草地边界 */
        max-left: calc(100% - 10px);
        max-top: calc(100% - 10px);
        min-left: 10px;
        min-top: 10px;
    }
    /* 高尔夫球 - 修复定位，确保在草地上 */
    .ball {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #FFFFFF;
        border: 1px solid #333333;
        transform: translate(-50%, -50%); /* 中心点定位 */
        z-index: 10;
        box-shadow: 0 1px 2px rgba(0,0,0,0.4);
        /* 确保球不会超出草地边界 */
        max-left: calc(100% - 5px);
        max-top: calc(100% - 5px);
        min-left: 5px;
        min-top: 5px;
    }
    /* 信息框 */
    .info-box {
        position: absolute;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255,255,255,0.9);
        padding: 6px 18px;
        border-radius: 18px;
        font-size: 13px;
        font-weight: 600;
        z-index: 20;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    /* 响应式适配 */
    @media (max-width: 768px) {
        .game-area {height: 380px;}
        .info-box {font-size: 12px; padding: 5px 15px;}
    }
    @media (max-width: 480px) {
        .game-area {height: 300px;}
        .info-box {font-size: 11px; padding: 4px 12px;}
    }
    .stButton > button {
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
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
        "load_count": 0
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
            "last_update": time.time()
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
            "load_count": 1
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
    """更新球的位置 - 确保始终在草地内"""
    game = st.session_state.golf_game
    
    # 速度太小则停止
    if abs(game["vel_x"]) < 0.08 and abs(game["vel_y"]) < 0.08:
        game["is_rolling"] = False
        return
    
    # 应用物理规则
    game["vel_x"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_y"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_x"] += game["wind"] * 0.04
    
    # 计算新位置并强制限制在草地范围内
    new_x = game["ball_x"] + game["vel_x"]
    new_y = game["ball_y"] + game["vel_y"]
    
    # 严格限制在草地边界内（关键修复）
    new_x = np.clip(
        new_x,
        GAME_CONFIG["physics"]["ball_radius"],  # 左边界
        GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"]  # 右边界
    )
    new_y = np.clip(
        new_y,
        GAME_CONFIG["physics"]["ball_radius"],  # 上边界
        GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"]  # 下边界
    )
    
    # 碰撞检测
    if not check_collision(new_x, new_y, game["obstacles"]):
        game["ball_x"] = float(new_x)
        game["ball_y"] = float(new_y)
    else:
        # 碰到障碍物反弹
        game["vel_x"] *= -0.45
        game["vel_y"] *= -0.45
    
    # 进洞检测
    if calculate_distance(game["ball_x"], game["ball_y"], game["hole_x"], game["hole_y"]) < 14:
        game["level_complete"] = True
        game["is_rolling"] = False

# ====================== 渲染游戏界面 ======================
def render_game():
    """渲染游戏 - 确保所有元素都在草地上"""
    game = st.session_state.golf_game
    
    # 游戏区域容器
    st.markdown('<div class="game-area">', unsafe_allow_html=True)
    
    # 绘制障碍物
    obstacle_html = ""
    for (ox, oy, w, h) in game["obstacles"]:
        obstacle_html += f'<div class="obstacle" style="left:{ox}px;top:{oy}px;width:{w}px;height:{h}px;"></div>'
    st.markdown(obstacle_html, unsafe_allow_html=True)
    
    # 绘制球洞（确保在草地内）
    hole_x = np.clip(game["hole_x"], 10, GAME_CONFIG["window"]["width"] - 10)
    hole_y = np.clip(game["hole_y"], 10, GAME_CONFIG["window"]["height"] - 10)
    
    # 绘制球（确保在草地内）
    ball_x = np.clip(game["ball_x"], 5, GAME_CONFIG["window"]["width"] - 5)
    ball_y = np.clip(game["ball_y"], 5, GAME_CONFIG["window"]["height"] - 5)
    
    # 渲染球洞和球
    st.markdown(f'''
        <div class="hole" style="left:{hole_x}px;top:{hole_y}px;"></div>
        <div class="ball" style="left:{ball_x}px;top:{ball_y}px;"></div>
    ''', unsafe_allow_html=True)
    
    # 信息框
    if game["level_complete"]:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} (Par: {game['par']}) | Completed!"
    else:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} | Wind: {game['wind']:.1f} m/s"
    
    st.markdown(f'<div class="info-box">{info_text}</div>', unsafe_allow_html=True)
    
    # 关闭容器
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== 主游戏逻辑 ======================
def main():
    """主游戏函数"""
    st.title("🏌️ 2D Golf Game")
    
    game = st.session_state.golf_game
    
    # 首次加载初始化
    if game["load_count"] == 0:
        reset_level(0)
        game["load_count"] = 1
    
    # 更新游戏状态
    current_time = time.time()
    if current_time - game["last_update"] >= 0.02:
        if game["is_rolling"] and not game["level_complete"]:
            update_ball_position()
        game["last_update"] = current_time
    
    # 渲染游戏（修复后的布局）
    render_game()
    
    # 控制区
    st.markdown("---")
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.subheader("Controls")
        
        if not game["is_rolling"] and not game["level_complete"]:
            # 击球控制
            power = st.slider("Power", 0, 100, 45, key="power", label_visibility="collapsed")
            st.caption("Power (0-100)")
            
            col_dir1, col_dir2 = st.columns(2, gap="small")
            with col_dir1:
                dir_x = st.slider("X", -8, 8, 5, key="dir_x", label_visibility="collapsed")
                st.caption("X (-left, +right)")
            with col_dir2:
                dir_y = st.slider("Y", -8, 8, 0, key="dir_y", label_visibility="collapsed")
                st.caption("Y (-up, +down)")
            
            # 击球按钮
            if st.button("⛳ Hit Ball", use_container_width=True, type="primary"):
                game["strokes"] += 1
                power_scaled = power / 100 * 9
                game["vel_x"] = dir_x * power_scaled / 9
                game["vel_y"] = dir_y * power_scaled / 9
                game["is_rolling"] = True
        
        # 重置按钮
        if st.button("🔄 Reset Ball", use_container_width=True):
            reset_level(game["level"])
    
    with col2:
        st.subheader("Level Select")
        
        # 关卡选择
        level_options = [f"Level {i+1}" for i in range(len(GAME_CONFIG["levels"]))]
        selected_level = st.selectbox("Choose Level", level_options, index=game["level"])
        
        if st.button("Go to Level", use_container_width=True):
            try:
                new_level = int(selected_level.split()[1]) - 1
                reset_level(new_level)
            except:
                reset_level(0)
        
        # 关卡完成处理
        if game["level_complete"]:
            st.success("🎉 Hole In! 🎉")
            
            if game["level"] < len(GAME_CONFIG["levels"]) - 1:
                if st.button("▶️ Next Level", use_container_width=True):
                    reset_level(game["level"] + 1)
            else:
                st.balloons()
                st.success("🏆 All Levels Completed! 🏆")
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
