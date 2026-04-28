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
prev_scroll_y = None
last_click_time = 0

# ── One Euro Filter: gold-standard adaptive smoothing ──
# Low speed = heavy filtering (kills jitter), high speed = instant response
class OneEuroFilter:
    def __init__(self, freq=120.0, min_cutoff=1.0, beta=0.005, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.last_time = None

    def _alpha(self, cutoff):
        te = 1.0 / self.freq
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def filter(self, x, t=None):
        if t is not None and self.last_time is not None and t != self.last_time:
            self.freq = 1.0 / (t - self.last_time)
        self.last_time = t
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            return x
        dx = (x - self.x_prev) * self.freq
        a_d = self._alpha(self.d_cutoff)
        self.dx_prev = a_d * dx + (1 - a_d) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * abs(self.dx_prev)
        a_x = self._alpha(cutoff)
        self.x_prev = a_x * x + (1 - a_x) * self.x_prev
        return self.x_prev

# Cursor filters — tuned for butter-smooth OS control
cursor_filter_x = OneEuroFilter(freq=120, min_cutoff=0.8, beta=0.004, d_cutoff=1.0)
cursor_filter_y = OneEuroFilter(freq=120, min_cutoff=0.8, beta=0.004, d_cutoff=1.0)

async def handle_connection(websocket):
    global is_mouse_down
    global prev_scroll_y, last_click_time
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
                    
                    # One Euro Filter — adaptive smoothing (replaces manual EMA + deadzone)
                    now = time.monotonic()
                    smoothed_x = cursor_filter_x.filter(target_x, now)
                    smoothed_y = cursor_filter_y.filter(target_y, now)
                    
                    pyautogui.moveTo(smoothed_x, smoothed_y, _pause=False)
                    
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
