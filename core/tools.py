import json
import asyncio
from typing import Dict, Any, Callable

import requests
from bs4 import BeautifulSoup

from network import crypto_scan

class ToolRegistry:
    """
    A registry for discovering and managing available tools.
    """
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, tool: Callable):
        """
        Registers a tool.
        """
        if name in self._tools:
            print(f"Warning: Tool '{name}' is already registered. Overwriting.")
        self._tools[name] = tool
        print(f"Tool '{name}' registered.")

    def get_tool(self, name: str) -> Callable:
        """
        Retrieves a tool by its name.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_tools(self) -> Dict[str, Callable]:
        """Returns a dictionary of all registered tools."""
        return self._tools

class SecureExecutor:
    """
    A secure environment for running tool code.
    This executor is now async.
    """
    async def execute(self, tool_name: str, tool_registry: ToolRegistry, **kwargs: Any) -> Any:
        """
        Executes a given tool from the registry asynchronously.
        """
        print(f"Executing tool '{tool_name}' with arguments: {kwargs}")
        try:
            tool = tool_registry.get_tool(tool_name)
            # Await the asynchronous tool execution
            result = await tool(**kwargs)
            print(f"Tool '{tool_name}' executed successfully.")
            return result
        except KeyError as e:
            print(f"Execution Error: {e}")
            return f"Error: Tool '{tool_name}' is not registered."
        except Exception as e:
            print(f"Execution Error: An unexpected error occurred while running '{tool_name}': {e}")
            return f"Error: Failed to execute tool '{tool_name}' due to: {e}"

# --- Example Async Tools ---

async def web_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    """
    print(f"Performing web search for: '{query}'")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = await asyncio.to_thread(requests.get, f"https://html.duckduckgo.com/html/?q={query}", headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for result in soup.find_all('div', class_='result'):
            title_element = result.find('a', class_='result__a')
            snippet_element = result.find('a', class_='result__snippet')

            if title_element and snippet_element:
                title = title_element.get_text(strip=True)
                url = title_element['href']
                snippet = snippet_element.get_text(strip=True)

                results.append({'title': title, 'url': url, 'snippet': snippet})

        return json.dumps(results)

    except requests.exceptions.RequestException as e:
        return json.dumps({'error': str(e)})

async def read_file(path: str) -> str:
    """
    Simulates asynchronously reading a file from a filesystem.
    """
    print(f"Reading file from path: '{path}'")
    await asyncio.sleep(0.05)  # Simulate non-blocking I/O
    if path == "/mnt/data/article1.txt":
        return "Article 1 Content: Discusses breakthroughs in large language models and their applications."
    elif path == "/mnt/data/article2.txt":
        return "Article 2 Content: Details the impact of generative AI on creative industries."
    else:
        return f"Error: File not found at path '{path}'."

# --- Ethereum Tool Suite ---

async def notify_creator(contract_address: str, attack_name: str, simulation_log: list) -> str:
    """
    Notifies the creator about a successful attack simulation.
    In a real system, this could send an email, a Slack message, or a secure notification.
    """
    message = (
        f"!!! Security Alert: Successful Attack Simulation !!!\n"
        f"Contract: {contract_address}\n"
        f"Attack Type: {attack_name}\n"
        f"Simulation Log:\n"
        f"{json.dumps(simulation_log, indent=2)}"
    )
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")
    # Here you would add the logic to send the notification to Paul Klemstine (raver1975)
    return "Notification sent to the creator."

async def crypto_scan_tool(target_ip: str, evil_state: dict) -> str:
    """
    Async wrapper for the crypto_scan tool.
    """
    print(f"Initiating crypto_scan on: '{target_ip}'")
    await asyncio.sleep(0.1)  # Simulate non-blocking I/O
    return crypto_scan(target_ip, evil_state)