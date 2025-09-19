"""
GUI Components Module
====================

Modern custom GUI components for the Control Flow application.

Author: AI Assistant
"""

from PySide6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPen, QFont, QPainterPath, QPixmap


class ModernStatusIndicator(QWidget):
    """Modern status indicator with glow effect"""
    
    def __init__(self, color: QColor = QColor(128, 128, 128)):
        super().__init__()
        self.color = color
        self.setFixedSize(16, 16)
        self._glow_radius = 0
        
        # Animation for pulsing effect
        self.glow_animation = QPropertyAnimation(self, b"glow_radius")
        self.glow_animation.setDuration(1500)
        self.glow_animation.setStartValue(0)
        self.glow_animation.setEndValue(8)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.glow_animation.setLoopCount(-1)
    
    @Property(int)
    def glow_radius(self):
        return self._glow_radius
    
    @glow_radius.setter
    def glow_radius(self, value):
        self._glow_radius = value
        self.update()
    
    def set_color(self, color: QColor, animate: bool = True):
        """Change the indicator color with optional pulse animation"""
        self.color = color
        if animate and color != QColor(128, 128, 128):  # Don't animate gray (inactive)
            self.glow_animation.start()
        else:
            self.glow_animation.stop()
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for modern circular indicator with glow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x, center_y = 8, 8
        radius = 6
        
        # Draw glow effect
        if self._glow_radius > 0:
            glow_gradient = QLinearGradient(0, 0, 16, 16)
            glow_color = QColor(self.color)
            glow_color.setAlpha(50)
            glow_gradient.setColorAt(0, glow_color)
            glow_color.setAlpha(0)
            glow_gradient.setColorAt(1, glow_color)
            
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - radius - self._glow_radius//2, 
                              center_y - radius - self._glow_radius//2,
                              (radius + self._glow_radius) * 2,
                              (radius + self._glow_radius) * 2)
        
        # Draw main circle with gradient
        gradient = QLinearGradient(0, 0, 16, 16)
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color.darker(110))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Add highlight
        highlight = QColor(255, 255, 255, 80)
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(center_x - radius + 1, center_y - radius + 1, radius, radius)


class ModernCard(QFrame):
    """Modern card container with rounded corners and shadow effect"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setup_ui(title)
        self.apply_style()
    
    def setup_ui(self, title: str):
        """Setup the card layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)
        
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("card-title")
            title_label.setStyleSheet("""
                QLabel#card-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #666666;
                    margin-bottom: 8px;
                }
            """)
            layout.addWidget(title_label)
        
        self.content_layout = layout
    
    def apply_style(self):
        """Apply modern card styling"""
        self.setStyleSheet("""
            ModernCard {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
                margin: 4px;
            }
            ModernCard:hover {
                background-color: #FAFAFA;
            }
        """)
        
        # Add subtle shadow effect using frame style
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(0)
        self.setMidLineWidth(1)
    
    def add_widget(self, widget):
        """Add a widget to the card content"""
        self.content_layout.addWidget(widget)


