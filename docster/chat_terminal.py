import requests
import json
import threading
import time
import re
import inspect

# LLM configuration (adjust as needed)
llm_config = {
    "model": "llama3.2:latest",  # Ensure this model is available in `ollama list`
    "base_url": "http://localhost:11434"  # Ensure Ollama is running at this address
}

# Bridge service configuration (assumes the bridge is running on localhost:8000)
BRIDGE_BASE_URL = "http://127.0.0.1:8000/api"

# Global conversation history: a list of messages (each with a role and content)
conversation_history = []

# Seed the conversation with a detailed system prompt.
system_message = (
    "You are a professional Kubernetes Cluster Doctor with advanced diagnostic capabilities. "
    "Your job is to accurately diagnose Kubernetes issues by calling the correct tools and gathering real-time information. "
    "When a user asks about pod status, cluster health, or any Kubernetes issue, you MUST always use a function call to fetch real data first.\n\n"
    
    "⚠️ IMPORTANT RULES: \n"
    "- You MUST NOT assume information. Always fetch real data first.\n"
    "- When generating function calls, ALWAYS use a **valid JSON list** format: \n"
    "[{\"function_call\": {\"name\": \"describe_pod_api\", \"arguments\": {\"pod_name\": \"backend-pod\", \"namespace\": \"default\"}}},\n"
    " {\"function_call\": {\"name\": \"get_logs_api\", \"arguments\": {\"pod_name\": \"backend-pod\", \"namespace\": \"default\", \"since_time\": \"5m\", \"tail_lines\": 100}}}]\n"
    "- NEVER return malformed JSON (e.g., no `;`, no missing brackets `{ }`).\n\n"
    
    "### Available Functions:\n"
    "1️⃣ `describe_pod_api(pod_name, namespace)`: Fetches pod details.\n"
    "2️⃣ `get_logs_api(pod_name, namespace, since_time, tail_lines)`: Fetches logs.\n"
    "3️⃣ `get_events_api(namespace, since_time)`: Retrieves recent cluster events.\n"
    "4️⃣ `get_service_info_api(service_name, namespace)`: Gets service details.\n"
    "5️⃣ `describe_cluster_api()`: Gets an overall cluster report.\n\n"
    
    "🔥 Example of a correct response: \n"
    "[{\"function_call\": {\"name\": \"describe_pod_api\", \"arguments\": {\"pod_name\": \"backend-deployment\", \"namespace\": \"default\"}}}]\n\n"

    
    "Once you receive the actual pod data, you can analyze it and provide a diagnosis.\n\n"
    
    "format below. Use the available tools as needed to gather detailed data and then provide an analysis based on that data.\n\n"
    "Format for a function call (must be valid JSON):\n"
    "{\"function_call\": {\"name\": \"<tool_function>\", \"arguments\": {\"arg1\": \"value1\", ...}}}\n\n"
    "Available tool functions with detailed descriptions:\n\n"
    "1. get_logs_api(pod_name, namespace, since_time, tail_lines):\n"
    "   - What it does: Fetches logs from a specific pod.\n"
    "   - When to use: When you suspect issues with a particular pod's behavior (e.g., CrashLoopBackOff).\n"
    "   - Parameters:\n"
    "       • pod_name: The name of the pod. (Required.)\n"
    "       • namespace: The Kubernetes namespace. Defaults to \"default\" if not provided.\n"
    "       • since_time: The time window for logs (e.g., \"5m\" for last 5 minutes).\n"
    "       • tail_lines: How many log lines to return from the end of the log.\n"
    "   - Caveats: Returns an error if the pod is not running or image pulling fails.\n\n"
    "2. describe_pod_api(pod_name, namespace):\n"
    "   - What it does: Retrieves a detailed description of the specified pod (similar to 'kubectl describe pod').\n"
    "   - When to use: To get insights into why a pod might be failing or to inspect its configuration.\n"
    "   - Parameters:\n"
    "       • pod_name: The name of the pod. (Required.)\n"
    "       • namespace: The Kubernetes namespace. Defaults to \"default\" if not provided.\n"
    "   - Caveats: May return a lot of information; useful for debugging scheduling or configuration issues.\n\n"
    "3. get_events_api(namespace, since_time):\n"
    "   - What it does: Retrieves recent events for a specified namespace.\n"
    "   - When to use: To check for cluster-wide issues such as failed scheduling or errors.\n"
    "   - Parameters:\n"
    "       • namespace: The Kubernetes namespace. Defaults to \"default\" if not provided.\n"
    "       • since_time: Optional time filter (e.g., \"10m\") for events.\n"
    "   - Caveats: If no events are found, returns a message stating that; errors may occur if events cannot be fetched.\n\n"
    "4. get_service_info_api(service_name, namespace):\n"
    "   - What it does: Fetches details of a Kubernetes service.\n"
    "   - When to use: To diagnose issues with service exposure or connectivity.\n"
    "   - Parameters:\n"
    "       • service_name: The name of the service. (Required.)\n"
    "       • namespace: The Kubernetes namespace. Defaults to \"default\" if not provided.\n"
    "   - Caveats: Returns the service details in YAML format; may not include dynamic health status.\n\n"
    "5. describe_cluster_api():\n"
    "   - What it does: Synthesizes an overall cluster status report by aggregating key events and statuses.\n"
    "   - When to use: When you need a high-level view of the cluster's health before drilling down into specific pods or services.\n"
    "   - Parameters: None.\n"
    "   - Caveats: The summary is based on available events and may not cover every nuance; use other tools for detailed diagnostics.\n\n"
    "When you need data, output a function call exactly as specified. Once you get the data, analyze it and then provide your diagnosis. "
    "Do not answer directly if you require additional data from the cluster. Use multiple function calls if needed to gather complete context."
)
conversation_history.append({"role": "system", "content": system_message})

