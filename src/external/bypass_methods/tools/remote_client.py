import os
import sys
import time
import logging
import argparse
from typing import Dict, Any, Optional

# Import the named pipe client
from named_pipe_manager import NamedPipeClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remote_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RemoteClient")

class RemoteClient:
    """
    Remote client that communicates with the accessibility controller
    using Windows Named Pipes for legitimate, secure IPC.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe"):
        """
        Initialize the remote client.
        
        Args:
            pipe_name: Base name for the pipe (without the \\\\.\pipe\ prefix)
        """
        self.pipe_client = NamedPipeClient(pipe_name)
        logger.info(f"Remote client initialized for pipe: {pipe_name}")
    
    def connect(self) -> bool:
        """
        Connect to the accessibility controller.
        
        Returns:
            True if connection successful, False otherwise
        """
        return self.pipe_client.connect()
    
    def disconnect(self):
        """Disconnect from the accessibility controller."""
        self.pipe_client.disconnect()
    
    def cycle_window(self, direction: str = "next") -> Dict[str, Any]:
        """
        Cycle to the next or previous window.
        
        Args:
            direction: Direction to cycle ("next" or "previous")
            
        Returns:
            Response data from the server
        """
        logger.info(f"Requesting window cycle: direction={direction}")
        
        return self.pipe_client.send_message("cycle_window", {
            "direction": direction
        }) or {"status": "error", "message": "Failed to send message"}
    
    def focus_window(self, window_name: str, partial_match: bool = True) -> Dict[str, Any]:
        """
        Focus a specific window by name.
        
        Args:
            window_name: Name of the window to focus
            partial_match: If True, match partial window names
            
        Returns:
            Response data from the server
        """
        logger.info(f"Requesting window focus: window_name={window_name}, partial_match={partial_match}")
        
        return self.pipe_client.send_message("focus_window", {
            "window_name": window_name,
            "partial_match": partial_match
        }) or {"status": "error", "message": "Failed to send message"}
    
    def minimize_windows(self, exception_window: Optional[str] = None) -> Dict[str, Any]:
        """
        Minimize all windows except the specified window.
        
        Args:
            exception_window: Name of the window to keep visible (None = use server default)
            
        Returns:
            Response data from the server
        """
        logger.info(f"Requesting minimize windows: exception_window={exception_window}")
        
        message_data = {}
        if exception_window:
            message_data["exception_window"] = exception_window
        
        return self.pipe_client.send_message("minimize_windows", message_data) or {
            "status": "error",
            "message": "Failed to send message"
        }
    
    def restore_windows(self) -> Dict[str, Any]:
        """
        Restore all previously minimized windows.
        
        Returns:
            Response data from the server
        """
        logger.info("Requesting restore windows")
        
        return self.pipe_client.send_message("restore_windows", {}) or {
            "status": "error",
            "message": "Failed to send message"
        }
    
    def take_screenshot(self, window_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of the current screen or a specific window.
        
        Args:
            window_name: Optional name of a specific window to capture.
                         If provided, will attempt to capture just that window.
        
        Returns:
            Response data from the server
        """
        logger.info(f"Requesting screenshot{f' of window: {window_name}' if window_name else ''}")
        
        message_data = {}
        if window_name:
            message_data["window_name"] = window_name
        
        return self.pipe_client.send_message("take_screenshot", message_data) or {
            "status": "error",
            "message": "Failed to send message"
        }
    
    def get_window_list(self) -> Dict[str, Any]:
        """
        Get a list of all visible windows.
        
        Returns:
            Response data from the server containing the window list
        """
        logger.info("Requesting window list")
        
        return self.pipe_client.send_message("get_window_list", {}) or {
            "status": "error", 
            "message": "Failed to send message"
        }


def print_response(response: Dict[str, Any]):
    """Print a formatted response from the server."""
    if response.get("status") == "success":
        print("\n[SUCCESS] " + response.get("message", "Operation completed successfully"))
        
        # Print any additional information
        for key, value in response.items():
            if key not in ["status", "message"]:
                print(f"{key}: {value}")
    else:
        print("\n[ERROR] " + response.get("message", "Unknown error"))


