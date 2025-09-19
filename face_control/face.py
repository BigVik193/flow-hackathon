#!/usr/bin/env python3
"""
Unified Face Control System for macOS
Combines desktop gesture control and mouse control in one application
Toggle between modes seamlessly
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
import subprocess

class UnifiedFaceController:
    def __init__(self):
        # Initialize MediaPipe face mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Control modes
        self.GESTURE_MODE = "gesture"
        self.MOUSE_MODE = "mouse"
        self.current_mode = self.GESTURE_MODE
        self.last_mode_toggle = 0
        self.mode_toggle_cooldown = 0.5
        
        # Screen dimensions for mouse mode
        self.screen_width, self.screen_height = pyautogui.size()
        
        # === GESTURE MODE VARIABLES ===
        self.gesture_cooldown_time = 1.5
        self.last_gesture_time = 0
        self.last_mouth_time = 0
        self.last_wide_eyes_time = 0
        
        # Head tracking for gestures
        self.gesture_center_x = None
        self.head_range = 0.15
        self.head_reset_range = 0.08
        self.gesture_active = False
        self.last_gesture_direction = None
        
        # Mouth calibration for gestures
        self.baseline_mar = None
        self.mouth_open_multiplier = 1.4
        self.mouth_calibration_frames = 0
        self.mouth_calibration_needed = 30
        
        # Wide eyes calibration for gestures
        self.baseline_ear = None
        self.wide_eyes_multiplier = 1.25
        self.wide_eyes_calibration_frames = 0
        self.wide_eyes_calibration_needed = 30
        
        # === MOUSE MODE VARIABLES ===
        self.mouse_center_x = None
        self.mouse_center_y = None
        self.mouse_calibration_frames = 0
        self.mouse_calibration_needed = 30
        self.mouse_is_calibrated = False
        
        # Mouse control settings
        self.face_box_width = 0.3
        self.face_box_height = 0.3
        self.smoothing_factor = 0.3
        self.mouse_sensitivity = 1.5
        
        # Mouse smoothing
        self.smoothed_x = None
        self.smoothed_y = None
        
        # Click gesture variables
        self.last_left_click = 0
        self.last_right_click = 0
        self.click_cooldown = 0.8
        
        # Face landmark indices
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.MOUTH_INDICES = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        
        # Enable pyautogui settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
    
    def calculate_eye_aspect_ratio(self, eye_landmarks):
        """Calculate Eye Aspect Ratio (EAR) for blink/wink detection"""
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def calculate_mouth_aspect_ratio(self, mouth_landmarks):
        """Calculate Mouth Aspect Ratio (MAR) for mouth opening detection"""
        A = np.linalg.norm(mouth_landmarks[3] - mouth_landmarks[9])
        B = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[10])
        C = np.linalg.norm(mouth_landmarks[4] - mouth_landmarks[8])
        D = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[6])
        mar = (A + B + C) / (3.0 * D)
        return mar
    
    # === GESTURE MODE FUNCTIONS ===
    def detect_head_gesture(self, face_landmarks):
        """Detect head movements for desktop switching"""
        if self.current_mode != self.GESTURE_MODE:
            return None
            
        nose_x = face_landmarks.landmark[1].x
        
        if self.gesture_center_x is None:
            self.gesture_center_x = nose_x
            return None
        
        movement = nose_x - self.gesture_center_x
        current_time = time.time()
        
        current_direction = None
        if abs(movement) > self.head_range:
            current_direction = "right" if movement > 0 else "left"
        
        if abs(movement) < self.head_reset_range:
            if self.gesture_active:
                print("🎯 Head returned to center - ready for next gesture")
            self.gesture_active = False
            self.last_gesture_direction = None
        
        if current_time - self.last_gesture_time < self.gesture_cooldown_time:
            return None
        
        if (current_direction is not None and 
            current_direction == self.last_gesture_direction and 
            self.gesture_active):
            return None
        
        if current_direction is not None:
            self.last_gesture_time = current_time
            self.gesture_active = True
            self.last_gesture_direction = current_direction
            
            if current_direction == "right":
                return "head_right"
            else:
                return "head_left"
        
        return None
    
    def detect_mouth_gesture(self, face_landmarks):
        """Detect mouth opening for Mission Control"""
        if self.current_mode != self.GESTURE_MODE:
            return None
            
        current_time = time.time()
        if current_time - self.last_mouth_time < self.gesture_cooldown_time:
            return None
        
        # Skip if head is turned (prevents false triggers)
        if self.gesture_center_x is not None:
            nose_x = face_landmarks.landmark[1].x
            head_movement = abs(nose_x - self.gesture_center_x)
            if head_movement > self.head_range * 0.7:
                return None
        
        mouth_points = []
        for idx in self.MOUTH_INDICES:
            landmark = face_landmarks.landmark[idx]
            mouth_points.append([landmark.x, landmark.y])
        mouth_points = np.array(mouth_points)
        
        mar = self.calculate_mouth_aspect_ratio(mouth_points)
        
        if self.baseline_mar is None:
            self.baseline_mar = mar
            self.mouth_calibration_frames += 1
            if self.mouth_calibration_frames >= self.mouth_calibration_needed:
                print("✅ Mouth calibration complete!")
            return None
        
        if self.mouth_calibration_frames < self.mouth_calibration_needed:
            self.baseline_mar = 0.9 * self.baseline_mar + 0.1 * mar
            self.mouth_calibration_frames += 1
            if self.mouth_calibration_frames >= self.mouth_calibration_needed:
                print("✅ Mouth calibration complete!")
            return None
        
        threshold = self.baseline_mar * self.mouth_open_multiplier
        mouth_ratio = mar / self.baseline_mar if self.baseline_mar > 0 else 0
        
        if mar > threshold and mouth_ratio > 1.4:
            self.last_mouth_time = current_time
            print(f"😮 MOUTH TRIGGERED! Opening Mission Control")
            return "mouth_open"
        
        return None
    
    def detect_wide_eyes_gesture(self, face_landmarks):
        """Detect wide eyes for app switching"""
        if self.current_mode != self.GESTURE_MODE:
            return None
            
        current_time = time.time()
        if current_time - self.last_wide_eyes_time < self.gesture_cooldown_time:
            return None
        
        left_eye_points = []
        right_eye_points = []
        
        for idx in self.LEFT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            left_eye_points.append([landmark.x, landmark.y])
            
        for idx in self.RIGHT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            right_eye_points.append([landmark.x, landmark.y])
        
        left_eye_points = np.array(left_eye_points)
        right_eye_points = np.array(right_eye_points)
        
        left_ear = self.calculate_eye_aspect_ratio(left_eye_points)
        right_ear = self.calculate_eye_aspect_ratio(right_eye_points)
        avg_ear = (left_ear + right_ear) / 2.0
        
        if self.baseline_ear is None:
            self.baseline_ear = avg_ear
            self.wide_eyes_calibration_frames += 1
            if self.wide_eyes_calibration_frames >= self.wide_eyes_calibration_needed:
                print("✅ Wide eyes calibration complete!")
            return None
        
        if self.wide_eyes_calibration_frames < self.wide_eyes_calibration_needed:
            self.baseline_ear = 0.9 * self.baseline_ear + 0.1 * avg_ear
            self.wide_eyes_calibration_frames += 1
            if self.wide_eyes_calibration_frames >= self.wide_eyes_calibration_needed:
                print("✅ Wide eyes calibration complete!")
            return None
        
        threshold = self.baseline_ear * self.wide_eyes_multiplier
        eyes_ratio = avg_ear / self.baseline_ear if self.baseline_ear > 0 else 0
        
        if avg_ear > threshold and eyes_ratio > 1.25:
            self.last_wide_eyes_time = current_time
            print(f"👀 WIDE EYES! Switching applications")
            return "wide_eyes"
        
        return None
    
    # === MOUSE MODE FUNCTIONS ===
    def detect_wink(self, face_landmarks):
        """Detect winks for mouse clicking and mode toggling"""
        current_time = time.time()
        
        # Check head pose to filter out false winks during head turns
        nose_x = face_landmarks.landmark[1].x  # Nose tip
        left_eye_center_x = face_landmarks.landmark[33].x  # Left eye center
        right_eye_center_x = face_landmarks.landmark[362].x  # Right eye center
        
        # Calculate head rotation based on eye positions relative to nose
        eye_center_x = (left_eye_center_x + right_eye_center_x) / 2
        head_rotation = abs(nose_x - eye_center_x)
        
        # If head is turned too much, don't detect winks (prevents false triggers)
        head_turn_threshold = 0.02  # Adjust this value as needed
        if head_rotation > head_turn_threshold:
            return None
        
        left_eye_points = []
        right_eye_points = []
        
        for idx in self.LEFT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            left_eye_points.append([landmark.x, landmark.y])
            
        for idx in self.RIGHT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            right_eye_points.append([landmark.x, landmark.y])
        
        left_eye_points = np.array(left_eye_points)
        right_eye_points = np.array(right_eye_points)
        
        left_ear = self.calculate_eye_aspect_ratio(left_eye_points)
        right_ear = self.calculate_eye_aspect_ratio(right_eye_points)
        
        # More lenient thresholds for better detection
        wink_threshold = 0.28
        ear_difference_threshold = 0.12
        
        # Left wink = toggle mode (works in both modes)
        if (left_ear < wink_threshold and right_ear > wink_threshold + ear_difference_threshold and
            current_time - self.last_right_click > self.click_cooldown):
            self.last_right_click = current_time
            print(f"🖁 LEFT WINK DETECTED! EAR values: left={left_ear:.3f}, right={right_ear:.3f}, head_rot={head_rotation:.3f}")
            return "mode_toggle"
        
        # Right wink = left click (only in mouse mode)
        if (self.current_mode == self.MOUSE_MODE and 
            right_ear < wink_threshold and left_ear > wink_threshold + ear_difference_threshold and
            current_time - self.last_left_click > self.click_cooldown):
            self.last_left_click = current_time
            print(f"🖁 RIGHT WINK DETECTED! EAR values: left={left_ear:.3f}, right={right_ear:.3f}, head_rot={head_rotation:.3f}")
            return "left_click"
        
        return None
    
    def calibrate_mouse_center(self, nose_x, nose_y):
        """Calibrate center position for mouse control"""
        if not self.mouse_is_calibrated:
            if self.mouse_center_x is None:
                self.mouse_center_x = nose_x
                self.mouse_center_y = nose_y
            else:
                self.mouse_center_x = 0.9 * self.mouse_center_x + 0.1 * nose_x
                self.mouse_center_y = 0.9 * self.mouse_center_y + 0.1 * nose_y
            
            self.mouse_calibration_frames += 1
            if self.mouse_calibration_frames >= self.mouse_calibration_needed:
                self.mouse_is_calibrated = True
                print("✅ Mouse calibration complete! Nose control active.")
    
    def nose_to_mouse_coords(self, nose_x, nose_y):
        """Convert nose position to screen coordinates"""
        if not self.mouse_is_calibrated or self.mouse_center_x is None:
            return None, None
        
        rel_x = (nose_x - self.mouse_center_x) / self.face_box_width
        rel_y = (nose_y - self.mouse_center_y) / self.face_box_height
        
        rel_x = max(-1.0, min(1.0, rel_x))
        rel_y = max(-1.0, min(1.0, rel_y))
        
        screen_x = self.screen_width // 2 + (rel_x * self.screen_width * self.mouse_sensitivity // 2)
        screen_y = self.screen_height // 2 + (rel_y * self.screen_height * self.mouse_sensitivity // 2)
        
        screen_x = max(0, min(self.screen_width - 1, screen_x))
        screen_y = max(0, min(self.screen_height - 1, screen_y))
        
        return int(screen_x), int(screen_y)
    
    def smooth_mouse_movement(self, target_x, target_y):
        """Apply smoothing to mouse movement"""
        if self.smoothed_x is None:
            self.smoothed_x = target_x
            self.smoothed_y = target_y
        else:
            self.smoothed_x = self.smoothed_x * (1 - self.smoothing_factor) + target_x * self.smoothing_factor
            self.smoothed_y = self.smoothed_y * (1 - self.smoothing_factor) + target_y * self.smoothing_factor
        
        return int(self.smoothed_x), int(self.smoothed_y)
    
    # === EXECUTION FUNCTIONS ===
    def execute_gesture_action(self, gesture):
        """Execute desktop control gestures"""
        try:
            if gesture == "head_left":
                print("🢀 EXECUTING: Head left - switching to previous desktop")
                pyautogui.keyDown('ctrl')
                pyautogui.press('left')
                pyautogui.keyUp('ctrl')
                
            elif gesture == "head_right":
                print("🢂 EXECUTING: Head right - switching to next desktop")
                pyautogui.keyDown('ctrl')
                pyautogui.press('right')
                pyautogui.keyUp('ctrl')
                
            elif gesture == "wide_eyes":
                print("👀 EXECUTING: Wide eyes - opening Mission Control")
                pyautogui.keyDown('ctrl')
                pyautogui.press('up')
                pyautogui.keyUp('ctrl')
                
            # elif gesture == "wide_eyes":
            #     print("👀 EXECUTING: Wide eyes - switching applications")
            #     try:
            #         subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke tab using command down'])
            #     except Exception as e:
            #         pyautogui.keyDown('cmd')
            #         pyautogui.press('tab')
            #         pyautogui.keyUp('cmd')
                
            # elif gesture == "mouth_open":  # Commented out - mouth now free for voice agent
            #     print("😮 EXECUTING: Mouth open - opening Mission Control")
            #     pyautogui.keyDown('ctrl')
            #     pyautogui.press('up')
            #     pyautogui.keyUp('ctrl')
                
        except Exception as e:
            print(f"⚠️  Gesture execution error: {e}")
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('cmd')
    
    def execute_click(self, click_type):
        """Execute mouse clicks"""
        try:
            if click_type == "left_click":
                pyautogui.click()
                print("🖱️  Left click")
            elif click_type == "right_click":
                pyautogui.rightClick()
                print("🖱️  Right click")
        except Exception as e:
            print(f"⚠️  Click error: {e}")
    
    def toggle_mode(self):
        """Toggle between gesture and mouse modes"""
        current_time = time.time()
        if current_time - self.last_mode_toggle > self.mode_toggle_cooldown:
            if self.current_mode == self.GESTURE_MODE:
                self.current_mode = self.MOUSE_MODE
                # Reset mouse calibration
                self.mouse_center_x = None
                self.mouse_center_y = None
                self.mouse_calibration_frames = 0
                self.mouse_is_calibrated = False
                self.smoothed_x = None
                self.smoothed_y = None
                print("🖱️  MOUSE MODE ACTIVATED")
                print("   Move nose to control cursor")
                print("   Right wink = left click, Left wink = right click")
            else:
                self.current_mode = self.GESTURE_MODE
                print("👋 GESTURE MODE ACTIVATED")
                print("   Head movements = desktop switching")
                print("   Wide eyes = app switching, Mouth = Mission Control")
            
            self.last_mode_toggle = current_time
    
    def reset_calibration(self):
        """Reset all calibrations"""
        if self.current_mode == self.GESTURE_MODE:
            self.gesture_center_x = None
            self.baseline_mar = None
            self.mouth_calibration_frames = 0
            self.baseline_ear = None
            self.wide_eyes_calibration_frames = 0
            self.gesture_active = False
            self.last_gesture_direction = None
            print("🎯 Gesture calibration reset")
        else:
            self.mouse_center_x = None
            self.mouse_center_y = None
            self.mouse_calibration_frames = 0
            self.mouse_is_calibrated = False
            self.smoothed_x = None
            self.smoothed_y = None
            print("🎯 Mouse calibration reset")
    
    def draw_overlays(self, frame, frame_width, frame_height, face_landmarks):
        """Draw mode-specific overlays"""
        # Draw EAR values for debugging wink detection
        left_eye_points = []
        right_eye_points = []
        
        for idx in self.LEFT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            left_eye_points.append([landmark.x, landmark.y])
            
        for idx in self.RIGHT_EYE_INDICES:
            landmark = face_landmarks.landmark[idx]
            right_eye_points.append([landmark.x, landmark.y])
        
        left_eye_points = np.array(left_eye_points)
        right_eye_points = np.array(right_eye_points)
        
        left_ear = self.calculate_eye_aspect_ratio(left_eye_points)
        right_ear = self.calculate_eye_aspect_ratio(right_eye_points)
        
        # Calculate head rotation for debugging
        nose_x = face_landmarks.landmark[1].x
        left_eye_center_x = face_landmarks.landmark[33].x
        right_eye_center_x = face_landmarks.landmark[362].x
        eye_center_x = (left_eye_center_x + right_eye_center_x) / 2
        head_rotation = abs(nose_x - eye_center_x)
        
        # Display debug values
        cv2.putText(frame, f"Left EAR: {left_ear:.3f}", (10, frame_height - 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Right EAR: {right_ear:.3f}", (10, frame_height - 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Head Rot: {head_rotation:.3f}", (10, frame_height - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if self.current_mode == self.GESTURE_MODE:
            # Draw center indicator for gesture mode
            if self.gesture_center_x is not None:
                center_pixel_x = int(self.gesture_center_x * frame_width)
                nose_y = int(face_landmarks.landmark[1].y * frame_height)
                cv2.circle(frame, (center_pixel_x, nose_y), 5, (0, 255, 0), -1)
                cv2.putText(frame, "CENTER", (center_pixel_x - 30, nose_y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        elif self.current_mode == self.MOUSE_MODE:
            # Draw mouse control area
            if self.mouse_center_x is not None and self.mouse_center_y is not None:
                center_pixel_x = int(self.mouse_center_x * frame_width)
                center_pixel_y = int(self.mouse_center_y * frame_height)
                
                box_width = int(self.face_box_width * frame_width)
                box_height = int(self.face_box_height * frame_height)
                
                # Control area rectangle
                top_left = (center_pixel_x - box_width//2, center_pixel_y - box_height//2)
                bottom_right = (center_pixel_x + box_width//2, center_pixel_y + box_height//2)
                cv2.rectangle(frame, top_left, bottom_right, (255, 255, 0), 2)
                
                # Center crosshair
                cv2.line(frame, (center_pixel_x - 10, center_pixel_y), 
                        (center_pixel_x + 10, center_pixel_y), (0, 255, 0), 2)
                cv2.line(frame, (center_pixel_x, center_pixel_y - 10), 
                        (center_pixel_x, center_pixel_y + 10), (0, 255, 0), 2)
    
    def run(self):
        """Main application loop"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("🚀 Unified Face Control System Started!")
        print("🎮 Starting in GESTURE MODE")
        print("")
        print("=== CONTROLS ===")
        print("- LEFT WINK: Toggle between Gesture Mode and Mouse Mode")
        print("- Press 'r' to reset calibration for current mode")
        print("- Press 'q' to quit")
        print("- Press ESC to switch back to gesture mode (from any mode)")
        print("- Move mouse to top-left corner for emergency quit")
        print("")
        print("=== GESTURE MODE ===")
        print("- Head LEFT/RIGHT: Switch desktops")
        print("- Wide eyes: Mission Control")
        print("- Left wink: Toggle to Mouse Mode")
        print("")
        print("=== MOUSE MODE ===")
        print("- Nose movement: Control cursor")
        print("- Right wink: Left click")
        print("- Left wink: Toggle back to Gesture Mode")
        print("-" * 70)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process face detection
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Draw face landmarks (minimal)
                    self.mp_draw.draw_landmarks(
                        frame,
                        face_landmarks,
                        self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )
                    
                    # Get nose position
                    nose_x = face_landmarks.landmark[1].x
                    nose_y = face_landmarks.landmark[1].y
                    
                    if self.current_mode == self.GESTURE_MODE:
                        # === GESTURE MODE PROCESSING ===
                        head_gesture = self.detect_head_gesture(face_landmarks)
                        # mouth_gesture = self.detect_mouth_gesture(face_landmarks)  # Commented out - mouth free for voice
                        wide_eyes_gesture = self.detect_wide_eyes_gesture(face_landmarks)
                        wink = self.detect_wink(face_landmarks)
                        
                        # Execute gestures
                        if head_gesture:
                            self.execute_gesture_action(head_gesture)
                        # elif mouth_gesture:  # Commented out - mouth free for voice
                        #     self.execute_gesture_action(mouth_gesture)
                        elif wide_eyes_gesture:
                            self.execute_gesture_action(wide_eyes_gesture)
                        elif wink == "mode_toggle":
                            self.toggle_mode()
                    
                    elif self.current_mode == self.MOUSE_MODE:
                        # === MOUSE MODE PROCESSING ===
                        if not self.mouse_is_calibrated:
                            self.calibrate_mouse_center(nose_x, nose_y)
                        else:
                            # Mouse movement
                            target_x, target_y = self.nose_to_mouse_coords(nose_x, nose_y)
                            if target_x is not None and target_y is not None:
                                smooth_x, smooth_y = self.smooth_mouse_movement(target_x, target_y)
                                try:
                                    pyautogui.moveTo(smooth_x, smooth_y)
                                except:
                                    pass
                        
                        # Detect wink actions
                        wink = self.detect_wink(face_landmarks)
                        if wink == "left_click":
                            self.execute_click(wink)
                        elif wink == "mode_toggle":
                            self.toggle_mode()
                        # elif wink == "right_click":  # Commented out - left wink now toggles mode
                        #     self.execute_click(wink)
                    
                    # Draw mode-specific overlays
                    self.draw_overlays(frame, frame_width, frame_height, face_landmarks)
            
            # === STATUS DISPLAY ===
            mode_text = f"🖱️  MOUSE MODE" if self.current_mode == self.MOUSE_MODE else f"👋 GESTURE MODE"
            mode_color = (0, 255, 255) if self.current_mode == self.MOUSE_MODE else (0, 255, 0)
            cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, mode_color, 2)
            
            if self.current_mode == self.GESTURE_MODE:
                # Gesture mode status
                head_cal = self.gesture_center_x is not None
                # mouth_cal = self.baseline_mar is not None and self.mouth_calibration_frames >= self.mouth_calibration_needed  # Commented out
                eyes_cal = self.baseline_ear is not None and self.wide_eyes_calibration_frames >= self.wide_eyes_calibration_needed
                
                if not head_cal:
                    cv2.putText(frame, "Look straight ahead to calibrate head tracking", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                elif not eyes_cal:
                    progress = f"{self.wide_eyes_calibration_frames}/{self.wide_eyes_calibration_needed}"
                    cv2.putText(frame, f"Keep eyes normal to calibrate: {progress}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, "✅ Ready! Head=desktop | Eyes=Mission Control | Left wink=mouse mode", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            elif self.current_mode == self.MOUSE_MODE:
                # Mouse mode status
                if not self.mouse_is_calibrated:
                    progress = f"{self.mouse_calibration_frames}/{self.mouse_calibration_needed}"
                    cv2.putText(frame, f"Keep head still to calibrate mouse center: {progress}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, "✅ Move nose=cursor | Right wink=click | Left wink=gesture mode", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.putText(frame, "Press 'r'=recalibrate | 'q'=quit | Left wink=toggle mode", 
                       (10, frame_height - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Unified Face Control System', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            # elif key == ord('m'):  # Commented out - left wink now toggles mode
            #     self.toggle_mode()
            elif key == ord('r'):
                self.reset_calibration()
            elif key == 27:  # ESC key - always return to gesture mode
                if self.current_mode == self.MOUSE_MODE:
                    self.current_mode = self.GESTURE_MODE
                    print("👋 Returned to GESTURE MODE")
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("Unified Face Control System closed.")

def main():
    try:
        controller = UnifiedFaceController()
        controller.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have installed the required packages:")
        print("pip install opencv-python mediapipe pyautogui")

if __name__ == "__main__":
    main()