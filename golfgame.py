import streamlit as st
import numpy as np
import time

# ====================== 线上部署优化配置 ======================
GAME_CONFIG = {
    "window": {"width": 750, "height": 450},  # 适配Streamlit Cloud默认宽高
    "physics": {
        "friction": 0.975,  # 微调摩擦力，让滚动更自然
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-2.5, 2.5)  # 降低风力影响，提升可控性
    },
    # 最终调整的关卡布局（适配线上显示）
    "levels": [
        # 第1关：新手友好，球洞位置居中偏右
        {"tee": (70, 225), "hole": (680, 225), "obstacles": [(350, 200, 70, 50)], "par": 3},
        # 第2关：中等难度，球洞在右下角（避开边缘）
        {"tee": (70, 90), "hole": (660, 380), "obstacles": [(230, 160, 55, 55), (480, 260, 90, 50)], "par": 4},
        # 第3关：进阶难度，球洞在右上角（视觉清晰）
        {"tee": (70, 380), "hole": (670, 110), "obstacles": [(180, 230, 65, 65), (380, 130, 75, 75), (530, 280, 65, 65)], "par": 5},
    ]
}

# ====================== 线上部署专属页面设置 ======================
st.set_page_config(
    page_title="2D Golf Game",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🏌️"
)

# 适配线上环境的CSS（优化渲染性能）
st.markdown("""
    <style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container {
        padding: 0.8rem !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    /* 游戏区域（适配线上容器） */
    .game-area {
        position: relative;
        width: 100%;
        max-width: 750px;
        height: 450px;
        background-color: #8CC051;
        border: 2px solid #6A9030;
        border-radius: 8px;
        margin: 10px auto;
        overflow: hidden;
        touch-action: none;  /* 禁用默认触摸行为，提升响应 */
    }
    /* 障碍物（沙坑） */
    .obstacle {
        position: absolute;
        background: #F4D35E;
        border: 1.5px solid #E0C040;
        border-radius: 3px;
    }
    /* 球洞（优化线上显示清晰度） */
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
    /* 高尔夫球（提升线上辨识度） */
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
    }
    /* 信息框（适配线上文字显示） */
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
    /* 响应式适配（线上多设备兼容） */
    @media (max-width: 768px) {
        .game-area {height: 380px;}
        .info-box {font-size: 12px; padding: 5px 15px;}
    }
    @media (max-width: 480px) {
        .game-area {height: 300px;}
        .info-box {font-size: 11px; padding: 4px 12px;}
    }
    /* 按钮样式优化（线上交互更友好） */
    .stButton > button {
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
    }
    .stSlider > div > div > div > div {
        height: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== 初始化游戏状态（线上兼容版） ======================
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
        "load_count": 0  # 线上加载计数，避免重复初始化
    }

# ====================== 核心函数（线上稳定性优化） ======================
def reset_level(level_idx):
    """重置关卡（适配线上状态管理）"""
    game = st.session_state.golf_game
    level = GAME_CONFIG["levels"][level_idx]
    
    # 线上环境安全更新状态
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
        # 线上环境异常容错
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
    """简化距离计算，提升线上性能"""
    return np.hypot(x1 - x2, y1 - y2)

def check_collision(x, y, obstacles):
    """轻量化碰撞检测（适配线上性能）"""
    radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - radius <= x <= ox + w + radius) and (oy - radius <= y <= oy + h + radius):
            return True
    return False

def update_ball_position():
    """优化球位置更新（减少线上计算量）"""
    game = st.session_state.golf_game
    
    # 速度阈值优化，避免线上无限循环
    if abs(game["vel_x"]) < 0.08 and abs(game["vel_y"]) < 0.08:
        game["is_rolling"] = False
        return
    
    # 物理参数适配线上运行
    game["vel_x"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_y"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_x"] += game["wind"] * 0.04  # 降低风力权重，提升可控性
    
    # 计算新位置（避免浮点数溢出）
    new_x = np.clip(
        game["ball_x"] + game["vel_x"],
        GAME_CONFIG["physics"]["ball_radius"],
        GAME_CONFIG["window"]["width"] - GAME_CONFIG["physics"]["ball_radius"]
    )
    new_y = np.clip(
        game["ball_y"] + game["vel_y"],
        GAME_CONFIG["physics"]["ball_radius"],
        GAME_CONFIG["window"]["height"] - GAME_CONFIG["physics"]["ball_radius"]
    )
    
    # 碰撞处理（线上稳定性优先）
    if not check_collision(new_x, new_y, game["obstacles"]):
        game["ball_x"] = float(new_x)
        game["ball_y"] = float(new_y)
    else:
        game["vel_x"] *= -0.45
        game["vel_y"] *= -0.45
    
    # 进洞检测（优化线上判定精度）
    if calculate_distance(game["ball_x"], game["ball_y"], game["hole_x"], game["hole_y"]) < 14:
        game["level_complete"] = True
        game["is_rolling"] = False

# ====================== 游戏渲染（线上适配版） ======================
def render_game():
    """优化线上渲染性能，减少DOM元素"""
    game = st.session_state.golf_game
    
    # 游戏区域容器
    st.markdown('<div class="game-area">', unsafe_allow_html=True)
    
    # 绘制障碍物（减少DOM节点）
    obstacle_html = ""
    for (ox, oy, w, h) in game["obstacles"]:
        obstacle_html += f'<div class="obstacle" style="left:{ox}px;top:{oy}px;width:{w}px;height:{h}px;"></div>'
    st.markdown(obstacle_html, unsafe_allow_html=True)
    
    # 绘制球洞和球（合并渲染）
    st.markdown(f'''
        <div class="hole" style="left:{game['hole_x']}px;top:{game['hole_y']}px;"></div>
        <div class="ball" style="left:{game['ball_x']}px;top:{game['ball_y']}px;"></div>
    ''', unsafe_allow_html=True)
    
    # 信息框（简化文本，提升线上加载速度）
    if game["level_complete"]:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} (Par: {game['par']}) | Completed!"
    else:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} | Wind: {game['wind']:.1f} m/s"
    
    st.markdown(f'<div class="info-box">{info_text}</div>', unsafe_allow_html=True)
    
    # 关闭容器
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== 主游戏逻辑（线上部署优化） ======================
def main():
    """线上专属主逻辑（稳定性优先）"""
    st.title("🏌️ 2D Golf Game")
    
    game = st.session_state.golf_game
    
    # 线上首次加载初始化
    if game["load_count"] == 0:
        reset_level(0)
        game["load_count"] = 1
    
    # 控制线上更新频率（避免过载）
    current_time = time.time()
    if current_time - game["last_update"] >= 0.02:  # ~50fps（平衡流畅度和性能）
        if game["is_rolling"] and not game["level_complete"]:
            update_ball_position()
        game["last_update"] = current_time
    
    # 渲染游戏（线上轻量化）
    render_game()
    
    # 控制区（适配线上交互）
    st.markdown("---")
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.subheader("Controls")
        
        if not game["is_rolling"] and not game["level_complete"]:
            # 简化滑块范围，提升线上操作体验
            power = st.slider("Power", 0, 100, 45, key="power", label_visibility="collapsed")
            st.caption("Power (0-100)")
            
            col_dir1, col_dir2 = st.columns(2, gap="small")
            with col_dir1:
                dir_x = st.slider("X", -8, 8, 5, key="dir_x", label_visibility="collapsed")
                st.caption("X (-left, +right)")
            with col_dir2:
                dir_y = st.slider("Y", -8, 8, 0, key="dir_y", label_visibility="collapsed")
                st.caption("Y (-up, +down)")
            
            # 击球按钮（线上交互优化）
            if st.button("⛳ Hit Ball", use_container_width=True, type="primary"):
                game["strokes"] += 1
                power_scaled = power / 100 * 9  # 降低最大力度，提升可控性
                game["vel_x"] = dir_x * power_scaled / 9
                game["vel_y"] = dir_y * power_scaled / 9
                game["is_rolling"] = True
        
        # 重置按钮（线上容错）
        if st.button("🔄 Reset Ball", use_container_width=True):
            reset_level(game["level"])
    
    with col2:
        st.subheader("Level Select")
        
        # 关卡选择（线上兼容性优化）
        level_options = [f"Level {i+1}" for i in range(len(GAME_CONFIG["levels"]))]
        selected_level = st.selectbox("Choose Level", level_options, index=game["level"])
        
        if st.button("Go to Level", use_container_width=True):
            try:
                new_level = int(selected_level.split()[1]) - 1
                reset_level(new_level)
            except:
                reset_level(0)
        
        # 关卡完成处理（线上反馈优化）
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

# ====================== 线上部署安全运行 ======================
if __name__ == "__main__":
    try:
        main()
        # 线上自动刷新（避免卡顿）
        if not st.session_state.golf_game["level_complete"]:
            st.experimental_rerun()
    except Exception as e:
        # 线上异常容错
        st.error("🔄 Game refreshed - minor issue resolved")
        st.session_state.golf_game = {"load_count": 0}
        st.experimental_rerun()
