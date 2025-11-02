# GitHub MCP Setup Guide for Cursor

This guide explains how to set up the GitHub Model Context Protocol (MCP) server in Cursor IDE to enable GitHub repository operations, including creating and uploading code to public repositories.

## Installation Status

✅ **GitHub MCP server package installed globally**
- Package: `@modelcontextprotocol/server-github`
- Installed via: `npm install -g @modelcontextprotocol/server-github`

✅ **Cursor MCP configuration created**
- Location: `~/.cursor/mcp.json`
- Configured to use npx to run the GitHub MCP server via stdio protocol

## Next Steps: GitHub Authentication

To enable the GitHub MCP server to interact with your GitHub account, you need to create a Personal Access Token (PAT) and configure it.

### Step 1: Create a GitHub Personal Access Token

1. Go to GitHub Settings:
   - Visit https://github.com/settings/tokens
   - Or navigate: GitHub Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. Generate a new token:
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Cursor MCP Server")
   - Set an expiration date (recommended: 90 days or custom)

3. Select required scopes/permissions:
   - ✅ **repo** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   - ✅ **workflow** (Update GitHub Action workflows)
   - ✅ **write:packages** (if you need to publish packages)
   - ✅ **delete:packages** (if you need to delete packages)
   - ✅ **admin:repo_hook** (Full control of repository hooks)
   - ✅ **admin:org_hook** (Full control of organization hooks)
   - ✅ **gist** (Create gists)
   - ✅ **notifications** (Access notifications)
   - ✅ **user:email** (Access user email addresses)
   - ✅ **user:follow** (Follow and unfollow users)

   **Minimum required for repository operations:**
   - `repo` (full control) - This is the most important scope for creating and managing repositories

4. Generate and copy the token:
   - Click "Generate token"
   - **Important**: Copy the token immediately - you won't be able to see it again!
   - Save it securely (password manager recommended)

### Step 2: Set Environment Variable

Set the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable in your shell profile:

#### For zsh (macOS default):
```bash
# Add to ~/.zshrc
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
```

Then reload your shell:
```bash
source ~/.zshrc
```

#### For bash:
```bash
# Add to ~/.bash_profile or ~/.bashrc
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
```

Then reload your shell:
```bash
source ~/.bash_profile
# or
source ~/.bashrc
```

#### Verify the environment variable is set:
```bash
echo $GITHUB_PERSONAL_ACCESS_TOKEN
```

### Step 3: Update Cursor MCP Configuration (if needed)

The configuration file is located at `~/.cursor/mcp.json`. If you need to modify the token reference or use a different environment variable name, edit this file.

Current configuration:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

**Note**: If the environment variable substitution doesn't work, you can directly specify the token in the config file (not recommended for security reasons) or use a different approach.

### Step 4: Restart Cursor

After setting up the environment variable:
1. Close Cursor completely
2. Ensure the environment variable is available in your shell
3. Launch Cursor from the terminal to inherit environment variables:
   ```bash
   /Applications/Cursor.app/Contents/MacOS/Cursor
   ```
   
   Or ensure Cursor is launched in a way that inherits your shell environment.

### Step 5: Verify GitHub MCP Server

1. Open Cursor
2. The GitHub MCP server should automatically connect when Cursor starts
3. You should see GitHub-related tools available in Cursor's MCP interface
4. Try using GitHub operations through Cursor's AI assistant

## Usage: Creating and Uploading a Public Repository

Once set up, you can use Cursor's AI assistant with GitHub MCP capabilities to:

1. **Create a new repository**:
   - Ask Cursor to create a GitHub repository
   - Specify name, description, and visibility (public/private)

2. **Upload code to a repository**:
   - Initialize git repository locally
   - Add files and commit
   - Push to GitHub using GitHub MCP tools

3. **Manage repositories**:
   - View repository information
   - Create issues
   - Manage pull requests
   - Update repository settings

## Troubleshooting

### Issue: MCP server not connecting

**Solution**:
- Verify the environment variable is set: `echo $GITHUB_PERSONAL_ACCESS_TOKEN`
- Restart Cursor from terminal to inherit environment variables
- Check `~/.cursor/mcp.json` configuration syntax

### Issue: Authentication errors

**Solution**:
- Verify your GitHub PAT is valid and not expired
- Check that the token has the required scopes (especially `repo`)
- Regenerate the token if needed

### Issue: Permission denied errors

**Solution**:
- Ensure your PAT has the `repo` scope with full permissions
- For organization repositories, ensure the token has organization permissions
- Check repository settings if working with private repos

### Issue: Package deprecation warning

**Note**: The npm package shows a deprecation warning. The GitHub MCP server is still functional, but you may want to check for:
- Alternative installation methods (Docker)
- Official migration path
- Community-maintained alternatives

## Alternative: Docker Setup

If the npm package doesn't work reliably, you can use Docker instead. Update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_HOST",
        "ghcr.io/github/github-mcp-server",
        "stdio"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}",
        "GITHUB_HOST": "${GITHUB_HOST:-github.com}"
      }
    }
  }
}
```

## Security Best Practices

1. **Never commit tokens to git**:
   - Add `~/.cursor/mcp.json` to `.gitignore` if it contains tokens
   - Use environment variables instead of hardcoding tokens

2. **Use token with minimal required permissions**:
   - Only grant the scopes you actually need
   - Regularly review and rotate tokens

3. **Set token expiration**:
   - Use short expiration periods (30-90 days)
   - Set calendar reminders to rotate tokens

4. **Monitor token usage**:
   - Regularly check GitHub's security log for token activity
   - Revoke tokens if suspicious activity is detected

## Additional Resources

- [GitHub Personal Access Tokens Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [GitHub MCP Server Repository](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

## Verification Checklist

- [ ] GitHub PAT created with `repo` scope
- [ ] Environment variable `GITHUB_PERSONAL_ACCESS_TOKEN` set in shell
- [ ] Environment variable verified with `echo $GITHUB_PERSONAL_ACCESS_TOKEN`
- [ ] Cursor MCP configuration file exists at `~/.cursor/mcp.json`
- [ ] Cursor restarted from terminal to inherit environment
- [ ] GitHub MCP server connects successfully in Cursor
- [ ] Can perform GitHub operations through Cursor

