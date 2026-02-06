"""
CAFÉCRAFT SECURITY UTILITIES

Responsibilities:
- Password hashing with bcrypt or SHA-256
- Password verification
- Secure cryptographic operations

No GUI dependencies.
"""

import hashlib
import os
import base64
from typing import Tuple

# Try to import bcrypt, fall back to hashlib if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


# =======================
# PASSWORD HASHING
# =======================

def hash_password(password: str) -> str:
    """
    Hash a password securely using bcrypt (preferred) or SHA-256 (fallback).
    
    If bcrypt is installed, uses bcrypt with salt rounds.
    Otherwise, uses SHA-256 with PBKDF2 key derivation.
    
    Args:
        password: Plain text password to hash.
        
    Returns:
        Hashed password as string.
        
    Raises:
        ValueError: If password is empty or invalid.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    
    if BCRYPT_AVAILABLE:
        # Use bcrypt (recommended for production)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        # Fallback to SHA-256 with PBKDF2
        return _hash_password_sha256(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain text password against its hash.
    
    Automatically detects which hashing method was used.
    
    Args:
        password: Plain text password to verify.
        password_hash: Previously hashed password.
        
    Returns:
        True if password matches hash, False otherwise.
        
    Raises:
        ValueError: If inputs are invalid.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    
    if not password_hash or not isinstance(password_hash, str):
        raise ValueError("Password hash must be a non-empty string")
    
    if BCRYPT_AVAILABLE:
        # Check if hash looks like bcrypt format
        if password_hash.startswith('$2'):
            try:
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    password_hash.encode('utf-8')
                )
            except Exception:
                return False
        else:
            # Fallback to SHA-256 verification
            return _verify_password_sha256(password, password_hash)
    else:
        # Use SHA-256 verification
        return _verify_password_sha256(password, password_hash)


# =======================
# SHA-256 FALLBACK IMPLEMENTATION
# =======================

def _hash_password_sha256(password: str) -> str:
    """
    Hash password using SHA-256 with PBKDF2 key derivation.
    
    This is a fallback when bcrypt is not available.
    
    Args:
        password: Plain text password.
        
    Returns:
        Formatted hash string: "sha256$salt$hash"
    """
    # Generate random salt
    salt = os.urandom(32)
    
    # Derive key using PBKDF2
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,  # iterations
        dklen=32
    )
    
    # Encode salt and key in base64
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    key_b64 = base64.b64encode(key).decode('utf-8')
    
    # Return formatted hash
    return f"sha256${salt_b64}${key_b64}"


def _verify_password_sha256(password: str, password_hash: str) -> bool:
    """
    Verify password against SHA-256 PBKDF2 hash.
    
    Args:
        password: Plain text password to verify.
        password_hash: Formatted hash string from _hash_password_sha256.
        
    Returns:
        True if password matches, False otherwise.
    """
    try:
        # Parse the hash format
        parts = password_hash.split('$')
        if len(parts) != 3 or parts[0] != 'sha256':
            return False
        
        salt_b64 = parts[1]
        key_b64 = parts[2]
        
        # Decode salt
        salt = base64.b64decode(salt_b64.encode('utf-8'))
        
        # Derive key from password using same parameters
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,  # Must match hashing iterations
            dklen=32
        )
        
        # Encode for comparison
        key_b64_computed = base64.b64encode(key).decode('utf-8')
        
        # Constant-time comparison to prevent timing attacks
        return _constant_time_compare(key_b64, key_b64_computed)
    
    except Exception:
        return False


# =======================
# UTILITY FUNCTIONS
# =======================

def _constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    
    Args:
        a: First string.
        b: Second string.
        
    Returns:
        True if strings are equal, False otherwise.
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0


def generate_random_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Useful for session tokens, password reset links, etc.
    
    Args:
        length: Length of token in bytes.
        
    Returns:
        Base64-encoded random token.
    """
    if length < 16:
        raise ValueError("Token length must be at least 16 bytes")
    
    random_bytes = os.urandom(length)
    return base64.b64encode(random_bytes).decode('utf-8')


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - Minimum 12 characters
    - At least 1 lowercase letter
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special character
    
    Args:
        password: Password to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, "").
        If invalid, returns (False, error_message).
    """
    if not isinstance(password, str):
        return False, "Password must be a string"
    
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""


# =======================
# HASH UTILITIES
# =======================

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm.
    
    Useful for creating unique identifiers, checksums, etc.
    
    Args:
        text: Text to hash.
        algorithm: Hash algorithm to use (sha256, sha512, md5).
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        ValueError: If algorithm is not supported.
    """
    if algorithm not in ["sha256", "sha512", "md5"]:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    h = hashlib.new(algorithm)
    h.update(text.encode('utf-8'))
    return h.hexdigest()
