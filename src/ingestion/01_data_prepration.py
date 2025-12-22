import io
import zipfile
import requests
import frontmatter
from urllib.parse import urlparse

def read_repo_data(repo_url: str):
    """
    Download and parse all markdown files from a GitHub repository.
    
    Args:
        repo_url: Full GitHub repository URL (e.g., https://github.com/owner/repo)
    
    Returns:
        List of dictionaries containing file content and metadata
    """
    # Parse the GitHub URL to extract owner and repo name
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}. Expected format: https://github.com/owner/repo")
    
    repo_owner = path_parts[0]
    repo_name = path_parts[1]
    
    prefix = 'https://codeload.github.com' 
    url = f'{prefix}/{repo_owner}/{repo_name}/zip/refs/heads/main'
    resp = requests.get(url)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to download repository: {resp.status_code}")

    repository_data = []
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    
    for file_info in zf.infolist():
        filename = file_info.filename
        filename_lower = filename.lower()

        if not (filename_lower.endswith('.md') 
            or filename_lower.endswith('.mdx')):
            continue
    
        try:
            with zf.open(file_info) as f_in:
                content = f_in.read().decode('utf-8', errors='ignore')
                post = frontmatter.loads(content)
                data = post.to_dict()
                data['filename'] = filename
                repository_data.append(data)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    zf.close()
    return repository_data
