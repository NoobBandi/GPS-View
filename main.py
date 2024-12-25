import tkinter as tk
from tkinter import filedialog
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
import customtkinter as ctk
import gpxpy
import os

def process_track_points(points, threshold=0.0001):
    """過濾重複點並平滑軌跡點."""
    if not points or len(points) < 2:
        return points

    filtered_points = [points[0]]
    for point in points[1:]:
        last_point = filtered_points[-1]
        if abs(point[0] - last_point[0]) > threshold or abs(point[1] - last_point[1]) > threshold:
            filtered_points.append(point)

    # 基本平滑處理（簡單平均法）
    smoothed_points = []
    for i in range(len(filtered_points)):
        lat, lon, count = 0, 0, 0
        for j in range(max(0, i - 1), min(len(filtered_points), i + 2)):  # 包含前後各1點
            lat += filtered_points[j][0]
            lon += filtered_points[j][1]
            count += 1
        smoothed_points.append((lat / count, lon / count))

    return smoothed_points

class ImageWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("圖片預覽")
        self.geometry("400x600")
        
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.current_image = None

    def update_image(self, image_path):
        try:
            # 載入圖片
            pil_image = Image.open(image_path)
            # 計算調整後的大小（保持比例）
            display_size = (780, 580)
            pil_image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # 使用 CTkImage 替代 PhotoImage
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=pil_image.size
            )
            
            # 更新標籤中的圖片
            self.image_label.configure(image=ctk_image)
            self.current_image = ctk_image 
            
        except Exception as e:
            print(f"更新圖片時發生錯誤: {e}")

