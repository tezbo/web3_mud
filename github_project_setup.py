#!/usr/bin/env python3
"""
GitHub Project Setup Script
Automates creation of GitHub Project, columns, and custom fields for Release 1.0

Prerequisites:
1. GitHub Personal Access Token with scopes: repo, project, write:org
2. Install requests: pip install requests

Usage:
    export GITHUB_TOKEN="your_token_here"
    python github_project_setup.py
"""

import os
import sys
import requests
import json
from typing import Dict, Any, List, Optional


class GitHubProjectSetup:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.project_id = None
        
    def graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request to GitHub API"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code} - {response.text}")
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
            
        return result["data"]
    
    def get_repository_id(self) -> str:
        """Get the repository node ID"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            id
          }
        }
        """
        
        data = self.graphql_request(query, {"owner": self.owner, "repo": self.repo})
        return data["repository"]["id"]
    
    def get_organization_id(self) -> Optional[str]:
        """Get organization ID if repository is owned by an org"""
        query = """
        query($owner: String!) {
          organization(login: $owner) {
            id
          }
        }
        """
        
        try:
            data = self.graphql_request(query, {"owner": self.owner})
            return data["organization"]["id"]
        except:
            return None
    
    def create_project(self, title: str, owner_id: str) -> str:
        """Create a new GitHub Project (v2)"""
        query = """
        mutation($ownerId: ID!, $title: String!) {
          createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 {
              id
              title
              number
            }
          }
        }
        """
        
        print(f"Creating project: {title}...")
        data = self.graphql_request(query, {"ownerId": owner_id, "title": title})
        project = data["createProjectV2"]["projectV2"]
        
        print(f"✅ Project created: {project['title']} (#{project['number']})")
        return project["id"]
    
    def link_project_to_repository(self, project_id: str, repo_id: str):
        """Link the project to the repository"""
        query = """
        mutation($projectId: ID!, $repositoryId: ID!) {
          linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
            repository {
              id
            }
          }
        }
        """
        
        print("Linking project to repository...")
        self.graphql_request(query, {"projectId": project_id, "repositoryId": repo_id})
        print("✅ Project linked to repository")
    
    def get_project_fields(self, project_id: str) -> Dict[str, str]:
        """Get existing project fields"""
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2Field {
                    id
                    name
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                  }
                  ... on ProjectV2IterationField {
                    id
                    name
                  }
                }
              }
            }
          }
        }
        """
        
        data = self.graphql_request(query, {"projectId": project_id})
        fields = {}
        for field in data["node"]["fields"]["nodes"]:
            fields[field["name"]] = field["id"]
        return fields
    
    def create_single_select_field(self, project_id: str, name: str, options: List[Dict[str, str]]) -> str:
        """Create a single-select custom field"""
        query = """
        mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            dataType: SINGLE_SELECT,
            name: $name,
            singleSelectOptions: $options
          }) {
            projectV2Field {
              ... on ProjectV2SingleSelectField {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Creating field: {name}...")
        formatted_options = [{"name": opt["name"], "color": opt["color"]} for opt in options]
        data = self.graphql_request(query, {
            "projectId": project_id,
            "name": name,
            "options": formatted_options
        })
        
        field_id = data["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"✅ Created field: {name}")
        return field_id
    
    def create_text_field(self, project_id: str, name: str) -> str:
        """Create a text custom field"""
        query = """
        mutation($projectId: ID!, $name: String!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            dataType: TEXT,
            name: $name
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Creating field: {name}...")
        data = self.graphql_request(query, {"projectId": project_id, "name": name})
        field_id = data["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"✅ Created field: {name}")
        return field_id
    
    def create_number_field(self, project_id: str, name: str) -> str:
        """Create a number custom field"""
        query = """
        mutation($projectId: ID!, $name: String!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            dataType: NUMBER,
            name: $name
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Creating field: {name}...")
        data = self.graphql_request(query, {"projectId": project_id, "name": name})
        field_id = data["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"✅ Created field: {name}")
        return field_id
    
    def create_date_field(self, project_id: str, name: str) -> str:
        """Create a date custom field"""
        query = """
        mutation($projectId: ID!, $name: String!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            dataType: DATE,
            name: $name
          }) {
            projectV2Field {
              ... on ProjectV2Field {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Creating field: {name}...")
        data = self.graphql_request(query, {"projectId": project_id, "name": name})
        field_id = data["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"✅ Created field: {name}")
        return field_id
    
    def create_iteration_field(self, project_id: str, name: str) -> str:
        """Create an iteration custom field"""
        query = """
        mutation($projectId: ID!, $name: String!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            dataType: ITERATION,
            name: $name
          }) {
            projectV2Field {
              ... on ProjectV2IterationField {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Creating field: {name}...")
        data = self.graphql_request(query, {"projectId": project_id, "name": name})
        field_id = data["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"✅ Created field: {name}")
        return field_id
    
    def setup_project(self):
        """Main setup method"""
        print("\n🚀 Starting GitHub Project Setup for Release 1.0\n")
        print(f"Repository: {self.owner}/{self.repo}\n")
        
        # Get repository ID
        print("Step 1: Getting repository information...")
        repo_id = self.get_repository_id()
        print(f"✅ Repository ID: {repo_id}\n")
        
        # Get owner ID (org or user)
        print("Step 2: Getting owner information...")
        owner_id = self.get_organization_id()
        if not owner_id:
            # If not an org, get user ID
            query = """
            query($login: String!) {
              user(login: $login) {
                id
              }
            }
            """
            data = self.graphql_request(query, {"login": self.owner})
            owner_id = data["user"]["id"]
        print(f"✅ Owner ID: {owner_id}\n")
        
        # Create project
        print("Step 3: Creating project...")
        project_id = self.create_project("Aethermoor MUD - Release 1.0", owner_id)
        self.project_id = project_id
        print()
        
        # Link project to repository
        print("Step 4: Linking project to repository...")
        self.link_project_to_repository(project_id, repo_id)
        print()
        
        # Create custom fields
        print("Step 5: Creating custom fields...\n")
        
        # Epic field
        epic_options = [
            {"name": "Technical Debt", "color": "RED"},
            {"name": "Sensory Richness", "color": "ORANGE"},
            {"name": "Ambient Life", "color": "YELLOW"},
            {"name": "AI NPCs", "color": "GREEN"},
            {"name": "World Expansion", "color": "BLUE"},
            {"name": "Polish", "color": "PURPLE"},
            {"name": "Testing", "color": "PINK"}
        ]
        self.create_single_select_field(project_id, "Epic", epic_options)
        
        # Priority field
        priority_options = [
            {"name": "P0 (Blocker)", "color": "RED"},
            {"name": "P1 (Critical)", "color": "ORANGE"},
            {"name": "P2 (Important)", "color": "YELLOW"},
            {"name": "P3 (Nice to Have)", "color": "GREEN"}
        ]
        self.create_single_select_field(project_id, "Priority", priority_options)
        
        # Effort field
        self.create_number_field(project_id, "Effort")
        
        # Owner field
        self.create_text_field(project_id, "Owner")
        
        # Sprint field
        self.create_iteration_field(project_id, "Sprint")
        
        # Due Date field
        self.create_date_field(project_id, "Due Date")
        
        print("\n✅ All custom fields created!\n")
        
        print("=" * 60)
        print("🎉 GitHub Project Setup Complete!")
        print("=" * 60)
        print(f"\nProject: Aethermoor MUD - Release 1.0")
        print(f"URL: https://github.com/users/{self.owner}/projects")
        print("\nNext steps:")
        print("1. View your project on GitHub")
        print("2. Adjust column names if needed (Status field)")
        print("3. Proceed to Step 2: Creating Labels")
        print("\n")


def main():
    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export GITHUB_TOKEN='your_github_token_here'")
        print("\nTo create a token:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Select scopes: repo, project, write:org")
        print("  4. Copy the token and set it as environment variable")
        sys.exit(1)
    
    # Repository details
    owner = "tezbo"
    repo = "web3_mud"
    
    # Run setup
    setup = GitHubProjectSetup(token, owner, repo)
    try:
        setup.setup_project()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
