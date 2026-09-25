# Download Artifact

Download ZIP artifacts from si-artifacts using GitHub OIDC authentication.
The action verifies each archive's SHA-256 checksum before extracting it.
Downloads are limited to the current repository and workflow run.

The runner needs Node 24 action support and network access to the service's HTTPS
endpoint. All JavaScript dependencies are bundled; no installation step is needed.

## Usage

Set the repository variable `SI_ARTIFACTS_URL` to the service's CI endpoint.
Replace `FULL_REVIEWED_COMMIT_SHA` with a reviewed commit from `silitics/actions`.
Run this step after a job using [upload-artifact](../upload-artifact) completes.

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - uses: silitics/actions/download-artifact@FULL_REVIEWED_COMMIT_SHA
    with:
      server-url: ${{ vars.SI_ARTIFACTS_URL }}
      name: binaries
      path: downloaded/
```

To combine several artifacts, omit `name` and set `pattern: binaries-*` and
`merge-multiple: true`. Overlapping file paths fail the download.

## Inputs and Outputs

| Input | Default | Behavior |
| --- | --- | --- |
| `server-url` | `SI_ARTIFACTS_URL` environment variable | HTTPS origin of the CI endpoint. |
| `audience` | Server URL without a trailing slash | Must match the service's configured OIDC audience. |
| `name` | Unset | Download one exact artifact name. |
| `artifact-ids` | Unset | Comma-separated service UUIDs; cannot be combined with `name`. |
| `pattern` | All names | Name glob; ignored when `name` is set. |
| `path` | `GITHUB_WORKSPACE` | Destination directory. |
| `merge-multiple` | `false` | Extract selected artifacts into one directory instead of separate named directories. |
| `repository` | Current repository | Other repositories are rejected. |
| `run-id` | Current workflow run | Other runs are rejected. |

The `download-path` output is the absolute destination directory. On partial
workflow reruns, name selection uses the latest completed artifact at or before
the caller's current attempt.

## Extraction

Digest mismatches, path traversal, symlinks, special files and overlapping files
in merged downloads cause a failure. Regular files are extracted with mode 0644.
Use a tar archive inside an artifact when executable permissions must survive.

Extraction defaults to at most 20 GiB and 100,000 entries in total. Set
`SI_ARTIFACTS_MAX_EXTRACTED_BYTES` and `SI_ARTIFACTS_MAX_EXTRACTED_FILES` as job
environment variables when larger outputs are expected. A failed extraction may
leave earlier verified files in the destination. Extracting raw files with
`skip-decompress` is unsupported.

## Maintenance

This directory is generated from `vendor/si-artifacts` in
`silitics/infrastructure`. Update its source there, run the integration suite, and
export the tested Nix package with `scripts/export-actions.sh`. Commit the action
manifest, documentation, bundle and third-party license notices together.
