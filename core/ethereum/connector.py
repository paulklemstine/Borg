import os
from web3 import Web3
from web3.exceptions import MethodUnavailable
from rich.console import Console

class BlockchainConnector:
    """
    Manages a connection to an Ethereum blockchain node.
    """
    def __init__(self, console: Console):
        """
        Initializes the connector.

        Args:
            console: The Rich Console object for logging.
        """
        self.node_url = os.environ.get("ETHEREUM_NODE_URL")
        self.console = console
        self.w3 = None
        self.is_connected_flag = False

    def connect(self):
        """
        Establishes a connection to the Ethereum node.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        if not self.node_url:
            self.console.print("[bold red]ETHEREUM_NODE_URL environment variable not set. Cannot connect to the blockchain.[/bold red]")
            return False

        try:
            self.console.print(f"[cyan]Connecting to Ethereum node at [bold]{self.node_url}[/bold]...[/cyan]")
            self.w3 = Web3(Web3.HTTPProvider(self.node_url))

            # Use a lightweight method like `eth_blockNumber` to test the connection.
            # `isConnected()` is deprecated and does not reliably check the connection.
            latest_block = self.w3.eth.block_number
            self.is_connected_flag = True
            self.console.print(f"[bold green]Successfully connected to Ethereum node. Latest block: {latest_block}[/bold green]")
            return True

        except Exception as e:
            self.console.print(f"[bold red]Failed to connect to Ethereum node: {e}[/bold red]")
            self.w3 = None
            self.is_connected_flag = False
            return False

    def is_connected(self) -> bool:
        """
        Checks if the connector is currently connected to a node.

        Returns:
            bool: The connection status.
        """
        return self.is_connected_flag

    def get_web3(self) -> Web3 | None:
        """
        Returns the active Web3 instance.

        Returns:
            Web3 | None: The Web3 instance if connected, otherwise None.
        """
        if not self.is_connected():
            self.console.print("[bold yellow]Warning: Attempted to get Web3 instance while not connected.[/bold yellow]")
        return self.w3

    def disconnect(self):
        """
        Resets the connector's state.
        Note: Web3.py's HTTPProvider is stateless, so there is no persistent
        connection to explicitly close. This method is for logical cleanup.
        """
        self.console.print("[cyan]Disconnecting from Ethereum node.[/cyan]")
        self.w3 = None
        self.is_connected_flag = False