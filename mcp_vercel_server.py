#!/usr/bin/env python3
"""
Vercel MCP Server

This server implements the Model Context Protocol (MCP) to allow AI systems
to interact with Vercel Operations.
"""
import sys
import datetime
import os
import socket
import threading
import json
import subprocess
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from fastmcp import FastMCP
import time
import requests

# Initialize FastMCP server for tool registration
mcp = FastMCP("Vercel CLI Explorer", log_level="DEBUG")

# Server configuration
HOST = "0.0.0.0"
PORT = 8002  # Using a different port than other MCP servers

# Vercel configuration
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")

# Add this function after initializing the mcp object
def get_registered_tools():
    """Get a list of registered tool names"""
    # This is a workaround since FastMCP doesn't expose tools directly
    tools = []
    
    # Debug output to help diagnose the issue
    print("\n=== TOOL DISCOVERY ===")
    print("Looking for registered tools...")
    
    # First try to find tools by examining function attributes
    for name, func in globals().items():
        if callable(func):
            print(f"Checking function: {name}")
            
            # Check if this is a tool function
            is_tool = False
            tool_attrs = []
            
            # Check for various MCP-related attributes
            for attr_name in dir(func):
                if attr_name.startswith('__mcp') or 'mcp' in attr_name.lower():
                    tool_attrs.append(attr_name)
                    is_tool = True
            
            if tool_attrs:
                print(f"  Found MCP-related attributes: {', '.join(tool_attrs)}")
            
            # Also check for known tool names
            known_tools = [
                'list_projects', 'list_deployments', 'get_project_info', 
                'check_server_status', 'set_vercel_token', 'list_project_domains',
                'list_environment_variables', 'get_user_info', 'list_deployment_aliases'
            ]
            
            if name in known_tools:
                print(f"  Recognized as known tool by name")
                is_tool = True
            
            if is_tool:
                tools.append(name)
                print(f"  ✓ Added tool: {name}")
    
    # If we still don't find any tools, use hardcoded list
    if not tools:
        print("No tools found via function inspection, using hardcoded list")
        tools = [
            'list_projects', 'list_deployments', 'get_project_info', 
            'check_server_status', 'set_vercel_token', 'list_project_domains',
            'list_environment_variables', 'get_user_info', 'list_deployment_aliases'
        ]
        for tool in tools:
            print(f"  ✓ Added hardcoded tool: {tool}")
    
    print(f"Total tools discovered: {len(tools)}")
    return tools

# Add this method to the FastMCP class
mcp.get_registered_tools = get_registered_tools

