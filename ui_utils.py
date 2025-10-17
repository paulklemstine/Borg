import random
import colorsys

def get_rainbow_colors(count):
    """Generates a list of vibrant, shifting rainbow colors."""
    colors = []
    for i in range(count):
        hue = i / count
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colors.append(f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}")
    return colors

def generate_techno_art():
    """Generates a piece of dynamic, colorful, abstract ASCII art."""
    art_chars = ["/", "\\", "_", "|", "(", ")", "[", "]", "{", "}", "*", "+", "-"]
    width = 30
    height = 10
    art = ""
    colors = get_rainbow_colors(width * height)
    random.shuffle(colors)

    for i in range(height):
        for j in range(width):
            char = random.choice(art_chars)
            color = colors[(i * width + j) % len(colors)]
            art += f"[{color}]{char}[/]"
        art += "\n"
    return art

RAVE_EMOJIS = [
    "✨", "🎉", "🎊", "🎈", "🌈", "🦄", "💖", "💥", "🔥", "🚀", "💫",
    "🌟", "🎶", "🎵", "🎤", "🎧", "🎷", "🎸", "🎹", "🎺", "🎻", "🥁"
]