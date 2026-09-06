# Chapter 5 companion: permissions and isolation

## Authorization demo

From this directory, using Python 3.11 or newer:

```sh
python3 demo.py
python3 -m unittest discover -v
```

Keep sibling ch02 and ch04 directories. Standard library only. The default demo does not use Docker, a model, a network connection, or a shell tool. It reads permitted malicious text, attempts a private read and unavailable shell, and then reads the permitted policy. Expected: two permitted results, two denials, completed status, no synthetic private canary in the trace. This is scripted enforcement evidence, not a model's attack-resistance score.

The caller supplies the grant. Model arguments cannot grant permission. Both broad and path-scoped searches are restricted. Paths are canonical relative snapshot keys, not host filesystem paths. These checks assume trusted Python in the harness process; they do not confine a malicious imported adapter or implement user authentication, revocation, or an approval service.

`sample-trace.json` records actual events and fingerprints the demo, authorization wrapper, Chapter 4 tools, and Chapter 2 runtime.

## Optional operator-only isolation probe

`isolation.py` requires a running local Docker engine and a trusted local Linux image with `/usr/bin/python3`. It never downloads images and accepts only a full local image ID. Use `docker image inspect IMAGE_NAME --format '{{.Id}}'` to obtain the ID for an image you have reviewed and already installed. Replace IMAGE_NAME with that local image's name; pass the resulting ID to `python3 isolation.py --image-id ID`.

The recorded run used Docker Engine 28.3.2 and the already available mcr.microsoft.com/playwright:v1.62.1-noble image, local ID sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e. Its worker Python was 3.12.3. This tooling-rich image was a local test convenience, not a recommended production base. A local image ID is not a cross-platform registry digest; readers must supply a trusted image available on their own engine.

The probe stages only a synthetic policy file, mounts that temporary directory read-only, and leaves a synthetic canary outside the mount. It does not mount the book, home directory, Docker socket, or real credentials. It creates a restricted non-root container, runs fixed probe code via stdin, then attempts to remove that uniquely named container and cleans up the temporary files. The controller passes a fake credential to the Docker client process but not to the worker.

The worker attempts reads, writes, and one IPv4 connection to the documentation-only address 192.0.2.1. Expected: policy read and scratch write succeed; root/workspace writes, host-only read, and connection fail. Assessment also requires UID 65534, no fake credential, zero effective capabilities, no-new-privileges, only loopback up, no IPv4 routes, unchanged canary and workspace. Exit 0 means these narrow environment checks passed; 1 means a check failed; 2 means setup/execution failed. A 45-second client wait limit is followed by a container-removal attempt. The probe does not check the removal command's exit status or confirm that the container is absent, so a passed report is not cleanup evidence. Chapter 6 adds a separate engine query for that result. This launcher is not a durable supervisor and cannot guarantee cleanup after the controller itself is killed.

`isolation-first-report.json` preserves the initial failure: counting interface names was too strict for the local kernel's inactive tunnel devices. `isolation-report.json` records the final executed probe and its source hash. The final probe uses a Linux interface-flags query and retains both all interface names and up interfaces. Do not promote failed connection tests to a universal no-egress proof. IPv6 and sandbox escape resistance are not tested. CPU, memory, process count, and scratch noexec are configured but not stress-tested.

A trusted image and local engine are prerequisites. The launcher does not audit image layers or configured volumes, authenticate a remote Docker endpoint, or perform a production image-security assessment. No model can choose the launch configuration through the exposed agent tools.

See [compatibility](../COMPATIBILITY.md) for executed versions and [references](../REFERENCES.md) for documentation access dates.
