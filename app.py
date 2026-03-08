import math
import streamlit as st

st.set_page_config(page_title="Projectile Motion Calculator", layout="centered")

st.title("Projectile Motion Simulator")
st.caption("Adjust the inputs to compute and visualize projectile motion results.")

# -----------------------------
# Input Section
# -----------------------------
st.header("Inputs")

col1, col2 = st.columns(2)
with col1:
    initial_speed = st.number_input(
        "Initial speed (m/s)", min_value=0.0, value=30.0, step=0.5
    )
    launch_angle_deg = st.number_input(
        "Launch angle (degrees)", min_value=0.0, max_value=90.0, value=45.0, step=1.0
    )

with col2:
    initial_height = st.number_input(
        "Initial height (m)", min_value=0.0, value=0.0, step=0.5
    )
    gravity = st.number_input(
        "Gravity (m/s²)", min_value=0.1, value=9.81, step=0.01
    )

# -----------------------------
# Calculations
# -----------------------------
theta = math.radians(launch_angle_deg)
vx = initial_speed * math.cos(theta)
vy = initial_speed * math.sin(theta)

# Solve: h(t) = h0 + vy*t - 0.5*g*t^2 = 0
a = -0.5 * gravity
b = vy
c = initial_height

discriminant = b**2 - 4 * a * c
if discriminant < 0:
    time_of_flight = 0.0
else:
    root1 = (-b + math.sqrt(discriminant)) / (2 * a)
    root2 = (-b - math.sqrt(discriminant)) / (2 * a)
    valid_times = [t for t in (root1, root2) if t >= 0]
    time_of_flight = max(valid_times) if valid_times else 0.0

max_height = initial_height + (vy**2) / (2 * gravity) if gravity > 0 else initial_height
horizontal_range = vx * time_of_flight

# Build trajectory points
num_points = 120
trajectory_points = []
if time_of_flight > 0:
    for i in range(num_points + 1):
        t = (time_of_flight * i) / num_points
        x = vx * t
        y = initial_height + vy * t - 0.5 * gravity * t**2
        trajectory_points.append({"x (m)": x, "y (m)": max(y, 0.0)})

# -----------------------------
# Result Section
# -----------------------------
st.header("Results")

m1, m2, m3 = st.columns(3)
m1.metric("Time of flight", f"{time_of_flight:.3f} s")
m2.metric("Maximum height", f"{max_height:.3f} m")
m3.metric("Horizontal range", f"{horizontal_range:.3f} m")

st.subheader("Velocity Components")
st.write(f"Horizontal velocity (vx): **{vx:.3f} m/s**")
st.write(f"Vertical velocity (vy): **{vy:.3f} m/s**")

if trajectory_points:
    st.subheader("Projectile Trajectory")

    x_max = max(point["x (m)"] for point in trajectory_points)
    y_max = max(point["y (m)"] for point in trajectory_points)

    # Fixed-axis graph for a cleaner physics-style trajectory view.
    st.vega_lite_chart(
        data=trajectory_points,
        spec={
            "width": "container",
            "height": 420,
            "mark": {"type": "line", "strokeWidth": 3, "color": "#1f77b4"},
            "encoding": {
                "x": {
                    "field": "x (m)",
                    "type": "quantitative",
                    "title": "Horizontal Distance (m)",
                    "scale": {"domain": [0, max(1.0, x_max * 1.05)]},
                },
                "y": {
                    "field": "y (m)",
                    "type": "quantitative",
                    "title": "Height (m)",
                    "scale": {"domain": [0, max(1.0, y_max * 1.1)]},
                },
            },
        },
        use_container_width=True,
    )
else:
    st.warning("No valid trajectory points for the current inputs.")
