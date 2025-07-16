#!/bin/bash
# Usage: sudo ./block_sites.sh block|unblock domain1 domain2 ...

HOSTS_FILE="/etc/hosts"
BACKUP_FILE="/etc/hosts.bak.aibuddies"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

if [ $# -lt 2 ]; then
  echo "Usage: $0 block|unblock domain1 domain2 ..."
  exit 1
fi

ACTION=$1
shift
DOMAINS=("$@")

# Backup hosts file if not already backed up
if [ ! -f "$BACKUP_FILE" ]; then
  cp "$HOSTS_FILE" "$BACKUP_FILE"
fi

block_sites() {
  for domain in "${DOMAINS[@]}"; do
    # Only add if not already present
    if ! grep -q "127.0.0.1 $domain" "$HOSTS_FILE"; then
      echo "127.0.0.1 $domain" >> "$HOSTS_FILE"
      echo "Blocked $domain"
    else
      echo "$domain already blocked"
    fi
    # Also block www version
    if ! grep -q "127.0.0.1 www.$domain" "$HOSTS_FILE"; then
      echo "127.0.0.1 www.$domain" >> "$HOSTS_FILE"
      echo "Blocked www.$domain"
    fi
  done
}

unblock_sites() {
  # Remove lines for each domain and www.domain
  TMP_FILE=$(mktemp)
  cp "$HOSTS_FILE" "$TMP_FILE"
  for domain in "${DOMAINS[@]}"; do
    sed -i '' "/127.0.0.1 $domain/d" "$TMP_FILE"
    sed -i '' "/127.0.0.1 www.$domain/d" "$TMP_FILE"
    echo "Unblocked $domain and www.$domain"
  done
  cp "$TMP_FILE" "$HOSTS_FILE"
  rm "$TMP_FILE"
}

case "$ACTION" in
  block)
    block_sites
    ;;
  unblock)
    unblock_sites
    ;;
  *)
    echo "Unknown action: $ACTION (use block or unblock)"
    exit 1
    ;;
esac

# Flush DNS cache (macOS)
echo "Flushing DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

echo "Done. Sites should now be blocked/unblocked immediately." 