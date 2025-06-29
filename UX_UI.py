import pygame
import serial
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)
print("Arduino connected")


pygame.init()
pygame.joystick.init()
controller = pygame.joystick.Joystick(0)
controller.init()
print("PS4 Controller connected")


max_points = 100
time_data = deque(maxlen=max_points)
voltages = [deque(maxlen=max_points) for _ in range(3)]
param_data = deque(maxlen=max_points)
experiment_running = False
current_experiment = 0
start_time = time.time()
min_intensity = 255
max_intensity = 0
min_signal_duration = 151
min_delay = 151


root = tk.Tk()
root.title("Позитивные вибрации")
root.geometry("800x400")
root.configure(bg="#ECEFF1")

font_medium = ('Arial', 16)
font_small = ('Arial', 12)


def set_experiment(exp):
    global current_experiment, experiment_running
    if not experiment_running:
        steps = (exp - current_experiment) % 4
        for _ in range(abs(steps)):
            if steps > 0:
                arduino.write(b"R1\n")
            else:
                arduino.write(b"L1\n")
            time.sleep(0.1)
        current_experiment = exp
        update_status()

def start_experiment():
    global experiment_running, start_time, time_data, voltages, param_data
    experiment_running = True
    start_time = time.time()

    time_data.clear()
    for v in voltages:
        v.clear()
    param_data.clear()
    arduino.write(b"X\n")
    update_status()

def stop_experiment():
    global experiment_running
    experiment_running = False
    arduino.write(b"O\n")
    update_status()

def update_status():
    status_label.config(text=f"Эксперимент: {current_experiment}, {'Запущен' if experiment_running else 'Приостановлен'}")

def update_params():
    min_intensity_label.config(text=f"Мин. интенсивность: {min_intensity}")
    max_intensity_label.config(text=f"Макс. интенсивность: {max_intensity}")
    min_signal_label.config(text=f"Мин. длительность: {min_signal_duration} мс")
    min_delay_label.config(text=f"Мин. задержка: {min_delay} мс")


button_frame = ttk.Frame(root, relief="raised", borderwidth=2)
button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)


style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", font=font_medium, padding=5, background="#2E7D32", foreground="white", borderwidth=2)
style.map("TButton", background=[('active', '#1B5E20')], foreground=[('active', 'white')])
style.configure("TLabel", font=font_medium, background="#ECEFF1", foreground="#37474F")
style.configure("Param.TLabel", font=font_small, background="#ECEFF1", foreground="#37474F")
style.configure("Custom.TFrame", background="#ECEFF1")


ttk.Button(button_frame, text="Интенсивность", command=lambda: set_experiment(0)).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(button_frame, text="Длительность", command=lambda: set_experiment(1)).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(button_frame, text="Задержка", command=lambda: set_experiment(2)).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(button_frame, text="Управление стиком", command=lambda: set_experiment(3)).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(button_frame, text="Начать", command=start_experiment).pack(side=tk.LEFT, padx=5, pady=5)
ttk.Button(button_frame, text="Остановить", command=stop_experiment).pack(side=tk.LEFT, padx=5, pady=5)

status_label = ttk.Label(button_frame, text="Эксперимент: 0, Приостановлен")
status_label.pack(side=tk.LEFT, padx=10, pady=5)


param_frame = ttk.Frame(root)
param_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

min_intensity_label = ttk.Label(param_frame, text=f"Мин. интенсивность: {min_intensity}", style="Param.TLabel")
min_intensity_label.pack(side=tk.LEFT, padx=5)
max_intensity_label = ttk.Label(param_frame, text=f"Макс. интенсивность: {max_intensity}", style="Param.TLabel")
max_intensity_label.pack(side=tk.LEFT, padx=5)
min_signal_label = ttk.Label(param_frame, text=f"Мин. длительность: {min_signal_duration} мс", style="Param.TLabel")
min_signal_label.pack(side=tk.LEFT, padx=5)
min_delay_label = ttk.Label(param_frame, text=f"Мин. задержка: {min_delay} мс", style="Param.TLabel")
min_delay_label.pack(side=tk.LEFT, padx=5)


plt.rcParams.update({'font.size': 10})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.5), facecolor="#ECEFF1")
fig.patch.set_facecolor("#ECEFF1")
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)
canvas.get_tk_widget().configure(bg="#ECEFF1", highlightthickness=1, highlightbackground="#37474F")

ax1.set_title("Напряжение на моторах", fontsize=12, color="#37474F")
ax1.set_xlabel("Время (с)", fontsize=10, color="#37474F")
ax1.set_ylabel("Напряжение (0-255)", fontsize=10, color="#37474F")
lines_voltage = [ax1.step([], [], label=f"Мотор {i+1}", linewidth=1.5, where='post')[0] for i in range(3)]
ax1.legend(fontsize=8, frameon=True, facecolor="#ECEFF1", edgecolor="#37474F")
ax1.set_ylim(0, 255)
ax1.tick_params(axis='both', labelsize=8, colors="#37474F")
ax1.set_facecolor("#ECEFF1")
ax1.grid(True, linestyle='--', alpha=0.7, color="#37474F")

