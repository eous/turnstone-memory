---
name: no-alpine-base-images
description: "Choosing a Docker base image for any builder or runtime stage: never Alpine (musl); use Debian slim (python:3.14-slim, bookworm-slim) or distroless."
metadata: 
  node_type: memory
  type: feedback
---

Don't use Alpine for Docker base images. User has had bad luck with musl.

**Why:** musl libc causes subtle compatibility issues (DNS resolution,
locale handling, static linking edge cases).

**How to apply:** Use a Debian-based slim image, never an Alpine one. Turnstone's
own root `Dockerfile` (one unified image for server/console/channel/eval) already
follows this: `FROM python:3.14-slim`, with Node.js added via
`COPY --from=node:24-slim /usr/local/bin/node ...` (binaries copied in, no
Alpine-based build stage anywhere in the image). For a Go binary elsewhere, the
equivalent is `golang:1.24-bookworm` for the builder stage and
`debian:bookworm-slim` / `gcr.io/distroless/static-debian12` for the runtime —
same principle, different ecosystem.
