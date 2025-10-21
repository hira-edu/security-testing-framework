import os
import sys
import time
import json
import logging
import win32pipe
import win32file
import pywintypes
import threading
import uuid
import base64
import traceback
from typing import Dict, Any, Callable, Optional, List, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.backends import default_backend

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("named_pipe_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NamedPipeManager")

class NamedPipeServer:
    """
    Server component for Windows Named Pipes communication.
    Uses legitimate Windows IPC mechanisms for secure component communication.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe"):
        """
        Initialize the Named Pipe Server.
        
        Args:
            pipe_name: Base name for the pipe (without the \\\\.\pipe\ prefix)
        """
        self.pipe_name = f"\\\\.\\pipe\\{pipe_name}"
        self.running = False
        self.server_thread = None
        self.pipe_handle = None
        self.connected_clients = set()
        self.message_handlers = {}
        self.security_manager = SecurityManager()
        
        # Track metrics
        self.message_count = 0
        self.client_connections = 0
        
        logger.info(f"Named Pipe Server initialized with pipe name: {self.pipe_name}")
    
    def start(self):
        """Start the named pipe server."""
        if self.running:
            return
            
        logger.info("Starting Named Pipe Server...")
        self.running = True
        
        # Start server thread
        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info("Named Pipe Server started.")
    
    def stop(self):
        """Stop the named pipe server."""
        if not self.running:
            return
            
        logger.info("Stopping Named Pipe Server...")
        self.running = False
        
        # Close pipe handle if open
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
            except:
                pass
            self.pipe_handle = None
        
        # Wait for server thread to terminate
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        
        logger.info("Named Pipe Server stopped.")
    
    def register_handler(self, message_type: str, handler_func: Callable[[Dict[str, Any], str], Dict[str, Any]]):
        """
        Register a handler function for a specific message type.
        
        Args:
            message_type: The type of message to handle
            handler_func: Function to call when message is received (takes message data and client_id)
        """
        self.message_handlers[message_type] = handler_func
        logger.info(f"Registered handler for message type: {message_type}")
    
    def _server_loop(self):
        """Main server loop for accepting connections."""
        try:
            while self.running:
                # Create a new pipe instance
                self.pipe_handle = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    4096,  # Output buffer size
                    4096,  # Input buffer size
                    0,     # Default timeout
                    None   # Security attributes
                )
                
                logger.debug("Waiting for client connection...")
                
                try:
                    # Wait for a client to connect
                    win32pipe.ConnectNamedPipe(self.pipe_handle, None)
                    
                    # Generate a client ID
                    client_id = str(uuid.uuid4())
                    self.connected_clients.add(client_id)
                    self.client_connections += 1
                    
                    logger.info(f"Client connected. Assigned ID: {client_id}")
                    
                    # Handle client communication in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(self.pipe_handle, client_id)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # Create a new pipe for the next client
                    self.pipe_handle = None
                    
                except pywintypes.error as e:
                    if not self.running:
                        break
                    logger.error(f"Error in pipe connection: {e}")
                    if self.pipe_handle:
                        win32file.CloseHandle(self.pipe_handle)
                        self.pipe_handle = None
                    time.sleep(0.1)  # Short delay before retrying
                
        except Exception as e:
            if self.running:  # Only log if we didn't intend to stop
                logger.error(f"Error in server loop: {e}")
                logger.error(traceback.format_exc())
        
        logger.info("Server loop terminated.")
    
    def _handle_client(self, pipe_handle, client_id: str):
        """
        Handle communication with a connected client.
        
        Args:
            pipe_handle: Handle to the pipe connected to the client
            client_id: Unique ID for this client
        """
        try:
            while self.running:
                try:
                    # Read message from client
                    result, data = win32file.ReadFile(pipe_handle, 4096)
                    if result != 0:
                        break
                    
                    # Process the message
                    if data:
                        # Decrypt and verify message
                        try:
                            encrypted_data = data.decode('utf-8')
                            decrypted_data = self.security_manager.decrypt_and_verify(encrypted_data)
                            message = json.loads(decrypted_data)
                            
                            message_type = message.get('type')
                            message_data = message.get('data', {})
                            
                            logger.debug(f"Received message of type: {message_type} from client: {client_id}")
                            self.message_count += 1
                            
                            # Process message based on type
                            response_data = None
                            if message_type in self.message_handlers:
                                # Call the registered handler
                                response_data = self.message_handlers[message_type](message_data, client_id)
                            else:
                                # Default response for unknown message type
                                response_data = {"status": "error", "message": f"Unsupported message type: {message_type}"}
                            
                            # Prepare and encrypt response
                            response = {
                                "type": f"{message_type}_response",
                                "data": response_data
                            }
                            
                            response_json = json.dumps(response)
                            encrypted_response = self.security_manager.encrypt_and_sign(response_json)
                            
                            # Send response back to client
                            win32file.WriteFile(pipe_handle, encrypted_response.encode('utf-8'))
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received from client: {client_id}")
                        except Exception as e:
                            logger.error(f"Error processing message from client {client_id}: {e}")
                            logger.error(traceback.format_exc())
                    
                except pywintypes.error as e:
                    if e.winerror == 109:  # Broken pipe
                        logger.info(f"Client {client_id} disconnected.")
                        break
                    else:
                        logger.error(f"Error reading from pipe for client {client_id}: {e}")
                        break
        
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            # Clean up
            try:
                if pipe_handle:
                    win32file.CloseHandle(pipe_handle)
            except:
                pass
            
            # Remove client from connected clients
            if client_id in self.connected_clients:
                self.connected_clients.remove(client_id)
            
            logger.info(f"Client {client_id} handler terminated.")
    
    def send_message_to_clients(self, message_type: str, message_data: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message_type: Type of message to send
            message_data: Data to include in the message
        """
        # This would require maintaining individual pipe connections to each client
        # For simplicity, we're not implementing this in the current version
        # This would be used for push notifications to clients
        pass


