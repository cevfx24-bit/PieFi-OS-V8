# Known limitations / integration gates

1. OpenNDS `ndsctl auth/deauth` command syntax and MAC/client mapping must be verified against the exact OpenNDS release. Controller command arguments are configurable via UCI.
2. OpenNDS FAS/captive portal landing redirect and voucher form are not wired in this prototype.
3. Coin serial reader is provided, but init supervision/config enable wiring and coin-value mapping/payment-to-session logic need testing.
4. The API uses a bearer token stored under `/etc/piefi/api.token`; local loopback only. Dashboard endpoint is also local server-side. Do not expose it without authentication-aware reverse proxy/security controls.
5. Redeem endpoint expects MAC; it does not validate MAC formatting beyond string length.
6. Expiry loop attempts `ndsctl deauth <MAC>` at expiration; compatibility must be tested. Voucher status changes to expired in DB.
7. This is not field-certified. Test in VM and on isolated hardware, inspect logs, verify deauth, captive flow, DNS, DHCP, firewall and serial hardware before production.
