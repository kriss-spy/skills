#!/bin/bash

STATE_FILE="$HOME/.ask-manus-state"

API_KEY="${MANUS_API_KEY}"
API_URL="https://api.manus.ai/v2"
CONTINUE=false
TASK_ID=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -k|--key) API_KEY="$2"; shift ;;
        -c|--continue) CONTINUE=true ;;
        -t|--task-id) TASK_ID="$2"; shift ;;
        -h|--help)
            echo "Usage: ask-manus [options] \"<prompt>\""
            echo ""
            echo "Options:"
            echo "  -c, --continue      Continue last conversation"
            echo "  -t, --task-id <id>  Continue a specific conversation"
            echo "  -k, --key <key>     Manus API key (defaults to MANUS_API_KEY env var)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ask-manus \"Write a poem about the command line.\""
            echo "  ask-manus -c \"Expand on that, make it funnier.\""
            echo "  ask-manus -t <task_id> \"What else can you do?\""
            exit 0
            ;;
        *) PROMPT="$1" ;;
    esac
    shift
done

if [ -z "$API_KEY" ]; then
    echo "Error: MANUS_API_KEY not set. Get it from Manus Settings -> API Integration."
    exit 1
fi

if [ -z "$PROMPT" ]; then
    echo "Error: No prompt provided."
    echo "Usage: ask-manus \"<prompt>\""
    exit 1
fi

# Resolve task_id and send message
if [ -n "$TASK_ID" ]; then
    echo "Continuing conversation: $TASK_ID"
elif [ "$CONTINUE" = true ]; then
    if [ ! -f "$STATE_FILE" ]; then
        echo "Error: No previous conversation found."
        exit 1
    fi
    TASK_ID=$(cat "$STATE_FILE")
    echo "Continuing conversation: $TASK_ID"
fi

if [ -n "$TASK_ID" ]; then
    curl -s -X POST "${API_URL}/task.sendMessage" \
      -H "x-manus-api-key: $API_KEY" \
      -H 'Content-Type: application/json' \
      -d "{\"task_id\": \"$TASK_ID\", \"message\": {\"role\": \"user\", \"content\": \"$PROMPT\"}}" \
      > /dev/null
else
    echo "Starting new Manus session..."
    TASK_ID=$(curl -s -X POST "${API_URL}/task.create" \
      -H "x-manus-api-key: $API_KEY" \
      -H 'Content-Type: application/json' \
      -d "{\"message\": {\"role\": \"user\", \"content\": \"$PROMPT\"}}" \
      | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('task_id', ''))")

    if [ -z "$TASK_ID" ]; then
        echo "Error: Failed to create task. Check your API key."
        exit 1
    fi
    echo "Task created: $TASK_ID"
    echo "$TASK_ID" > "$STATE_FILE"
    echo "You can view this task in your Manus webpage history."
fi

echo "Waiting for Manus to finish..."

MAX_POLL_ATTEMPTS=120
poll_attempt=0
seen_active=false
while true; do
  poll_attempt=$((poll_attempt + 1))
  if [ "$poll_attempt" -gt "$MAX_POLL_ATTEMPTS" ]; then
    echo "Error: Timed out waiting for Manus to finish."
    exit 1
  fi

  STATUS=$(curl -s "${API_URL}/task.listMessages?task_id=$TASK_ID&order=desc&limit=10" \
    -H "x-manus-api-key: $API_KEY" \
    | python3 -c "
import sys, json
try:
    msgs = json.load(sys.stdin).get('messages', [])
    for m in msgs:
        if m.get('type') == 'status_update':
            print(m.get('status_update', {}).get('agent_status', ''))
            break
except Exception:
    pass
" 2>/dev/null)

  if [ -n "$STATUS" ] && [ "$STATUS" != "stopped" ] && [ "$STATUS" != "error" ]; then
    seen_active=true
  fi

  if [ "$STATUS" = "error" ]; then
    break
  fi

  if [ "$STATUS" = "stopped" ]; then
    if [ "$seen_active" = true ]; then
      break
    fi
    # If stuck on stale "stopped" too long (10 polls = 50s), force-break anyway
    if [ "$poll_attempt" -gt 10 ]; then
      break
    fi
  fi

  sleep 5
done

echo ""
echo "--- Result ---"
echo ""

# Retry result fetch with backoff in case the API hasn't fully settled
max_retries=10
retry_delay=2
for ((i=1; i<=max_retries; i++)); do
  RESULT=$(curl -s "${API_URL}/task.listMessages?task_id=$TASK_ID&order=desc&limit=100" \
    -H "x-manus-api-key: $API_KEY" \
    | python3 -c "
import sys, json
try:
    msgs = json.load(sys.stdin).get('messages', [])
    for m in msgs:
        if m.get('type') == 'assistant_message':
            print(m.get('assistant_message', {}).get('content', ''))
            sys.exit(0)
    sys.exit(2)
except Exception:
    sys.exit(1)
" 2>/dev/null)

  exit_code=$?
  if [ $exit_code -eq 0 ] && [ -n "$RESULT" ]; then
    echo "$RESULT"
    break
  fi
  if [ "$i" -lt "$max_retries" ]; then
    sleep "$retry_delay"
    retry_delay=$((retry_delay * 2))
  else
    echo "Warning: Could not fetch result after $max_retries attempts."
    echo "Check your Manus webpage history for task: $TASK_ID"
  fi
done

echo "--- End ---"
