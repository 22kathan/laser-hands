import asyncio
import json
import logging
import pyautogui
import websockets
import time
import math

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
HOVER_TOLERANCE_PX = 25  # relaxed tolerance
HOVER_DURATION_SEC = 2.0
has_right_clicked = False

# New State tracking for stability, scroll, and zoom
prev_mouse_x = None
prev_mouse_y = None
prev_scroll_y = None
prev_zoom_size = None

async def handle_connection(websocket):
    global is_mouse_down, hover_start_time, hover_pos, has_right_clicked
    global prev_mouse_x, prev_mouse_y, prev_scroll_y, prev_zoom_size
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
                    
                    # EMA Smoothing & Deadzone Filter
                    if prev_mouse_x is None:
                        prev_mouse_x, prev_mouse_y = target_x, target_y
                        
                    alpha = 0.5
                    smoothed_x = prev_mouse_x + (target_x - prev_mouse_x) * alpha
                    smoothed_y = prev_mouse_y + (target_y - prev_mouse_y) * alpha
                    
                    if math.hypot(target_x - prev_mouse_x, target_y - prev_mouse_y) > 3.0:
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
                        
                    # Right Click Hook
                    if hover_start_time is None:
                        hover_start_time = time.time()
                        hover_pos = (target_x, target_y)
                        has_right_clicked = False
                    else:
                        if math.hypot(target_x - hover_pos[0], target_y - hover_pos[1]) > HOVER_TOLERANCE_PX:
                            hover_start_time = time.time()
                            hover_pos = (target_x, target_y)
                            has_right_clicked = False
                        elif not has_right_clicked and (time.time() - hover_start_time) >= HOVER_DURATION_SEC:
                            pyautogui.rightClick()
                            has_right_clicked = True
                            logging.info("Right Click Executed")
                            
                elif gesture == "scroll":
                    if prev_scroll_y is None:
                        prev_scroll_y = norm_y
                    else:
                        dy = norm_y - prev_scroll_y
                        if abs(dy) > 0.015:
                            clicks = int(-dy * 4000) # Negative because y grows downwards
                            pyautogui.scroll(clicks)
                            prev_scroll_y = norm_y
                            
                elif gesture == "zoom":
                    if prev_zoom_size is None:
                        prev_zoom_size = norm_y
                    else:
                        dz = norm_y - prev_zoom_size
                        if abs(dz) > 0.04:
                            if dz > 0: # hand stretched outwards
                                pyautogui.hotkey('ctrl', '-')
                                logging.info("Zooming Out (Hand Stretched)")
                            else: # hand pinched inwards
                                pyautogui.hotkey('ctrl', '+')
                                logging.info("Zooming In (Hand Contracted)")
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
    start_server = websockets.serve(handle_connection, "localhost", 8765)
    logging.info("OS Control WebSocket Server running on ws://localhost:8765")
    logging.info("Waiting for browser to connect...")
    await start_server
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
