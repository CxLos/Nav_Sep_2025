import os
import requests
import base64
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

class GitHubReplicator:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY")  # Format: "username/repo"
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        if not self.repo:
            raise ValueError("GITHUB_REPOSITORY not found in environment variables")
            
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = f"https://api.github.com/repos/{self.repo}"
        print(f"🔗 Repository: {self.repo}")
        print(f"🔗 API Base: {self.base_url}")

    def debug_repository(self):
        """Debug repository structure"""
        print(f"\n🔍 Debugging repository structure...")
        
        # Check repository root
        url = f"{self.base_url}/contents"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            contents = response.json()
            print(f"\n📁 Repository root contains:")
            for item in contents[:10]:  # Show first 10 items
                icon = "📁" if item['type'] == 'dir' else "📄"
                print(f"  {icon} {item['name']}")
            if len(contents) > 10:
                print(f"  ... and {len(contents) - 10} more items")
        else:
            print(f"❌ Error accessing repository: {response.status_code}")
            if response.status_code == 401:
                print("   This might be a token permission issue")
            elif response.status_code == 404:
                print("   Repository not found - check GITHUB_REPOSITORY in .env")
            return

        # Check for potential October folders
        potential_paths = [
            "October_2025",
            "Nav_Oct_2025", 
            "Dashboard",
            "reports",
            "2025"
        ]
        
        print(f"\n🔍 Checking for potential source folders:")
        for path in potential_paths:
            url = f"{self.base_url}/contents/{path}"
            response = requests.get(url, headers=self.headers)
            status = "✓ EXISTS" if response.status_code == 200 else "✗ NOT FOUND"
            print(f"  {status}: {path}")

    def get_folder_contents(self, path: str) -> List[Dict]:
        """Get all files and folders in a directory"""
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching {path}: {response.status_code}")
            if response.status_code == 404:
                print(f"  Path '{path}' not found in repository")
            return []

    def get_file_content(self, path: str) -> tuple[str, str]:
        """Get content and SHA of a specific file"""
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            file_data = response.json()
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content, file_data['sha']
        else:
            print(f"Error fetching file {path}: {response.status_code}")
            return "", ""

    def create_file(self, path: str, content: str, message: str):
        """Create a new file"""
        url = f"{self.base_url}/contents/{path}"
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
        }
        
        response = requests.put(url, json=data, headers=self.headers)
        
        if response.status_code == 201:
            print(f"✓ Created: {path}")
            return True
        else:
            print(f"✗ Error creating {path}: {response.status_code}")
            return False

    def update_content_references(self, content: str) -> str:
        """Update internal references from October to October"""
        replacements = {
            'Nav_Oct_2025': 'Nav_Oct_2025',
            'October_2025': 'October_2025',
            'October': 'October',
            'october': 'october',
            'Oct': 'Oct',
            'oct': 'oct',
            '2025-10': '2025-10',
            '10/2025': '10/2025',
        }
        
        updated_content = content
        for old, new in replacements.items():
            updated_content = updated_content.replace(old, new)
        
        return updated_content

    def replicate_folder(self, source_folder: str, target_folder: str):
        """Replicate folder structure from source to target"""
        print(f"\n🚀 Starting replication: {source_folder} → {target_folder}")
        
        # Get all contents from source folder
        contents = self.get_folder_contents(source_folder)
        
        if not contents:
            print(f"❌ No contents found in {source_folder}")
            return
        
        success_count = 0
        total_count = 0
        
        for item in contents:
            total_count += 1
            
            if item['type'] == 'file':
                # Process file
                source_path = item['path']
                target_path = source_path.replace(source_folder, target_folder)
                
                print(f"📄 Processing: {source_path}")
                
                # Get file content
                content, sha = self.get_file_content(source_path)
                
                if content:
                    # Update content references
                    updated_content = self.update_content_references(content)
                    
                    # Create new file
                    if self.create_file(
                        target_path, 
                        updated_content, 
                        f"chore: replicate {source_folder} structure for {target_folder}"
                    ):
                        success_count += 1
                        
            elif item['type'] == 'dir':
                # Recursively process subdirectories
                print(f"📁 Processing directory: {item['path']}")
                self.replicate_folder(
                    item['path'], 
                    item['path'].replace(source_folder, target_folder)
                )
        
        print(f"\n✅ Completed: {success_count}/{total_count} files processed successfully")

def main():
    try:
        replicator = GitHubReplicator()
        
        # Since the files are in the root, we need to replicate the root structure
        # to a new October_2025 folder
        
        print("\n🚀 Starting replication of root files to October_2025 folder...")
        
        # Get all files and folders from root
        contents = replicator.get_folder_contents("")  # Empty string for root
        
        if not contents:
            print("❌ No contents found in repository root")
            return
        
        # Create October_2025 folder by replicating each file
        success_count = 0
        total_count = len(contents)
        
        for item in contents:
            if item['type'] == 'file' and item['name'] not in ['.gitignore', 'README.md']:
                # Skip certain files, replicate others
                source_path = item['name']
                target_path = f"October_2025/{source_path}"
                
                print(f"📄 Replicating: {source_path} → {target_path}")
                
                # Get file content
                content, sha = replicator.get_file_content(source_path)
                
                if content:
                    # Update content references
                    updated_content = replicator.update_content_references(content)
                    
                    # Create new file in October_2025 folder
                    if replicator.create_file(
                        target_path, 
                        updated_content, 
                        "chore: replicate Nav_Oct_2025 structure for October_2025"
                    ):
                        success_count += 1
                        
            elif item['type'] == 'dir':
                # Replicate entire folders
                source_folder = item['name']
                target_folder = f"October_2025/{source_folder}"
                
                print(f"📁 Replicating folder: {source_folder} → {target_folder}")
                replicator.replicate_folder(source_folder, target_folder)
        
        print(f"\n✅ Completed: Successfully replicated repository structure to October_2025/")
        print(f"📊 Files processed: {success_count}/{total_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

# =====================================================================

# import os
# from dotenv import load_dotenv
# from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
# from langchain_community.utilities.github import GitHubAPIWrapper
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain_openai import ChatOpenAI
# from langchain import hub

# # Load environment variables
# load_dotenv()

# # Auth and setup - Read token and repo from environment file
# github = GitHubAPIWrapper(
#     github_token=os.getenv("GITHUB_TOKEN"),
#     github_repository=os.getenv("GITHUB_REPOSITORY")
# )

# toolkit = GitHubToolkit.from_github_api_wrapper(github)
# tools = toolkit.get_tools()

# # Updated agent initialization
# llm = ChatOpenAI(model="gpt-4")
# prompt = hub.pull("hwchase17/react")
# agent = create_react_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# # Task prompt
# task = """
# Replicate the folder structure and files from October_2025 to a new folder called October_2025.
# Update any internal references to 'October' or '2025-10' to 'October' or '2025-10'.
# Preserve formatting, filenames, and markdown structure.
# Commit with message: 'chore: replicate October_2025 structure for October_2025'
# """

# agent_executor.run(task)