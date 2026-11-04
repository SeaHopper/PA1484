Source: https://github.com/micropython/micropython-lib/tree/master/python-ecosys/requests
Retrieved: 2026-10-22
Manifest version: 1.1.1
Change: fall back to ssl when the tls module name is unavailable.
Upstream TLS certificate verification defaults are unchanged (CERT_NONE).
The firmware's TLS stack and HTTPS behavior must be tested on the device.

