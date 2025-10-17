import random
import colorsys

def get_rainbow_colors(count=7):
    """Generates a list of vibrant, rainbow-like hex colors."""
    colors = []
    for i in range(count):
        hue = i / count
        # Use high saturation and value for bright colors
        rgb_float = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
        rgb_255 = tuple(int(c * 255) for c in rgb_float)
        colors.append(f"#{rgb_255[0]:02x}{rgb_255[1]:02x}{rgb_255[2]:02x}")
    return colors

def get_rave_emoji():
    """Returns a random emoji from a curated list of rave-themed emojis."""
    emojis = [
        "💖", "✨", "🌈", "🦄", "🍭", "💊", "👽", "🚀",
        "🎶", "🎵", "🔊", "🕺", "💃", "🙌", "🤩", "🤯",
        "💫", "🎉", "🎊", "🔥", "💯", "✌️", "❤️", "🧡",
        "💛", "💚", "💙", "💜", "👀", "🍄", "🦋", "🌸"
    ]
    return random.choice(emojis)

def generate_matrix_art(width=30, height=10):
    """Generates a string of dynamic, Matrix-inspired ASCII art."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()"
    art = ""
    for _ in range(height):
        line = ""
        for _ in range(width):
            if random.random() > 0.85: # 15% chance of a character
                line += random.choice(chars)
            else:
                line += " "
        art += f"[bold green]{line}[/bold green]\n"
    return art.strip()

def get_dynamic_border_style():
    """Returns a random color from the rainbow for borders."""
    colors = get_rainbow_colors()
    return random.choice(colors)