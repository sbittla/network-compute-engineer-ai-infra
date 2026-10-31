# 3.7 — Four properties of a production-safe collector

Source: manuscript Section 3.10 ("Building a safe, repeatable collector") and the lab's collector guard
(Part A2, `argv_is_read_only()`). Any four of the six below earn full credit.

1. **Default-deny allowlist of exact read-only forms, not a deny-list.** An argv runs only if it matches a
   listed form after `--opt=value` is split. Refused because they are not listed: `ethtool -s rail0 speed
   200000`, `ip link set rail0 mtu 1500`, `dmesg -c` (clears the ring buffer), `nvidia-smi
   --power-limit=300`, `nvidia-smi -mig 1`, `taskset -cp 0-3 1234` (sets affinity). A deny-list misses new
   setters such as `-lmc` or `--set-priv-flags`.
2. **No shell, argv only.** Commands are executed as argument vectors, so a hostname or interface name
   containing `; rm -rf /` or `lspci -s '5d:00.0;reboot'` is passed literally and cannot inject a command.
3. **Timeouts on every command.** A `lspci -vv` that hangs on a wedged device, or an `nvidia-smi` stuck
   behind a hung driver, is killed and recorded as `status: timeout`, so the collector still finishes.
4. **Never escalates privilege.** No `sudo`. If `dmesg` is denied, record `denied` and fall back to the
   read-only `journalctl -k -b --no-pager`. Missing capabilities in `lspci` (`<access denied>`) fall back
   to sysfs.
5. **Records every outcome.** A missing `iostat` becomes `status: missing` in the snapshot, not a
   traceback, so an evidence gap is visible rather than silent.
6. **Stable locale (`LC_ALL=C`).** Parsers do not break on localized decimal separators, 12-hour `mpstat`
   timestamps or translated headers.
