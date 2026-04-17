import math
import time

class MouseController:
    def __init__(self, smoothing=5):
        import pyautogui
        self.pyautogui = pyautogui
        self.pyautogui.FAILSAFE = False # Prevent system crash on screen edges
        self.pyautogui.PAUSE = 0
        
        self.screen_width, self.screen_height = self.pyautogui.size()
        
        self.smoothing = smoothing
        self.prev_mx, self.prev_my = 0, 0
        
        # Advanced Gesture State Machine
        self.pinch_count = 0
        self.pinch_start_time = 0
        self.pinch_release_time = 0
        self.is_dragging = False
        self.was_pinched = False
        
        # Scrolling
        self.prev_scroll_y = 0

    def move_to(self, target_x, target_y):
        # Linear Interpolation
        curr_mx = self.prev_mx + (target_x - self.prev_mx) / self.smoothing
        curr_my = self.prev_my + (target_y - self.prev_my) / self.smoothing
        
        try:
            self.pyautogui.moveTo(curr_mx, curr_my)
            self.prev_mx, self.prev_my = curr_mx, curr_my
        except Exception:
            pass

    def evaluate_pinch(self, is_pinched):
        curr_time = time.time()
        
        # 1. Edge triggered: Just Pinched
        if is_pinched and not self.was_pinched:
            self.pinch_start_time = curr_time
            self.pinch_count += 1
            self.was_pinched = True
            
        # 2. Edge triggered: Just Released Pinch
        elif not is_pinched and self.was_pinched:
            self.pinch_release_time = curr_time
            self.was_pinched = False
            
            if self.is_dragging:
                self.pyautogui.mouseUp(button='left')
                self.is_dragging = False
                self.pinch_count = 0 # Consume the pinch
                
        # 3. State Maintained: Holding Pinch (Drag & Drop detection)
        if is_pinched:
            if not self.is_dragging and (curr_time - self.pinch_start_time > 0.4):
                self.pyautogui.mouseDown(button='left')
                self.is_dragging = True
                self.pinch_count = 0 # Consume it so it doesn't trigger normal click on release

        # 4. State Evaluator: Window closed (Decision time)
        if not is_pinched and self.pinch_count > 0:
            if curr_time - self.pinch_release_time > 0.28:
                if self.pinch_count == 1:
                    self.pyautogui.click(button='left')
                elif self.pinch_count >= 2:
                    self.pyautogui.click(button='right')
                self.pinch_count = 0

    def perform_scroll(self, hand_y):
        if self.prev_scroll_y != 0:
            diff = self.prev_scroll_y - hand_y
            # Mult by factor to feel natural
            if abs(diff) > 2:
                self.pyautogui.scroll(int(diff * 5))
        self.prev_scroll_y = hand_y

    def reset_scroll(self):
        self.prev_scroll_y = 0

    def perform_volume_control(self, hand_y):
        if self.prev_scroll_y != 0:
            diff = self.prev_scroll_y - hand_y
            # Mult by factor to feel natural. diff > 0 means hand moved UP
            if diff > 10:
                self.pyautogui.press('volumeup')
                self.prev_scroll_y = hand_y
            elif diff < -10:
                self.pyautogui.press('volumedown')
                self.prev_scroll_y = hand_y
        else:
            self.prev_scroll_y = hand_y
