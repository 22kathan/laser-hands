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

# Cursor smoothing constants (improved for stability)
MIN_DEADZONE_PX = 5  # Ignore tiny movements
SMOOTHING_ALPHA = 0.65  # Higher = more smoothing (0.5-0.7 is sweet spot)
MAX_VELOCITY = 100  # Prevent cursor jump
VELOCITY_SMOOTHING = 0.4  # Smooth out acceleration

async def handle_connection(websocket):
    global is_mouse_down, hover_start_time, hover_pos
    global prev_mouse_x, prev_mouse_y, prev_scroll_y, prev_zoom_size, prev_speed, last_click_time
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
                    
                    # PERFECTED: Left Click Hook with debouncing
                    if is_pinching and not is_mouse_down:
                        pyautogui.mouseDown()
                        is_mouse_down = True
                        last_click_time = time.time()
                        logging.info("✓ Left Mouse Down (Click Started)")
                    elif not is_pinching and is_mouse_down:
                        # Only register if pinch stayed down > 50ms (prevents accidental clicks)
                        if time.time() - last_click_time > 0.05:
                            pyautogui.mouseUp()
                            is_mouse_down = False
                            logging.info("✓ Left Mouse Up (Click Complete)")
                        else:
                            # Reject accidental short click
                            pyautogui.mouseUp()
                            is_mouse_down = False
                            logging.info("⊗ Click ignored (too short)")
                        
                    # PERFECTED: Right Click Hook with better hover detection
                    if hover_start_time is None:
                        hover_start_time = time.time()
                        hover_pos = (target_x, target_y)
                    else:
                        hover_distance = math.hypot(target_x - hover_pos[0], target_y - hover_pos[1])
                        hover_duration = time.time() - hover_start_time
                        
                        # Reset if hand moved too much
                        if hover_distance > HOVER_TOLERANCE_PX:
                            hover_start_time = time.time()
                            hover_pos = (target_x, target_y)
                        # Execute right click only after stable hover
                        elif hover_duration >= HOVER_DURATION_SEC and hover_distance < HOVER_TOLERANCE_PX:
                            pyautogui.rightClick()
                            logging.info("✓ Right Click Executed (Stable Hover)")
                            hover_start_time = None  # Reset hover state
                            
                elif gesture == "scroll":
                    if prev_scroll_y is None:
                        prev_scroll_y = norm_y
                    else:
                        dy = norm_y - prev_scroll_y
                        if abs(dy) > 0.015:
                            clicks = int(-dy * 4000)
                            pyautogui.scroll(clicks)
                            prev_scroll_y = norm_y
                            logging.info(f"✓ Scroll: {clicks} clicks")
                            
                elif gesture == "zoom":
                    if prev_zoom_size is None:
                        prev_zoom_size = norm_y
                    else:
                        dz = norm_y - prev_zoom_size
                        if abs(dz) > 0.04:
                            if dz > 0:
                                pyautogui.hotkey('ctrl', '-')
                                logging.info("✓ Zooming Out")
                            else:
                                pyautogui.hotkey('ctrl', '+')
                                logging.info("✓ Zooming In")
                            prev_zoom_size = norm_y
                    
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
            print("\n" + "="*50)
            print("   LASER HANDS OS DAEMON IS ACTIVE")
            print("="*50)
            print("✓ WebSocket Server: ws://localhost:8765")
            
            # Smart HTML Auto-Launch
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
            if os.path.exists(html_path):
                html_url = f"file:///{html_path.replace(os.sep, '/')}"
                logging.info(f"Opening local web interface: {html_url}")
                webbrowser.open(html_url)
            else:
                print("\n[INFO] index.html not found in current directory.")
                print("       This is okay! Keep your browser tab open at:")
                print("       http://localhost:8000  OR  your github portfolio site.")
            
            print("\n[READY] Waiting for browser to connect...")
            print("(Minimize this window and use gestures in the browser)\n")
            
            await asyncio.Future()  # run forever
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:
            print("\n[ERROR] Port 8765 is already in use!")
            print("        Make sure another instance of this script isn't already running.\n")
        else:
            logging.error(f"Server error: {e}")
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