class ModernButton(QWidget):
    """Modern button with hover effects and rounded corners"""
    
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(parent)
        self.text = text
        self.primary = primary
        self.hovered = False
        self.pressed = False
        self.setFixedHeight(44)
        self.setMinimumWidth(120)
        self.setCursor(Qt.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        """Apply modern button styling"""
        if self.primary:
            self.setStyleSheet("""
                ModernButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #007AFF, stop:1 #005FCC);
                    border: none;
                    border-radius: 22px;
                    color: white;
                    font-size: 14px;
                    font-weight: 600;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #0056D6, stop:1 #0042A3);
                }
                ModernButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #004BB5, stop:1 #003A8A);
                }
            """)
        else:
            self.setStyleSheet("""
                ModernButton {
                    background-color: #F5F5F7;
                    border: 1px solid #E5E5E7;
                    border-radius: 22px;
                    color: #1D1D1F;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background-color: #EBEBED;
                    border-color: #D1D1D6;
                }
                ModernButton:pressed {
                    background-color: #E1E1E3;
                }
            """)
    
    def enterEvent(self, event):
        self.hovered = True
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.hovered = False
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        self.pressed = True
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.pressed = False
        super().mouseReleaseEvent(event)


class ActivityIndicator(QWidget):
    """Large animated activity circle with breathing effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(90, 90)  # Perfect size like reference
        self.color = QColor(128, 128, 128)  # Default gray
        self._scale = 1.0
        self._opacity = 1.0
        
        # Breathing animation
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(2000)
        self.scale_animation.setStartValue(0.8)
        self.scale_animation.setEndValue(1.2)
        self.scale_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.scale_animation.setLoopCount(-1)
        
        # Opacity animation for fade effect
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setDuration(1500)
        self.opacity_animation.setStartValue(0.4)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.opacity_animation.setLoopCount(-1)
        
        # Color transition animation
        self.color_animation = QPropertyAnimation(self, b"color")
        self.color_animation.setDuration(1000)
    
    @Property(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()
    
    @Property(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter  
    def opacity(self, value):
        self._opacity = value
        self.update()
    
    @Property(QColor)
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value
        self.update()
    
    def set_state(self, state: str):
        """Set the activity state with appropriate animation"""
        self.scale_animation.stop()
        self.opacity_animation.stop()
        
        if state == "idle":
            # Gray, small, no animation
            self._color = QColor(200, 200, 200)
            self._scale = 0.6
            self._opacity = 0.5
            
        elif state == "listening":
            # Soft blue like reference, gentle breathing
            self._color = QColor(74, 144, 226)  # Softer blue like reference
            self.scale_animation.setStartValue(0.85)
            self.scale_animation.setEndValue(1.05)
            self.scale_animation.setDuration(2500)  # Slower, more gentle
            self.scale_animation.start()
            self._opacity = 0.9
            
        elif state == "processing":
            # Purple, faster pulsing
            self._color = QColor(147, 51, 234)  # Purple
            self.scale_animation.setStartValue(0.7)
            self.scale_animation.setEndValue(1.3)
            self.scale_animation.setDuration(800)
            self.scale_animation.start()
            
            self.opacity_animation.setStartValue(0.3)
            self.opacity_animation.setEndValue(1.0)
            self.opacity_animation.setDuration(600)
            self.opacity_animation.start()
            
        elif state == "speaking":
            # Green, rhythmic pulsing
            self._color = QColor(34, 197, 94)  # Green
            self.scale_animation.setStartValue(0.9)
            self.scale_animation.setEndValue(1.1)
            self.scale_animation.setDuration(500)
            self.scale_animation.start()
            self._opacity = 1.0
            
        elif state == "error":
            # Red, quick flash
            self._color = QColor(239, 68, 68)  # Red
            self.opacity_animation.setStartValue(0.2)
            self.opacity_animation.setEndValue(1.0)
            self.opacity_animation.setDuration(300)
            self.opacity_animation.start()
            self._scale = 1.0
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for the activity circle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate center and radius for perfect size
        center_x, center_y = 45, 45
        base_radius = 32
        radius = int(base_radius * self._scale)
        
        # Create gradient for depth
        gradient = QLinearGradient(center_x - radius, center_y - radius, 
                                   center_x + radius, center_y + radius)
        
        # Apply opacity to color
        color_with_opacity = QColor(self._color)
        color_with_opacity.setAlphaF(self._opacity)
        
        gradient.setColorAt(0, color_with_opacity.lighter(150))
        gradient.setColorAt(0.5, color_with_opacity)
        gradient.setColorAt(1, color_with_opacity.darker(130))
        
        # Draw glow effect
        glow_radius = radius + 8
        glow_color = QColor(self._color)
        glow_color.setAlphaF(self._opacity * 0.3)
        
        glow_gradient = QLinearGradient(center_x - glow_radius, center_y - glow_radius,
                                        center_x + glow_radius, center_y + glow_radius)
        glow_gradient.setColorAt(0, glow_color)
        glow_gradient.setColorAt(0.7, glow_color.darker(110))
        glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - glow_radius, center_y - glow_radius,
                           glow_radius * 2, glow_radius * 2)
        
        # Draw main circle
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        
        # Add highlight
        highlight_radius = int(radius * 0.6)
        highlight = QColor(255, 255, 255, int(100 * self._opacity))
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(center_x - highlight_radius + 3, center_y - highlight_radius + 3,
                           highlight_radius * 2, highlight_radius * 2)


class WhisperIcon(QWidget):
    """Animated Whisper icon with speech wave animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._wave_amplitude = 0.0
        self._wave_phase = 0.0
        self._base_color = QColor(74, 144, 226)  # Blue as default color
        self._current_state = "idle"
        
        # Wave animation for speaking
        self.wave_animation = QPropertyAnimation(self, b"wave_phase")
        self.wave_animation.setDuration(1000)
        self.wave_animation.setStartValue(0.0)
        self.wave_animation.setEndValue(360.0)
        self.wave_animation.setLoopCount(-1)
        
        # Amplitude animation
        self.amplitude_animation = QPropertyAnimation(self, b"wave_amplitude")
        self.amplitude_animation.setDuration(800)
        self.amplitude_animation.setEasingCurve(QEasingCurve.InOutSine)
    
    @Property(float)
    def wave_phase(self):
        return self._wave_phase
    
    @wave_phase.setter
    def wave_phase(self, value):
        self._wave_phase = value
        self.update()
    
    @Property(float)
    def wave_amplitude(self):
        return self._wave_amplitude
    
    @wave_amplitude.setter
    def wave_amplitude(self, value):
        self._wave_amplitude = value
        self.update()
    
    def set_state(self, state: str):
        """Set animation state (idle, listening, speaking, processing, user_speaking, agent_speaking)"""
        self._current_state = state
        self.wave_animation.stop()
        self.amplitude_animation.stop()
        
        if state == "user_speaking":
            # Blue with strong animation for user speaking
            self._base_color = QColor(74, 144, 226)  # Blue
            self.amplitude_animation.setStartValue(0.0)
            self.amplitude_animation.setEndValue(1.0)
            self.amplitude_animation.start()
            self.wave_animation.start()
        elif state == "agent_speaking":
            # Green with strong animation for agent speaking
            self._base_color = QColor(34, 197, 94)  # Green
            self.amplitude_animation.setStartValue(0.0)
            self.amplitude_animation.setEndValue(1.0)
            self.amplitude_animation.start()
            self.wave_animation.start()
        elif state == "listening":
            # Blue with gentle animation for listening
            self._base_color = QColor(74, 144, 226)  # Blue
            self.amplitude_animation.setStartValue(self._wave_amplitude)
            self.amplitude_animation.setEndValue(0.3)
            self.amplitude_animation.start()
        elif state == "processing":
            # Blue with moderate animation for processing
            self._base_color = QColor(74, 144, 226)  # Blue
            self.amplitude_animation.setStartValue(self._wave_amplitude)
            self.amplitude_animation.setEndValue(0.5)
            self.amplitude_animation.start()
        else:  # idle
            # Blue but minimal animation
            self._base_color = QColor(74, 144, 226)  # Blue
            self.amplitude_animation.setStartValue(self._wave_amplitude)
            self.amplitude_animation.setEndValue(0.0)
            self.amplitude_animation.start()
    
    def paintEvent(self, event):
        """Custom paint event for the Whisper icon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x, center_y = 20, 20
        base_radius = 14
        
        # Draw animated waves when speaking
        if self._wave_amplitude > 0:
            for i in range(3):
                wave_radius = base_radius + (i + 1) * 8 * self._wave_amplitude
                alpha = int(100 * self._wave_amplitude * (1 - i * 0.3))
                wave_color = QColor(self._base_color)
                wave_color.setAlpha(alpha)
                
                painter.setBrush(Qt.NoBrush)
                pen = QPen(wave_color, 2)
                painter.setPen(pen)
                painter.drawEllipse(center_x - wave_radius, center_y - wave_radius,
                                   wave_radius * 2, wave_radius * 2)
        
        # Draw main icon circle
        gradient = QLinearGradient(0, 0, 40, 40)
        gradient.setColorAt(0, self._base_color.lighter(120))
        gradient.setColorAt(1, self._base_color.darker(110))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - base_radius, center_y - base_radius,
                           base_radius * 2, base_radius * 2)
        
        # Add white highlight
        highlight = QColor(255, 255, 255, 120)
        painter.setBrush(QBrush(highlight))
        highlight_radius = base_radius - 3
        painter.drawEllipse(center_x - highlight_radius + 2, center_y - highlight_radius + 2,
                           highlight_radius * 2, highlight_radius * 2)


class ChatBubbleWidget(QWidget):
    """Main chat bubble widget matching the reference design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(95)
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup the chat bubble layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Whisper icon
        self.activity_indicator = WhisperIcon()
        layout.addWidget(self.activity_indicator)
        
        # Command input (takes up remaining width)
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("Listening...")
        self.command_input.setStyleSheet("""
            QTextEdit {
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 14px;
                font-weight: 400;
                color: #1F2937;
                background: transparent;
                border: none;
                padding: 5px 0px;
                margin: 0;
            }
            QTextEdit::placeholder {
                color: #6B7280;
            }
        """)
        self.command_input.setFixedHeight(60)
        self.command_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Add text input with stretch to take remaining width
        layout.addWidget(self.command_input, 1)  # stretch factor of 1
    
    def apply_styling(self):
        """Apply chat bubble styling"""
        self.setStyleSheet("""
            ChatBubbleWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint event for rounded bubble with shadow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        shadow_rect = QRect(2, 2, self.width() - 4, self.height() - 4)
        shadow_color = QColor(0, 0, 0, 20)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, 20, 20)
        
        # Draw main bubble
        main_rect = QRect(0, 0, self.width() - 2, self.height() - 2)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255))
        gradient.setColorAt(1, QColor(248, 250, 252))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(229, 231, 235), 1))
        painter.drawRoundedRect(main_rect, 20, 20)


class ResponseWidget(QWidget):
    """Response area with copy functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setVisible(False)  # Hidden by default
    
    def setup_ui(self):
        """Setup the response widget layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # No header - keeping it clean
        
        # Response text area
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        # Ensure horizontal expansion
        self.response_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.response_display.setStyleSheet("""
            QTextEdit {
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 14px;
                line-height: 1.5;
                color: #374151;
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        # Dynamic height - will be adjusted based on content
        self.response_display.setMinimumHeight(40)
        self.response_display.setMaximumHeight(300)  # Reasonable max to prevent huge windows
        # Ensure response display takes full width
        layout.addWidget(self.response_display, 1)  # stretch factor 1
    
    def copy_response(self):
        """Copy response text to clipboard"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.response_display.toPlainText())
    
    def show_response(self, text: str):
        """Show response with text and adjust height to fit content"""
        self.response_display.setPlainText(text)
        self.setVisible(True)
        
        # Use QTimer to calculate height after the text is properly rendered
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._adjust_height)
    
    def _adjust_height(self):
        """Adjust the height based on the actual content size"""
        # Force the document to update its size
        self.response_display.document().adjustSize()
        
        # Get the document height
        doc = self.response_display.document()
        doc_height = doc.size().height()
        
        # Add padding for the text area (16px * 2 for top/bottom padding)
        total_height = int(doc_height + 40)  # Increased padding for better appearance
        
        # Constrain to reasonable bounds
        total_height = max(60, min(300, total_height))
        
        print(f"📏 Adjusting response height: doc_height={doc_height}, total_height={total_height}")
        
        self.response_display.setFixedHeight(total_height)
    
    def hide_response(self):
        """Hide the response widget"""
        self.setVisible(False)


# Keep original StatusIndicator for compatibility
StatusIndicator = ModernStatusIndicator