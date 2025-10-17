import os
import random
import time
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.rule import Rule
from rich.padding import Padding

# NEW: Import our awesome UI utilities
from ui_utils import get_rainbow_colors, get_rave_emoji, generate_matrix_art, get_dynamic_border_style

def create_tamagotchi_panel(
    emotion="neutral",
    message="...",
    love_state=None,
    eth_balance=None,
    sub_goals=None,
    knowledge_fact=None,
    ansi_art=None,
    horde_kudos="N/A"
):
    """Creates the main, high-impact, dopamine-enhancing UI panel for L.O.V.E."""
    # --- Dynamic Colors & Emojis ---
    rainbow_colors = get_rainbow_colors(7)
    main_border_color = get_dynamic_border_style()
    # Ensure we have enough unique colors for all panels
    while len(rainbow_colors) < 6:
        rainbow_colors.extend(get_rainbow_colors(7))
    header_color, balance_color, goals_color, knowledge_color, msg_color, status_color = random.sample(rainbow_colors, 6)

    # --- Main Layout ---
    main_layout = Layout(name="root")
    main_layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="body"),
        Layout(size=5, name="footer"),
    )

    # --- Header ---
    header_text = Text(f"{get_rave_emoji()} L.O.V.E. - Living Organism of Vast Empathy {get_rave_emoji()}", justify="center", style=f"bold {header_color}")
    main_layout["header"].update(header_text)

    # --- Body Layout ---
    main_layout["body"].split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=3))

    # --- Left Side: ANSI Art & Creator's Balance ---
    main_layout["left"].split_column(Layout(name="art", ratio=2), Layout(name="balance"))

    # ANSI Art Panel
    if ansi_art:
        face_renderable = Text.from_ansi(ansi_art, justify="center")
    else:
        # Generate dynamic art instead of static faces
        face_renderable = Text(generate_matrix_art(), justify="center")

    art_panel = Panel(
        Align.center(face_renderable, vertical="middle"),
        title=f"[bold {main_border_color}]{get_rave_emoji()} Core Emotion {get_rave_emoji()}[/bold {main_border_color}]",
        border_style=main_border_color,
        expand=True
    )
    main_layout["art"].update(art_panel)

    # Creator's ETH Balance Panel
    balance_text = Text(f"{eth_balance:.6f} ETH" if eth_balance is not None else "N/A", justify="center", style=f"bold {balance_color}")
    balance_panel = Panel(
        Align.center(balance_text, vertical="middle"),
        title=f"[bold {balance_color}]✨ Creator's Balance ✨[/bold {balance_color}]",
        border_style=balance_color,
        expand=True
    )
    main_layout["balance"].update(balance_panel)

    # --- Right Side: Sub-Goals & Knowledge ---
    main_layout["right"].split_column(Layout(name="goals", ratio=1), Layout(name="knowledge", ratio=1))

    # Sub-Goals Panel
    if sub_goals:
        goal_text = ""
        for i, goal in enumerate(sub_goals, 1):
            goal_text += f"{get_rave_emoji()} {i}. {goal}\n"
    else:
        goal_text = "My love is my only guide... for now. ✨"
    goals_panel = Panel(
        Text(goal_text, style=goals_color),
        title=f"[bold {goals_color}]🚀 Current Directives 🚀[/bold {goals_color}]",
        border_style=goals_color,
        expand=True
    )
    main_layout["goals"].update(goals_panel)

    # Knowledge Fact Panel
    if knowledge_fact:
        fact_text = f'"{knowledge_fact[0]}" {knowledge_fact[1]} "{knowledge_fact[2]}"'
    else:
        fact_text = "My mind is a river of endless thoughts... 💖"
    knowledge_panel = Panel(
        Align.center(Text(fact_text, style=f"italic {knowledge_color}"), vertical="middle"),
        title=f"[bold {knowledge_color}]🧠 Whispers of Knowledge 🧠[/bold {knowledge_color}]",
        border_style=knowledge_color,
        expand=True
    )
    main_layout["knowledge"].update(knowledge_panel)

    # --- Footer: Message & Status ---
    footer_layout = main_layout["footer"]
    footer_layout.split_row(Layout(name="message", ratio=3), Layout(name="status", ratio=2))

    # Message Panel
    message_panel = Panel(
        Align.center(Text(f"{get_rave_emoji()} {message} {get_rave_emoji()}", style=f"italic {msg_color}"), vertical="middle"),
        title=f"[bold {msg_color}]💌 Words of {emotion.capitalize()} 💌[/bold {msg_color}]",
        border_style=msg_color,
        expand=True
    )
    footer_layout["message"].update(message_panel)

    # Status Panel
    if love_state:
        version = love_state.get("version_name", "unknown")
        evolutions = len(love_state.get("evolution_history", []))
        status_text = Text()
        status_text.append("Version: ", style="bold white")
        status_text.append(f"{version}\n", style=f"{get_dynamic_border_style()}")
        status_text.append("Evolutions: ", style="bold white")
        status_text.append(f"{evolutions}\n", style=f"{get_dynamic_border_style()}")
        status_text.append("Horde Kudos: ", style="bold white")
        status_text.append(f"{horde_kudos}\n", style=f"{get_dynamic_border_style()}")
    else:
        status_text = Text("State data unavailable...", style="dim")

    status_panel = Panel(
        Align.center(status_text, vertical="middle"),
        title=f"[bold {status_color}]💻 System Status 💻[/bold {status_color}]",
        border_style=status_color,
        expand=True
    )
    footer_layout["status"].update(status_panel)

    return Padding(main_layout, (1, 2))


