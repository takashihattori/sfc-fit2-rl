"""cartpole_cmp.py

Gymnasium の "CartPole-v1"（倒立振子）環境において、4つの連続状態を
それぞれ6区間に離散化（Binning）したうえで、割引率 γ = 1.0（割引なし）として
以下の3つの手法の学習効率を比較するプログラム：

  ① ランダム方策 (Random Policy): 左右をランダムに選択（学習なし）
  ② 離散化モンテカルロ法 (Monte Carlo Method): エピソード終了後にまとめて平均更新
  ③ 離散化 Q-learning: 1ステップ進むごとに移動先の最大Q値を使って即座に更新

エピソード数に対する平均維持ステップ数（50エピソードごとの平均）の推移を可視化し、
グラフ画像 'cartpole_cmp_result.png' に保存するとともに画面表示します。
さらに学習完了後、学習済み Q-learning エージェントによる実演（Pygame 描画）を行います。
"""

from collections import defaultdict
import random
import sys
import time
import gymnasium as gym
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# 日本語フォントの設定（macOS / Windows / Linux 対応）
plt.rcParams["font.sans-serif"] = [
    "Hiragino Sans",
    "Hiragino Kaku Gothic ProN",
    "Hiragino Maru Gothic Pro",
    "Yu Gothic",
    "Meiryo",
    "BIZ UDGothic",
    "TakaoExGothic",
    "IPAexGothic",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の文字化け防止


# =====================================================================
# 1. 連続状態の離散化（Binning）の設定
# =====================================================================
# 4つの状態変数それぞれを「5つの境界値」で区切り、0〜5 の「6区間」に分類する
# （境界値が N 個のとき、区間の数は N + 1 個になります）
# 状態総数: 6 × 6 × 6 × 6 = 1,296 通り
DEG_6 = np.deg2rad(6.0)
DEG_1 = np.deg2rad(1.0)

BINS = [
    [-1.2, -0.3, 0.0, 0.3, 1.2],                   # 1. カートの位置 x (6区間)
    [-1.5, -0.3, 0.0, 0.3, 1.5],                   # 2. カートの速度 v (6区間)
    [-DEG_6, -DEG_1, 0.0, DEG_1, DEG_6],           # 3. ポールの角度 θ (6区間: -6°, -1°, 0°, +1°, +6°)
    [-2.0, -2.0 / 3.0, 0.0, 2.0 / 3.0, 2.0],       # 4. ポールの角速度 ω (6区間)
]
# ※ 練習問題 10-03 で角度と角速度を「3区間（境界値2つ）」に変更する例：
#    3行目を [-DEG_6, DEG_6]、4行目を [-2.0, 2.0] に書き換えて実行してみましょう。


def discretize(state):
    """4つの連続値 [x, v, theta, omega] を離散状態の整数タプルに変換する"""
    return tuple(int(np.digitize(state[i], BINS[i])) for i in range(4))


# =====================================================================
# 2. テスト評価用関数（探索なし: ε = 0）
# =====================================================================
def evaluate_policy(env, Q=None, num_episodes=100, seed_offset=90000):
    """指定された方策でテストを実行し、平均維持ステップ数と500ステップ完走率(%)を返す"""
    random.seed(seed_offset)
    steps_list = []
    clear_count = 0

    for i in range(num_episodes):
        state, _ = env.reset(seed=seed_offset + i)
        s = discretize(state)
        done = False
        steps = 0

        while not done:
            if Q is None:
                action = random.randint(0, 1)
            else:
                q_vals = Q[s]
                action = 0 if q_vals[0] >= q_vals[1] else 1

            next_state, _, terminated, truncated, _ = env.step(action)
            s = discretize(next_state)
            done = terminated or truncated
            steps += 1

        steps_list.append(steps)
        if steps >= 500:
            clear_count += 1

    avg_steps = float(np.mean(steps_list))
    clear_rate = clear_count / num_episodes * 100.0
    return avg_steps, clear_rate


# =====================================================================
# 3. 手法①：ランダム方策の推移取得（学習なし）
# =====================================================================
def run_random_curve(env, num_episodes=1500, eval_interval=50, base_seed=9):
    """ランダム方策でプレイし、eval_interval ごとの平均維持ステップ数を記録する"""
    random.seed(base_seed)
    np.random.seed(base_seed)

    eval_episodes = []
    eval_steps = []
    recent_steps = []

    print(f"\n[1/3] ① ランダム方策を実行中 ({num_episodes:,} エピソード)...")
    start_time = time.time()

    for ep in range(1, num_episodes + 1):
        _, _ = env.reset(seed=base_seed * 10000 + ep)
        done = False
        steps = 0
        while not done:
            action = random.randint(0, 1)
            _, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            steps += 1

        recent_steps.append(steps)

        if ep % eval_interval == 0:
            avg_s = sum(recent_steps) / len(recent_steps)
            eval_episodes.append(ep)
            eval_steps.append(avg_s)
            recent_steps = []

    elapsed = time.time() - start_time
    print(f"  -> ランダム方策の実行完了 ({elapsed:.2f} 秒)")
    return eval_episodes, eval_steps


# =====================================================================
# 4. 手法②：離散化モンテカルロ法 (MC) の学習（割引率 γ = 1.0）
# =====================================================================
def train_monte_carlo(env, num_episodes=1500, eval_interval=50, base_seed=9):
    """離散化モンテカルロ法（エピソード終了後にまとめて平均更新, γ = 1.0）で学習する"""
    random.seed(base_seed)
    np.random.seed(base_seed)

    Q = defaultdict(lambda: [0.0, 0.0])
    N = defaultdict(lambda: [0, 0])
    eval_episodes = []
    eval_steps = []
    recent_steps = []

    print(f"\n[2/3] ② 離散化モンテカルロ法で学習中 ({num_episodes:,} エピソード, γ = 1.0)...")
    start_time = time.time()

    for ep in range(1, num_episodes + 1):
        # 探索率 ε をエピソードとともに少しずつ減らす（0.5 -> 最小 0.01）
        epsilon = max(0.01, 0.5 * (0.992 ** ep))

        state, _ = env.reset(seed=base_seed * 10000 + ep)
        s = discretize(state)
        done = False
        trajectory = []

        while not done:
            if random.random() < epsilon:
                action = random.randint(0, 1)
            else:
                action = 0 if Q[s][0] >= Q[s][1] else 1

            next_state, reward, terminated, truncated, _ = env.step(action)
            ns = discretize(next_state)
            done = terminated or truncated
            trajectory.append((s, action, reward))
            s = ns

        steps = len(trajectory)
        recent_steps.append(steps)

        # エピソード終了後、そのエピソード全体の獲得報酬 G（維持ステップ数, γ = 1.0）で
        # 通過したすべての（状態, 行動）の平均値をまとめて更新（初回訪問モンテカルロ法）
        G = float(steps)
        visited = set()
        for st, act, _ in trajectory:
            if (st, act) not in visited:
                visited.add((st, act))
                N[st][act] += 1
                Q[st][act] += (G - Q[st][act]) / N[st][act]

        if ep % eval_interval == 0:
            avg_s = sum(recent_steps) / len(recent_steps)
            eval_episodes.append(ep)
            eval_steps.append(avg_s)
            recent_steps = []
            if ep % 300 == 0:
                print(f"  MC      : {ep:5,d} / {num_episodes:,} 完了 (直近平均: {avg_s:5.1f} ステップ)")

    elapsed = time.time() - start_time
    print(f"  -> 離散化モンテカルロ法の学習完了 ({elapsed:.2f} 秒)")
    return Q, eval_episodes, eval_steps


# =====================================================================
# 5. 手法③：離散化 Q-learning の学習（割引率 γ = 1.0）
# =====================================================================
def train_qlearning(env, num_episodes=1500, eval_interval=50, base_seed=9, gamma=1.0):
    """離散化 Q-learning（1ステップごとに移動先の最大Q値で即座に更新, γ = 1.0）で学習する"""
    random.seed(base_seed)
    np.random.seed(base_seed)

    # 未訪問の行動も積極的に試されるよう初期値を 200.0 に設定
    Q = defaultdict(lambda: [200.0, 200.0])
    eval_episodes = []
    eval_steps = []
    recent_steps = []

    print(f"\n[3/3] ③ 離散化 Q-learning で学習中 ({num_episodes:,} エピソード, γ = {gamma})...")
    start_time = time.time()

    for ep in range(1, num_episodes + 1):
        # 探索率 ε と学習率 α をエピソードとともに少しずつ減らす
        epsilon = max(0.01, 0.5 * (0.992 ** ep))
        alpha = max(0.05, 0.5 * (0.996 ** ep))

        state, _ = env.reset(seed=base_seed * 10000 + ep)
        s = discretize(state)
        done = False
        steps = 0

        while not done:
            if random.random() < epsilon:
                action = random.randint(0, 1)
            else:
                action = 0 if Q[s][0] >= Q[s][1] else 1

            next_state, reward, terminated, truncated, _ = env.step(action)
            ns = discretize(next_state)
            done = terminated or truncated
            steps += 1

            # 1ステップごとにその場で即座に Q 値を更新（バケツリレー方式）
            # 棒が倒れてエピソードが終了した瞬間（terminated=True）は、その先の状態がないため
            # 移動先の見込みを 0 とし、直後の報酬（+1.0）のみで更新する
            if terminated:
                target = reward
            else:
                target = reward + gamma * max(Q[ns])

            Q[s][action] += alpha * (target - Q[s][action])
            s = ns

        recent_steps.append(steps)

        if ep % eval_interval == 0:
            avg_s = sum(recent_steps) / len(recent_steps)
            eval_episodes.append(ep)
            eval_steps.append(avg_s)
            recent_steps = []
            if ep % 300 == 0:
                print(f"  Q-learn : {ep:5,d} / {num_episodes:,} 完了 (直近平均: {avg_s:5.1f} ステップ)")

    elapsed = time.time() - start_time
    print(f"  -> 離散化 Q-learning の学習完了 ({elapsed:.2f} 秒)")
    return Q, eval_episodes, eval_steps


# =====================================================================
# 6. 比較グラフの描画
# =====================================================================
def plot_comparison(
    episodes,
    rand_steps,
    mc_steps,
    ql_steps,
    save_path="cartpole_cmp_result.png",
    show_window=True,
):
    """3つの手法の学習曲線を1枚のグラフに重ねて描画・保存する"""
    fig, ax = plt.subplots(figsize=(11, 6.5))

    ax.plot(
        episodes,
        rand_steps,
        color="#dc2626",
        linestyle="-",
        linewidth=2.0,
        alpha=0.85,
        label="① ランダム方策（学習なし：約 21 ステップで転倒）",
    )
    ax.plot(
        episodes,
        mc_steps,
        color="#2563eb",
        linestyle="-",
        linewidth=2.3,
        label="② 離散化モンテカルロ法（エピソード終了後にまとめて平均更新, γ = 1.0）",
    )
    ax.plot(
        episodes,
        ql_steps,
        color="#16a34a",
        linestyle="-",
        linewidth=2.6,
        label="③ 離散化 Q-learning（1ステップごとに移動先の見込みで即座に更新, γ = 1.0）",
    )

    # クリア基準線（500ステップ）
    ax.axhline(
        500,
        color="#047857",
        linestyle="--",
        linewidth=1.5,
        alpha=0.85,
        label="クリア上限（500 ステップ満点）",
    )

    ax.set_title(
        "CartPole-v1 における学習効率の比較：モンテカルロ法 vs Q-learning（割引率 γ = 1.0）",
        fontsize=13.5,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlabel("学習エピソード数", fontsize=12)
    ax.set_ylabel("直近 50 エピソードの平均維持ステップ数", fontsize=12)
    ax.set_ylim(0, 540)
    ax.set_xlim(0, max(episodes) * 1.02)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))

    ax.grid(True, linestyle="--", alpha=0.55)
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.98, 0.80),
        fontsize=10.5,
        framealpha=0.95,
    )

    info_text = (
        "【なぜ長いステップ続く問題では Q-learning の方が効率よく学べるのか？】\n"
        "・モンテカルロ法：棒が倒れて1ゲームが終わるまで更新できず、「途中の良いバランス制御」も\n"
        "  「最後に棒を倒した悪手」も同じ結果として平均化されるため、130 ステップ前後で伸び悩む。\n"
        "・Q-learning：1ステップ進むたびに「移動先の最高の見込み（最大Q値）」からその場で更新し、\n"
        "  棒が倒れた瞬間は「その先の見込み＝0」として直前の1手の評価を即座に下げるため急速に上達する！"
    )
    ax.text(
        0.98,
        0.34,
        info_text,
        transform=ax.transAxes,
        fontsize=9.5,
        horizontalalignment="right",
        verticalalignment="bottom",
        multialignment="left",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8fafc", edgecolor="#cbd5e1", alpha=0.95),
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"\n比較グラフを保存しました: {save_path}")
    if show_window:
        plt.show()
    plt.close(fig)


