#!/bin/bash
users=("admin" "raj_ops")
passw=("admin" "hadoop" "raj_ops" "atlas" "admin123" "holger_gov" "password")

for u in "${users[@]}"; do
    for p in "${passw[@]}"; do
        status=$(curl -s -o /dev/null -w "%{http_code}" -u "$u:$p" http://localhost:21000/api/atlas/v2/types/typedefs)
        echo "Testing $u:$p -> $status"
        if [ "$status" == "200" ]; then
            echo "SUCCESS: $u:$p is working!"
            exit 0
        fi
    done
done