ax2.set_title("Изменение параметра", fontsize=12, color="#37474F")
ax2.set_xlabel("Время (с)", fontsize=10, color="#37474F")
ax2.set_ylabel("Параметр", fontsize=10, color="#37474F")
line_param, = ax2.plot([], [], color="#2E7D32", linewidth=1.5)
ax2.tick_params(axis='both', labelsize=8, colors="#37474F")
ax2.set_facecolor("#ECEFF1")
ax2.grid(True, linestyle='--', alpha=0.7, color="#37474F")

def update_plots():
    if experiment_running and len(time_data) > 0:
        print(f"Updating plots: time_data={len(time_data)}, voltages={[len(v) for v in voltages]}, param_data={len(param_data)}")
        print(f"Max voltages: {[max(v) if v else 0 for v in voltages]}")
        for i in range(3):
            lines_voltage[i].set_data(time_data, voltages[i])
        ax1.relim()
        ax1.autoscale_view()

        line_param.set_data(time_data, param_data)
        if len(param_data) > 0:
            min_param = min(param_data)
            max_param = max(param_data)
            margin = (max_param - min_param) * 0.1 if max_param > min_param else 10
            ax2.set_ylim(min_param - margin, max_param + margin)
            if current_experiment == 0:
                ax2.set_ylabel("Интенсивность (0-255)", fontsize=10, color="#37474F")
            elif current_experiment == 1:
                ax2.set_ylabel("Длительность (мс)", fontsize=10, color="#37474F")
            elif current_experiment == 2:
                ax2.set_ylabel("Задержка (мс)", fontsize=10, color="#37474F")
            elif current_experiment == 3:
                ax2.set_ylabel("Интенсивность (0-255)", fontsize=10, color="#37474F")
        ax2.relim()
        ax2.autoscale_view(scaley=False)

        canvas.draw()
    root.after(50, update_plots)


last_l1 = False
last_r1 = False
last_cross = False
last_circle = False

def gamepad_loop():
    pygame.event.pump()

    l1 = controller.get_button(9)
    r1 = controller.get_button(10)
    cross = controller.get_button(0)
    circle = controller.get_button(1)
    l2 = controller.get_axis(4)

    global last_l1, last_r1, last_cross, last_circle, min_intensity, max_intensity, min_signal_duration, min_delay
    if l1 and not last_l1:
        arduino.write(b"L1\n")
    if r1 and not last_r1:
        arduino.write(b"R1\n")
    if cross and not last_cross:
        start_experiment()
    if circle and not last_circle:
        stop_experiment()

    stick_x = controller.get_axis(0)
    stick_y = controller.get_axis(1)
    l2_value = int((l2 + 1) * 127.5)
    stick_cmd = f"S:{int(stick_x * 127)}:{int(stick_y * 127)}:{l2_value}\n"
    arduino.write(stick_cmd.encode())

    last_l1, last_r1, last_cross, last_circle = l1, r1, cross, circle

    while arduino.in_waiting > 0:
        response = arduino.readline().decode().strip()
        print("Arduino response: ", response)
        current_time = time.time() - start_time
        if response.startswith("V:"):
            motor, value = map(int, response[2:].split(":"))
            time_data.append(current_time)
            voltages[motor].append(value)
            for i in range(3):
                if i != motor:
                    voltages[i].append(voltages[i][-1] if len(voltages[i]) > 0 else 0)
            if len(param_data) < len(time_data):
                param_data.append(param_data[-1] if len(param_data) > 0 else 0)
        elif response.startswith("P:"):
            param, value = response[2:].split(":")
            time_data.append(current_time)
            param_data.append(int(value))
            for i in range(3):
                voltages[i].append(voltages[i][-1] if len(voltages[i]) > 0 else 0)
        elif response.startswith("MIN_I:"):
            min_intensity = int(response.split(":")[1])
            update_params()
        elif response.startswith("MAX_I:"):
            max_intensity = int(response.split(":")[1])
            update_params()
        elif response.startswith("MIN_S:"):
            min_signal_duration = int(response.split(":")[1])
            update_params()
        elif response.startswith("MIN_D:"):
            min_delay = int(response.split(":")[1])
            update_params()
        elif response.startswith("Switch to experiment:"):
            current_experiment = int(response.split(":")[1].strip())
            update_status()
        elif response == "Experiment started":
            experiment_running = True
            update_status()
        elif response == "Experiment paused":
            experiment_running = False
            update_status()

    root.after(10, gamepad_loop)


root.after(0, gamepad_loop)
root.after(0, update_plots)
root.mainloop()

pygame.quit()
arduino.close()