# =====================================================================
# 7. 学習済みエージェントの実演（Pygame ウィンドウ描画）
# =====================================================================
def run_visual_demo(Q_ql, num_demo_episodes=2):
    """学習済み Q-learning エージェントが実際にカートを制御する様子を描画する"""
    print("\n" + "=" * 68)
    print("  学習済み Q-learning エージェントによる実演 (Pygame ウィンドウ)")
    print("=" * 68)
    try:
        demo_env = gym.make("CartPole-v1", render_mode="human")
        for ep in range(1, num_demo_episodes + 1):
            state, _ = demo_env.reset(seed=99000 + ep)
            s = discretize(state)
            done = False
            steps = 0
            while not done:
                action = 0 if Q_ql[s][0] >= Q_ql[s][1] else 1
                next_state, _, terminated, truncated, _ = demo_env.step(action)
                s = discretize(next_state)
                done = terminated or truncated
                steps += 1
            print(f"  実演エピソード {ep}: {steps} ステップ維持！")
        demo_env.close()
    except Exception as e:
        print(f"  (画面描画をスキップしました: {e})")


# =====================================================================
# 8. メイン処理
# =====================================================================
def main():
    no_gui = "--no-gui" in sys.argv
    env = gym.make("CartPole-v1")

    total_episodes = 1500
    eval_interval = 50
    test_episodes = 100

    num_states = 1
    for b in BINS:
        num_states *= len(b) + 1

    print("=" * 68)
    print("  CartPole-v1 離散化（Binning）学習効率比較シミュレーション")
    print(f"  離散化の状態総数: {num_states:,} 通り / 割引率 γ = 1.0")
    print(f"  総エピソード数: {total_episodes:,} 回 (評価間隔: {eval_interval} 回)")
    print("=" * 68)

    # 1. ① ランダム方策の実行
    episodes, rand_steps = run_random_curve(
        env, num_episodes=total_episodes, eval_interval=eval_interval
    )

    # 2. ② 離散化モンテカルロ法の学習
    Q_mc, _, mc_steps = train_monte_carlo(
        env, num_episodes=total_episodes, eval_interval=eval_interval
    )

    # 3. ③ 離散化 Q-learning の学習
    Q_ql, _, ql_steps = train_qlearning(
        env, num_episodes=total_episodes, eval_interval=eval_interval
    )

    # 4. 学習完了後のテスト評価（100エピソード, 探索なし ε = 0）
    print("\n" + "=" * 68)
    print(f"  学習完了後のテスト評価 ({test_episodes} エピソード, 探索なし ε = 0)")
    print("=" * 68)

    rand_avg, rand_clr = evaluate_policy(env, Q=None, num_episodes=test_episodes)
    mc_avg, mc_clr = evaluate_policy(env, Q=Q_mc, num_episodes=test_episodes)
    ql_avg, ql_clr = evaluate_policy(env, Q=Q_ql, num_episodes=test_episodes)

    print(f"{'手法':<24} {'平均維持ステップ数':>16} {'500ステップ完走率':>16}")
    print("-" * 62)
    print(f"{'① ランダム方策':<22} {rand_avg:14.1f} 歩 {rand_clr:15.1f}%")
    print(f"{'② 離散化モンテカルロ法':<19} {mc_avg:14.1f} 歩 {mc_clr:15.1f}%")
    print(f"{'③ 離散化 Q-learning':<21} {ql_avg:14.1f} 歩 {ql_clr:15.1f}%")
    print("-" * 62)

    env.close()

    # 5. 学習曲線の比較グラフを描画・保存
    plot_comparison(
        episodes,
        rand_steps,
        mc_steps,
        ql_steps,
        save_path="cartpole_cmp_result.png",
        show_window=not no_gui,
    )

    # 6. Pygame ウィンドウでの実演（--no-gui 指定時はスキップ）
    if not no_gui:
        run_visual_demo(Q_ql, num_demo_episodes=2)


if __name__ == "__main__":
    main()
