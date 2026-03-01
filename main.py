import tkinter as tk
from tkinter import ttk
import numpy as np
import fastf1
import pandas as pd
from f1_data import F1DataQuery
import time
import math
from PIL import Image, ImageTk, ImageDraw

class F1ReplayApp:
    def __init__(self, root, f1_data):
        self.root = root
        self.root.title("F1 Race Replay")
        self.root.geometry("1400x900")
        self.root.configure(bg='#111111') # Darker premium background
        
        self.f1_data = f1_data
        self.drivers = []
        self.telemetry_data = {}
        
        self.min_time = 0
        self.max_time = 0
        self.current_time = 0
        
        self.track_x = []
        self.track_y = []
        
        self.playing = False
        self.play_speed = 1.0 # Real time multiplier
        
        # Leaderboard animation tracking
        self.leaderboard_order = []
        self.row_height = 45
        self.driver_frames = {}
        self.driver_y_pos = {}
        
        self.setup_ui()
        self.load_race_data()
        
    def setup_ui(self):
        # Top Config Bar
        self.top_frame = tk.Frame(self.root, bg='#1a1a1a', height=60, highlightbackground="#e10600", highlightthickness=0, highlightcolor="#e10600")
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.top_frame.pack_propagate(False)
        
        # Draw F1 Logo text (approximate with Canvas)
        self.logo_canvas = tk.Canvas(self.top_frame, width=80, height=40, bg='#1a1a1a', highlightthickness=0)
        self.logo_canvas.pack(side=tk.LEFT, padx=15, pady=10)
        # Red 'F'
        self.logo_canvas.create_polygon([10,30, 30,30, 35,20, 15,20], fill="#e10600", outline="")
        self.logo_canvas.create_polygon([15,20, 45,20, 50,10, 20,10], fill="#e10600", outline="")
        # White '1'
        self.logo_canvas.create_polygon([40,30, 60,30, 70,10, 55,10, 50,20, 60,20], fill="white", outline="")
        
        tk.Label(self.top_frame, text="RACE REPLAY", fg="white", bg="#1a1a1a", font=("Arial", 16, "bold", "italic")).pack(side=tk.LEFT, padx=5)
        
        self.btn_play = tk.Button(self.top_frame, text="▶ PLAY", command=self.toggle_play, bg="#e10600", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5)
        self.btn_play.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Speed controls
        self.speed_var = tk.StringVar(value="5x")
        self.speed_dropdown = ttk.Combobox(self.top_frame, textvariable=self.speed_var, values=["1x", "2x", "5x", "10x", "20x"], width=5, state="readonly")
        self.speed_dropdown.pack(side=tk.LEFT, padx=5, pady=15)
        self.speed_dropdown.bind("<<ComboboxSelected>>", self.on_speed_change)
        
        self.time_slider = ttk.Scale(self.top_frame, from_=0, to=100, orient="horizontal", command=self.on_slider_move)
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=20)
        
        self.time_label = tk.Label(self.top_frame, text="00:00:00", fg="#e10600", bg="#1a1a1a", font=("Courier", 16, "bold"))
        self.time_label.pack(side=tk.RIGHT, padx=20)
        
        # Main Content
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#111111', sashwidth=4)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (Leaderboard & Telemetry)
        self.left_panel = tk.Frame(self.main_pane, bg='#181818', width=350)
        self.left_panel.pack_propagate(False)
        self.main_pane.add(self.left_panel, minsize=350)
        
        header_frame = tk.Frame(self.left_panel, bg="#222")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="LIVE LEADERBOARD", fg="white", bg="#e10600", font=("Arial", 12, "bold", "italic"), anchor="w", padx=10, pady=5).pack(fill=tk.X)
        
        # Use Canvas for smooth vertical animations of leaderboard rows
        self.lb_canvas = tk.Canvas(self.left_panel, bg='#181818', highlightthickness=0)
        self.lb_scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.lb_canvas.yview)
        
        self.lb_canvas.pack(side="left", fill="both", expand=True)
        self.lb_scrollbar.pack(side="right", fill="y")
        self.lb_canvas.configure(yscrollcommand=self.lb_scrollbar.set)
        
        self.driver_labels = {}
        self.driver_speeds = {}
        self.driver_gears = {}
        self.driver_badges = {}
        
        # Right Panel (Track Map)
        self.track_frame = tk.Frame(self.main_pane, bg='#111111')
        self.main_pane.add(self.track_frame)
        
        self.track_canvas = tk.Canvas(self.track_frame, bg='#111111', highlightthickness=0)
        self.track_canvas.pack(fill=tk.BOTH, expand=True)
        self.track_canvas.bind("<Configure>", self.on_canvas_resize)
        
        self.car_dots = {}
        self.car_glows = {}
        
    def on_speed_change(self, event):
        val = self.speed_var.get()
        self.play_speed = float(val.replace('x', ''))
        
    def draw_team_badge(self, abbreviation, color_hex):
        # Create a tiny 30x20 image with PIL for the team logo/badge
        img = Image.new('RGBA', (40, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle
        draw.rounded_rectangle((0, 0, 39, 23), radius=4, fill=color_hex, outline="#ffffff", width=1)
        
        return ImageTk.PhotoImage(img)

    def load_race_data(self):
        print("Loading Formula 1 session...")
        # Load a recent race (e.g. 2023 Bahrain)
        self.f1_data.load_session(2023, 'Bahrain', 'R')
        
        self.track_x, self.track_y = self.f1_data.get_track_layout()
        self.drivers = self.f1_data.get_drivers()
        print(f"Loaded {len(self.drivers)} drivers.")
        
        raw_telemetry = self.f1_data.get_all_laps()
        self.process_telemetry(raw_telemetry)
        self.setup_leaderboard()
        self.draw_track()
        
    def process_telemetry(self, raw_telemetry):
        print("Processing telemetry data...")
        
        global_min = pd.Timedelta(days=100)
        global_max = pd.Timedelta(0)
        
        for abb, tel in raw_telemetry.items():
            if not tel.empty and 'SessionTime' in tel.columns:
                min_t = tel['SessionTime'].min()
                max_t = tel['SessionTime'].max()
                if min_t < global_min:
                    global_min = min_t
                if max_t > global_max:
                    global_max = max_t
                    
        self.min_time = global_min.total_seconds()
        self.max_time = global_max.total_seconds()
        self.current_time = self.min_time
        
        self.time_slider.configure(from_=self.min_time, to=self.max_time)
        self.time_slider.set(self.min_time)
        self.play_speed = 5.0
        
        for abb, tel in raw_telemetry.items():
            if not tel.empty:
                tel = tel.copy()
                tel['TimeSecs'] = tel['SessionTime'].dt.total_seconds()
                
                # Make sure we have Distance
                if 'Distance' not in tel.columns:
                    tel['Distance'] = 0
                    
                self.telemetry_data[abb] = tel
                
    def setup_leaderboard(self):
        # Initial sorting by number string as fallback, later updated dynamically by Distance
        self.leaderboard_order = [d['abb'] for d in self.drivers]
        
        total_height = len(self.drivers) * self.row_height
        self.lb_canvas.configure(scrollregion=(0, 0, 350, total_height))
        
        for i, driver in enumerate(self.drivers):
            abb = driver['abb']
            color = f"#{driver['color']}" if driver['color'] else "#ffffff"
            
            y_pos = i * self.row_height
            self.driver_y_pos[abb] = y_pos
            
            # Create a frame in the canvas for each driver
            frame = tk.Frame(self.lb_canvas, bg='#2a2a2a', width=330, height=38, highlightthickness=1, highlightbackground="#444")
            self.driver_frames[abb] = self.lb_canvas.create_window(10, y_pos + 5, window=frame, anchor="nw", width=330, height=38)
            frame.pack_propagate(False)
            
            # Left color strip
            tk.Label(frame, bg=color, width=1).pack(side=tk.LEFT, fill=tk.Y)
            
            # Team Badge / Abbreviation
            self.driver_badges[abb] = self.draw_team_badge(abb, color)
            badge_lbl = tk.Label(frame, image=self.driver_badges[abb], bg="#2a2a2a")
            badge_lbl.pack(side=tk.LEFT, padx=(5, 5))
            
            # Position text (will be drawn by canvas but for now driver abbreviation over badge)
            tk.Label(frame, text=abb, fg="white", bg=color, font=("Arial", 9, "bold")).place(x=17, y=10)
            
            # Driver Name
            name_lbl = tk.Label(frame, text=f"{driver['name']}", fg="white", bg="#2a2a2a", font=("Arial", 10, "bold"))
            name_lbl.pack(side=tk.LEFT, padx=5)
            
            # Telemetry info
            info_frame = tk.Frame(frame, bg="#2a2a2a")
            info_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y, pady=5)
            
            speed_lbl = tk.Label(info_frame, text="0 km/h", fg="#00ff00", bg="#2a2a2a", font=("Consolas", 10, "bold"), width=8, anchor="e")
            speed_lbl.pack(side=tk.LEFT)
            
            gear_lbl = tk.Label(info_frame, text="N", fg="#ffaa00", bg="#2a2a2a", font=("Consolas", 10, "bold"), width=2)
            gear_lbl.pack(side=tk.LEFT, padx=(5,0))
            
            self.driver_speeds[abb] = speed_lbl
            self.driver_gears[abb] = gear_lbl
            
    def on_canvas_resize(self, event):
        self.draw_track()
        self.update_cars(interpolate=False)
        
    def draw_track(self):
        if self.track_x is None or len(self.track_x) == 0:
            return
            
        self.track_canvas.delete("track")
        
        w = self.track_canvas.winfo_width()
        h = self.track_canvas.winfo_height()
        
        if w <= 1 or h <= 1:
            return
            
        padding = 60
        
        min_x, max_x = np.min(self.track_x), np.max(self.track_x)
        min_y, max_y = np.min(self.track_y), np.max(self.track_y)
        
        scale_x = (w - 2 * padding) / (max_x - min_x)
        scale_y = (h - 2 * padding) / (max_y - min_y)
        self.scale = min(scale_x, scale_y)
        
        self.offset_x = (w - (max_x - min_x) * self.scale) / 2 - min_x * self.scale
        self.offset_y = (h - (max_y - min_y) * self.scale) / 2 - min_y * self.scale
        
        self.offset_y = h - self.offset_y
        self.scale_y_dir = -1
        
        pts = []
        for x, y in zip(self.track_x, self.track_y):
            cx = x * self.scale + self.offset_x
            cy = y * self.scale * self.scale_y_dir + self.offset_y
            pts.append(cx)
            pts.append(cy)
            
        if len(pts) >= 4:
            # Outer glow
            self.track_canvas.create_polygon(pts, fill='', outline='#333333', width=16, smooth=True, tags="track", joinstyle=tk.ROUND)
            # Main track asphalt
            self.track_canvas.create_polygon(pts, fill='', outline='#555555', width=10, smooth=True, tags="track", joinstyle=tk.ROUND)
            # Racing line indicator
            self.track_canvas.create_polygon(pts, fill='', outline='#111111', width=2, smooth=True, tags="track", dash=(4, 4))
            
    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.btn_play.configure(text="❚❚ PAUSE", bg="#ff9900")
            self.last_update_time = time.time()
            self.update_loop()
        else:
            self.btn_play.configure(text="▶ PLAY", bg="#e10600")
            
    def on_slider_move(self, val):
        self.current_time = float(val)
        self.update_cars(interpolate=False)
        self.update_leaderboard()
        
    def update_loop(self):
        if not self.playing:
            return
            
        now = time.time()
        dt = (now - self.last_update_time) * self.play_speed
        self.last_update_time = now
        
        self.current_time += dt
        
        if self.current_time >= self.max_time:
            self.current_time = self.min_time
            self.playing = False
            self.btn_play.configure(text="▶ PLAY", bg="#e10600")
            
        self.time_slider.set(self.current_time)
        self.update_cars(interpolate=True)
        self.update_leaderboard()
        self.animate_leaderboard()
        
        if self.playing:
            self.root.after(30, self.update_loop) # ~33fps for smooth animation
            
    def update_cars(self, interpolate=True):
        secs = self.current_time
        
        td = pd.Timedelta(seconds=secs)
        total_s = int(td.total_seconds())
        h = total_s // 3600
        m = (total_s % 3600) // 60
        s = total_s % 60
        self.time_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        
        for driver in self.drivers:
            abb = driver['abb']
            if abb not in self.telemetry_data:
                continue
                
            tel = self.telemetry_data[abb]
            times = tel['TimeSecs'].values
            
            idx = np.searchsorted(times, secs)
            
            if idx > 0 and idx < len(tel):
                row1 = tel.iloc[idx-1]
                row2 = tel.iloc[idx]
                
                # Interpolate for ultra-smooth movement between telemetry points
                t1 = row1['TimeSecs']
                t2 = row2['TimeSecs']
                
                if interpolate and t2 > t1:
                    ratio = (secs - t1) / (t2 - t1)
                    x = row1['X'] + (row2['X'] - row1['X']) * ratio
                    y = row1['Y'] + (row2['Y'] - row1['Y']) * ratio
                else:
                    x = row1['X']
                    y = row1['Y']
                
                speed = row1['Speed']
                gear = row1['nGear']
                
                # Update UI
                if not pd.isna(speed):
                    self.driver_speeds[abb].configure(text=f"{int(speed)} km/h")
                if not pd.isna(gear):
                    g_text = str(int(gear)) if gear > 0 else "N"
                    self.driver_gears[abb].configure(text=g_text)
                
                if not pd.isna(x) and not pd.isna(y):
                    cx = x * self.scale + self.offset_x
                    cy = y * self.scale * self.scale_y_dir + self.offset_y
                    
                    r = 8
                    if abb not in self.car_dots:
                        color = f"#{driver['color']}" if driver['color'] else "#ffffff"
                        
                        # Add a glow effect
                        self.car_glows[abb] = self.track_canvas.create_oval(cx-r-3, cy-r-3, cx+r+3, cy+r+3, fill='', outline=color, tags="car", width=2)
                        
                        self.car_dots[abb] = self.track_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline='white', tags="car", width=1.5)
                        # Add label next to car with dark background for contrast
                        self.track_canvas.create_text(cx+15, cy+15, text=abb, fill='white', font=("Arial", 9, "bold"), tags=f"lbl_{abb}")
                    else:
                        self.track_canvas.coords(self.car_glows[abb], cx-r-3, cy-r-3, cx+r+3, cy+r+3)
                        self.track_canvas.coords(self.car_dots[abb], cx-r, cy-r, cx+r, cy+r)
                        self.track_canvas.coords(f"lbl_{abb}", cx+15, cy+15)
                        
                        # Bring to front so they don't hide each other badly
                        self.track_canvas.tag_raise(self.car_glows[abb])
                        self.track_canvas.tag_raise(self.car_dots[abb])
                        self.track_canvas.tag_raise(f"lbl_{abb}")

    def update_leaderboard(self):
        # Calculate current distances to sort leaderboard
        distances = []
        secs = self.current_time
        
        for driver in self.drivers:
            abb = driver['abb']
            if abb not in self.telemetry_data:
                distances.append((abb, -1))
                continue
                
            tel = self.telemetry_data[abb]
            times = tel['TimeSecs'].values
            idx = np.searchsorted(times, secs)
            
            if idx > 0 and idx < len(tel):
                row = tel.iloc[idx-1]
                dist = row.get('Distance', 0)
                if pd.isna(dist):
                    dist = 0
                distances.append((abb, dist))
            else:
                distances.append((abb, -1))
        
        # Sort by distance descending
        distances.sort(key=lambda x: x[1], reverse=True)
        self.leaderboard_order = [d[0] for d in distances]
        
    def animate_leaderboard(self):
        # Move canvases to target positions
        for i, abb in enumerate(self.leaderboard_order):
            target_y = i * self.row_height
            current_y = self.driver_y_pos.get(abb, target_y)
            
            # Linear interpolation for smooth vertical swap
            if abs(target_y - current_y) > 1:
                new_y = current_y + (target_y - current_y) * 0.2 # 20% closer each frame
                self.driver_y_pos[abb] = new_y
            else:
                new_y = target_y
                self.driver_y_pos[abb] = target_y
                
            self.lb_canvas.coords(self.driver_frames[abb], 10, new_y + 5)


if __name__ == "__main__":
    root = tk.Tk()
    query = F1DataQuery()
    app = F1ReplayApp(root, query)
    root.mainloop()
