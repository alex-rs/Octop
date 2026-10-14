#!/bin/bash
# Get the instance ID from the Tencent Cloud metadata service
# Example: instance-name returns lh-1251810746-lhins-dtx9e79f, extract lhins-dtx9e79f

INSTANCE_NAME=$(curl -s http://metadata.tencentyun.com/meta-data/instance-name)

# Check whether instance-name contains an ID that starts with lhins-
LHINS_ID=$(echo "$INSTANCE_NAME" | grep -oE 'lhins-[a-zA-Z0-9]+')

if [ -n "$LHINS_ID" ]; then
    # Extract the ID in the lhins-xxx format and print it
    echo "$LHINS_ID"
else
    # Fall back to instance-id, removing whitespace characters
    curl -s http://metadata.tencentyun.com/meta-data/instance-id | tr -d '[:space:]'
    echo
fi