def interactive_mode(client: RemoteClient):
    """Run the client in interactive mode with a command menu."""
    print("\nUndownUnlock Remote Client - Interactive Mode")
    print("============================================")
    
    while True:
        print("\nAvailable commands:")
        print("  1. List all windows")
        print("  2. Cycle to next window")
        print("  3. Cycle to previous window")
        print("  4. Focus specific window")
        print("  5. Minimize all except specific window")
        print("  6. Restore all windows")
        print("  7. Take screenshot")
        print("  0. Exit")
        
        choice = input("\nEnter command number: ")
        
        if choice == "0":
            break
        
        if choice == "1":
            response = client.get_window_list()
            if response.get("status") == "success":
                print("\nAvailable Windows:")
                for i, window in enumerate(response.get("windows", [])):
                    print(f"  {i+1}. {window}")
                print(f"\nTotal windows: {response.get('count', 0)}")
            else:
                print_response(response)
        
        elif choice == "2":
            response = client.cycle_window("next")
            print_response(response)
        
        elif choice == "3":
            response = client.cycle_window("previous")
            print_response(response)
        
        elif choice == "4":
            window_name = input("Enter window name (can be partial): ")
            response = client.focus_window(window_name)
            print_response(response)
        
        elif choice == "5":
            exception_window = input("Enter window to keep visible (leave blank for default): ")
            if not exception_window:
                exception_window = None
            response = client.minimize_windows(exception_window)
            print_response(response)
        
        elif choice == "6":
            response = client.restore_windows()
            print_response(response)
        
        elif choice == "7":
            window_choice = input("Enter window name to capture (leave blank for entire screen): ")
            if window_choice.strip():
                response = client.take_screenshot(window_choice)
            else:
                response = client.take_screenshot()
            print_response(response)
            if response.get("status") == "success" and response.get("screenshot_path"):
                print(f"Screenshot saved to: {response.get('screenshot_path')}")
        
        else:
            print("Invalid command. Please try again.")


def main():
    """Main entry point for the remote client."""
    parser = argparse.ArgumentParser(description="Remote client for UndownUnlock Accessibility Controller")
    
    # Add command-line arguments
    parser.add_argument("--pipe", default="UndownUnlockAccessibilityPipe", help="Named pipe to connect to")
    parser.add_argument("--command", choices=["list", "cycle", "focus", "minimize", "restore", "screenshot"], 
                      help="Command to execute")
    parser.add_argument("--direction", choices=["next", "previous"], default="next", 
                      help="Direction to cycle windows (for cycle command)")
    parser.add_argument("--window", help="Window name (for focus and minimize commands)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Create client
    client = RemoteClient(args.pipe)
    
    # Connect to server
    if not client.connect():
        print("Failed to connect to the accessibility controller.")
        print("Make sure the controller is running.")
        return 1
    
    try:
        if args.interactive:
            # Run in interactive mode
            interactive_mode(client)
        elif args.command:
            # Execute a single command
            response = None
            
            if args.command == "list":
                response = client.get_window_list()
                if response.get("status") == "success":
                    print("\nAvailable Windows:")
                    for i, window in enumerate(response.get("windows", [])):
                        print(f"  {i+1}. {window}")
                    print(f"\nTotal windows: {response.get('count', 0)}")
                
            elif args.command == "cycle":
                response = client.cycle_window(args.direction)
                
            elif args.command == "focus":
                if not args.window:
                    print("Error: --window parameter is required for focus command")
                    return 1
                response = client.focus_window(args.window)
                
            elif args.command == "minimize":
                response = client.minimize_windows(args.window)
                
            elif args.command == "restore":
                response = client.restore_windows()
                
            elif args.command == "screenshot":
                response = client.take_screenshot(args.window)
            
            if response and args.command != "list":
                print_response(response)
                
        else:
            # No command or interactive mode specified
            parser.print_help()
            
    finally:
        # Disconnect from server
        client.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 