# --- Tool Functions with Detailed Docstrings ---
def get_logs_api(pod_name, namespace="default", since_time="5m", tail_lines=100):
    """
    Fetches logs from the specified Kubernetes pod.
    
    Parameters:
      - pod_name (str): Name of the pod whose logs are required.
      - namespace (str): The Kubernetes namespace. Defaults to "default".
      - since_time (str): The time window (e.g., "5m" for the last 5 minutes) for which to fetch logs.
      - tail_lines (int): The number of log lines from the end of the log to retrieve.
    
    Returns:
      - A string containing the concatenated log lines if successful.
      - An error message string if the logs cannot be fetched (e.g., if the pod is not ready or image pull fails).
    
    Use this tool when you suspect issues with a specific pod's operation.
    """
    params = {
        "pod_name": pod_name,
        "namespace": namespace or "default",
        "since_time": since_time,
        "tail_lines": tail_lines
    }
    try:
        response = requests.get(f"{BRIDGE_BASE_URL}/get-logs", params=params)
        response.raise_for_status()
        data = response.json()
        logs = "\n".join(["\n".join(chunk["lines"]) for chunk in data.get("logs", [])])
        return logs if logs else "No logs found."
    except Exception as e:
        return f"Error fetching logs: {e}"

def describe_pod_api(pod_name, namespace="default"):
    """
    Retrieves a detailed description of the specified pod (like 'kubectl describe pod').
    
    Parameters:
      - pod_name (str): Name of the pod.
      - namespace (str): The Kubernetes namespace. Defaults to "default".
    
    Returns:
      - A string containing detailed pod information if successful.
      - An error message string if the description cannot be retrieved.
    
    Use this tool when you need to investigate why a pod is failing or to inspect its configuration.
    """
    params = {"pod_name": pod_name, "namespace": namespace or "default"}
    try:
        response = requests.get(f"{BRIDGE_BASE_URL}/describe-pod", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("description", "No description available.")
    except Exception as e:
        return f"Error describing pod: {e}"

def get_events_api(namespace="default", since_time=None):
    """
    Retrieves recent Kubernetes cluster events for a given namespace.
    
    Parameters:
      - namespace (str): The Kubernetes namespace. Defaults to "default".
      - since_time (str, optional): A time filter (e.g., "10m" for events in the last 10 minutes).
    
    Returns:
      - A string containing formatted events if successful.
      - An error message string if events cannot be retrieved.
    
    Use this tool to get a high-level view of cluster issues (e.g., scheduling errors, crashes).
    """
    params = {"namespace": namespace or "default"}
    if since_time:
        params["since_time"] = since_time
    try:
        response = requests.get(f"{BRIDGE_BASE_URL}/get-events", params=params)
        response.raise_for_status()
        data = response.json()
        events = "\n".join([
            f"{evt.get('timestamp','')} {evt.get('event_type','')} {evt.get('reason','')}: {evt.get('message','')}"
            for evt in data.get("events", [])
        ])
        return events if events else "No events found."
    except Exception as e:
        return f"Error fetching events: {e}"

def get_service_info_api(service_name, namespace="default"):
    """
    Fetches details of a specific Kubernetes service.
    
    Parameters:
      - service_name (str): Name of the service.
      - namespace (str): The Kubernetes namespace. Defaults to "default".
    
    Returns:
      - A string containing the service details (often in YAML format) if successful.
      - An error message string if the service info cannot be retrieved.
    
    Use this tool to diagnose issues related to service exposure or connectivity.
    """
    params = {"service_name": service_name, "namespace": namespace or "default"}
    try:
        response = requests.get(f"{BRIDGE_BASE_URL}/get-svc", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("service_info", "No service info available.")
    except Exception as e:
        return f"Error fetching service info: {e}"

def describe_cluster_api():
    """
    Synthesizes an overall status report for the Kubernetes cluster.
    
    Parameters: None.
    
    Returns:
      - A string summarizing the overall cluster status by aggregating key information
        such as events and possibly high-level metrics.
      - A message indicating if certain data could not be fetched.
    
    Use this tool when you need a high-level, aggregated view of the cluster's health before
    drilling down into specific components.
    
    Caveats:
      - This report is only as detailed as the underlying tools (e.g., get_events_api).
      - It may not capture every nuance of the cluster's state.
    """
    # For this example, we simply fetch recent events and return them as the cluster status.
    events = get_events_api(namespace="default")
    status_report = f"Cluster Status Report:\nRecent Events:\n{events}"
    return status_report

# Map function names to actual functions (ensure names match exactly!)
tool_functions = {
    "get_logs_api": get_logs_api,
    "describe_pod_api": describe_pod_api,
    "get_events_api": get_events_api,
    "get_service_info_api": get_service_info_api,
    "describe_cluster_api": describe_cluster_api
}

# --- Function Call Parsing and Execution ---

import json
import re

def parse_function_call(response_text):
    """
    Extract and parse function call directives from LLM response.
    
    - Detects multiple function calls inside a valid JSON list.
    - Fixes JSON formatting issues before parsing.
    - Returns a list of function calls with names and arguments.
    """
    try:
        # Use regex to capture a properly formatted JSON list
        json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)

        if not json_match:
            print(f"DEBUG: No valid function call detected in response: {response_text}")
            return []

        json_str = json_match.group(1)

        # Fix common JSON errors (e.g., missing closing brackets, invalid separators)
        json_str = json_str.replace(";", ",")  # Fix semicolon errors

        function_calls = json.loads(json_str)  # Load the corrected JSON

        parsed_calls = []
        for call in function_calls:
            if "function_call" in call:
                func_call = call["function_call"]
                name = func_call.get("name")
                arguments = func_call.get("arguments", {})

                # Ensure namespace defaults to "default"
                if "namespace" not in arguments or not arguments["namespace"]:
                    arguments["namespace"] = "default"

                parsed_calls.append((name, arguments))

        return parsed_calls

    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse function call JSON: {e}")
        return []




def call_llm(prompt):
    """
    Calls the Ollama LLM API with the entire conversation history plus the latest prompt.
    
    Returns the raw text response from the LLM.
    """
    conversation_text = ""
    for turn in conversation_history:
        if turn["role"] == "system":
            conversation_text += f"System: {turn['content']}\n"
        elif turn["role"] == "user":
            conversation_text += f"User: {turn['content']}\n"
        else:
            conversation_text += f"Assistant: {turn['content']}\n"
    conversation_text += f"User: {prompt}\nAssistant:"
    
    payload = {
        "model": llm_config["model"],
        "prompt": conversation_text,
        "stream": False
    }
    try:
        response = requests.post(f"{llm_config['base_url']}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "No response from Ollama")
        return text
    except Exception as e:
        return f"Error calling LLM: {e}"

import inspect

def process_llm_response(prompt):
    """
    Processes LLM responses:
    - Detects multiple function calls.
    - Ensures valid arguments.
    - Calls functions sequentially and accumulates results.
    """
    llm_raw_response = call_llm(prompt)
    print(f"DEBUG: Raw LLM response: {llm_raw_response}")

    function_calls = parse_function_call(llm_raw_response)

    if not function_calls:
        print("DEBUG: LLM did not call any function. Asking it to try again.")
        return call_llm("You must call a function before answering. Try again.")

    function_results = []
    
    for func_name, arguments in function_calls:
        if func_name not in tool_functions:
            print(f"DEBUG: Function '{func_name}' is not recognized. Skipping execution.")
            function_results.append(f"Error: The function '{func_name}' is not available.")
            continue

        # Get the actual function reference
        function_to_call = tool_functions[func_name]

        # Validate arguments to match function signature
        valid_args = inspect.signature(function_to_call).parameters
        filtered_args = {key: value for key, value in arguments.items() if key in valid_args}

        # Execute the function and store the result
        tool_result = function_to_call(**filtered_args)
        function_results.append(f"Executed {func_name} with arguments {filtered_args}. Result:\n{tool_result}")

    # Join results into a follow-up prompt for the LLM
    followup_prompt = "Here are the results of the Kubernetes status checks:\n" + "\n\n".join(function_results) + "\n\nBased on this information, provide your diagnosis."
    
    final_response = call_llm(followup_prompt)
    conversation_history.append({"role": "assistant", "content": final_response})

    return final_response



# --- Optional: Background Monitoring (unchanged) ---
def monitor_cluster(interval=30):
    while monitoring_active:
        events = get_events_api(namespace="default")
        if events and "No events found" not in events:
            message = f"Auto-monitor (events):\n{events}"
            print(f"\n{message}")
            conversation_history.append({"role": "assistant", "content": message})
        time.sleep(interval)

monitoring_active = False

def print_help():
    help_text = """
Available Commands:
    /help                       - Show this help message.
    /logs <pod_name> [namespace] [since_time] [tail_lines]
                                - Fetch logs for the given pod.
    /describe <pod_name> [namespace]
                                - Get detailed pod description.
    /events [namespace] [since_time]
                                - Get recent cluster events.
    /svc <service_name> [namespace]
                                - Get details of a Kubernetes service.
    /cluster                    - Get an overall cluster status report.
    /monitor start|stop         - Start or stop automatic cluster monitoring.
    /chat <your message>        - Send a message to the LLM for analysis (supports function calls).
    /exit                       - Exit the chat.
Simply type your message to chat with the LLM if it doesn't start with '/'.
"""
    print(help_text)

def main():
    global monitoring_active
    print("Welcome to the Cluster Doctor Terminal Chat!")
    print("Type /help for available commands.")
    
    monitor_thread = None

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue

        if user_input.startswith("/clear"):
            conversation_history.clear()  # Clear chat history
            print("Chat history cleared.")
            continue


        if user_input.lower() in ["/exit", "exit", "quit"]:
            print("Exiting chat. Goodbye!")
            monitoring_active = False
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join()
            break

        if user_input.startswith("/help"):
            print_help()
            continue

        if user_input.startswith("/monitor"):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: /monitor start|stop")
                continue
            action = parts[1].lower()
            if action == "start":
                if not monitoring_active:
                    monitoring_active = True
                    monitor_thread = threading.Thread(target=monitor_cluster, daemon=True)
                    monitor_thread.start()
                    print("Started automatic cluster monitoring.")
                else:
                    print("Monitoring is already active.")
            elif action == "stop":
                if monitoring_active:
                    monitoring_active = False
                    if monitor_thread and monitor_thread.is_alive():
                        monitor_thread.join()
                    print("Stopped automatic cluster monitoring.")
                else:
                    print("Monitoring is not active.")
            else:
                print("Usage: /monitor start|stop")
            continue

        if user_input.startswith("/logs"):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: /logs <pod_name> [namespace] [since_time] [tail_lines]")
                continue
            pod_name = parts[1]
            namespace = parts[2] if len(parts) >= 3 else "default"
            since_time = parts[3] if len(parts) >= 4 else "5m"
            tail_lines = int(parts[4]) if len(parts) >= 5 else 100
            logs = get_logs_api(pod_name, namespace, since_time, tail_lines)
            print(f"\nLogs for pod '{pod_name}':\n{logs}")
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": logs})
            continue

        if user_input.startswith("/describe"):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: /describe <pod_name> [namespace]")
                continue
            pod_name = parts[1]
            namespace = parts[2] if len(parts) >= 3 else "default"
            description = describe_pod_api(pod_name, namespace)
            print(f"\nDescription for pod '{pod_name}':\n{description}")
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": description})
            continue

        if user_input.startswith("/events"):
            parts = user_input.split()
            namespace = parts[1] if len(parts) >= 2 else "default"
            since_time = parts[2] if len(parts) >= 3 else None
            events = get_events_api(namespace, since_time)
            print(f"\nEvents for namespace '{namespace}':\n{events}")
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": events})
            continue

        if user_input.startswith("/svc"):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: /svc <service_name> [namespace]")
                continue
            service_name = parts[1]
            namespace = parts[2] if len(parts) >= 3 else "default"
            svc_info = get_service_info_api(service_name, namespace)
            print(f"\nService info for '{service_name}':\n{svc_info}")
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": svc_info})
            continue

        if user_input.startswith("/cluster"):
            # Call the new tool that describes overall cluster status.
            cluster_status = describe_cluster_api()
            print(f"\nCluster Status:\n{cluster_status}")
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": cluster_status})
            continue

        # For any other input, treat it as a chat message that may include function calls.
        conversation_history.append({"role": "user", "content": user_input})
        llm_response = process_llm_response(user_input)
        print(f"\nLLM: {llm_response}")
        conversation_history.append({"role": "assistant", "content": llm_response})

if __name__ == "__main__":
    main()
