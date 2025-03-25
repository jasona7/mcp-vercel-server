#!/usr/bin/env python3
"""
MCP Vercel HTTP Client

This client connects to the MCP Vercel Server using HTTP.
It provides a terminal interface for interacting with Vercel API operations.
"""
import sys
import requests
import json
import socket
import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
import time
import os

# Server address
SERVER_HOST = "127.0.0.1"  # Use IP address instead of hostname
SERVER_PORT = 8002  # Match the port in the server
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

console = Console()

def call_tool(tool_name, params=None):
    """
    Calls a tool on the MCP server using HTTP.
    
    Args:
        tool_name: The name of the tool to call
        params: A dictionary of parameters to pass to the tool
    
    Returns:
        The response from the server, or None on error
    """
    try:
        if params is None:
            params = {}
        
        url = f"{BASE_URL}/tools/{tool_name}"
        console.print(f"[dim]DEBUG: Calling {url} with params {json.dumps(params)}[/dim]")
        response = requests.post(url, json=params, timeout=10)
        
        if response.status_code == 200:
            if not response.text:
                console.print("[bold red]Error: Server returned empty response[/bold red]")
                return None
            try:
                return response.json()
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Invalid JSON response: {response.text}[/bold red]")
                return None
        else:
            console.print(f"[bold red]Error: Server returned status code {response.status_code}[/bold red]")
            console.print(f"Response: {response.text}")
            return None
    except requests.RequestException as e:
        console.print(f"[bold red]Request error: {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        return None

def list_tools():
    """Lists all available tools on the server"""
    try:
        # First verify the server is running with a simple request
        if not check_server_running():
            console.print("[bold red]Server is not responding to basic requests[/bold red]")
            return None
            
        url = f"{BASE_URL}/tools"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Invalid JSON response from /tools endpoint[/bold red]")
                return None
        else:
            console.print(f"[bold red]Error: Server returned status code {response.status_code} for /tools endpoint[/bold red]")
            return None
    except requests.RequestException as e:
        console.print(f"[bold red]Request error when listing tools: {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred when listing tools: {e}[/bold red]")
        return None

def check_server_running():
    """Check if the server is running and responding"""
    try:
        response = requests.get(f"{BASE_URL}/tools", timeout=2)
        return response.status_code == 200
    except:
        return False

def select_project():
    """Presents a list of projects for the user to select from"""
    console.print("[yellow]Fetching projects list...[/yellow]")
    response = call_tool("list_projects")
    
    if not response or response.get("status") != "success":
        console.print("[bold red]Failed to fetch projects list[/bold red]")
        return None
    
    projects = response.get("data", {}).get("projects", [])
    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return None
    
    # Create a table to display projects
    table = Table(title="Available Projects")
    table.add_column("#", style="dim")
    table.add_column("Name", style="green")
    table.add_column("ID", style="blue")
    table.add_column("Framework", style="cyan")
    
    # Add projects to the table
    for i, project in enumerate(projects, 1):
        table.add_row(
            str(i),
            project.get("name", "Unknown"),
            project.get("id", "Unknown"),
            project.get("framework", "Unknown")
        )
    
    console.print(table)
    
    # Let user select a project
    choice = Prompt.ask(
        "[bold]Select a project by number[/bold]",
        default="1",
        choices=[str(i) for i in range(1, len(projects) + 1)]
    )
    
    selected_project = projects[int(choice) - 1]
    console.print(f"[green]Selected project: {selected_project.get('name')} ({selected_project.get('id')})[/green]")
    return selected_project

def select_deployment(project_id=None):
    """Presents a list of deployments for the user to select from"""
    params = {"limit": 10}
    if project_id:
        params["project_id"] = project_id
    
    console.print("[yellow]Fetching deployments list...[/yellow]")
    response = call_tool("list_deployments", params)
    
    if not response or response.get("status") != "success":
        console.print("[bold red]Failed to fetch deployments list[/bold red]")
        return None
    
    deployments = response.get("data", {}).get("deployments", [])
    if not deployments:
        console.print("[yellow]No deployments found[/yellow]")
        return None
    
    # Create a table to display deployments
    table = Table(title="Available Deployments")
    table.add_column("#", style="dim")
    table.add_column("URL", style="green")
    table.add_column("ID", style="blue")
    table.add_column("State", style="cyan")
    table.add_column("Created", style="magenta")
    
    # Add deployments to the table
    for i, deployment in enumerate(deployments, 1):
        created_at = deployment.get("created", "Unknown")
        # Format the date if it's a timestamp
        if isinstance(created_at, int):
            created_at = datetime.datetime.fromtimestamp(created_at/1000).strftime('%Y-%m-%d %H:%M')
        
        table.add_row(
            str(i),
            deployment.get("url", "Unknown"),
            deployment.get("id", "Unknown"),
            deployment.get("state", "Unknown"),
            str(created_at)
        )
    
    console.print(table)
    
    # Let user select a deployment
    choice = Prompt.ask(
        "[bold]Select a deployment by number[/bold]",
        default="1",
        choices=[str(i) for i in range(1, len(deployments) + 1)]
    )
    
    selected_deployment = deployments[int(choice) - 1]
    console.print(f"[green]Selected deployment: {selected_deployment.get('url')} ({selected_deployment.get('id')})[/green]")
    return selected_deployment

def main():
    """Main function for the MCP Vercel Explorer client"""
    console.print(Panel.fit(
        "[bold]MCP Vercel Explorer[/bold]\nA terminal UI for interacting with Vercel API operations",
        border_style="blue"
    ))
    
    # Check if server is running
    if not check_server_running():
        console.print("[bold red]Server not running![/bold red]")
        console.print("Please start the server with: python mcp_vercel_server.py")
        return 1
    
    # Get available tools
    tools_info = list_tools()
    if tools_info is None:
        console.print("[bold red]Could not retrieve tools list from server![/bold red]")
        return 1
    
    # Display available tools
    if isinstance(tools_info, list):
        console.print(f"[green]Connected to server. {len(tools_info)} tools available.[/green]")
    elif isinstance(tools_info, dict) and 'tools' in tools_info:
        console.print(f"[green]Connected to server. {len(tools_info.get('tools', []))} tools available.[/green]")
    else:
        console.print("[yellow]Connected to server but received unexpected tools format.[/yellow]")
    
    # Main menu loop
    debug_mode = False
    while True:
        console.print("\n[bold]Available Actions:[/bold]")
        console.print("1. List Projects")
        console.print("2. List Deployments")
        console.print("3. Get Project Info")
        console.print("4. List Project Domains")
        console.print("5. List Environment Variables")
        console.print("6. Get User Info")
        console.print("7. List Deployment Aliases")
        console.print("8. Check Server Status")
        console.print("9. Exit")
        console.print("10. Toggle Debug Mode")
        
        choice = Prompt.ask("[bold]Choose an option[/bold]", default="1")

        if choice == "1":
            console.print("[yellow]Listing projects...[/yellow]")
            response = call_tool("list_projects")
            if response:
                console.print("[bold]JSON Response:[/bold]")
                console.print_json(json.dumps(response, indent=2))
            else:
                console.print("[yellow]No projects found or error occurred.[/yellow]")
                
        elif choice == "2":
            # Let user select a project first (optional)
            use_project = Prompt.ask(
                "[yellow]Filter by project?[/yellow]", 
                choices=["y", "n"], 
                default="n"
            ) == "y"
            
            project_id = None
            if use_project:
                project = select_project()
                if project:
                    project_id = project.get("id")
            
            limit = Prompt.ask("[yellow]Enter limit[/yellow]", default="5")
            
            params = {"limit": int(limit)}
            if project_id:
                params["project_id"] = project_id
                
            console.print(f"[yellow]Listing deployments...[/yellow]")
            response = call_tool("list_deployments", params)
            if response:
                console.print("[bold]JSON Response:[/bold]")
                console.print_json(json.dumps(response, indent=2))
            else:
                console.print("[yellow]No deployments found or error occurred.[/yellow]")
                
        elif choice == "3":
            project = select_project()
            if project:
                project_id = project.get("id")
                console.print(f"[yellow]Getting project info for {project.get('name')}...[/yellow]")
                response = call_tool("get_project_info", {"project_id": project_id})
                if response:
                    console.print("[bold]JSON Response:[/bold]")
                    console.print_json(json.dumps(response, indent=2))
                else:
                    console.print("[yellow]Project not found or error occurred.[/yellow]")
                
        elif choice == "4":
            project = select_project()
            if project:
                project_id = project.get("id")
                console.print(f"[yellow]Listing domains for project {project.get('name')}...[/yellow]")
                response = call_tool("list_project_domains", {"project_id": project_id})
                if response:
                    console.print("[bold]JSON Response:[/bold]")
                    console.print_json(json.dumps(response, indent=2))
                else:
                    console.print("[yellow]No domains found or error occurred.[/yellow]")
                
        elif choice == "5":
            project = select_project()
            if project:
                project_id = project.get("id")
                console.print(f"[yellow]Listing environment variables for project {project.get('name')}...[/yellow]")
                response = call_tool("list_environment_variables", {"project_id": project_id})
                if response:
                    console.print("[bold]JSON Response:[/bold]")
                    console.print_json(json.dumps(response, indent=2))
                else:
                    console.print("[yellow]No environment variables found or error occurred.[/yellow]")
                
        elif choice == "6":
            console.print("[yellow]Getting user info...[/yellow]")
            response = call_tool("get_user_info")
            if response:
                console.print("[bold]JSON Response:[/bold]")
                console.print_json(json.dumps(response, indent=2))
            else:
                console.print("[yellow]User info not found or error occurred.[/yellow]")
                
        elif choice == "7":
            deployment = select_deployment()
            if deployment:
                deployment_id = deployment.get("id")
                console.print(f"[yellow]Listing aliases for deployment {deployment.get('url')}...[/yellow]")
                response = call_tool("list_deployment_aliases", {"deployment_id": deployment_id})
                if response:
                    console.print("[bold]JSON Response:[/bold]")
                    console.print_json(json.dumps(response, indent=2))
                else:
                    console.print("[yellow]No aliases found or error occurred.[/yellow]")
                
        elif choice == "8":
            console.print("[yellow]Checking server status...[/yellow]")
            response = call_tool("check_server_status")
            if response:
                console.print("[bold]JSON Response:[/bold]")
                console.print_json(json.dumps(response, indent=2))
            else:
                console.print("[yellow]Could not retrieve server status.[/yellow]")

        elif choice == "9":
            console.print("[bold green]Exiting MCP Vercel Explorer. Goodbye![/bold green]")
            break

        elif choice == "10":
            debug_mode = not debug_mode
            console.print(f"[yellow]Debug mode {'enabled' if debug_mode else 'disabled'}[/yellow]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 