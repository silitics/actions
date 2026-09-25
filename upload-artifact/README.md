# Upload Artifact

Upload files to si-artifacts, a separate artifact service with local storage.
The action creates a ZIP archive and authenticates with a short-lived GitHub OIDC
token. The service must allow the calling repository and workflow.

The runner needs Node 24 action support and network access to the service's HTTPS
endpoint. All JavaScript dependencies are bundled; no installation step is needed.

## Usage

Set the repository variable `SI_ARTIFACTS_URL` to the service's CI endpoint.
Replace `FULL_REVIEWED_COMMIT_SHA` with a reviewed commit from `silitics/actions`.

```yaml
permissions:
  contents: read
  id-token: write

steps:
  # After checkout and build:
  - uses: silitics/actions/upload-artifact@FULL_REVIEWED_COMMIT_SHA
    id: upload
    with:
      server-url: ${{ vars.SI_ARTIFACTS_URL }}
      name: binaries
      path: |
        build/**
        !build/**/*.log
      if-no-files-found: error
      retention-days: 7
```

No storage secret or GitHub personal access token is required. The service checks
the job's repository, workflow and run identity before accepting an upload.

## Inputs

| Input | Default | Behavior |
| --- | --- | --- |
| `server-url` | `SI_ARTIFACTS_URL` environment variable | HTTPS origin of the CI endpoint. |
| `audience` | Server URL without a trailing slash | Must match the service's configured OIDC audience. |
| `name` | `artifact` | Artifact name within the current run attempt. |
| `path` | Required | Files, directories, or newline-separated globs; prefix exclusions with `!`. |
| `if-no-files-found` | `warn` | `warn`, `error`, or `ignore`. |
| `retention-days` | `0` | Zero uses the service default; the service enforces a maximum. |
| `compression-level` | `6` | ZIP deflate level from 0 to 9. |
| `overwrite` | `false` | Atomically replace the same name in the current run attempt. |
| `include-hidden-files` | `false` | Include dotfiles and files in hidden directories. |

## Outputs and Storage

| Output | Value |
| --- | --- |
| `artifact-id` | Service UUID. |
| `artifact-url` | Download page requiring browser sign-in. |
| `artifact-digest` | SHA-256 checksum of the uploaded ZIP archive. |

Artifacts are stored by si-artifacts and do not consume GitHub artifact storage.
They do not appear in GitHub's native artifact list; the action adds a link to the
job summary. Other jobs in the same workflow run can retrieve them with
[download-artifact](../download-artifact).

Archives use paths relative to the common search root. Symlinks and special files
are excluded. Executable permissions are not preserved during extraction; create
a tar archive first when permissions matter. Raw-file uploads are unsupported.

## Maintenance

This directory is generated from `vendor/si-artifacts` in
`silitics/infrastructure`. Update its source there, run the integration suite, and
export the tested Nix package with `scripts/export-actions.sh`. Commit the action
manifest, documentation, bundle and third-party license notices together.
