"""
Vectra API Authentication Module

This module handles authentication to the Vectra API using OAuth2.
It can be imported by other scripts that need to access the Vectra API.
"""

import os
import json
import base64
import datetime
import requests
import sys
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Initialize colorama for colored terminal output
colorama.init()

def print_success(message):
    """Print a success message"""
    print(f"{Fore.GREEN}+ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message"""
    print(f"{Fore.RED}X {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an info message"""
    print(f"{Fore.BLUE}> {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Fore.YELLOW}! {message}{Style.RESET_ALL}")

def color_status(status, default='white'):
    """
    Colorize status text based on severity
    
    Args:
        status (str): Status text to colorize
        default (str, optional): Default color if no specific coloring applies
    
    Returns:
        str: Colorized status text
    """
    status_lower = str(status).lower()
    
    # Positive statuses (green)
    if any(x in status_lower for x in ['ok', 'enabled', 'healthy', 'good', 'success']):
        return f"{Fore.GREEN}{status}{Style.RESET_ALL}"
    
    # Warning statuses (yellow)
    elif any(x in status_lower for x in ['warning', 'partially', 'limited', 'degraded']):
        return f"{Fore.YELLOW}{status}{Style.RESET_ALL}"
    
    # Error/Critical statuses (red)
    elif any(x in status_lower for x in ['critical', 'disabled', 'error', 'fail', 'stopped', 'unavailable']):
        return f"{Fore.RED}{status}{Style.RESET_ALL}"
    
    # Neutral or informational statuses (blue)
    elif any(x in status_lower for x in ['info', 'unknown', 'pending']):
        return f"{Fore.BLUE}{status}{Style.RESET_ALL}"
    
    # Default handling
    return f"{Fore.WHITE}{status}{Style.RESET_ALL}"

def load_config(env_file="cred.env"):
    """
    Load configuration from environment variables
    
    Args:
        env_file (str, optional): Path to environment file. Defaults to 'cred.env'.
    
    Returns:
        dict: Configuration dictionary or None if loading fails
    """
    load_dotenv(env_file)
    
    config = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'vectra_url': os.getenv('VECTRA_URL'),
    }
    
    # Validate config
    missing = [k for k, v in config.items() if not v]
    if missing:
        print_error(f"Missing required environment variables in {env_file}:")
        for param in missing:
            print_error(f"  - {param.upper()}")
        print_info(f"Please set these variables in your {env_file} file and try again.")
        return None
    
    # Ensure URL ends with a slash
    if not config['vectra_url'].endswith('/'):
        config['vectra_url'] += '/'
    
    return config

def get_token(config=None, env_file="cred.env", token_file="vectra_token.json", 
              force_new=False, quiet=False, timeout=30):
    """
    Get authentication token for Vectra API
    
    Args:
        config (dict, optional): Pre-loaded configuration. Defaults to None.
        env_file (str, optional): Path to environment file. Defaults to 'cred.env'.
        token_file (str, optional): File to save/load token. Defaults to 'vectra_token.json'.
        force_new (bool, optional): Force getting a new token. Defaults to False.
        quiet (bool, optional): Suppress output messages. Defaults to False.
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
    
    Returns:
        dict: Token data or None if authentication fails
    """
    # Load configuration if not provided
    if not config:
        config = load_config(env_file)
        if not config:
            return None
    
    # Check if we have a saved token and it's still valid
    if not force_new and os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Check if token is expired
            if 'expires_in' in token_data and 'timestamp' in token_data:
                created = datetime.datetime.fromisoformat(token_data['timestamp'])
                expires_in = token_data['expires_in']
                now = datetime.datetime.utcnow()
                expiry = created + datetime.timedelta(seconds=expires_in)
                
                # If token is still valid, return it
                if now < expiry:
                    if not quiet:
                        print_info(f"Using existing token (expires at {expiry.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                    return token_data
                
                # Check if refresh token is available and valid
                if 'refresh_token' in token_data and 'refresh_expires_in' in token_data:
                    refresh_expiry = created + datetime.timedelta(seconds=token_data['refresh_expires_in'])
                    if now < refresh_expiry:
                        # Use refresh token to get a new access token
                        if not quiet:
                            print_info("Access token expired. Using refresh token to get a new one...")
                        return refresh_token(config, token_data['refresh_token'], quiet, timeout)
        except Exception as e:
            if not quiet:
                print_warning(f"Error reading saved token: {str(e)}")
    
    # Get a new token
    if not quiet:
        print_info(f"Authenticating to Vectra API at {config['vectra_url']}...")
    
    # Create authentication string
    auth_string = f"{config['client_id']}:{config['client_secret']}"
    auth_bytes = auth_string.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_auth = base64_bytes.decode('ascii')
    
    # Set up request for token
    token_url = f"{config['vectra_url']}oauth2/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Authorization': f'Basic {base64_auth}'
    }
    payload = 'grant_type=client_credentials'
    
    # Execute authentication request
    try:
        response = requests.post(token_url, headers=headers, data=payload, timeout=timeout)
        
        # Check for successful response
        if response.status_code == 200:
            token_data = response.json()
            
            # Add timestamp when token was created
            token_data['timestamp'] = datetime.datetime.utcnow().isoformat()
            
            # Save token to file
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            if not quiet:
                print_success("Authentication successful!")
            return token_data
        else:
            if not quiet:
                print_error(f"Authentication failed with status code: {response.status_code}")
                print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        if not quiet:
            print_error(f"Authentication error: {str(e)}")
        return None

def refresh_token(config, refresh_token, quiet=False, timeout=30):
    """
    Refresh an access token using a refresh token
    
    Args:
        config (dict): Configuration dictionary
        refresh_token (str): Refresh token to use
        quiet (bool, optional): Suppress output messages. Defaults to False.
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
    
    Returns:
        dict: New token data or None if refresh fails
    """
    if not quiet:
        print_info("Refreshing access token...")
    
    # Set up request for token refresh
    token_url = f"{config['vectra_url']}oauth2/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }
    payload = f'grant_type=refresh_token&refresh_token={refresh_token}'
    
    # Execute refresh request
    try:
        response = requests.post(
            token_url, 
            headers=headers, 
            data=payload,
            auth=(config['client_id'], config['client_secret']),
            timeout=timeout
        )
        
        # Check for successful response
        if response.status_code == 200:
            token_data = response.json()
            
            # Add timestamp when token was refreshed
            token_data['timestamp'] = datetime.datetime.utcnow().isoformat()
            
            # Save token to file
            with open('vectra_token.json', 'w') as f:
                json.dump(token_data, f, indent=2)
            
            if not quiet:
                print_success("Token refresh successful!")
            return token_data
        else:
            if not quiet:
                print_error(f"Token refresh failed with status code: {response.status_code}")
                print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        if not quiet:
            print_error(f"Token refresh error: {str(e)}")
        return None

def make_api_request(endpoint, token_data=None, method='GET', params=None, data=None, 
                     config=None, env_file="cred.env", quiet=False, timeout=60):
    """
    Make a request to the Vectra API
    
    Args:
        endpoint (str): API endpoint to call (without base URL)
        token_data (dict, optional): Token data to use for authentication
        method (str, optional): HTTP method to use. Defaults to 'GET'.
        params (dict, optional): Query parameters
        data (dict, optional): Request body for POST/PATCH requests
        config (dict, optional): Pre-loaded configuration
        env_file (str, optional): Environment file to load if config not provided
        quiet (bool, optional): Suppress output messages
        timeout (int, optional): Request timeout in seconds. Defaults to 60.
    
    Returns:
        Response object or None if request failed
    """
    # Get token if not provided
    if not token_data:
        token_data = get_token(config, env_file, quiet=quiet)
        if not token_data:
            return None
    
    # Load configuration if not provided
    if not config:
        config = load_config(env_file)
        if not config:
            return None
    
    # Prepare request
    url = f"{config['vectra_url']}{endpoint.lstrip('/')}"
    headers = {
        'Authorization': f"Bearer {token_data['access_token']}",
        'Accept': 'application/json'
    }
    
    if not quiet:
        print_info(f"Making {method} request to {endpoint}...")
    
    # Execute request
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method.upper() == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, params=params, json=data, timeout=timeout)
        elif method.upper() == 'PATCH':
            headers['Content-Type'] = 'application/json'
            response = requests.patch(url, headers=headers, params=params, json=data, timeout=timeout)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=timeout)
        else:
            if not quiet:
                print_error(f"Unsupported method: {method}")
            return None
        
        # Check for successful response
        if response.status_code in [200, 201, 202, 204]:
            if not quiet:
                print_success(f"Request successful ({response.status_code})")
            return response
        else:
            if not quiet:
                print_error(f"Request failed with status code: {response.status_code}")
                print_error(f"Response: {response.text}")
            return response
            
    except Exception as e:
        if not quiet:
            print_error(f"Request error: {str(e)}")
        return None

# For testing this module directly
if __name__ == "__main__":
    print(f"{Fore.CYAN}Vectra API Authentication Module Test{Style.RESET_ALL}")
    token_data = get_token()
    if token_data:
        print_success("Authentication successful!")
        print(json.dumps(token_data, indent=2))
    else:
        print_error("Authentication failed.")
