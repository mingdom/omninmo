# Deploying Folio on Hugging Face Spaces

This document provides step-by-step instructions for deploying the Folio application on Hugging Face Spaces using Docker with your existing GitHub repository.

## Prerequisites

Before you begin, make sure you have:

1. A [Hugging Face account](https://huggingface.co/join)
2. The Folio application containerized with Docker (completed in previous steps)
3. Your existing GitHub repository for the Folio application
4. Git installed on your local machine
5. Docker installed on your local machine

## Step 1: Create a New Hugging Face Space

1. Log in to your Hugging Face account
2. Navigate to [Hugging Face Spaces](https://huggingface.co/spaces)
3. Click on "Create new Space"
4. Fill in the following details:
   - **Owner**: `mingdom` (your Hugging Face username)
   - **Space name**: `folio`
   - **License**: Choose an appropriate license (e.g., MIT)
   - **Space SDK**: Select "Docker"
   - **Visibility**: Choose "Public" or "Private" based on your needs
5. Click "Create Space"

## Step 2: Add Hugging Face Space as a Git Remote

Instead of using the GitHub integration, we'll directly push to the Hugging Face Space repository using Git remotes:

1. Navigate to your local repository:

```bash
cd /path/to/your/folio/repository
```

2. Add the Hugging Face Space as a remote repository:

```bash
git remote add space https://huggingface.co/spaces/mingdom/folio
```

3. Verify the remote was added correctly:

```bash
git remote -v
```

You should see both your original GitHub remote (`origin`) and the new Hugging Face Space remote (`space`).

## Step 3: Push Your Repository to Hugging Face

The Dockerfile has been configured to automatically detect the Hugging Face environment and use the correct port (7860 for Hugging Face Spaces, 8050 for local development). No modifications to your code are needed.

Simply push your repository to the Hugging Face Space:

```bash
# Push to the Hugging Face Space repository
git push space main:main
```

This command pushes your `main` branch to the `main` branch of the Hugging Face Space repository.

The Dockerfile includes logic to detect the Hugging Face environment and automatically use port 7860 when running on Hugging Face Spaces.

## Step 4: Monitor the Deployment

1. Go to your Hugging Face Space page (`https://huggingface.co/spaces/mingdom/folio`)
2. Click on the "Settings" tab
3. Select "Factory" from the sidebar
4. Monitor the build logs to ensure the deployment is successful

The build process may take a few minutes. Once completed, your Folio application will be available at `https://huggingface.co/spaces/mingdom/folio`.

## Step 5: Configure Persistent Storage (Optional)

If you want to store uploaded portfolios persistently:

1. Go to your Space's Settings
2. Click on "Persistent storage"
3. Enable persistent storage
4. Update your application to save uploaded files to the persistent storage directory (typically `/data`)

## Troubleshooting

### Common Issues

1. **Git Authentication Issues**:
   - You may need to authenticate with Hugging Face when pushing to the Space repository
   - Use a personal access token if prompted for credentials
   - If using SSH, ensure your SSH keys are properly configured

2. **Build Failures**:
   - Check the build logs in the Factory tab
   - Ensure all dependencies are correctly specified in the Dockerfile
   - Verify that the port configuration is correct (7860)
   - Make sure your Dockerfile is in the root of the repository

3. **Application Errors**:
   - Check the application logs in the Logs tab
   - Ensure environment variables are correctly set
   - Verify that the application is binding to the correct host (0.0.0.0)

4. **Performance Issues**:
   - Consider upgrading your Space's hardware if the application is slow
   - Optimize the Docker image size by removing unnecessary dependencies

### Getting Help

If you encounter issues that you can't resolve:

1. Check the [Hugging Face Spaces documentation](https://huggingface.co/docs/hub/spaces)
2. Refer to the [Hugging Face Spaces GitHub Actions guide](https://huggingface.co/docs/hub/spaces-github-actions)
3. Ask for help in the [Hugging Face community forums](https://discuss.huggingface.co/)

## Updating the Deployment

To update your deployed application:

1. Make changes to your local `main` branch
2. Test the changes locally using Docker
3. Commit your changes
4. Push directly to the Hugging Face Space repository:

```bash
git push space main:main
```

This will trigger a rebuild of your Space with the updated code.

## Security Considerations

1. Be careful with sensitive financial data
2. Consider using a private Space if your data is sensitive
3. Do not include API keys or credentials in your repository
4. Use environment variables for configuration when possible
5. Be cautious with Git credentials when pushing to the Hugging Face repository

## Conclusion

Your Folio application is now deployed on Hugging Face Spaces and accessible at `https://huggingface.co/spaces/mingdom/folio`. By using Git remotes, you can easily maintain and update your deployment directly from your local repository. The application will automatically restart if it crashes, and Hugging Face provides monitoring and logging capabilities to help you maintain your deployment.

This deployment approach gives you full control over the deployment process while leveraging the hosting capabilities of Hugging Face Spaces.
