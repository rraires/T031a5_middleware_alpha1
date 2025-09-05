"""Authentication and Authorization Manager for API Gateway.

Manages JWT tokens, user authentication, and access control.
"""

import asyncio
import logging
import time
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class UserRole(Enum):
    """User roles for access control."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """System permissions."""
    # System control
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    
    # Robot control
    ROBOT_CONTROL = "robot:control"
    ROBOT_MOTION = "robot:motion"
    ROBOT_AUDIO = "robot:audio"
    ROBOT_VIDEO = "robot:video"
    ROBOT_LEDS = "robot:leds"
    
    # Data access
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    
    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"


@dataclass
class UserInfo:
    """User information."""
    user_id: str
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.GUEST
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    login_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenInfo:
    """JWT token information."""
    token: str
    token_type: str = "bearer"
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    user_id: str = ""
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Authentication configuration."""
    # JWT settings
    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 30
    
    # Password settings
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    # Security settings
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    
    # API key settings
    api_key_length: int = 32
    api_key_expire_days: int = 365
    
    # Rate limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    
    # Default permissions by role
    role_permissions: Dict[UserRole, Set[Permission]] = field(default_factory=lambda: {
        UserRole.ADMIN: {
            Permission.SYSTEM_ADMIN, Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITOR,
            Permission.ROBOT_CONTROL, Permission.ROBOT_MOTION, Permission.ROBOT_AUDIO,
            Permission.ROBOT_VIDEO, Permission.ROBOT_LEDS,
            Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_DELETE,
            Permission.API_READ, Permission.API_WRITE, Permission.API_ADMIN
        },
        UserRole.OPERATOR: {
            Permission.SYSTEM_MONITOR,
            Permission.ROBOT_CONTROL, Permission.ROBOT_MOTION, Permission.ROBOT_AUDIO,
            Permission.ROBOT_VIDEO, Permission.ROBOT_LEDS,
            Permission.DATA_READ, Permission.DATA_WRITE,
            Permission.API_READ, Permission.API_WRITE
        },
        UserRole.VIEWER: {
            Permission.SYSTEM_MONITOR,
            Permission.DATA_READ,
            Permission.API_READ
        },
        UserRole.GUEST: {
            Permission.API_READ
        }
    })


@dataclass
class AuthStats:
    """Authentication statistics."""
    total_logins: int = 0
    successful_logins: int = 0
    failed_logins: int = 0
    active_sessions: int = 0
    total_tokens_issued: int = 0
    total_tokens_revoked: int = 0
    
    # Security events
    brute_force_attempts: int = 0
    invalid_token_attempts: int = 0
    permission_denied_attempts: int = 0
    
    def get_success_rate(self) -> float:
        """Get login success rate."""
        if self.total_logins == 0:
            return 0.0
        return self.successful_logins / self.total_logins


