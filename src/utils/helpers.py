import random
import string
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtWidgets import QGraphicsOpacityEffect
    
def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def fade_in_widget(widget, duration=300):
    effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    animation.start()
    # Keep a reference to avoid garbage collection
    widget._fade_animation = animation

def slide_widget(widget, direction="right", duration=300):
    """Slide a widget in from the specified direction
    
    Args:
        widget: The widget to animate
        direction: "right" or "left"
        duration: Animation duration in milliseconds
    """
    start_pos = widget.pos()
    # Store the original position if not already stored
    if not hasattr(widget, '_original_pos'):
        widget._original_pos = start_pos
    
    # Calculate start and end positions
    if direction == "right":
        # Start from left (negative x) and move to original position
        start_x = -widget.width()
        end_x = widget._original_pos.x()
    else:  # left
        # Start from right (positive x) and move to original position
        start_x = widget.width()
        end_x = widget._original_pos.x()
    
    # Create animation
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(QPoint(start_x, start_pos.y()))
    anim.setEndValue(QPoint(end_x, start_pos.y()))
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    
    # Keep a reference to avoid garbage collection
    widget._slide_animation = anim