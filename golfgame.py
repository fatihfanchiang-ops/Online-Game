import streamlit as st
import numpy as np
import time
import math

# ====================== 游戏配置 ======================
GAME_CONFIG = {
    "window": {"width": 750, "height": 450},
    "physics": {
        "friction": 0.975,
        "ball_radius": 5,
        "hole_radius": 10,
        "wind_strength": (-2.5, 2.5),
        "power_scale": 0.15
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

# CSS样式
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    .block-container {padding: 1rem !important; max-width: 850px !important; margin: 0 auto !important;}
    
    /* 游戏区域 */
    .game-area {
        position: relative;
        width: 750px;
        height: 450px;
        background-color: #8CC051;
        border: 2px solid #6A9030;
        border-radius: 8px;
        margin: 20px auto;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* 游戏元素 */
    .obstacle {position: absolute; background: #F4D35E; border: 1.5px solid #E0C040; border-radius: 3px;}
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
    
    /* 瞄准线 */
    .aim-line {
        position: absolute;
        border: 2px dashed #ff6b6b;
        z-index: 8;
        pointer-events: none;
        opacity: 0.7;
    }
    
    /* 信息面板 */
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
    }
    
    /* 控制区样式 */
    .control-panel {
        margin: 20px auto;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        width: 750px;
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
        # 瞄准/力度控制
        "aim_angle": 0.0,
        "power": 50,
        "aim_target_x": 0,
        "aim_target_y": 0
    }

# ====================== 核心函数 ======================
def reset_level(level_idx):
    """重置关卡"""
    game = st.session_state.golf_game
    level = GAME_CONFIG["levels"][level_idx]
    
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
        "aim_angle": math.atan2(level["hole"][1] - level["tee"][1], level["hole"][0] - level["tee"][0]),
        "power": 50
    })

def calculate_distance(x1, y1, x2, y2):
    """计算两点距离"""
    return math.hypot(x1 - x2, y1 - y2)

def check_collision(x, y, obstacles):
    """碰撞检测"""
    radius = GAME_CONFIG["physics"]["ball_radius"]
    for (ox, oy, w, h) in obstacles:
        if (ox - radius <= x <= ox + w + radius) and (oy - radius <= y <= oy + h + radius):
            return True
    return False

def update_ball_position():
    """更新球的位置"""
    game = st.session_state.golf_game
    
    # 球已停止
    if abs(game["vel_x"]) < 0.08 and abs(game["vel_y"]) < 0.08:
        game["is_rolling"] = False
        return
    
    # 物理计算
    game["vel_x"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_y"] *= GAME_CONFIG["physics"]["friction"]
    game["vel_x"] += game["wind"] * 0.04  # 风力影响
    
    # 新位置
    new_x = game["ball_x"] + game["vel_x"]
    new_y = game["ball_y"] + game["vel_y"]
    
    # 边界限制
    new_x = np.clip(new_x, 5, 745)
    new_y = np.clip(new_y, 5, 445)
    
    # 碰撞检测
    if not check_collision(new_x, new_y, game["obstacles"]):
        game["ball_x"] = float(new_x)
        game["ball_y"] = float(new_y)
    else:
        game["vel_x"] *= -0.45
        game["vel_y"] *= -0.45
    
    # 进洞检测
    if calculate_distance(game["ball_x"], game["ball_y"], game["hole_x"], game["hole_y"]) < 14:
        game["level_complete"] = True
        game["is_rolling"] = False

def shoot_ball():
    """击球"""
    game = st.session_state.golf_game
    if game["is_rolling"] or game["level_complete"]:
        return
    
    game["strokes"] += 1
    game["is_rolling"] = True
    
    # 根据角度和力度计算速度
    power_scale = game["power"] / 100 * GAME_CONFIG["physics"]["power_scale"]
    game["vel_x"] = math.cos(game["aim_angle"]) * power_scale * 10
    game["vel_y"] = math.sin(game["aim_angle"]) * power_scale * 10

def update_aim_angle(target_x, target_y):
    """更新瞄准角度"""
    game = st.session_state.golf_game
    dx = target_x - game["ball_x"]
    dy = target_y - game["ball_y"]
    game["aim_angle"] = math.atan2(dy, dx)
    game["aim_target_x"] = target_x
    game["aim_target_y"] = target_y

# ====================== 渲染游戏界面 ======================
def render_game():
    """渲染游戏"""
    game = st.session_state.golf_game
    
    # 游戏区域HTML
    game_html = '<div class="game-area">'
    
    # 绘制障碍物
    for (ox, oy, w, h) in game["obstacles"]:
        game_html += f'<div class="obstacle" style="left:{ox}px;top:{oy}px;width:{w}px;height:{h}px;"></div>'
    
    # 绘制球洞
    game_html += f'<div class="hole" style="left:{game["hole_x"]}px;top:{game["hole_y"]}px;"></div>'
    
    # 绘制瞄准线（仅球静止时显示）
    if not game["is_rolling"] and not game["level_complete"]:
        aim_length = game["power"] * 3
        end_x = game["ball_x"] + math.cos(game["aim_angle"]) * aim_length
        end_y = game["ball_y"] + math.sin(game["aim_angle"]) * aim_length
        
        # 瞄准线
        line_angle = math.degrees(game["aim_angle"])
        line_length = calculate_distance(game["ball_x"], game["ball_y"], end_x, end_y)
        game_html += f'''
        <div class="aim-line" style="
            width: {line_length}px;
            height: 0;
            left: {game["ball_x"]}px;
            top: {game["ball_y"]}px;
            transform-origin: 0% 50%;
            transform: rotate({line_angle}deg);
        "></div>
        '''
    
    # 绘制小球
    game_html += f'<div class="ball" style="left:{game["ball_x"]}px;top:{game["ball_y"]}px;"></div>'
    
    # 信息框
    if game["level_complete"]:
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} (Par: {game['par']}) | Completed!"
    else:
        wind_dir = "→" if game["wind"] > 0 else "←"
        info_text = f"Level {game['level']+1} | Strokes: {game['strokes']} | Wind: {wind_dir} {abs(game['wind']):.1f} m/s"
    
    game_html += f'<div class="info-box">{info_text}</div>'
    game_html += '</div>'
    
    # 渲染游戏区域
    st.markdown(game_html, unsafe_allow_html=True)

# ====================== 主游戏逻辑 ======================
def main():
    st.title("🏌️ 2D Golf Game")
    game = st.session_state.golf_game
    
    # 自动更新球的位置
    if game["is_rolling"] and not game["level_complete"]:
        current_time = time.time()
        if current_time - game["last_update"] >= 0.05:
            update_ball_position()
            game["last_update"] = current_time
            st.rerun()
    
    # 渲染游戏界面
    render_game()
    
    # 控制面板
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    
    # 分栏控制
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("🎯 Aiming")
        # 角度控制
        game["aim_angle"] = st.slider(
            "Aim Angle (°)",
            0.0, 360.0,
            math.degrees(game["aim_angle"]) % 360,
            1.0,
            disabled=game["is_rolling"] or game["level_complete"]
        )
        game["aim_angle"] = math.radians(game["aim_angle"])
        
        # 直接瞄准球洞按钮
        if st.button("🎯 Aim to Hole", disabled=game["is_rolling"] or game["level_complete"]):
            dx = game["hole_x"] - game["ball_x"]
            dy = game["hole_y"] - game["ball_y"]
            game["aim_angle"] = math.atan2(dy, dx)
    
    with col2:
        st.subheader("💪 Power")
        # 力度控制
        game["power"] = st.slider(
            "Shot Power (%)",
            0, 100,
            game["power"],
            1,
            disabled=game["is_rolling"] or game["level_complete"]
        )
        
        # 击球按钮
        if st.button("⛳ Hit Ball", type="primary", disabled=game["is_rolling"] or game["level_complete"]):
            shoot_ball()
            st.rerun()
    
    with col3:
        st.subheader("🔄 Game")
        # 重置按钮
        if st.button("🔄 Reset Ball"):
            reset_level(game["level"])
            st.rerun()
        
        # 关卡选择
        level_options = [f"Level {i+1}" for i in range(len(GAME_CONFIG["levels"]))]
        selected_level = st.selectbox(
            "Select Level",
            level_options,
            index=game["level"],
            disabled=game["is_rolling"]
        )
        
        if st.button("Go to Level"):
            new_level = int(selected_level.split()[1]) - 1
            reset_level(new_level)
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 关卡完成提示
    if game["level_complete"]:
        st.success(f"🎉 Hole In! You used {game['strokes']} strokes (Par: {game['par']})!")
        
        col_buttons = st.columns([1, 1])
        with col_buttons[0]:
            if game["level"] < len(GAME_CONFIG["levels"]) - 1:
                if st.button("▶️ Next Level"):
                    reset_level(game["level"] + 1)
                    st.rerun()
            else:
                st.balloons()
                st.success("🏆 You Completed All Levels! 🏆")
        
        with col_buttons[1]:
            if st.button("🔁 Play Again"):
                reset_level(0)
                st.rerun()

# ====================== 运行游戏 ======================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"⚠️ Game Error: {str(e)}")
        # 重置游戏状态
        if "golf_game" in st.session_state:
            reset_level(st.session_state.golf_game["level"])
        st.rerun()
