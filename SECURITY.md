# Security policy

Ajazz Linux is an early development preview. There is no maintained-release support matrix yet. Please investigate against the current source and identify the exact commit or version; do not assume an older build receives fixes.

## Reporting a potential vulnerability

Private vulnerability reporting is enabled on GitHub. Use [Security > Report a vulnerability](https://github.com/a32fred/ajazz-linux/security/advisories/new) for a private advisory. Do not post credentials, personal information, exploit payloads, private captures or detailed vulnerability steps in a public issue.

No private reporting email has been configured. If the advisory channel is unavailable, open a minimal public issue asking maintainers to establish a private reporting channel, without disclosing sensitive details. No response-time or bounty commitment is made.

A useful private report includes the affected version, environment, expected/actual behavior, impact and minimal reproduction using synthetic files or the simulator when possible. Do not perform unsolicited testing on another person's computer or mouse. Physical device writes are not required to report a vulnerability.

## Relevant boundaries

Ajazz Linux parses imported profiles/macros, reads local workspace data and communicates with USB HID devices. File parsers must validate sizes/types/references before use; no imported pointer-like value is an address. GUI recording is focused within the application, not a global hook. Device changes require explicit Apply. Run the GUI as your normal desktop user, not root.

See the [README](README.md) and [validation record](docs/VALIDATION.md) for known platform and hardware limits. An indefinitely stalled native HID call can delay shutdown; that accepted platform limitation is documented separately from a vulnerability report.
