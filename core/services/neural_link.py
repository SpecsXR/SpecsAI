from PySide6.QtCore import QObject, Signal, QThread
import time
import json
import socket
import threading

class NeuralLinkService(QObject):
    """
    The 'Neural Link' connects the Body (SpecsAI) to the Brain (SpecsAI_SOS).
    It listens for commands from the Brain via TCP Socket (Port 6000).
    """
    # Signals to control the Body
    command_received = Signal(str, dict)  # command_type, data
    
    # Specific actions
    request_speak = Signal(str)
    request_expression = Signal(str)
    request_move = Signal(int, int)
    
    def __init__(self, host='127.0.0.1', port=6000):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.client_handler_thread = None

    def start_listening(self):
        """Starts the TCP Server in a separate thread"""
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"[NeuralLink] Online: Listening on {self.host}:{self.port}")
    
    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()

    def _run_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            while self.is_running:
                try:
                    client, addr = self.server_socket.accept()
                    print(f"[NeuralLink] Connected to Brain at {addr}")
                    self._handle_client(client)
                except OSError:
                    break  # Socket closed
        except Exception as e:
            print(f"[NeuralLink] Server Error: {e}")

    def _handle_client(self, client_socket):
        with client_socket:
            while self.is_running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    message = data.decode('utf-8')
                    # Handle multiple JSONs stuck together or partials (simple version)
                    # For now, assume one command per line or transmission
                    self.process_command(message)
                    
                except Exception as e:
                    print(f"[NeuralLink] Connection Error: {e}")
                    break
        print("[NeuralLink] Brain Disconnected")

    def process_command(self, command_json):
        try:
            # Check if it's a valid JSON
            data = json.loads(command_json)
            cmd_type = data.get("type")
            payload = data.get("payload", {})
            
            print(f"[NeuralLink] Received: {cmd_type}")
            
            if cmd_type == "speak":
                self.request_speak.emit(payload.get("text"))
            elif cmd_type == "expression":
                self.request_expression.emit(payload.get("name"))
            elif cmd_type == "move":
                self.request_move.emit(payload.get("x"), payload.get("y"))
                
            self.command_received.emit(cmd_type, payload)
            
        except json.JSONDecodeError:
            print(f"[NeuralLink] Invalid JSON received: {command_json}")
        except Exception as e:
            print(f"[NeuralLink] Error processing command: {e}")
