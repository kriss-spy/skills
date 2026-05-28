---
name: ask-manus
description: Send requests to Manus.ai and trigger sessions that appear in the user's history. Use when the user wants to interact with Manus from the command line while keeping the history synchronized with the webpage.
---
# Ask Manus CLI Skill

This skill provides a command-line interface (CLI) script to interact with Manus.ai. It allows users to send prompts to Manus from their terminal, wait for the response, and see the results directly in the CLI. Importantly, because it uses the user's API key to create a task, these sessions will appear in the user's Manus webpage history, just like a session started from the UI.

## Overview

The core mechanism is using the `task.create` and `task.listMessages` endpoints of the Manus API. By authenticating with a personal API key (`x-manus-api-key`), tasks created via the API are fully owned by the user and appear in their standard history.

## Bundled Resources

- `scripts/ask-manus.sh`: A Bash script that encapsulates the API calls (task creation, polling, and result retrieval).

## Usage Instructions

To use this skill, follow these steps:

1. **Set up the API Key:**
   The script requires a Manus API key. The user can provide it via the `MANUS_API_KEY` environment variable
   Instruct the user to get their API key from **Manus Settings → API Integration**.

2. **Run the Script:**
   Execute the bundled `ask-manus.sh` script with a prompt.

   ```bash
   path/to/ask-manus/scripts/ask-manus.sh "Write a short poem about the command line."
   ```

## How it Works

The `ask-manus.sh` script performs the following sequence:

1. **Create Task:** Calls `POST /v2/task.create` with the user's prompt. This returns a `task_id`. This step is what makes the session appear in the user's history.
2. **Poll Status:** Calls `GET /v2/task.listMessages` in a loop, checking the `agent_status` field of `status_update` events until it becomes `stopped` or `error`.
3. **Fetch Result:** Once stopped, it calls `GET /v2/task.listMessages` again to retrieve the `assistant_message` events and prints the final output to the console.

## Alternative: Using the Default IM Agent

If the user prefers to send messages to the *same* continuous thread (the default IM agent) rather than creating a *new* session in their history every time, they can modify the script to use `task.sendMessage` with the `agent-default-main_task` shortcut instead of `task.create`. The provided script defaults to creating a new task per invocation, matching the typical "new chat" behavior.