class AuthManager:
    """Authentication and authorization manager.
    
    Manages JWT tokens, user authentication, and access control.
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or AuthConfig()
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # HTTP Bearer for token extraction
        self.security = HTTPBearer(auto_error=False)
        
        # User storage (in production, this would be a database)
        self.users: Dict[str, UserInfo] = {}
        self.user_passwords: Dict[str, str] = {}  # username -> hashed_password
        
        # Token storage
        self.active_tokens: Dict[str, TokenInfo] = {}
        self.revoked_tokens: Set[str] = set()
        
        # API keys
        self.api_keys: Dict[str, UserInfo] = {}  # api_key -> user_info
        
        # Session management
        self.active_sessions: Dict[str, datetime] = {}  # user_id -> last_activity
        
        # Security tracking
        self.login_attempts: Dict[str, List[datetime]] = {}  # username -> attempt_times
        self.locked_accounts: Dict[str, datetime] = {}  # username -> unlock_time
        
        # Statistics
        self.stats = AuthStats()
        
        # Callbacks
        self.login_callbacks: List[Callable] = []
        self.logout_callbacks: List[Callable] = []
        self.permission_denied_callbacks: List[Callable] = []
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Create default admin user
        self._create_default_users()
        
        self.logger.info("Auth Manager initialized")
    
    def _create_default_users(self) -> None:
        """Create default users."""
        # Default admin user
        admin_user = UserInfo(
            user_id="admin",
            username="admin",
            email="admin@unitree.com",
            role=UserRole.ADMIN,
            permissions=self.config.role_permissions[UserRole.ADMIN].copy()
        )
        self.users["admin"] = admin_user
        self.user_passwords["admin"] = self.hash_password("admin123")
        
        # Default operator user
        operator_user = UserInfo(
            user_id="operator",
            username="operator",
            email="operator@unitree.com",
            role=UserRole.OPERATOR,
            permissions=self.config.role_permissions[UserRole.OPERATOR].copy()
        )
        self.users["operator"] = operator_user
        self.user_passwords["operator"] = self.hash_password("operator123")
        
        self.logger.info("Default users created")
    
    async def initialize(self) -> bool:
        """Initialize authentication manager.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info("Auth Manager initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing Auth Manager: {e}")
            return False
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Token cleanup task
        task = asyncio.create_task(self._token_cleanup_loop())
        self._background_tasks.append(task)
        
        # Session cleanup task
        task = asyncio.create_task(self._session_cleanup_loop())
        self._background_tasks.append(task)
        
        # Security monitoring task
        task = asyncio.create_task(self._security_monitoring_loop())
        self._background_tasks.append(task)
    
    def hash_password(self, password: str) -> str:
        """Hash password.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password(self, password: str) -> List[str]:
        """Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters long")
        
        if self.config.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.config.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked.
        
        Args:
            username: Username to check
        
        Returns:
            True if account is locked, False otherwise
        """
        if username not in self.locked_accounts:
            return False
        
        unlock_time = self.locked_accounts[username]
        if datetime.utcnow() >= unlock_time:
            # Account lock has expired
            del self.locked_accounts[username]
            return False
        
        return True
    
    def _record_login_attempt(self, username: str, success: bool) -> None:
        """Record login attempt.
        
        Args:
            username: Username
            success: Whether login was successful
        """
        current_time = datetime.utcnow()
        
        # Initialize attempts list if needed
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        
        # Add current attempt
        self.login_attempts[username].append(current_time)
        
        # Remove old attempts (older than lockout duration)
        cutoff_time = current_time - timedelta(minutes=self.config.lockout_duration_minutes)
        self.login_attempts[username] = [
            attempt for attempt in self.login_attempts[username]
            if attempt > cutoff_time
        ]
        
        # Update statistics
        self.stats.total_logins += 1
        if success:
            self.stats.successful_logins += 1
            # Clear failed attempts on successful login
            self.login_attempts[username] = []
        else:
            self.stats.failed_logins += 1
            
            # Check if account should be locked
            if len(self.login_attempts[username]) >= self.config.max_login_attempts:
                unlock_time = current_time + timedelta(minutes=self.config.lockout_duration_minutes)
                self.locked_accounts[username] = unlock_time
                self.stats.brute_force_attempts += 1
                self.logger.warning(f"Account locked due to too many failed attempts: {username}")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserInfo]:
        """Authenticate user with username and password.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User information if authentication successful, None otherwise
        """
        try:
            # Check if account is locked
            if self._is_account_locked(username):
                self.logger.warning(f"Login attempt on locked account: {username}")
                return None
            
            # Check if user exists
            if username not in self.users:
                self._record_login_attempt(username, False)
                return None
            
            user = self.users[username]
            
            # Check if user is active
            if not user.is_active:
                self._record_login_attempt(username, False)
                return None
            
            # Verify password
            stored_password = self.user_passwords.get(username)
            if not stored_password or not self.verify_password(password, stored_password):
                self._record_login_attempt(username, False)
                return None
            
            # Authentication successful
            self._record_login_attempt(username, True)
            
            # Update user login info
            user.last_login = datetime.utcnow()
            user.login_count += 1
            
            # Update session
            self.active_sessions[user.user_id] = datetime.utcnow()
            self.stats.active_sessions = len(self.active_sessions)
            
            # Notify callbacks
            await self._notify_login_callbacks(user)
            
            self.logger.info(f"User authenticated successfully: {username}")
            return user
        
        except Exception as e:
            self.logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    def create_access_token(self, user: UserInfo, expires_delta: Optional[timedelta] = None) -> TokenInfo:
        """Create JWT access token.
        
        Args:
            user: User information
            expires_delta: Token expiration time
        
        Returns:
            Token information
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        # Create token payload
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # Encode token
        token = jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
        
        # Create token info
        token_info = TokenInfo(
            token=token,
            expires_at=expire,
            user_id=user.user_id,
            permissions=user.permissions.copy()
        )
        
        # Store active token
        self.active_tokens[token] = token_info
        self.stats.total_tokens_issued += 1
        
        return token_info
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token.
        
        Args:
            token: JWT token
        
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                self.stats.invalid_token_attempts += 1
                return None
            
            # Decode token
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            
            # Check if token is in active tokens
            if token not in self.active_tokens:
                self.stats.invalid_token_attempts += 1
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            self.logger.debug("Token has expired")
            # Remove from active tokens
            self.active_tokens.pop(token, None)
            self.stats.invalid_token_attempts += 1
            return None
        
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid token: {e}")
            self.stats.invalid_token_attempts += 1
            return None
    
    async def get_current_user(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserInfo]:
        """Get current user from token.
        
        Args:
            credentials: HTTP authorization credentials
        
        Returns:
            User information if valid token, None otherwise
        """
        if not credentials:
            return None
        
        # Decode token
        payload = self.decode_token(credentials.credentials)
        if not payload:
            return None
        
        # Get user
        user_id = payload.get("sub")
        if not user_id or user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Check if user is still active
        if not user.is_active:
            return None
        
        # Update session activity
        self.active_sessions[user_id] = datetime.utcnow()
        
        return user
    
    async def require_permission(self, permission: Permission) -> Callable:
        """Create dependency for permission requirement.
        
        Args:
            permission: Required permission
        
        Returns:
            Dependency function
        """
        async def permission_dependency(user: UserInfo = Depends(self.get_current_user)) -> UserInfo:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if permission not in user.permissions:
                self.stats.permission_denied_attempts += 1
                await self._notify_permission_denied_callbacks(user, permission)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}"
                )
            
            return user
        
        return permission_dependency
    
    async def require_role(self, role: UserRole) -> Callable:
        """Create dependency for role requirement.
        
        Args:
            role: Required role
        
        Returns:
            Dependency function
        """
        async def role_dependency(user: UserInfo = Depends(self.get_current_user)) -> UserInfo:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check role hierarchy (admin can access everything)
            role_hierarchy = {
                UserRole.GUEST: 0,
                UserRole.VIEWER: 1,
                UserRole.OPERATOR: 2,
                UserRole.ADMIN: 3
            }
            
            if role_hierarchy.get(user.role, 0) < role_hierarchy.get(role, 0):
                self.stats.permission_denied_attempts += 1
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )
            
            return user
        
        return role_dependency
    
    def revoke_token(self, token: str) -> bool:
        """Revoke JWT token.
        
        Args:
            token: Token to revoke
        
        Returns:
            True if token revoked successfully, False otherwise
        """
        try:
            # Add to revoked tokens
            self.revoked_tokens.add(token)
            
            # Remove from active tokens
            self.active_tokens.pop(token, None)
            
            self.stats.total_tokens_revoked += 1
            return True
        
        except Exception as e:
            self.logger.error(f"Error revoking token: {e}")
            return False
    
    async def logout_user(self, user_id: str) -> bool:
        """Logout user and revoke all tokens.
        
        Args:
            user_id: User ID to logout
        
        Returns:
            True if logout successful, False otherwise
        """
        try:
            # Remove from active sessions
            self.active_sessions.pop(user_id, None)
            self.stats.active_sessions = len(self.active_sessions)
            
            # Revoke all user tokens
            tokens_to_revoke = [
                token for token, token_info in self.active_tokens.items()
                if token_info.user_id == user_id
            ]
            
            for token in tokens_to_revoke:
                self.revoke_token(token)
            
            # Get user for callbacks
            user = self.users.get(user_id)
            if user:
                await self._notify_logout_callbacks(user)
            
            self.logger.info(f"User logged out: {user_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error logging out user {user_id}: {e}")
            return False
    
    def create_api_key(self, user: UserInfo) -> str:
        """Create API key for user.
        
        Args:
            user: User information
        
        Returns:
            Generated API key
        """
        # Generate API key
        api_key = secrets.token_urlsafe(self.config.api_key_length)
        
        # Store API key
        self.api_keys[api_key] = user
        
        self.logger.info(f"API key created for user: {user.username}")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[UserInfo]:
        """Validate API key.
        
        Args:
            api_key: API key to validate
        
        Returns:
            User information if valid, None otherwise
        """
        return self.api_keys.get(api_key)
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key.
        
        Args:
            api_key: API key to revoke
        
        Returns:
            True if revoked successfully, False otherwise
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False
    
    async def _token_cleanup_loop(self) -> None:
        """Background token cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.cleanup_expired_tokens()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in token cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _session_cleanup_loop(self) -> None:
        """Background session cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.cleanup_expired_sessions()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _security_monitoring_loop(self) -> None:
        """Background security monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.monitor_security_events()
                await asyncio.sleep(60)  # Monitor every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in security monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def cleanup_expired_tokens(self) -> None:
        """Cleanup expired tokens."""
        try:
            current_time = datetime.utcnow()
            expired_tokens = []
            
            for token, token_info in self.active_tokens.items():
                if current_time >= token_info.expires_at:
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                self.active_tokens.pop(token, None)
                self.revoked_tokens.discard(token)  # Remove from revoked set too
            
            if expired_tokens:
                self.logger.debug(f"Cleaned up {len(expired_tokens)} expired tokens")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up expired tokens: {e}")
    
    async def cleanup_expired_sessions(self) -> None:
        """Cleanup expired sessions."""
        try:
            current_time = datetime.utcnow()
            timeout_delta = timedelta(minutes=self.config.session_timeout_minutes)
            expired_sessions = []
            
            for user_id, last_activity in self.active_sessions.items():
                if current_time - last_activity > timeout_delta:
                    expired_sessions.append(user_id)
            
            for user_id in expired_sessions:
                await self.logout_user(user_id)
            
            if expired_sessions:
                self.logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
    
    async def monitor_security_events(self) -> None:
        """Monitor security events."""
        try:
            # Check for suspicious activity
            current_time = datetime.utcnow()
            
            # Check for accounts with too many recent failed attempts
            for username, attempts in self.login_attempts.items():
                recent_attempts = [
                    attempt for attempt in attempts
                    if current_time - attempt < timedelta(minutes=10)
                ]
                
                if len(recent_attempts) >= self.config.max_login_attempts // 2:
                    self.logger.warning(f"Suspicious login activity detected for user: {username}")
            
            # Check for high error rates
            if self.stats.total_logins > 0:
                error_rate = (self.stats.failed_logins + self.stats.invalid_token_attempts) / self.stats.total_logins
                if error_rate > 0.5:  # More than 50% error rate
                    self.logger.warning(f"High authentication error rate detected: {error_rate:.2%}")
        
        except Exception as e:
            self.logger.error(f"Error monitoring security events: {e}")
    
    async def _notify_login_callbacks(self, user: UserInfo) -> None:
        """Notify login callbacks."""
        for callback in self.login_callbacks:
            try:
                await callback(user)
            except Exception as e:
                self.logger.error(f"Error in login callback: {e}")
    
    async def _notify_logout_callbacks(self, user: UserInfo) -> None:
        """Notify logout callbacks."""
        for callback in self.logout_callbacks:
            try:
                await callback(user)
            except Exception as e:
                self.logger.error(f"Error in logout callback: {e}")
    
    async def _notify_permission_denied_callbacks(self, user: UserInfo, permission: Permission) -> None:
        """Notify permission denied callbacks."""
        for callback in self.permission_denied_callbacks:
            try:
                await callback(user, permission)
            except Exception as e:
                self.logger.error(f"Error in permission denied callback: {e}")
    
    # Public API methods
    def add_login_callback(self, callback: Callable) -> None:
        """Add login callback."""
        self.login_callbacks.append(callback)
    
    def add_logout_callback(self, callback: Callable) -> None:
        """Add logout callback."""
        self.logout_callbacks.append(callback)
    
    def add_permission_denied_callback(self, callback: Callable) -> None:
        """Add permission denied callback."""
        self.permission_denied_callbacks.append(callback)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'total_logins': self.stats.total_logins,
            'successful_logins': self.stats.successful_logins,
            'failed_logins': self.stats.failed_logins,
            'success_rate': self.stats.get_success_rate(),
            'active_sessions': self.stats.active_sessions,
            'total_tokens_issued': self.stats.total_tokens_issued,
            'total_tokens_revoked': self.stats.total_tokens_revoked,
            'brute_force_attempts': self.stats.brute_force_attempts,
            'invalid_token_attempts': self.stats.invalid_token_attempts,
            'permission_denied_attempts': self.stats.permission_denied_attempts,
            'locked_accounts': len(self.locked_accounts),
            'active_api_keys': len(self.api_keys)
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status.
        
        Returns:
            Health status dictionary
        """
        error_rate = 0.0
        if self.stats.total_logins > 0:
            error_rate = (self.stats.failed_logins + self.stats.invalid_token_attempts) / self.stats.total_logins
        
        return {
            'healthy': error_rate < 0.5,  # Healthy if error rate < 50%
            'active_sessions': self.stats.active_sessions,
            'error_rate': error_rate,
            'locked_accounts': len(self.locked_accounts)
        }
    
    async def shutdown(self) -> None:
        """Shutdown authentication manager."""
        try:
            self.logger.info("Shutting down Auth Manager")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Stop background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._background_tasks.clear()
            
            self.logger.info("Auth Manager shutdown complete")
        
        except Exception as e:
            self.logger.error(f"Error during Auth Manager shutdown: {e}")