class NamedPipeClient:
    """
    Client component for Windows Named Pipes communication.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe", reconnect_attempts: int = 3):
        """
        Initialize the Named Pipe Client.
        
        Args:
            pipe_name: Base name for the pipe (without the \\\\.\pipe\ prefix)
            reconnect_attempts: Number of times to attempt reconnection
        """
        self.pipe_name = f"\\\\.\\pipe\\{pipe_name}"
        self.pipe_handle = None
        self.connected = False
        self.reconnect_attempts = reconnect_attempts
        self.security_manager = SecurityManager()
        
        logger.info(f"Named Pipe Client initialized for pipe: {self.pipe_name}")
    
    def connect(self):
        """
        Connect to the named pipe server.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connected:
            return True
            
        logger.info(f"Connecting to pipe: {self.pipe_name}")
        
        attempts = 0
        while attempts < self.reconnect_attempts:
            try:
                # Wait for pipe to be available
                win32pipe.WaitNamedPipe(self.pipe_name, 5000)  # 5 second timeout
                
                # Connect to the pipe
                self.pipe_handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,      # No sharing
                    None,   # Default security
                    win32file.OPEN_EXISTING,
                    0,      # Default attributes
                    None    # No template file
                )
                
                # Set pipe to message mode
                win32pipe.SetNamedPipeHandleState(
                    self.pipe_handle,
                    win32pipe.PIPE_READMODE_MESSAGE,
                    None,
                    None
                )
                
                self.connected = True
                logger.info("Connected to pipe server successfully.")
                return True
                
            except pywintypes.error as e:
                logger.error(f"Connection attempt {attempts + 1} failed: {e}")
                attempts += 1
                time.sleep(1)  # Wait before retrying
                
                # Clean up handle if any
                if self.pipe_handle:
                    try:
                        win32file.CloseHandle(self.pipe_handle)
                    except:
                        pass
                    self.pipe_handle = None
        
        logger.error(f"Failed to connect after {self.reconnect_attempts} attempts.")
        return False
    
    def disconnect(self):
        """Disconnect from the named pipe server."""
        if not self.connected:
            return
            
        logger.info("Disconnecting from pipe server.")
        
        try:
            win32file.CloseHandle(self.pipe_handle)
        except:
            pass
        
        self.pipe_handle = None
        self.connected = False
    
    def send_message(self, message_type: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a message to the server and wait for a response.
        
        Args:
            message_type: Type of message to send
            message_data: Data to include in the message
            
        Returns:
            Response data dictionary or None if operation failed
        """
        # Ensure we are connected
        if not self.connected and not self.connect():
            return None
        
        try:
            # Prepare message
            message = {
                "type": message_type,
                "data": message_data
            }
            
            # Convert to JSON and encrypt
            message_json = json.dumps(message)
            encrypted_message = self.security_manager.encrypt_and_sign(message_json)
            
            # Send message
            win32file.WriteFile(self.pipe_handle, encrypted_message.encode('utf-8'))
            
            # Wait for response
            result, data = win32file.ReadFile(self.pipe_handle, 4096)
            
            if result != 0:
                logger.error(f"Error reading response: {result}")
                self.disconnect()
                return None
            
            # Decrypt and parse response
            encrypted_response = data.decode('utf-8')
            decrypted_response = self.security_manager.decrypt_and_verify(encrypted_response)
            response = json.loads(decrypted_response)
            
            # Return response data
            return response.get('data')
            
        except pywintypes.error as e:
            logger.error(f"Pipe communication error: {e}")
            self.disconnect()
            return None
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            logger.error(traceback.format_exc())
            return None


class SecurityManager:
    """
    Manages encryption and security for the pipe communication.
    """
    
    def __init__(self):
        """Initialize the security manager with encryption keys."""
        # In a production system, these would be securely generated and managed
        # For this demonstration, we're using fixed keys for simplicity
        self.encryption_key = b'Sixteen byte key'  # 16 bytes for AES-128
        self.hmac_key = b'HMAC authentication key for signature verification'
        
        # Initialize cryptographic components
        self.backend = default_backend()
    
    def encrypt_and_sign(self, data: str) -> str:
        """
        Encrypt and sign data for secure transmission.
        
        Args:
            data: String data to encrypt
            
        Returns:
            Base64-encoded string of encrypted data and signature
        """
        # Convert data to bytes
        data_bytes = data.encode('utf-8')
        
        # Generate a random IV
        iv = os.urandom(16)
        
        # Create encryptor
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Add padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data_bytes) + padder.finalize()
        
        # Encrypt data
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Create HMAC signature of IV + encrypted data
        h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=self.backend)
        h.update(iv + encrypted_data)
        signature = h.finalize()
        
        # Format as IV + Encrypted Data + Signature
        full_message = iv + encrypted_data + signature
        
        # Encode in base64 for easier transmission
        return base64.b64encode(full_message).decode('utf-8')
    
    def decrypt_and_verify(self, encrypted_data: str) -> str:
        """
        Decrypt and verify the signature of received data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data with signature
            
        Returns:
            Original decrypted string data
            
        Raises:
            ValueError: If signature verification fails
        """
        # Decode base64
        full_message = base64.b64decode(encrypted_data)
        
        # Extract components
        iv = full_message[:16]
        signature = full_message[-32:]  # SHA256 is 32 bytes
        encrypted_data_bytes = full_message[16:-32]
        
        # Verify HMAC signature
        h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=self.backend)
        h.update(iv + encrypted_data_bytes)
        
        try:
            h.verify(signature)
        except Exception:
            raise ValueError("Signature verification failed. Data may have been tampered with.")
        
        # Decrypt data
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data_bytes) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        data_bytes = unpadder.update(padded_data) + unpadder.finalize()
        
        # Convert back to string
        return data_bytes.decode('utf-8')

    def encrypt_message(self, message: Dict[str, Any]) -> str:
        """Serialize, encrypt and sign a message dictionary."""
        message_json = json.dumps(message)
        return self.encrypt_and_sign(message_json)

    def decrypt_message(self, encrypted_message: str) -> Dict[str, Any]:
        """Decrypt, verify and deserialize a message dictionary."""
        decrypted_json = self.decrypt_and_verify(encrypted_message)
        return json.loads(decrypted_json)

    def sign_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Return the message with an attached HMAC signature."""
        message_json = json.dumps(message, sort_keys=True)
        h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=self.backend)
        h.update(message_json.encode("utf-8"))
        signature = base64.b64encode(h.finalize()).decode("utf-8")
        return {"message": message, "signature": signature}

    def verify_message(self, signed_message: Dict[str, Any]) -> bool:
        """Verify the HMAC signature of a signed message."""
        try:
            message_json = json.dumps(signed_message.get("message"), sort_keys=True)
            signature = base64.b64decode(signed_message.get("signature", ""))
            h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=self.backend)
            h.update(message_json.encode("utf-8"))
            h.verify(signature)
            return True
        except Exception:
            return False
