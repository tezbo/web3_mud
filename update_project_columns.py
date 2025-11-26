import os
import sys
import requests
from github_project_setup import GitHubProjectSetup

class ProjectColumnUpdater(GitHubProjectSetup):
    def get_status_field(self, project_id):
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        data = self.graphql_request(query, {"projectId": project_id})
        for field in data["node"]["fields"]["nodes"]:
            if field.get("name") == "Status":
                return field
        return None

    def add_option(self, project_id, field_id, name, color="GRAY"):
        query = """
        mutation($projectId: ID!, $fieldId: ID!, $name: String!, $color: ProjectV2SingleSelectFieldOptionColor!) {
          updateProjectV2SingleSelectField(input: {
            projectId: $projectId,
            fieldId: $fieldId,
            singleSelectOptions: [{
              name: $name,
              color: $color,
              description: ""
            }]
          }) {
            projectV2SingleSelectField {
              id
              options {
                id
                name
              }
            }
          }
        }
        """
        # Note: updateProjectV2SingleSelectField replaces ALL options if you pass the list.
        # We need to append. But the API might be different.
        # Actually, there isn't a simple "add option" mutation. We have to update the field definition.
        # Wait, let's check if we can just create options.
        # The mutation is `updateProjectV2SingleSelectField`.
        pass

    def update_status_options(self, project_id):
        field = self.get_status_field(project_id)
        if not field:
            print("❌ Status field not found")
            return

        print(f"Found Status field: {field['id']}")
        current_options = field['options']
        print(f"Current options: {[opt['name'] for opt in current_options]}")
        
        # Desired options in order
        desired = ["Backlog", "Planning", "In Progress", "Review", "Done", "Blocked"]
        
        # We need to construct the full list of options to send
        # We'll map existing options to preserve IDs if possible, or just send names
        # The API requires existing option IDs to update them, or no ID to create new.
        
        new_options = []
        for name in desired:
            existing = next((o for o in current_options if o['name'] == name), None)
            if existing:
                new_options.append({"id": existing['id'], "name": name, "color": "GRAY"}) # Keep existing
            else:
                # New option
                color = "GRAY"
                if name == "In Progress": color = "BLUE"
                if name == "Review": color = "YELLOW"
                if name == "Done": color = "GREEN"
                if name == "Blocked": color = "RED"
                if name == "Planning": color = "PURPLE"
                new_options.append({"name": name, "color": color})

        query = """
        mutation($projectId: ID!, $fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
          updateProjectV2SingleSelectField(input: {
            projectId: $projectId,
            fieldId: $fieldId,
            singleSelectOptions: $options
          }) {
            projectV2SingleSelectField {
              id
              options {
                id
                name
              }
            }
          }
        }
        """
        
        print(f"Updating options to: {[o['name'] for o in new_options]}")
        self.graphql_request(query, {
            "projectId": project_id,
            "fieldId": field['id'],
            "options": new_options
        })
        print("✅ Status options updated!")

def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return
        
    updater = ProjectColumnUpdater(token, "tezbo", "web3_mud")
    
    # Need project ID. We can fetch it or hardcode if we knew it.
    # Let's fetch it via repo.
    repo_id = updater.get_repository_id()
    
    # Fetch projects from owner (User)
    query = """
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 10) {
          nodes {
            id
            title
          }
        }
      }
    }
    """
    data = updater.graphql_request(query, {"login": "tezbo"})
    projects = data["user"]["projectsV2"]["nodes"]
    
    target_project = next((p for p in projects if "Aethermoor MUD" in p["title"]), None)
    
    if not target_project:
        print("❌ Project 'Aethermoor MUD' not found in user projects")
        return
        
    project_id = target_project["id"]
    print(f"Found Project: {target_project['title']} ({project_id})")
    
    updater.update_status_options(project_id)

if __name__ == "__main__":
    main()
