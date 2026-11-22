# Integration and validation gates

Included: voucher database/API prototype, expiry monitor, coin serial event reader, dashboard prototype, FAS page template and unified build workflow.

FAS is not yet wired into a proven OpenNDS config. Configure OpenNDS FAS/redirect according to the exact installed version and verify the MAC/client query parameters. Validate `ndsctl auth` and `ndsctl deauth` syntax on the image.

The workflow runs Python syntax validation and attempts an OpenWrt build. A successful CI build is not proof of boot or gateway behavior. Required: QEMU boot, Wyse boot, captive redirect, voucher redemption, expiry disconnect, coin serial test, reboot persistence, and security review.