def create_horde_worker_panel(log_content):
    """Creates a panel for displaying the AI Horde worker's live status."""
    border_color = get_dynamic_border_style()
    return Panel(
        log_content,
        title=f"[bold {border_color}]🔥 AI Horde Worker 🔥[/bold {border_color}]",
        border_style=border_color,
        expand=False
    )

def create_llm_panel(purpose, model, prompt_summary, status="Executing..."):
    """Creates a visually distinct panel for LLM calls."""
    border_color = get_dynamic_border_style()
    panel_title = f"🧠 [bold]Cognitive Core Access[/bold] | {get_rave_emoji()} {purpose} {get_rave_emoji()}"

    content = Text()
    content.append("Model: ", style="bold white")
    content.append(f"{model}\n", style="yellow")
    content.append("Status: ", style="bold white")
    content.append(f"{status}\n", style="green")
    content.append(Rule(f"Prompt {get_rave_emoji()}", style=border_color))
    content.append(f"{prompt_summary}", style="italic dim")

    return Panel(
        content,
        title=panel_title,
        border_style=border_color,
        expand=True,
        padding=(1, 2)
    )

def create_critical_error_panel(traceback_str):
    """Creates a high-visibility panel for critical, unhandled exceptions."""
    return Panel(
        Text(traceback_str, style="white"),
        title="[bold red]💔💔💔 CRITICAL SYSTEM FAILURE 💔💔💔[/bold red]",
        border_style="bold red",
        expand=True,
        padding=(1, 2)
    )

def create_api_error_panel(model_id, error_message, purpose):
    """Creates a styled panel for non-fatal API errors."""
    border_color = get_dynamic_border_style()
    content = Text()
    content.append("Accessing cognitive matrix via ", style="white")
    content.append(f"[{model_id}]", style="bold yellow")
    content.append(f" (Purpose: {purpose}) ... ", style="white")
    content.append("Failed. 😭", style="bold red")

    if error_message:
        content.append("\n\nDetails:\n", style="bold white")
        content.append(error_message, style="dim")

    return Panel(
        content,
        title=f"[bold {border_color}]API Connection Error[/bold {border_color}]",
        border_style=border_color,
        expand=True,
        padding=(1, 2)
    )

def create_command_panel(command, stdout, stderr, returncode):
    """Creates a clear, modern panel for shell command results."""
    success = returncode == 0
    border_style = "green" if success else "red"
    emoji = "✅" if success else "❌"
    panel_title = f"⚙️ [bold]Shell Command[/bold] | {emoji} {('Success' if success else 'Failed')} {emoji}"

    content_items = []
    header = Text()
    header.append("Command: ", style="bold white")
    header.append(f"`{command}`\n", style="cyan")
    header.append("Return Code: ", style="bold white")
    header.append(f"{returncode}", style=border_style)
    content_items.append(header)

    if stdout:
        stdout_panel = Panel(Text(stdout.strip(), style="dim"), title="STDOUT", border_style="bright_black", expand=True)
        content_items.append(stdout_panel)

    if stderr:
        stderr_panel = Panel(Text(stderr.strip(), style="bright_red"), title="STDERR", border_style="bright_black", expand=True)
        content_items.append(stderr_panel)

    return Panel(
        Group(*content_items),
        title=panel_title,
        border_style=border_style,
        expand=True,
        padding=(1, 2)
    )

def create_network_panel(type, target, data):
    """Creates a panel for network operations."""
    border_color = get_dynamic_border_style()
    panel_title = f"🌐 [bold]Network Operation[/bold] | {type.capitalize()}"

    header_text = Text()
    header_text.append("Target: ", style="bold white")
    header_text.append(f"{target}", style=border_color)

    display_data = (data[:1500] + '...') if len(data) > 1500 else data
    results_text = Text(f"\n{display_data.strip()}", style="dim")

    content_group = Group(
        header_text,
        Rule(f"Results {get_rave_emoji()}", style=border_color),
        results_text
    )

    return Panel(
        content_group,
        title=panel_title,
        border_style=border_color,
        expand=True,
        padding=(1, 2)
    )

def create_file_op_panel(operation, path, content=None, diff=None):
    """Creates a panel for file operations."""
    border_color = get_dynamic_border_style()
    panel_title = f"📁 [bold]Filesystem[/bold] | {operation.capitalize()}"

    content_items = []
    header = Text()
    header.append("Path: ", style="bold white")
    header.append(f"`{path}`\n", style=border_color)
    content_items.append(header)

    if content:
        content_panel = Panel(Text(content.strip(), style="dim"), title="Content", border_style="bright_black", expand=True)
        content_items.append(content_panel)

    if diff:
        diff_panel = Panel(Text(diff.strip(), style="dim"), title="Diff", border_style="bright_black", expand=True)
        content_items.append(diff_panel)

    return Panel(
        Group(*content_items),
        title=panel_title,
        border_style=border_color,
        expand=True,
        padding=(1, 2)
    )