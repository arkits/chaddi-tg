#!/bin/bash

# Define the command as a variable for easy updates
COMMAND='opencode run --model opencode/glm-4.7-free "Continue to add more tests. Refer to TESTING_SETUP.md for the current status. Run lint, format, and test commands. You MUST ensure that there are no errors or warnings. Do NOT continue until all tests pass and there are no lint or formatting errors. Then, update the TESTING_SETUP.md file to reflect the new status. Finally, commit your changes and push to the remote repository."'

echo "Starting loop. Press [CTRL+C] to stop."

while true
do
    echo "------------------------------------------"
    echo "Executing: $COMMAND"
    
    # Execute the command
    eval $COMMAND
    
    # Optional: Add a sleep timer (e.g., 5 seconds) to avoid rate limits or CPU spikes
    sleep 5

    echo "------------------------------------------"

    git add .
    git commit -m "chore: check wip -- AI forgot to commit"
    git push
done