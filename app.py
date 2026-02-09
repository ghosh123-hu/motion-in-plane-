import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

G_EARTH = 9.8


def ideal_trajectory(speed, angle_deg, height, g, points=240):
    a = math.radians(angle_deg)
    vx = speed * math.cos(a)
    vy = speed * math.sin(a)
    disc = vy * vy + 2 * g * height
    t_flight = (vy + math.sqrt(max(disc, 0.0))) / g
    t = np.linspace(0, t_flight, points)
    x = vx * t
    y = height + vy * t - 0.5 * g * t * t
    return x, np.maximum(y, 0), t_flight


def drag_trajectory(speed, angle_deg, height, g, drag_k, dt=1 / 240, max_t=180):
    a = math.radians(angle_deg)
    x, y = 0.0, height
    vx, vy = speed * math.cos(a), speed * math.sin(a)
    t = 0.0
    xs, ys = [x], [y]

    while t < max_t and y >= 0:
        rel_speed = math.hypot(vx, vy)
        drag = drag_k * rel_speed
        ax = -drag * vx
        ay = -g - drag * vy
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        t += dt
        xs.append(x)
        ys.append(max(y, 0))
    return np.array(xs), np.array(ys)


def inclined_trajectory(speed, angle_deg, incline_deg, height, g, dt=1 / 240, max_t=180):
    a = math.radians(angle_deg)
    phi = math.radians(incline_deg)
    tan_phi = math.tan(phi)
    x, y = 0.0, height
    vx, vy = speed * math.cos(a), speed * math.sin(a)
    xs, ys = [x], [y]
    t = 0.0

    while t < max_t:
        px, py = x, y
        vy -= g * dt
        x += vx * dt
        y += vy * dt
        t += dt
        plane_y = x * tan_phi
        if x >= 0 and y <= plane_y:
            d0 = py - px * tan_phi
            d1 = y - plane_y
            f = d0 / (d0 - d1) if (d0 - d1) != 0 else 0
            x = px + (x - px) * f
            y = py + (y - py) * f
            xs.append(x)
            ys.append(y)
            break
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)


def rocket_mass_loss_trajectory(v0, angle_deg, h0, m0, mdry, thrust, burn_time, dt=1 / 240, max_t=180):
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    m_dot = (m0 - mdry) / max(burn_time, 1e-6)

    x, y = 0.0, h0
    vx, vy = v0 * ux, v0 * uy
    m, t = m0, 0.0

    xs, ys, ts = [x], [y], [t]
    powered_flags = [True]
    cutoff = None

    while t < max_t and y >= 0:
        powered = t < burn_time and m > mdry + 1e-9
        ax, ay = 0.0, -G_EARTH
        if powered:
            acc_t = thrust / max(m, 1e-6)
            ax += acc_t * ux
            ay += acc_t * uy
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        t += dt
        if powered:
            m = max(mdry, m - m_dot * dt)
        else:
            m = mdry
        if cutoff is None and t >= burn_time:
            cutoff = (x, y)
        xs.append(x)
        ys.append(max(y, 0))
        ts.append(t)
        powered_flags.append(powered)
    return np.array(xs), np.array(ys), np.array(ts), np.array(powered_flags, dtype=bool), cutoff


def make_fig(title, traces):
    fig = go.Figure()
    for tr in traces:
        fig.add_trace(tr)
    fig.update_layout(
        title=title,
        xaxis_title="x (m)",
        yaxis_title="y (m)",
        template="plotly_white",
        height=460,
        legend=dict(orientation="h"),
    )
    return fig


st.set_page_config(page_title="Projectile Physics (Python)", layout="wide")
st.title("Projectile Physics - Python Version")
st.caption("Converted from JavaScript to Python using Streamlit + NumPy + Plotly.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Ideal", "Air Drag", "Inclined", "Varying g", "Rocket (Mass Loss)"]
)

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    v = c1.slider("Speed (m/s)", 1, 120, 45)
    ang = c2.slider("Angle (deg)", 1, 89, 45)
    h = c3.slider("Height (m)", 0, 80, 0)
    g = c4.slider("g (m/s²)", 0.5, 30.0, 9.8, 0.1)
    x, y, t_f = ideal_trajectory(v, ang, h, g)
    fig = make_fig("Ideal Projectile", [go.Scatter(x=x, y=y, mode="lines", name="Ideal", line=dict(color="#1f6f78"))])
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"Time of flight: `{t_f:.2f} s`")

