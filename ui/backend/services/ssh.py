from sshtunnel import SSHTunnelForwarder
import paramiko
from typing import Optional
import threading

class SSHService:
    def __init__(self):
        self.tunnels: dict[int, SSHTunnelForwarder] = {}
        self.lock = threading.Lock()

    def create_tunnel(
        self,
        instance_id: int,
        ssh_host: str,
        ssh_port: int,
        remote_port: int,
        local_port: int,
        ssh_key_path: str
    ) -> int:
        """Create SSH tunnel to instance, return local port."""
        with self.lock:
            if instance_id in self.tunnels:
                return self.tunnels[instance_id].local_bind_port

            tunnel = SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username="root",
                ssh_pkey=ssh_key_path,
                remote_bind_address=("127.0.0.1", remote_port),
                local_bind_address=("127.0.0.1", local_port)
            )
            tunnel.start()
            self.tunnels[instance_id] = tunnel
            return tunnel.local_bind_port

    def close_tunnel(self, instance_id: int):
        """Close SSH tunnel for instance."""
        with self.lock:
            if instance_id in self.tunnels:
                self.tunnels[instance_id].stop()
                del self.tunnels[instance_id]

    def get_tunnel_port(self, instance_id: int) -> Optional[int]:
        """Get local port for existing tunnel."""
        with self.lock:
            if instance_id in self.tunnels:
                return self.tunnels[instance_id].local_bind_port
            return None

ssh_service = SSHService()
