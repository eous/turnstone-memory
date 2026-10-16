---
name: project_docker_apt_cache_security_updates
description: "Saying a Debian security fix (a curl CVE etc.) reached a published image: the gha layer cache reuses the apt layer; check the image with dpkg-query; the apt step has a curl floor."
metadata:
  type: project
---

The image publish workflow builds with `cache-from: type=gha`, so the Dockerfile's
`apt-get update && apt-get upgrade` layer is reused while the Dockerfile and the
`python:3.14-slim` base image are unchanged. A published image does not pick up trixie-security
updates on its own. On 2026-10-14 the 1.8.6 and 1.9.0a2 images both carried curl
8.14.1-2+deb13u5 while trixie-security had deb13u7 (CVE-2026-92392).

**Why:** the base image's apt sources already include trixie-security, so "the apt upgrade
fixes it" holds only for a fresh build. A hard version pin is worse: the security archive keeps
only the newest build, so a pin breaks the image build when the next update ships.

**How to apply:** before saying an image has a fix, read the published image's package versions
with `docker run --rm --entrypoint dpkg-query <image>:<tag> -W <package>`. To get a fix in, change
the apt step: PRs #1385 (dev) and #1386 (main) add a floor check (`dpkg --compare-versions ... ge
<fixed version>`) that any newer build passes. Raising the floor for the next CVE also forces the
layer to rebuild. The maintainer would rather not pin when the upgrade alone suffices.
