import tkinter as tk
from tkinter import ttk, filedialog
from tkintermapview import TkinterMapView
import gpxpy
import os
import time


class GPXViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("GPX 軌跡檢視器")
        self.geometry("1024x800")

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"當前工作目錄: {self.current_dir}")

        # Create Control Frame
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create Button to Load GPX
        self.load_gpx_btn = ttk.Button(
            self.control_frame, text="載入 GPX", command=self.load_gpx)
        self.load_gpx_btn.pack(side='left', padx=5)

        # Create Clean GPX Button
        self.clean_gpx_btn = ttk.Button(
            self.control_frame, text="清除 GPX", command=self.clean_gpx)
        self.clean_gpx_btn.pack(side='left', padx=5)

        # Create Play Button
        self.play_btn = ttk.Button(
            self.control_frame, text="播放", command=self.toggle_play, state="disabled")
        self.play_btn.pack(side='left', padx=5)

        # Create Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.control_frame, from_=0, to=100,
                                      orient='horizontal', variable=self.progress_var,
                                      command=self.on_progress_change)
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=5)

        # Create Speed Control
        self.speed_var = tk.StringVar(value="1x")
        self.speed_combobox = ttk.Combobox(self.control_frame,
                                           values=["0.5x", "1x", "2x", "4x"],
                                           textvariable=self.speed_var,
                                           width=5,
                                           state="readonly")
        self.speed_combobox.pack(side='left', padx=5)

        # Create Map Frame
        self.map_widget = TkinterMapView(self, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)

        self.map_path = None
        self.current_path = None
        self.track_points = []
        self.is_playing = False

        self.current_point_index = 0
        self.animation_speed = 1.0  # 動畫播放速度倍率

        self.initialize_map()

    def initialize_map(self):
        ncut_lat = 24.1448
        ncut_lng = 120.7300
        self.map_widget.set_position(ncut_lat, ncut_lng)
        self.map_widget.set_zoom(17)
        self.map_widget.set_marker(ncut_lat, ncut_lng, text="勤益科技大學")

    def clean_gpx(self):
        self.stop_animation()
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.initialize_map()
        self.map_path = None
        self.track_points = []
        self.progress_var.set(0)
        self.play_btn.configure(state="disabled")
        print("已清除 GPX 軌跡")

    def load_gpx(self):
        file_path = filedialog.askopenfilename(filetypes=[("GPX Files", "*.gpx")])
        if file_path:
            try:
                self.stop_animation()
                self.map_widget.delete_all_marker()
                self.map_widget.delete_all_path()
                
                with open(file_path, 'r', encoding='utf-8') as gpx_file:
                    gpx = gpxpy.parse(gpx_file)

                self.track_points = []
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            self.track_points.append((point.latitude, point.longitude))

                if len(self.track_points) >= 2:  # 確保至少有兩個點
                    if self.current_path:
                        self.map_widget.delete(self.current_path)

                    # 初始只顯示起點
                    self.map_widget.set_position(self.track_points[0][0], self.track_points[0][1])
                    self.map_widget.set_zoom(17)

                    # 設置起點標記
                    self.map_widget.set_marker(
                        self.track_points[0][0], 
                        self.track_points[0][1], 
                        text="起點"
                    )
                    
                    # 重置播放狀態
                    self.current_point_index = 0
                    self.progress_var.set(0)
                    print(f"已載入 GPX 檔案: {file_path}")
                    print(f"軌跡點數量: {len(self.track_points)}")

                    self.play_btn.configure(state="normal")
                else:
                    print("GPX 檔案中的點數量不足")

            except Exception as e:
                print(f"載入 GPX 檔案時發生錯誤: {e}")

    def toggle_play(self):
        if not self.track_points:
            return

        if self.is_playing:
            self.stop_animation()
        else:
            self.start_animation()

    def start_animation(self):
        self.is_playing = True
        self.play_btn.configure(text="暫停")
        self.animate_path()

    def stop_animation(self):
        self.is_playing = False
        self.play_btn.configure(text="播放")

    def animate_path(self):
        if not self.is_playing or self.current_point_index >= len(self.track_points):
            return

        # 確保至少有兩個點來繪製路徑
        if self.current_point_index < 1:
            self.current_point_index = 1  # 確保至少有兩個點

        # 更新路徑
        current_path = self.track_points[:self.current_point_index + 1]
        if len(current_path) >= 2:  # 確保有足夠的點來繪製路徑
            self.current_path = self.map_widget.set_path(current_path)

            # 更新進度條
            progress = (self.current_point_index /
                        (len(self.track_points) - 1)) * 100
            self.progress_var.set(progress)

            # 更新地圖視角
            current_pos = self.track_points[self.current_point_index]
            self.map_widget.set_position(current_pos[0], current_pos[1])

            # 移動到下一個點
            self.current_point_index += 1

            # 設置動畫速度
            speed_value = float(self.speed_var.get().replace('x', ''))
            delay = int(100 / speed_value)  # 基礎延遲100毫秒

            if self.current_point_index < len(self.track_points):
                self.after(delay, self.animate_path)
            else:
                self.stop_animation()
                self.current_point_index = 0

    def on_progress_change(self, value):
        if not self.is_playing and self.track_points:
            progress = float(value)
            index = int((progress / 100) * (len(self.track_points) - 1))
            self.current_point_index = index
            current_path = self.track_points[:index + 1]
            self.current_path = self.map_widget.set_path(current_path)
            if index < len(self.track_points):
                self.map_widget.set_position(
                    self.track_points[index][0],
                    self.track_points[index][1]
                )


if __name__ == "__main__":
    app = GPXViewer()
    app.mainloop()