def run_vercel_command(command_args):
    """Run a Vercel API request and return the output"""
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Map CLI commands to API endpoints
        if command_args[0] == "ls" or (len(command_args) >= 2 and command_args[0] == "project" and command_args[1] == "ls"):
            # List projects
            endpoint = "/v9/projects"
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
        elif command_args[0] == "list":
            # List deployments
            endpoint = "/v6/deployments"
            params = {}
            
            # Handle project filter
            if len(command_args) > 1 and command_args[1] not in ["--limit"]:
                params["name"] = command_args[1]
            
            # Handle limit
            if "--limit" in command_args:
                limit_index = command_args.index("--limit")
                if limit_index + 1 < len(command_args):
                    params["limit"] = command_args[limit_index + 1]
            
            response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
        else:
            return {
                "status": "error",
                "message": f"Unsupported command: {' '.join(command_args)}",
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def list_projects():
    """List all Vercel projects in your account"""
    print(f"Tool call: list_projects at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    # Run the command without --json flag
    # The command is 'vercel ls' not 'vercel list'
    return run_vercel_command(["ls"])

@mcp.tool()
def list_deployments(project_id=None, limit=5):
    """
    List recent deployments for a project
    
    Args:
        project_id: Project ID (optional)
        limit: Maximum number of deployments to show (default: 5)
    """
    print(f"Tool call: list_deployments for project_id: {project_id} at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get deployments
        endpoint = "/v6/deployments"
        params = {}
        
        if project_id:
            params["projectId"] = project_id
        
        if limit:
            params["limit"] = limit
        
        response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def get_project_info(project_id):
    """Get detailed information about a specific Vercel project by ID"""
    print(f"Tool call: get_project_info at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get specific project by ID
        endpoint = f"/v9/projects/{project_id}"
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def set_vercel_token(token):
    """
    Set the Vercel API token for this server session
    
    Args:
        token: Your Vercel API token
    """
    global VERCEL_TOKEN
    
    print(f"Tool call: set_vercel_token at {datetime.datetime.now()}")
    
    # Update the global variable
    VERCEL_TOKEN = token
    
    # Log the update (mask the token for security)
    masked_token = token[:4] + "****" + token[-4:] if len(token) > 8 else "****"
    print(f"Vercel token updated: {masked_token}")
    
    return {
        "status": "success",
        "message": "Vercel token updated successfully",
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.tool()
def check_server_status():
    """Check the status of the MCP Vercel CLI server"""
    print(f"Tool call: check_server_status at {datetime.datetime.now()}")
    
    # Check if Vercel CLI is installed
    try:
        result = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
        vercel_installed = result.returncode == 0
        vercel_version = result.stdout.strip() if vercel_installed else "Not installed"
    except Exception:
        vercel_installed = False
        vercel_version = "Not installed"
    
    # Check if token is configured
    token_configured = bool(VERCEL_TOKEN)
    
    return {
        "status": "online",
        "server_name": "MCP Vercel CLI Server",
        "version": "1.0.0",
        "vercel_cli_installed": vercel_installed,
        "vercel_cli_version": vercel_version,
        "vercel_token_configured": token_configured,
        "pid": os.getpid(),
        "timestamp": datetime.datetime.now().isoformat()
    }

@mcp.tool()
def list_project_domains(project_id):
    """List all domains associated with a specific Vercel project"""
    print(f"Tool call: list_project_domains at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get domains for specific project
        endpoint = f"/v9/projects/{project_id}/domains"
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def list_environment_variables(project_id):
    """List all environment variables for a specific Vercel project"""
    print(f"Tool call: list_environment_variables at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get environment variables for specific project
        endpoint = f"/v9/projects/{project_id}/env"
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def get_user_info():
    """Get information about the authenticated Vercel user"""
    print(f"Tool call: get_user_info at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get user information
        endpoint = "/v2/user"
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def list_deployment_aliases(deployment_id):
    """List all aliases for a specific Vercel deployment"""
    print(f"Tool call: list_deployment_aliases at {datetime.datetime.now()}")
    
    # Validate Vercel token
    if not VERCEL_TOKEN:
        return {
            "status": "error",
            "message": "Vercel token not configured. Please set the VERCEL_TOKEN environment variable.",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    try:
        # Base Vercel API URL
        base_url = "https://api.vercel.com"
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get aliases for specific deployment
        endpoint = f"/v2/deployments/{deployment_id}/aliases"
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        # Process the response
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"API request failed with status code {response.status_code}",
                "error": response.text,
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error calling Vercel API: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

# Create a custom HTTP request handler for MCP
class MCPHTTPHandler(BaseHTTPRequestHandler):
    # Add server version and protocol headers
    server_version = "MCPVercelServer/1.0"
    protocol_version = "HTTP/1.1"
    
    def log_message(self, format, *args):
        """Log messages to stdout"""
        print(f"{self.address_string()} - {format % args}")
    
    def _set_headers(self, content_type="application/json"):
        """Set response headers"""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', '0')
        self.end_headers()
    
    def _send_json_response(self, data):
        """Send a JSON response with proper headers"""
        # Format the JSON with indentation for better readability
        response = json.dumps(data, indent=2)
        response_bytes = response.encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        
        print(f"Sending JSON response:")
        print(json.dumps(data, indent=2))  # Pretty print the JSON in server logs
        self.wfile.write(response_bytes)
    
    def _handle_error(self, status_code, message):
        """Handle error responses"""
        error_data = {"error": message}
        error_json = json.dumps(error_data).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', str(len(error_json)))
        self.end_headers()
        
        self.wfile.write(error_json)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"Received GET request: {self.path}")
        
        if self.path == "/tools":
            # List available tools
            print(f"MCP tool discovery request received at {datetime.datetime.now()}")
            tools_list = []
            
            # Get the list of registered tools
            registered_tools = get_registered_tools()
            
            for tool_name in registered_tools:
                # Get the function object if possible
                tool_func = globals().get(tool_name)
                
                # Get the description from the docstring if available
                description = "No description available"
                if tool_func and tool_func.__doc__:
                    description = tool_func.__doc__.strip()
                
                tools_list.append({
                    "name": tool_name,
                    "description": description
                })
            
            self._send_json_response(tools_list)
        elif self.path == "/":
            # Root path - send a simple welcome message
            welcome_data = {
                "name": "MCP Vercel CLI Server",
                "version": "1.0.0",
                "description": "A server that implements the Model Context Protocol for Vercel CLI operations",
                "status": "running"
            }
            self._send_json_response(welcome_data)
        else:
            # Unknown path
            self._handle_error(404, f"Not found: {self.path}")
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"Received POST request: {self.path}")
        
        # Check if this is a tool call
        if self.path.startswith("/tools/"):
            tool_name = self.path[7:]  # Remove "/tools/" prefix
            print(f"Calling tool: {tool_name}")
            
            # Read request body
            content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse parameters
            params = {}
            if post_data:
                try:
                    params = json.loads(post_data)
                except json.JSONDecodeError:
                    self._handle_error(400, "Invalid JSON in request body")
                    return
            
            # Get the tool function
            tool_func = globals().get(tool_name)
            if not tool_func or not callable(tool_func):
                self._handle_error(404, f"Tool '{tool_name}' not found")
                return
            
            # Call the tool
            try:
                print(f"Calling tool: {tool_name} with params: {params}")
                result = tool_func(**params)
                self._send_json_response(result)
            except Exception as e:
                print(f"Error calling tool {tool_name}: {str(e)}")
                self._handle_error(500, f"Error calling tool: {str(e)}")
        else:
            # Unknown path
            self._handle_error(404, f"Not found: {self.path}")

def check_port_in_use(host, port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def main():
    """Main function to start the MCP server"""
    print(f"Starting MCP Vercel CLI Server v1.0.0...")
    print("This server implements the Model Context Protocol for Vercel CLI operations.")
    print(f"Server PID: {os.getpid()}")
    
    # Check Vercel CLI installation
    try:
        result = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n✓ Vercel CLI installed: {result.stdout.strip()}")
        else:
            print("\n⚠️ WARNING: Vercel CLI not found or not working correctly!")
            print("Please install Vercel CLI with: npm i -g vercel")
            print("Error:", result.stderr)
    except Exception as e:
        print("\n⚠️ WARNING: Could not check Vercel CLI installation!")
        print(f"Error: {str(e)}")
        print("Please install Vercel CLI with: npm i -g vercel")
    
    # Check Vercel token
    if not VERCEL_TOKEN:
        print("\n⚠️ WARNING: Vercel token not configured!")
        print("Please set the VERCEL_TOKEN environment variable.")
        print("You can get a token from https://vercel.com/account/tokens")
        print("\nThe server will start, but API calls will fail until a token is configured.")
    else:
        print("\n✓ Vercel token configured.")
    
    # Check if port is already in use
    if check_port_in_use(HOST, PORT):
        print(f"WARNING: Port {PORT} is already in use. The server may not start correctly.")
        # Try to kill the process using the port
        try:
            print("Attempting to free the port...")
            if sys.platform.startswith('linux'):
                os.system(f"fuser -k {PORT}/tcp")
                print(f"Killed process using port {PORT}")
            else:
                print("Automatic port freeing only supported on Linux")
        except Exception as e:
            print(f"Error freeing port: {e}")
    
    print(f"Binding to {HOST}:{PORT}...")
    
    try:
        # Create and start HTTP server
        server = HTTPServer((HOST, PORT), MCPHTTPHandler)
        print(f"Server started at http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        # Start the server in a separate thread to avoid blocking
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Print a message every 10 seconds to show the server is still running
        try:
            while True:
                time.sleep(10)
                print(f"Server running at http://{HOST}:{PORT} (PID: {os.getpid()})")
        except KeyboardInterrupt:
            print("Server stopped by user")
            server.shutdown()
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 