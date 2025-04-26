# Deploying Folio to Hugging Face Spaces

This guide explains how to deploy the Folio application to Hugging Face Spaces using GitHub Actions.

## Prerequisites

1. A [Hugging Face](https://huggingface.co/) account
2. A GitHub repository with the Folio application code

## Setup Steps

### 1. Create a Hugging Face Space

1. Log in to your Hugging Face account
2. Go to your profile and click on "New Space"
3. Choose a name for your Space (e.g., "folio")
4. Select "Docker" as the Space SDK
5. Make the Space public or private according to your needs
6. Click "Create Space"

### 2. Generate a Hugging Face Access Token

1. Go to your Hugging Face profile settings
2. Navigate to "Access Tokens"
3. Create a new token with "write" permissions
4. Copy the token for the next step

### 3. Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:
   - `HF_TOKEN`: Your Hugging Face access token
   - `HF_USERNAME`: Your Hugging Face username

### 4. Deploy to Hugging Face Spaces

The GitHub Actions workflow will automatically deploy to Hugging Face Spaces when you push to the main branch. You can also trigger the deployment manually:

1. Go to your GitHub repository
2. Navigate to "Actions" > "Deploy to Hugging Face Spaces"
3. Click "Run workflow"

## How It Works

The GitHub Actions workflow:

1. Checks out your code
2. Logs in to Hugging Face using your token
3. Clones your Hugging Face Space repository
4. Copies the necessary files to the Space repository
5. Creates a README.md for the Space
6. Adds Hugging Face Space configuration
7. Commits and pushes the changes to your Space

## Accessing Your Deployed Application

Once deployed, your application will be available at:

```
https://huggingface.co/spaces/{HF_USERNAME}/folio
```

## Troubleshooting

- **Deployment Failures**: Check the GitHub Actions logs for detailed error messages
- **Application Errors**: Check the Hugging Face Space logs in the "Factory" tab
- **Docker Build Issues**: Ensure your Dockerfile is correctly configured for Hugging Face Spaces

## Command-Line Deployment

For manual deployment from the command line:

1. Install the Hugging Face CLI:
   ```bash
   pip install huggingface_hub
   ```

2. Log in to Hugging Face:
   ```bash
   huggingface-cli login
   ```

3. Clone your Space repository:
   ```bash
   git clone https://huggingface.co/{HF_USERNAME}/folio space-repo
   ```

4. Copy your files to the Space repository:
   ```bash
   cp -r src space-repo/
   cp -r config space-repo/
   cp requirements.txt space-repo/
   cp Dockerfile space-repo/
   ```

5. Commit and push changes:
   ```bash
   cd space-repo
   git add .
   git commit -m "Update application"
   git push
   ```

## Monitoring and Maintenance

- Monitor your application's performance in the Hugging Face Space dashboard
- Check resource usage and logs in the "Factory" tab
- Update your application by pushing new changes to the Space repository
