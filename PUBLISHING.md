# Publishing to PyPI with Trusted Publisher

This project is configured to use PyPI's Trusted Publisher feature with GitHub Actions for secure, credential-free publishing.

## Setup Steps

### 1. Configure PyPI Trusted Publisher

Before the first publish, you need to configure the trusted publisher on PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Scroll to "Add a new pending publisher"
3. Fill in the form:
   - **PyPI Project Name**: `pythonalsa`
   - **Owner**: `865charlesw`
   - **Repository name**: `pythonalsa`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click "Add"

This tells PyPI to trust releases from your GitHub repository's workflow.

### 2. Create a GitHub Environment (Optional but Recommended)

For additional security, create a protected environment:

1. Go to your repository settings: https://github.com/865charlesw/pythonalsa/settings/environments
2. Click "New environment"
3. Name it `pypi`
4. (Optional) Add protection rules:
   - Required reviewers: Add yourself or team members
   - Deployment branches: Only allow releases from `main` branch

### 3. Publishing a Release

Once configured, publish new versions by creating a GitHub release:

```bash
# Tag a new version
git tag v0.1.0
git push origin v0.1.0

# Or create a release through GitHub UI
```

**Via GitHub UI:**
1. Go to https://github.com/865charlesw/pythonalsa/releases/new
2. Choose or create a tag (e.g., `v0.1.0`)
3. Fill in release title and description
4. Click "Publish release"

The GitHub Action will automatically:
- Build the package
- Publish to PyPI using trusted publishing (no tokens/passwords needed!)

### 4. Manual Triggering (Optional)

You can also manually trigger the workflow:
1. Go to https://github.com/865charlesw/pythonalsa/actions/workflows/publish.yml
2. Click "Run workflow"
3. Select the branch and run

## Workflow Overview

The workflow (`.github/workflows/publish.yml`) has two jobs:

1. **build**: Builds the Python package distribution files (wheel and sdist)
2. **publish-to-pypi**: Publishes the built distributions to PyPI using OpenID Connect (OIDC) for authentication

## Benefits of Trusted Publishing

- ✅ No API tokens or passwords to manage
- ✅ No secrets stored in GitHub
- ✅ Short-lived, automatically rotating credentials
- ✅ More secure than long-lived API tokens
- ✅ Easier to set up and maintain

## Troubleshooting

If publishing fails:

1. **"Trusted publisher not configured"**: Complete Step 1 above
2. **"Permission denied"**: Ensure the workflow has `id-token: write` permission (already configured)
3. **"Environment not found"**: Create the `pypi` environment in GitHub settings or remove the `environment` section from the workflow

## Version Bumping

Remember to update the version in `pyproject.toml` before creating a release:

```toml
[project]
version = "0.1.1"  # Increment this
```

Then commit, tag, and create a release with the matching version.