with tab2:
    c1, c2, c3, c4, c5 = st.columns(5)
    v = c1.slider("Speed (m/s)", 1, 120, 45, key="d_v")
    ang = c2.slider("Angle (deg)", 1, 89, 43, key="d_a")
    h = c3.slider("Height (m)", 0, 80, 0, key="d_h")
    drag = c4.slider("Air drag (strength)", 0.0, 0.08, 0.008, 0.001)
    g = c5.slider("g (m/s²)", 0.5, 30.0, 9.8, 0.1, key="d_g")
    x_drag, y_drag = drag_trajectory(v, ang, h, g, drag)
    x_id, y_id, _ = ideal_trajectory(v, ang, h, g)
    fig = make_fig(
        "Projectile with Air Drag",
        [
            go.Scatter(x=x_id, y=y_id, mode="lines", name="Ideal (reference)", line=dict(color="#9aa5b1", dash="dash")),
            go.Scatter(x=x_drag, y=y_drag, mode="lines", name="With drag", line=dict(color="#355c9a", width=3)),
        ],
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    c1, c2, c3, c4, c5 = st.columns(5)
    v = c1.slider("Speed (m/s)", 1, 120, 40, key="i_v")
    ang = c2.slider("Launch angle (deg)", 1, 89, 50, key="i_a")
    inc = c3.slider("Incline angle (deg)", 0, 60, 20)
    h = c4.slider("Height (m)", 0, 50, 0, key="i_h")
    g = c5.slider("g (m/s²)", 0.5, 30.0, 9.8, 0.1, key="i_g")
    x, y = inclined_trajectory(v, ang, inc, h, g)
    x_plane = np.linspace(0, max(30, float(np.max(x) * 1.1)), 150)
    y_plane = x_plane * math.tan(math.radians(inc))
    fig = make_fig(
        "Inclined Surface Projectile",
        [
            go.Scatter(x=x_plane, y=y_plane, mode="lines", name="Inclined surface", line=dict(color="#b05f2b")),
            go.Scatter(x=x, y=y, mode="lines", name="Trajectory", line=dict(color="#1f6f78", width=3)),
        ],
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    c1, c2, c3, c4 = st.columns(4)
    v = c1.slider("Speed (m/s)", 1, 120, 45, key="g_v")
    ang = c2.slider("Angle (deg)", 1, 89, 45, key="g_a")
    h = c3.slider("Height (m)", 0, 80, 0, key="g_h")
    g_user = c4.slider("User gravity (m/s²)", 0.5, 30.0, 3.7, 0.1)
    x_f, y_f, _ = ideal_trajectory(v, ang, h, 9.8)
    x_u, y_u, _ = ideal_trajectory(v, ang, h, g_user)
    fig = make_fig(
        "Gravity Comparison",
        [
            go.Scatter(x=x_f, y=y_f, mode="lines", name="Fixed g = 9.8", line=dict(color="#888", dash="dot")),
            go.Scatter(x=x_u, y=y_u, mode="lines", name=f"User g = {g_user:.1f}", line=dict(color="#d1495b", width=3)),
        ],
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    c1, c2, c3, c4 = st.columns(4)
    v0 = c1.slider("Initial speed (m/s)", 0, 120, 12)
    ang = c2.slider("Launch angle (deg)", 5, 85, 55)
    h0 = c3.slider("Height (m)", 0, 40, 0)
    thrust = c4.slider("Thrust (N)", 0, 220, 90)
    c5, c6, c7 = st.columns(3)
    m0 = c5.slider("Initial mass m0 (kg)", 0.8, 8.0, 3.2, 0.1)
    mdry = c6.slider("Dry mass mdry (kg)", 0.3, 7.5, 1.6, 0.1)
    burn = c7.slider("Burn time (s)", 0.2, 8.0, 3.0, 0.1)
    mdry = min(mdry, m0 - 0.05)

    x, y, t_arr, powered, cutoff = rocket_mass_loss_trajectory(v0, ang, h0, m0, mdry, thrust, burn)
    powered_idx = np.where(powered)[0]
    coast_idx = np.where(~powered)[0]

    traces = []
    if powered_idx.size > 1:
        traces.append(
            go.Scatter(
                x=x[powered_idx],
                y=y[powered_idx],
                mode="lines",
                name="Phase 1 (powered)",
                line=dict(color="#d1495b", width=3),
            )
        )
    if coast_idx.size > 1:
        traces.append(
            go.Scatter(
                x=x[coast_idx],
                y=y[coast_idx],
                mode="lines",
                name="Phase 2 (ballistic)",
                line=dict(color="#1f6f78", width=3),
            )
        )
    fig = make_fig("Rocket-Assisted Projectile (Decreasing Mass)", traces)
    if cutoff is not None:
        fig.add_trace(
            go.Scatter(
                x=[cutoff[0]],
                y=[max(0, cutoff[1])],
                mode="markers+text",
                text=["Engine cutoff"],
                textposition="top right",
                marker=dict(symbol="x", size=10, color="#2d6a4f"),
                name="Cutoff",
            )
        )

    frame_step = max(1, len(x) // 140)
    frame_ids = list(range(0, len(x), frame_step))
    if frame_ids[-1] != len(x) - 1:
        frame_ids.append(len(x) - 1)

    fig.add_trace(
        go.Scatter(
            x=[x[0]],
            y=[y[0]],
            mode="markers",
            marker=dict(size=12, color="#ff8c42", line=dict(width=1, color="#6b3d1f")),
            name="Rocket",
        )
    )

    frames = []
    for i in frame_ids:
        phase_text = "Phase 1" if powered[i] else "Phase 2"
        frames.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=[x[i]],
                        y=[y[i]],
                        mode="markers+text",
                        text=[f"{phase_text}, t={t_arr[i]:.1f}s"],
                        textposition="top center",
                        marker=dict(size=12, color="#ff8c42", line=dict(width=1, color="#6b3d1f")),
                        showlegend=False,
                    )
                ],
                traces=[len(fig.data) - 1],
                name=str(i),
            )
        )
    fig.frames = frames
    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0.01,
                "y": 1.15,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 35, "redraw": True}, "fromcurrent": True}],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [[None], {"mode": "immediate", "frame": {"duration": 0, "redraw": False}}],
                    },
                ],
            }
        ]
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info("Phase 1: thrust + mass loss. Phase 2: thrust off, pure gravity (parabolic segment).")
