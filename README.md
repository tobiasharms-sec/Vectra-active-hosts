# Vectra Active Hosts Script

A Python script for retrieving and exporting active hosts from the Vectra RUX Platform using the Vectra API v3.4.

## Features

- **OAuth2 Authentication**: Secure authentication with automatic token management and refresh
- **Flexible Host Filtering**: Filter hosts by state (active, inactive, or all)
- **Pagination Support**: Handles large datasets with configurable page sizes
- **CSV Export**: Exports host data to CSV format with customizable filenames
- **Robust Error Handling**: Includes retry logic and timeout handling
- **Colored Output**: Easy-to-read terminal output with color-coded status messages
- **Token Caching**: Saves and reuses authentication tokens to minimize API calls

## Requirements

- Python 3.6+
- Required Python packages:
  - `requests`
  - `python-dotenv`
  - `colorama`

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd vectra-active-hosts
```

2. Install required dependencies:
```bash
pip install requests python-dotenv colorama
```

## Configuration

1. Create a `cred.env` file in the same directory as the script:
```env
CLIENT_ID=your_vectra_client_id
CLIENT_SECRET=your_vectra_client_secret
VECTRA_URL=https://your-vectra-instance.com/
```

2. Ensure your Vectra API credentials have the necessary permissions to read host data.

## Usage

### Basic Usage

Retrieve all active hosts and export to CSV:
```bash
python3 active_hosts_rux.py
```

### Advanced Usage

```bash
# Specify custom output file
python3 active_hosts_rux.py --output my_hosts.csv

# Retrieve inactive hosts
python3 active_hosts_rux.py --state inactive

# Retrieve all hosts (active and inactive)
python3 active_hosts_rux.py --state all

# Custom page size and timeout
python3 active_hosts_rux.py --page-size 500 --timeout 180

# Use different environment file
python3 active_hosts_rux.py --env-file production.env
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--env-file` | Path to environment file with credentials | `cred.env` |
| `--output` | Output CSV filename | `active_hosts-TIMESTAMP.csv` |
| `--page-size` | Number of hosts per page (max: 5000) | `100` |
| `--state` | Filter hosts by state: `active`, `inactive`, `all` | `active` |
| `--timeout` | API request timeout in seconds | `120` |
| `--max-retries` | Maximum retry attempts for failed requests | `3` |

## Output Format

The script exports the following host information to CSV:

| Field | Description |
|-------|-------------|
| `id` | Unique host identifier |
| `name` | Host name |
| `sensor` | Associated sensor name |
| `last_source` | Last detection source |
| `ip_address` | Host IP address |
| `state` | Host state (active/inactive) |
| `last_modified` | Last modification timestamp |
| `last_detection_timestamp` | Last detection timestamp |
| `threat` | Threat score |
| `certainty` | Certainty score |
| `privilege_level` | Host privilege level |
| `privilege_category` | Host privilege category |
| `host_artifact_set` | Associated artifacts (semicolon-separated) |
| `tags` | Host tags (comma-separated) |

## Authentication Module

The `vectra_auth.py` module provides:

- **Token Management**: Automatic token acquisition, caching, and refresh
- **API Request Wrapper**: Simplified API request handling with error management
- **Configuration Loading**: Environment variable loading and validation
- **Colored Output**: Utility functions for formatted terminal output

### Using the Authentication Module

```python
from vectra_auth import get_token, make_api_request

# Get authentication token
token_data = get_token()

# Make API request
response = make_api_request('api/v3.4/hosts', token_data)
```

## Error Handling

The script includes comprehensive error handling:

- **Authentication Errors**: Clear messages for credential issues
- **API Timeouts**: Configurable timeouts with retry logic
- **Rate Limiting**: Automatic delays between requests
- **Network Issues**: Exponential backoff for failed requests
- **Data Validation**: Handles missing or malformed API responses

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your `CLIENT_ID` and `CLIENT_SECRET` in the environment file
   - Ensure the Vectra URL is correct and accessible
   - Check that your API credentials have the necessary permissions

2. **Timeout Errors**
   - Increase the `--timeout` value for slower networks
   - Reduce `--page-size` to handle smaller chunks of data

3. **Missing Dependencies**
   - Install required packages: `pip install requests python-dotenv colorama`

4. **Empty Results**
   - Verify the `--state` parameter matches your expected host states
   - Check that hosts exist in your Vectra instance

### Debug Information

The script provides detailed logging information:
- Authentication status
- API request progress
- Pagination information
- Error messages with status codes

## File Structure

```
vectra-active-hosts/
├── active_hosts_rux.py    # Main script
├── vectra_auth.py         # Authentication module
├── cred.env              # Environment configuration (create this)
├── README.md             # This file
└── requirements.txt      # Python dependencies (optional)
```

## Security Notes

- Keep your `cred.env` file secure and never commit it to version control
- The script automatically manages token refresh to maintain security
- API tokens are cached locally in `vectra_token.json` (excluded from git)
- Use appropriate file permissions for credential files

## License

This project is provided as-is for educational and operational purposes. Please ensure compliance with your organization's security policies and Vectra's terms of service.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this script.

## Author

**Tobias Harms**

## Support

For issues related to:
- **Script functionality**: Open an issue in this repository
- **Vectra API**: Consult the official Vectra API documentation
- **Authentication**: Check your Vectra platform permissions and API credentials
