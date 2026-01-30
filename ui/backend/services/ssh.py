from sshtunnel import SSHTunnelForwarder
import paramiko
from typing import Optional, Tuple
import threading
import os

class SSHService:
    def __init__(self):
        self.tunnels: dict[int, SSHTunnelForwarder] = {}
        self.clients: dict[int, paramiko.SSHClient] = {}
        self.lock = threading.Lock()
        self._cached_key = None
        self._cached_key_path = None

    def _get_ssh_key_path(self) -> str:
        """Get default SSH key path, trying multiple common locations."""
        # Try keys in order of preference
        key_paths = [
            "~/.ssh/vast_rsa",      # vast.ai RSA key (usually unencrypted)
            "~/.ssh/id_ed25519",    # ed25519 (often unencrypted)
            "~/.ssh/id_rsa",        # RSA key
            "~/.ssh/vast_ai",       # vast.ai key (might be encrypted)
        ]
        for path in key_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                # Check if key can actually be loaded without password
                # The old check for 'ENCRYPTED' in content doesn't work for new OpenSSH format
                if self._can_load_key(expanded):
                    return expanded
        raise FileNotFoundError("No unencrypted SSH key found. Tried: " + ", ".join(key_paths))
    
    def _load_key(self, key_path: str) -> paramiko.PKey:
        """Load a private key from file, trying different key types."""
        # Expand ~ in path
        key_path = os.path.expanduser(key_path)
        
        # Try RSA first (most common for vast.ai)
        try:
            return paramiko.RSAKey.from_private_key_file(key_path)
        except paramiko.ssh_exception.SSHException:
            pass
        
        # Try Ed25519
        try:
            return paramiko.Ed25519Key.from_private_key_file(key_path)
        except paramiko.ssh_exception.SSHException:
            pass
        
        # Try ECDSA
        try:
            return paramiko.ECDSAKey.from_private_key_file(key_path)
        except paramiko.ssh_exception.SSHException:
            pass
        
        raise ValueError(f"Could not load key from {key_path}")
    
    def _get_pkey(self) -> paramiko.PKey:
        """Get a cached pkey object. This avoids re-parsing the key every time."""
        if self._cached_key is None:
            key_path = self._get_ssh_key_path()
            self._cached_key = self._load_key(key_path)
            self._cached_key_path = key_path
        return self._cached_key
    
    def _can_load_key(self, key_path: str) -> bool:
        """Check if a key can be loaded without a password."""
        try:
            # Try loading as each key type
            try:
                paramiko.RSAKey.from_private_key_file(key_path)
                return True
            except paramiko.ssh_exception.PasswordRequiredException:
                return False
            except paramiko.ssh_exception.SSHException:
                pass  # Not an RSA key, try next
            
            try:
                paramiko.Ed25519Key.from_private_key_file(key_path)
                return True
            except paramiko.ssh_exception.PasswordRequiredException:
                return False
            except paramiko.ssh_exception.SSHException:
                pass  # Not an Ed25519 key, try next
            
            try:
                paramiko.ECDSAKey.from_private_key_file(key_path)
                return True
            except paramiko.ssh_exception.PasswordRequiredException:
                return False
            except paramiko.ssh_exception.SSHException:
                pass  # Not an ECDSA key
            
            # If we got here, no key type worked
            return False
        except Exception:
            return False

    def connect(self, ssh_host: str, ssh_port: int, instance_id: int = None) -> paramiko.SSHClient:
        """Create SSH connection to instance."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use pkey instead of key_filename to avoid auto-detection issues
        client.connect(
            hostname=ssh_host,
            port=ssh_port,
            username="root",
            pkey=self._get_pkey(),
            timeout=30,
            allow_agent=False,  # Don't use ssh-agent
            look_for_keys=False  # Don't scan ~/.ssh for keys
        )
        if instance_id:
            with self.lock:
                self.clients[instance_id] = client
        return client

    def exec_command(
        self,
        ssh_host: str,
        ssh_port: int,
        command: str,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """Execute command on remote instance. Returns (exit_code, stdout, stderr)."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Use pkey instead of key_filename to avoid auto-detection issues
            client.connect(
                hostname=ssh_host,
                port=ssh_port,
                username="root",
                pkey=self._get_pkey(),
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, stdout.read().decode(), stderr.read().decode()
        finally:
            client.close()

    def exec_command_async(
        self,
        ssh_host: str,
        ssh_port: int,
        command: str
    ) -> Tuple[paramiko.SSHClient, paramiko.ChannelFile, paramiko.ChannelFile]:
        """Execute command asynchronously. Returns (client, stdout, stderr). Caller must close client."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Use pkey instead of key_filename to avoid auto-detection issues
        client.connect(
            hostname=ssh_host,
            port=ssh_port,
            username="root",
            pkey=self._get_pkey(),
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        return client, stdout, stderr

    def create_tunnel(
        self,
        instance_id: int,
        ssh_host: str,
        ssh_port: int,
        remote_port: int,
        local_port: int,
        ssh_key_path: str = None
    ) -> int:
        """Create SSH tunnel to instance, return local port."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"create_tunnel called: instance={instance_id}, {ssh_host}:{ssh_port}, remote={remote_port}, local={local_port}")
        
        with self.lock:
            if instance_id in self.tunnels:
                logger.info(f"Tunnel already exists for instance {instance_id}")
                return self.tunnels[instance_id].local_bind_port

            # Load the key as a paramiko PKey object
            # sshtunnel can accept either a path or a pkey object
            if ssh_key_path:
                # Expand and validate the custom key path
                expanded_path = os.path.expanduser(ssh_key_path)
                if os.path.exists(expanded_path):
                    key_path = expanded_path
                    pkey = self._load_key(key_path)
                    logger.info(f"Using custom SSH key: {key_path}")
                else:
                    # Custom path doesn't exist, fall back to default
                    logger.warning(f"Custom key path not found: {expanded_path}, using default key")
                    pkey = self._get_pkey()
                    key_path = self._cached_key_path
            else:
                pkey = self._get_pkey()
                key_path = self._cached_key_path
            
            logger.info(f"Using SSH key: {key_path} (type: {pkey.get_name()})")
            
            try:
                tunnel = SSHTunnelForwarder(
                    (ssh_host, ssh_port),
                    ssh_username="root",
                    ssh_pkey=pkey,  # Pass the loaded key object, not path
                    remote_bind_address=("127.0.0.1", remote_port),
                    local_bind_address=("127.0.0.1", local_port),
                    allow_agent=False,           # Don't try to use ssh-agent
                    host_pkey_directories=None   # Don't try to load host keys from ~/.ssh
                )
                logger.info("Starting tunnel...")
                tunnel.start()
                self.tunnels[instance_id] = tunnel
                logger.info(f"Tunnel started successfully on port {tunnel.local_bind_port}")
                return tunnel.local_bind_port
            except Exception as e:
                logger.error(f"Failed to create tunnel: {e}", exc_info=True)
                raise

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
