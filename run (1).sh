#!/bin/bash

# List of date arguments
dates=("2023-23" "2024-10" "2023-14" "2023-06" "2024-26" "2024-33" "2024-42" "2023-50" "2022-05" "2022-21" "2023-40" "2022-40" "2024-22" "2024-38" "2024-18")
# dates=("2024-10" "2024-26" "2024-42" "2023-50" "2023-40" "2024-22" "2024-38" "2024-18")
# USER_AGENTS=("Amazonbot" "AI2Bot" "anthropic-ai" "Applebot" "Applebot-Extended" "Bytespider" "CCBot" "ChatGPT-User" "Claude-Web" "ClaudeBot" "cohere-ai" "Diffbot" "FacebookBot" "Google-Extended" "GPTBot" "Kangaroo Bot" "Meta-ExternalAgent" "Meta-ExternalFetcher" "OAI-SearchBot" "omgili" "PerplexityBot" "Timpibot" "Webzio-Extended" "YouBot")
# USER_AGENTS=("Amazonbot" "AI2Bot" "Applebot" "Applebot-Extended" "Bytespider" "CCBot" "ChatGPT-User" "Claude-Web" "ClaudeBot" "cohere-ai" "Diffbot" "FacebookBot" "Google-Extended" "Kangaroo Bot" "Meta-ExternalAgent" "Meta-ExternalFetcher" "OAI-SearchBot" "omgili" "PerplexityBot" "Timpibot" "Webzio-Extended" "YouBot")
# USER_AGENTS=("Amazonbot" "AI2Bot" "Applebot" "Applebot-Extended" "Bytespider")
USER_AGENTS=("CCBot" "ChatGPT-User" "Claude-Web" "ClaudeBot" "cohere-ai" "Diffbot" "FacebookBot" "Google-Extended" "Kangaroo Bot" "Meta-ExternalAgent" "Meta-ExternalFetcher" "OAI-SearchBot" "omgili" "PerplexityBot" "Timpibot" "Webzio-Extended" "YouBot")


for agent in "${USER_AGENTS[@]}"; do
    echo "$agent"
    # Loop through each date and run the Python script concurrently
    for date in "${dates[@]}"; do
        python3 robots_analysis_final.py "$agent" "$date" &
    done
    wait
done

# # Loop through each date and run the Python script concurrently
# for date in "${dates[@]}"; do
#     python3 robots_analysis_final.py anthropic-ai "$date" &
# done

# Wait for all background jobs to finish
wait
