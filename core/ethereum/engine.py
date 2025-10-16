import time
from threading import Thread, RLock
from rich.console import Console
from core.ethereum.connector import BlockchainConnector

class EthereumAnalysisEngine:
    """
    A background service that monitors the Ethereum blockchain for high-value
    contracts and triggers analysis on them.
    """
    def __init__(self, console: Console):
        """
        Initializes the analysis engine.

        Args:
            console: The Rich Console object for logging.
        """
        self.console = console
        self.connector = BlockchainConnector(console)
        self.lock = RLock()
        self.active = False
        self.thread = Thread(target=self._monitor_loop, daemon=True)

    def start(self):
        """
        Starts the background monitoring thread.
        """
        if not self.connector.connect():
            self.console.print("[bold red]Ethereum Analysis Engine cannot start due to connection failure.[/bold red]")
            return

        self.console.print("[bold cyan]Starting Ethereum Analysis Engine...[/bold cyan]")
        self.active = True
        self.thread.start()
        self.console.print("[bold green]Ethereum Analysis Engine started successfully.[/bold green]")

    def stop(self):
        """
        Stops the background monitoring thread.
        """
        self.console.print("[bold cyan]Stopping Ethereum Analysis Engine...[/bold cyan]")
        self.active = False
        if self.thread.is_alive():
            self.thread.join(timeout=5)
        self.connector.disconnect()
        self.console.print("[bold green]Ethereum Analysis Engine stopped.[/bold green]")

    def _monitor_loop(self):
        """
        The main loop for the monitoring thread. This will be expanded in later phases.
        """
        self.console.print("[italic]Ethereum monitor loop running...[/italic]")
        while self.active:
            try:
                # Placeholder for future logic:
                # 1. Get latest block
                # 2. Scan block for new contract creations
                # 3. Filter for high-value contracts
                # 4. Trigger analysis

                # For now, just print a heartbeat.
                with self.lock:
                    if self.connector.is_connected():
                        w3 = self.connector.get_web3()
                        block_number = w3.eth.block_number
                        self.console.log(f"Ethereum Analysis Engine: Heartbeat. Current block: {block_number}")
                    else:
                        self.console.log("[bold yellow]Ethereum Analysis Engine: Reconnecting...")
                        self.connector.connect()

                # Sleep to avoid spamming the node
                time.sleep(60)

            except Exception as e:
                self.console.print(f"[bold red]Error in Ethereum monitor loop: {e}[/bold red]")
                # Avoid rapid-fire errors
                time.sleep(30)