class GPXViewer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GPX 軌跡檢視器 (Beta v0.3)")
        self.geometry("1024x800")

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"當前工作目錄: {self.current_dir}")

        # Create Map Frame
        self.map_frame = ctk.CTkFrame(self)
        self.map_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.map_widget = TkinterMapView(self.map_frame, corner_radius=10)
        self.map_widget.pack(fill=tk.BOTH, expand=True)

        # Create Control Frame
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(padx=5, pady=20)

        # Configure grid layout
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)
        self.control_frame.grid_columnconfigure(2, weight=1)
        self.control_frame.grid_columnconfigure(3, weight=1)
        self.control_frame.grid_columnconfigure(4, weight=1)

        # Create Button to Load GPX
        self.load_gpx_btn = ctk.CTkButton(
            self.control_frame, text="載入 GPX 文件", command=self.load_gpx)
        self.load_gpx_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Create Clean GPX Button
        self.clean_gpx_btn = ctk.CTkButton(
            self.control_frame, text="清除 GPX 文件", command=self.clean_gpx)
        self.clean_gpx_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Create Progress Bar and Play Button Frame
        self.progress_play_frame = ctk.CTkFrame(self.control_frame)
        self.progress_play_frame.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Create Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkSlider(self.progress_play_frame, from_=0, to=100,
              variable=self.progress_var,
              command=self.on_progress_change)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        # Create Play Button
        self.play_btn = ctk.CTkButton(
            self.progress_play_frame, text="播放", command=self.toggle_play, state="disabled")
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Create Speed Control
        self.speed_var = tk.StringVar(value="1x")
        self.speed_combobox = ctk.CTkComboBox(self.control_frame,
              values=["0.5x", "1x", "2x", "4x"],
              variable=self.speed_var,
              width=80,  # 增加寬度
              state="readonly",
              corner_radius=5)  # 圓角設計
        self.speed_combobox.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        
        # 圖片相關變量
        self.image_folder = r"D:\●●Python_Project●●\GPS\IMG_5840_frames"
        self.total_frames = 6655
        self.current_frame = 0

        self.image_window = None
        self.map_path = None
        self.current_path = None
        self.track_points = []
        self.is_playing = False

        self.current_point_index = 0
        self.animation_speed = 1.0  # 動畫播放速度倍率

        self.initialize_map()

    def toggle_image_window(self):
        if self.image_window is None or not self.image_window.winfo_exists():
            self.image_window = ImageWindow()
        else:
            self.image_window.focus()

    def initialize_map(self):
        ncut_lat = 24.1448
        ncut_lng = 120.7300
        self.map_widget.set_position(ncut_lat, ncut_lng)
        self.map_widget.set_zoom(17)
        self.map_widget.set_marker(ncut_lat, ncut_lng, text="NCUT")

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
        
        if self.image_window and self.image_window.winfo_exists():
            self.image_window.destroy()
            self.image_window = None

    def load_gpx(self):
        file_path = filedialog.askopenfilename(filetypes=[("GPX Files", "*.gpx")])
        if file_path:
            try:
                # 檢查檔案名稱
                gpx_filename = os.path.basename(file_path)
                show_images = (gpx_filename == "2024-12-13_21-01-07.gpx")

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

                # 路線修正
                self.track_points = process_track_points(self.track_points)
                print(f"修正後的軌跡點數量: {len(self.track_points)}")
                
                # 只在特定 GPX 檔案時開啟圖片視窗
                if show_images:
                    self.toggle_image_window()
                elif self.image_window and self.image_window.winfo_exists():
                    # 如果載入其他 GPX 檔案，關閉已開啟的圖片視窗
                    self.image_window.destroy()
                    self.image_window = None

                if len(self.track_points) >= 2:
                    self.map_widget.set_position(self.track_points[0][0], self.track_points[0][1])
                    self.map_widget.set_zoom(17)
                    self.map_widget.set_marker(self.track_points[0][0], self.track_points[0][1], text="起點")
                    self.current_point_index = 0
                    self.progress_var.set(0)
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
            self.current_point_index = 1

        # 更新路徑
        current_path = self.track_points[:self.current_point_index + 1]
        if len(current_path) >= 2:
            self.current_path = self.map_widget.set_path(current_path)

            # 更新進度條
            progress = (self.current_point_index / (len(self.track_points) - 1)) * 100
            self.progress_var.set(progress)

            # 更新地圖視角
            current_pos = self.track_points[self.current_point_index]
            self.map_widget.set_position(current_pos[0], current_pos[1])

            # 更新圖片
            # 根據當前進度計算對應的圖片編號
            if self.image_window and self.image_window.winfo_exists():
                frame_index = int((self.current_point_index / len(self.track_points)) * self.total_frames)
                image_path = os.path.join(self.image_folder, f"frame_{frame_index:06d}.jpg")
                if os.path.exists(image_path):
                    self.image_window.update_image(image_path)

            # 移動到下一個點
            self.current_point_index += 1

            # 設置動畫速度
            speed_value = float(self.speed_var.get().replace('x', ''))
            delay = int(100 / speed_value)

            if self.current_point_index < len(self.track_points):
                self.after(delay, self.animate_path)
            else:
                self.stop_animation()
                self.current_point_index = 0

    def update_image(self, frame_index):
        try:
            # 格式化圖片文件名
            image_path = os.path.join(self.image_folder, f"frame_{frame_index:06d}.jpg")
            
            if os.path.exists(image_path):
                # 加載並調整圖片大小
                image = Image.open(image_path)
                # 調整圖片大小以適應顯示區域（例如寬度固定為400像素）
                width = 400
                ratio = width / image.width
                height = int(image.height * ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                # 轉換為 CTk 可用的格式
                photo = ImageTk.PhotoImage(image)
                
                # 更新標籤中的圖片
                self.image_label.configure(image=photo)
                self.image_label.image = photo  # 保持引用以防止垃圾回收
                
                print(f"已更新圖片: frame_{frame_index:06d}.jpg")
        except Exception as e:
            print(f"更新圖片時發生錯誤: {e}")

    def on_progress_change(self, value):
        if not self.is_playing and self.track_points:
            progress = float(value)
            index = int((progress / 100) * (len(self.track_points) - 1))
            self.current_point_index = index
            current_path = self.track_points[:index + 1]
            self.current_path = self.map_widget.set_path(current_path)
            
            # 更新圖片
            if self.image_window and self.image_window.winfo_exists():
                frame_index = int((float(value) / 100) * self.total_frames)
                image_path = os.path.join(self.image_folder, f"frame_{frame_index:06d}.jpg")
                if os.path.exists(image_path):
                    self.image_window.update_image(image_path)
            
            if index < len(self.track_points):
                self.map_widget.set_position(
                    self.track_points[index][0],
                    self.track_points[index][1]
                )

if __name__ == "__main__":
    app = GPXViewer()
    app.mainloop()
