# Silitics' GitHub Actions

This repository contains reusable GitHub actions used across Silitics projects.
Reference an action's directory and pin it to a reviewed commit:

```yaml
- uses: silitics/actions/upload-artifact@FULL_REVIEWED_COMMIT_SHA
```

## Available Actions

| Action | Purpose |
| --- | --- |
| [deploy-site](deploy-site/action.yml) | Deploy a static site to S3-compatible storage. |
| [upload-artifact](upload-artifact) | Upload files to si-artifacts using GitHub OIDC. |
| [download-artifact](download-artifact) | Download and verify artifacts from the current workflow run. |

## Artifact Storage

The artifact actions connect to a separately operated si-artifacts service.
The service stores archives outside GitHub and authorizes requests using the
calling job's OIDC identity. Its HTTPS endpoint must be reachable from the runner.

Grant each uploading or downloading job `id-token: write`. Set the repository
variable `SI_ARTIFACTS_URL` to the service's CI endpoint, then pass
`server-url: ${{ vars.SI_ARTIFACTS_URL }}`. Refer to each action's documentation for
complete examples, inputs and compatibility limits.

Public access to these action bundles does not grant access to artifact storage.
The service must explicitly permit the caller's repository and workflow.

## Artifact Action Maintenance

The artifact action directories are generated from
`vendor/si-artifacts` in `silitics/infrastructure`. Their source and integration
tests are maintained with the service so protocol changes can be tested together.
To update the bundles, run this command from an infrastructure checkout:

```sh
bash vendor/si-artifacts/scripts/export-actions.sh /path/to/actions-checkout
```

The export builds the Nix package and runs its integration suite before copying
the two artifact action directories. Review and commit the resulting files here.
The export does not modify `deploy-site` or push changes.
