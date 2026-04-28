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

# State tracking
is_mouse_down = False

# Cursor smoothing state
prev_mouse_x = None
prev_mouse_y = None
prev_scroll_y = None
prev_speed = 0
last_click_time = 0

# Enterprise-grade cursor constants
MIN_DEADZONE_PX = 3       # Tight deadzone for precision
SMOOTHING_ALPHA = 0.55     # Base smoothing (0.4-0.7 sweet spot)
MAX_VELOCITY = 120         # Cap max cursor jump
VELOCITY_SMOOTHING = 0.35  # Smooth acceleration transitions

async def handle_connection(websocket):
    global is_mouse_down
    global prev_mouse_x, prev_mouse_y, prev_scroll_y, prev_speed, last_click_time
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
                
                    # Map normalised hand coords to screen with edge margins
                    margin_x, margin_y = 0.18, 0.22
                    scaled_x = (norm_x - margin_x) / (1.0 - 2 * margin_x)
                    scaled_y = (norm_y - margin_y) / (1.0 - 2 * margin_y)
                    
                    scaled_x = max(0.005, min(0.995, scaled_x))
                    scaled_y = max(0.005, min(0.995, scaled_y))
                    target_x = scaled_x * SCREEN_WIDTH
                    target_y = scaled_y * SCREEN_HEIGHT
                    
                    # Initialize on first frame
                    if prev_mouse_x is None:
                        prev_mouse_x, prev_mouse_y = target_x, target_y
                        prev_speed = 0
                    
                    # Raw movement distance
                    raw_distance = math.hypot(target_x - prev_mouse_x, target_y - prev_mouse_y)
                    
                    # Deadzone: eliminate micro-jitter
                    if raw_distance < MIN_DEADZONE_PX:
                        # Still process clicks even in deadzone
                        pass
                    else:
                        # Velocity-adaptive smoothing
                        current_speed = min(raw_distance, MAX_VELOCITY)
                        prev_speed = prev_speed * VELOCITY_SMOOTHING + current_speed * (1 - VELOCITY_SMOOTHING)
                        
                        # Fast motion = responsive, slow motion = ultra-stable
                        adaptive_alpha = SMOOTHING_ALPHA * (1.0 + (prev_speed / 40.0) * 0.25)
                        adaptive_alpha = max(0.3, min(adaptive_alpha, 0.85))
                        
                        smoothed_x = prev_mouse_x + (target_x - prev_mouse_x) * adaptive_alpha
                        smoothed_y = prev_mouse_y + (target_y - prev_mouse_y) * adaptive_alpha
                        
                        pyautogui.moveTo(smoothed_x, smoothed_y, _pause=False)
                        prev_mouse_x, prev_mouse_y = smoothed_x, smoothed_y
                    
                    # LEFT CLICK: Index + Thumb pinch
                    if is_pinching and not is_mouse_down:
                        pyautogui.mouseDown()
                        is_mouse_down = True
                        last_click_time = time.time()
                        logging.info("✓ Left Mouse Down")
                    elif not is_pinching and is_mouse_down:
                        if time.time() - last_click_time > 0.04:
                            pyautogui.mouseUp()
                            is_mouse_down = False
                            logging.info("✓ Left Mouse Up")
                        else:
                            pyautogui.mouseUp()
                            is_mouse_down = False
                        
                elif gesture == "scroll":
                    # Middle + Thumb pinch held = scroll
                    if prev_scroll_y is None:
                        prev_scroll_y = norm_y
                    else:
                        dy = norm_y - prev_scroll_y
                        if abs(dy) > 0.012:
                            clicks = int(-dy * 5000)
                            pyautogui.scroll(clicks)
                            prev_scroll_y = norm_y
                            logging.info(f"✓ Scroll: {clicks} clicks")


    except websockets.exceptions.ConnectionClosed:
        logging.info("Browser disconnected.")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
    finally:
        # Safety: release mouse if connection drops
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
            print("\n  Controls:")
            print("  • Move:        Index finger (point)")
            print("  • Left Click:  Pinch Thumb + Index")
            print("  • Scroll:      Pinch & hold Thumb + Middle")

            
            # Smart HTML Auto-Launch
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
            if os.path.exists(html_path):
                html_url = f"file:///{html_path.replace(os.sep, '/')}"
                logging.info(f"Opening local web interface: {html_url}")
                webbrowser.open(html_url)
            else:
                print("\n[INFO] index.html not found in current directory.")
                print("       Keep your browser tab open at your portfolio site.")
            
            print("\n[READY] Waiting for browser to connect...")
            print("(Minimize this window and use gestures in the browser)\n")
            
            await asyncio.Future()  # run forever
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:
            print("\n[ERROR] Port 8765 is already in use!")
            print("        Make sure another instance isn't already running.\n")
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
