#!/usr/bin/env python3
"""
Active Hosts Script for Vectra RUX Platform

This script uses the Vectra API v3.4 to retrieve all active hosts
from the Vectra platform and export them to a CSV file.
It uses the OAuth2 authentication method from vectra_auth.py.
"""

import sys
import csv
import time
import argparse
import logging
from urllib.parse import urlparse, parse_qs

# Import the authentication module
try:
    from vectra_auth import get_token, make_api_request, print_success, print_error, print_info, print_warning
except ImportError as error:
    sys.exit(f"\nMissing import requirement: {error}\n")

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Retrieve active hosts from Vectra platform')
    parser.add_argument('--env-file', default='cred.env', help='Path to environment file with credentials')
    parser.add_argument('--output', default=None, help='Output file name (default: active_hosts-TIMESTAMP.csv)')
    parser.add_argument('--page-size', type=int, default=100, help='Number of hosts per page (default: 100, max: 5000)')
    parser.add_argument('--state', default='active', choices=['active', 'inactive', 'all'], 
                        help='Filter hosts by state (default: active)')
    parser.add_argument('--timeout', type=int, default=120, help='API request timeout in seconds (default: 120)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retry attempts (default: 3)')
    return parser.parse_args()

def get_all_hosts(token_data, config, page_size=100, state='active', timeout=120, max_retries=3):
    """
    Retrieve all hosts from the Vectra API, handling pagination
    
    Args:
        token_data (dict): Authentication token data
        config (dict): Configuration data
        page_size (int): Number of hosts per page
        state (str): Filter hosts by state ('active', 'inactive', or 'all')
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts for failed requests
    
    Returns:
        list: All host records
    """
    all_hosts = []
    page = 1
    next_url = None
    
    # Prepare query parameters
    params = {'page_size': page_size}
    if state != 'all':
        params['state'] = state
    
    # Make sure we're using the v3.4 API endpoint
    endpoint = 'api/v3.4/hosts'
    
    while True:
        if next_url:
            # Parse the next URL to get the page number
            parsed_url = urlparse(next_url)
            query_params = parse_qs(parsed_url.query)
            if 'page' in query_params:
                params['page'] = query_params['page'][0]
        
        # Try the request with retries
        response = None
        retries = 0
        while retries <= max_retries:
            if retries > 0:
                print_warning(f"Retry attempt {retries}/{max_retries} for page {page}...")
                # Exponential backoff between retries
                time.sleep(2 ** retries)
            
            print_info(f"Retrieving hosts (page {page})...")
            response = make_api_request(endpoint, token_data, params=params, config=config, timeout=timeout)
            
            # Success or non-timeout error, no need to retry
            if response and response.status_code != 504:
                break
                
            retries += 1
        
        if not response or response.status_code != 200:
            error_msg = f"Failed to retrieve hosts on page {page} after {max_retries} retry attempts"
            if response:
                error_msg += f": {response.status_code} - {response.text}"
            print_error(error_msg)
            break
        
        data = response.json()
        hosts = data.get('results', [])
        all_hosts.extend(hosts)
        
        print_success(f"Retrieved {len(hosts)} hosts from page {page}")
        
        # Check if there's a next page
        next_url = data.get('next')
        if not next_url:
            break
        
        page += 1
        
        # Add a small delay between requests to avoid overwhelming the API
        time.sleep(1)
    
    return all_hosts

def extract_host_data(host):
    """
    Extract relevant fields from a host record
    
    Args:
        host (dict): Host record from the API
    
    Returns:
        dict: Extracted host data
    """
    # Extract host_artifact_set details
    artifact_details = []
    for artifact in host.get('host_artifact_set', []):
        artifact_type = artifact.get('type', 'Unknown')
        value = artifact.get('value', 'Unknown')
        artifact_details.append(f"{artifact_type}:{value}")
    
    # Handle cases where fields might be missing
    return {
        'id': host.get('id', ''),
        'name': host.get('name', ''),
        'sensor': host.get('sensor_name', host.get('sensor', '')),
        'last_source': host.get('last_source', ''),
        'ip_address': host.get('ip', ''),
        'state': host.get('state', ''),
        'last_modified': host.get('last_modified', ''),
        'last_detection_timestamp': host.get('last_detection_timestamp', ''),
        'threat': host.get('threat', 0),
        'certainty': host.get('certainty', 0),
        'privilege_level': host.get('privilege_level', ''),
        'privilege_category': host.get('privilege_category', ''),
        'host_artifact_set': '; '.join(artifact_details),
        'tags': ', '.join(host.get('tags', []))
    }

def write_to_csv(hosts_data, filename):
    """
    Write hosts data to a CSV file
    
    Args:
        hosts_data (list): List of host data dictionaries
        filename (str): Output file name
    """
    if not hosts_data:
        print_error("No host data to write")
        return
    
    fieldnames = [
        'id', 'name', 'sensor', 'last_source', 'ip_address', 'state',
        'last_modified', 'last_detection_timestamp', 'threat', 'certainty',
        'privilege_level', 'privilege_category', 'host_artifact_set', 'tags'
    ]
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for host in hosts_data:
                writer.writerow(host)
        
        print_success(f"Successfully wrote {len(hosts_data)} hosts to {filename}")
    except Exception as e:
        print_error(f"Error writing to CSV file: {str(e)}")

def main():
    """Main function"""
    args = parse_arguments()
    
    # Generate output filename if not provided
    if not args.output:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        args.output = f"active_hosts-{timestr}.csv"
    
    # Get authentication token
    print_info("Authenticating to Vectra API...")
    token_data = get_token(env_file=args.env_file)
    if not token_data:
        sys.exit("Authentication failed. Check your credentials.")
    
    # Load configuration from the same environment file
    from vectra_auth import load_config
    config = load_config(args.env_file)
    
    # Get all hosts with timeout parameter
    hosts = get_all_hosts(token_data, config, args.page_size, args.state, 
                         timeout=args.timeout, max_retries=args.max_retries)
    print_info(f"Retrieved {len(hosts)} hosts total")
    
    # Process host data
    host_data = [extract_host_data(host) for host in hosts]
    
    # Write to CSV
    write_to_csv(host_data, args.output)

if __name__ == "__main__":
    main()
