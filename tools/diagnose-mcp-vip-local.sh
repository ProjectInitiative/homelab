#!/usr/bin/env bash
# Diagnose why ONLY astrolabe gets TCP-RST on the MCP VIP (100.64.72.152:80)
# while other tailnet devices and the laptop work fine.
# Everything here is host-local (astrolabe); no kubectl needed.
# Run as your normal user; uses sudo for privileged reads.
#   tools/diagnose-mcp-vip-local.sh > /tmp/mcp-vip-local.txt 2>&1
set -u
VIP="100.64.72.152"

section() { printf '\n===== %s =====\n' "$1"; }
sudo_() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo -n "$@" 2>/dev/null || sudo "$@"; fi; }

section "1. Self identity"
tailscale status --json | jq '{DNSName:.Self.DNSName, Tags:.Self.Tags, TailscaleIPs:.Self.TailscaleIPs, Online:.Self.Online}'

section "2. Which peers serve the MCP VIP? (vip-services capability per peer)"
# Each advertising peer lists VIPs in its capabilities; a peer missing the
# MCP entry while others have it = client-side pin to a non-serving peer.
tailscale status --json | jq -r '
  .Peer | to_entries[]
  | .value as $p
  | ($p.Capabilities // []) | map(select(test("vip-services"; "i"))) as $caps
  | select($caps | length > 0)
  | {peer: ($p.DNSName // $p.HostName), ips: $p.TailscaleIPs, online: $p.Online, caps: $caps}
  | tostring'

section "3. Route + rule priority for the VIP"
ip route get "$VIP"
ip rule show
ip route show table 52 | grep -E "100\.64\.72\.152|100\.64\.0" || echo "(no table-52 entry!)"

section "4. Local firewall rules mentioning the VIP or tailscale"
echo "--- nft ---"
sudo_ nft list ruleset 2>/dev/null | grep -n -B2 -A2 "$VIP" || echo "(no VIP mentions)"
sudo_ nft list ruleset 2>/dev/null | grep -n -iE "ts-input|ts-forward|tailscale" | head -20
echo "--- iptables ---"
sudo_ iptables-save 2>/dev/null | grep -n -E "$VIP|ts-|tailscale" | head -30

section "5. Conntrack entries for the VIP"
sudo_ conntrack -L 2>/dev/null | grep "$VIP" || echo "(none)"
sudo_ conntrack -D -d "$VIP" 2>/dev/null || true
echo "(stale entries flushed; retest curl after this)"

section "6. Wire-level proof: where does the RST come from?"
echo "Capturing tailscale0 + mgmnt for ~8s while making 3 curl attempts..."
sudo_ timeout 8 tcpdump -ni any "host $VIP" -c 40 2>/dev/null > /tmp/vip-tcpdump.txt &
TPID=$!
for i in 1 2 3; do
  curl -s -o /dev/null --connect-timeout 2 --max-time 4 "http://$VIP/sse" 2>/dev/null
  sleep 1
done
wait $TPID 2>/dev/null
cat /tmp/vip-tcpdump.txt | head -40
echo "Interpretation:"
echo "  SYN out on tailscale0 + RST in on tailscale0  -> remote peer refuses (proxy-side)"
echo "  SYN out + RST with NO matching SYN on any if  -> local stack generating RST"
echo "  nothing on tailscale0, SYN on mgmnt           -> route regression (vip not in 52)"

section "7. ts proxy vars / netstack listeners"
sudo_ ss -ltnp 2>/dev/null | grep -E "100\.64\.72\.152|:80 " | head -10 || true

section "8. Version sanity"
tailscale version
