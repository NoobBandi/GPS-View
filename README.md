# GPS View GPS 定位資訊回放程式
> NCUT 四慧一乙 Python 期末報告

## Version 版本
* 2024-12-13 Beta v0.1
* 2024-12-19 Beta v0.2

## Use Package 使用的套件
| 套件名稱 | 套件用途   |
|---------|---------   |
| tkinter | Python GUI |
| tkintermapview  | 在 GUI 上可以正常顯示地圖 |
| gpxpy | 讀取&解析 GPX 文件 |
| os | 抓取 GPX 文件位置 |

## Install Package 安裝套件
透過 `pip install` 在終端機上進行安裝。

❗❗注意:
進行 `pip install` 前請先記得要先安裝 **[Python](https://www.python.org/downloads/)**

Command: 
```
pip install -r requirements.txt
```

## Run Test 進行測試
安裝完所需套件後，可在該檔案資料夾內執行 `py main.py`，如果執行成功將會跳出 GUI 的介面出來。

Command:
```
py main.py
```
OR
```
python main.py
```

## Process 運作流程
1. 系統初始化 (地圖、GUI)
2. 等待載入 GPX 文件
3. 載入並讀取 GPX 文件
4. 重新定位地圖座標
5. 開啟軌跡播放按鈕
6. 開始播放
7. 可調整移動速率
8. 清除已載入 GPX 文件
9. 系統重新初始化 (地圖、GUI)
10. 結束
