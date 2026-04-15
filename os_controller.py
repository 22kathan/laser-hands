import asyncio
import json
import logging
import pyautogui
import websockets
import time
import math
import os
import webbrowser

# Disable failsafe to prevent crashes if cursor moves to exact corners
pyautogui.FAILSAFE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
logging.info(f"Detected screen resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

# State tracking for drag/drop and hover
is_mouse_down = False
hover_start_time = None
hover_pos = None
HOVER_TOLERANCE_PX = 35  # increased for stability
HOVER_DURATION_SEC = 1.5  # faster right-click

# New State tracking for stability, scroll, and zoom
prev_mouse_x = None
prev_mouse_y = None
prev_scroll_y = None
prev_zoom_size = None
prev_speed = 0
last_click_time = 0
last_click_pos = None
gesture_start_time = None

# Cursor smoothing constants (improved for stability)
MIN_DEADZONE_PX = 5  # Ignore tiny movements
SMOOTHING_ALPHA = 0.65  # Higher = more smoothing (0.5-0.7 is sweet spot)
MAX_VELOCITY = 100  # Prevent cursor jump
VELOCITY_SMOOTHING = 0.4  # Smooth out acceleration

async def handle_connection(websocket):
    global is_mouse_down, hover_start_time, hover_pos
    global prev_mouse_x, prev_mouse_y, prev_scroll_y, prev_zoom_size, prev_speed, last_click_time, last_click_pos, gesture_start_time
    logging.info("Browser connected!")
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "tracking":
                norm_x = data.get("x", 0.5)
                norm_y = data.get("y", 0.5)
                is_pinching = data.get("isPinching", False)
                gesture = data.get("gesture", "move")
                hand_distance = data.get("handDistance", 0)
                hand_open = data.get("handOpen", True)
                
                if gesture == "move":
                    # Clear alternate gesture states
                    prev_scroll_y = None
                    prev_zoom_size = None
                
                    margin_x, margin_y = 0.20, 0.25
                    scaled_x = (norm_x - margin_x) / (1.0 - 2 * margin_x)
                    scaled_y = (norm_y - margin_y) / (1.0 - 2 * margin_y)
                    
                    scaled_x = max(0.01, min(0.99, scaled_x))
                    scaled_y = max(0.01, min(0.99, scaled_y))
                    target_x = scaled_x * SCREEN_WIDTH
                    target_y = scaled_y * SCREEN_HEIGHT
                    
                    # IMPROVED: Multi-level smoothing for stability
                    if prev_mouse_x is None:
                        prev_mouse_x, prev_mouse_y = target_x, target_y
                        prev_speed = 0
                    
                    # Calculate movement distance (raw)
                    raw_distance = math.hypot(target_x - prev_mouse_x, target_y - prev_mouse_y)
                    
                    # Deadzone: Ignore tiny jitter movements
                    if raw_distance < MIN_DEADZONE_PX:
                        continue
                    
                    # Adaptive smoothing based on velocity
                    current_speed = min(raw_distance, MAX_VELOCITY)
                    prev_speed = prev_speed * VELOCITY_SMOOTHING + current_speed * (1 - VELOCITY_SMOOTHING)
                    
                    # Higher alpha for faster movements (more responsive), lower for slow (more stable)
                    adaptive_alpha = SMOOTHING_ALPHA * (1.0 + (prev_speed / 50.0) * 0.3)
                    adaptive_alpha = min(adaptive_alpha, 0.85)  # Cap maximum
                    
                    smoothed_x = prev_mouse_x + (target_x - prev_mouse_x) * adaptive_alpha
                    smoothed_y = prev_mouse_y + (target_y - prev_mouse_y) * adaptive_alpha
                    
                    pyautogui.moveTo(smoothed_x, smoothed_y, _pause=False)
                    prev_mouse_x, prev_mouse_y = smoothed_x, smoothed_y
                    
                    # Left Click Hook
                    if is_pinching and not is_mouse_down:
                        pyautogui.mouseDown()
                        is_mouse_down = True
                        logging.info("Left Mouse Down")
                    elif not is_pinching and is_mouse_down:
                        pyautogui.mouseUp()
                        is_mouse_down = False
                        logging.info("Left Mouse Up")
                        
                    # Right Click Hook (Hover-based)
                    if hover_start_time is None:
                        hover_start_time = time.time()
                        hover_pos = (target_x, target_y)
                    else:
                        if math.hypot(target_x - hover_pos[0], target_y - hover_pos[1]) > HOVER_TOLERANCE_PX:
                            hover_start_time = time.time()
                            hover_pos = (target_x, target_y)
                        elif (time.time() - hover_start_time) >= HOVER_DURATION_SEC:
                            pyautogui.rightClick()
                            logging.info("Right Click Executed")
                            hover_start_time = None  # Reset
                            
                elif gesture == "scroll":
                    if prev_scroll_y is None:
                        prev_scroll_y = norm_y
                    else:
                        dy = norm_y - prev_scroll_y
                        if abs(dy) > 0.015:
                            clicks = int(-dy * 4000)
                            pyautogui.scroll(clicks)
                            prev_scroll_y = norm_y
                            logging.info(f"Scroll: {clicks} clicks")
                            
                elif gesture == "zoom":
                    if prev_zoom_size is None:
                        prev_zoom_size = norm_y
                    else:
                        dz = norm_y - prev_zoom_size
                        if abs(dz) > 0.04:
                            if dz > 0:
                                pyautogui.hotkey('ctrl', '-')
                                logging.info("Zooming Out")
                            else:
                                pyautogui.hotkey('ctrl', '+')
                                logging.info("Zooming In")
                            prev_zoom_size = norm_y
                
                # NEW GESTURES: No lag, hardware-level speed
                elif gesture == "double_click":
                    pyautogui.click()
                    pyautogui.click()
                    logging.info("Double Click")
                
                elif gesture == "swipe_left":
                    pyautogui.hotkey('alt', 'left')
                    logging.info("Swipe Left: Alt+Left (Back)")
                
                elif gesture == "swipe_right":
                    pyautogui.hotkey('alt', 'right')
                    logging.info("Swipe Right: Alt+Right (Forward)")
                
                elif gesture == "swipe_up":
                    pyautogui.hotkey('win', 'tab')
                    logging.info("Swipe Up: Task View")
                
                elif gesture == "swipe_down":
                    pyautogui.hotkey('win', 'd')
                    logging.info("Swipe Down: Show Desktop")
                
                elif gesture == "hand_open":
                    # Hand fully open (palm facing camera)
                    if not hand_open:
                        pyautogui.hotkey('win', 'up')
                        logging.info("Hand Open: Maximize Window")
                
                elif gesture == "hand_closed":
                    # Hand fully closed (fist)
                    if hand_open:
                        pyautogui.hotkey('win', 'down')
                        logging.info("Hand Closed: Minimize Window")
                
                elif gesture == "thumbs_up":
                    pyautogui.hotkey('ctrl', 'l')
                    logging.info("Thumbs Up: Focus Address Bar")
                
                elif gesture == "peace":
                    # Two fingers up (peace sign)
                    pyautogui.hotkey('ctrl', 't')
                    logging.info("Peace: New Tab")
                
                elif gesture == "ok_sign":
                    # Thumb & index circle
                    pyautogui.hotkey('ctrl', 'w')
                    logging.info("OK Sign: Close Tab")
                
                elif gesture == "volume_up":
                    pyautogui.hotkey('volumeup')
                    logging.info("Volume Up")
                
                elif gesture == "volume_down":
                    pyautogui.hotkey('volumedown')
                    logging.info("Volume Down")
                
    except websockets.exceptions.ConnectionClosed:
        logging.info("Browser disconnected.")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
    finally:
        # Safety catch: release mouse if connection drops while holding
        if is_mouse_down:
            pyautogui.mouseUp()
            is_mouse_down = False

async def main():
    try:
        async with websockets.serve(handle_connection, "localhost", 8765):
            logging.info("OS Control WebSocket Server running on ws://localhost:8765")
            
            # Auto-launch the web interface index.html
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
            html_url = f"file:///{html_path.replace(os.sep, '/')}"
            logging.info(f"Automatically opening browser to {html_url}")
            webbrowser.open(html_url)
            
            logging.info("Waiting for browser to connect...")
            await asyncio.Future()  # run forever
    except Exception as e:
        logging.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ImportError as e:
        logging.error(f"Missing dependency: {e}")
        logging.error("Please install required packages: pip install -r requirements.txt")
        exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        exit(1)
