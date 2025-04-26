# Hugging Face Deployment Command

Date: 2025-04-05

## Overview

This update adds a new `make deploy-hf` command to simplify the deployment process to Hugging Face Spaces. The command automates the Git LFS setup and push process to ensure a smooth deployment experience.

## Changes

### 1. Added `deploy-hf` Target to Makefile

Added a new target to the Makefile that:

1. Checks if Git LFS is installed
2. Verifies or adds the Hugging Face Space remote
3. Ensures Git LFS is properly configured for `.pkl` files
4. Initializes Git LFS
5. Pushes the current branch to the Hugging Face Space

```makefile
# Deploy to Hugging Face Spaces
deploy-hf:
	@echo "Deploying to Hugging Face Spaces..."
	@echo "Checking for Git LFS..."
	@if ! command -v git-lfs &> /dev/null; then \
		echo "Error: Git LFS is not installed. Please install it first."; \
		echo "  macOS: brew install git-lfs"; \
		echo "  Linux: apt-get install git-lfs"; \
		exit 1; \
	fi
	@echo "Checking if Hugging Face Space remote exists..."
	@if ! git remote | grep -q "space"; then \
		echo "Adding Hugging Face Space remote..."; \
		git remote add space git@huggingface.co:mingdom/folio; \
	fi
	@echo "Ensuring Git LFS is tracking .pkl files..."
	@grep -q "*.pkl filter=lfs diff=lfs merge=lfs -text" .gitattributes || \
		echo "*.pkl filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
	@echo "Initializing Git LFS..."
	@git lfs install
	@echo "Pushing to Hugging Face Space..."
	@git push space main:main
	@echo "\n✅ Deployment to Hugging Face Space completed!"
	@echo "Your application is now available at: https://huggingface.co/spaces/mingdom/folio"
```

## Usage

To deploy the application to Hugging Face Spaces:

1. Make sure you have Git LFS installed:
   ```bash
   # macOS
   brew install git-lfs
   
   # Ubuntu/Debian
   apt-get install git-lfs
   ```

2. Commit your changes to the main branch

3. Run the deployment command:
   ```bash
   make deploy-hf
   ```

4. The application will be deployed to Hugging Face Spaces and available at:
   ```
   https://huggingface.co/spaces/mingdom/folio
   ```

## Benefits

- Simplifies the deployment process to a single command
- Ensures Git LFS is properly configured for binary files
- Automatically sets up the Hugging Face Space remote if it doesn't exist
- Provides clear feedback during the deployment process
- Handles the SSH-based remote configuration for Hugging Face

## Notes

- This command assumes you have already set up SSH authentication for Hugging Face
- The command pushes from the current branch to the `main` branch on Hugging Face
- Binary files (`.pkl`) are automatically handled by Git LFS
- The deployment uses the existing Dockerfile which is configured for Hugging Face Spaces
