# Vercel API Explorer

A Python-based tool for interacting with the Vercel API via a Model Context Protocol (MCP) implementation that can be extended to allow AI systems and humans to interact with Vercel's API in a structured way.

## Features

- **REST API Integration**: Directly communicates with Vercel's REST API
- **Interactive Client**: Terminal-based UI for exploring Vercel resources
- **AI-Friendly Interface**: Designed to work with AI assistants through the MCP protocol

## Available Tools

- List all Vercel projects
- List deployments with filtering options
- Get detailed project information
- List project domains
- List environment variables
- Get user account information
- List deployment aliases
- Check server status

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/jasona7/mcp-vercel-server.git
   cd mcp-vercel-server
   ```

2. Install dependencies:
   ```
   pip install requests rich fastmcp
   ```

3. Set your Vercel API token:
   ```
   export VERCEL_TOKEN=your_vercel_token
   ```

## Usage

### Starting the Server

```python mcp_vercel_server.py
```
### Using the MCP Client

```python mcp_vercel_client.py
```

    ╭──────────────────────────────────────────────────────────╮
    │ MCP Vercel Explorer                                      │
    │ A terminal UI for interacting with Vercel API operations │
    ╰──────────────────────────────────────────────────────────╯
    Connected to server. 9 tools available.

    Available Actions:
    1. List Projects
    2. List Deployments
    3. Get Project Info
    4. List Project Domains
    5. List Environment Variables
    6. Get User Info
    7. List Deployment Aliases
    8. Check Server Status
    9. Exit
    10. Toggle Debug Mode

    Enter the number of the action you want to perform: 8

    JSON Response:
        {
        "status": "online",
        "server_name": "MCP Vercel CLI Server",
        "version": "1.0.0",
        "vercel_cli_installed": true,
        "vercel_cli_version": "33.0.2",
        "vercel_token_configured": true,
        "pid": 1108902,
        "timestamp": "2025-03-25T17:24:21.471169"
        }

    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
