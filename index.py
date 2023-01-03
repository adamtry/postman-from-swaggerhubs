import requests
import json

with open("config.json") as outfile:
    config = json.loads(outfile)

with open(config["POSTMAN_API_KEY_FILE"], "r") as outfile:
    # Auth headers to use with every Postman request
    POSTMAN_AUTH_HEADERS = {
        "X-API-Key": outfile.read().strip()
    }


def get_or_create_workspace(workspace_name):
    """
    Creates a workspace based on the workspace name in the config, or finds it if it already exists
    """
    response = requests.get("https://api.getpostman.com/workspaces", headers=POSTMAN_AUTH_HEADERS)
    assert response.status_code == 200, f"{response.status_code}: {response.json()}"
    workspaces_data = response.json()["workspaces"]
    for workspace in workspaces_data:
        if workspace["name"] == workspace_name:
            return workspace["id"]
    else:
        payload = {"workspace": {"name": workspace_name, "description": "APIs in the MTFH Finance context",
                                 "type": "personal"}}

        response = requests.post("https://api.getpostman.com/workspaces", json=payload, headers=POSTMAN_AUTH_HEADERS)
        assert response.status_code == 200, f"{response.status_code}: {response.json()}"
        ws_id = response.json()["workspace"]["id"]
        print(f"workspace {ws_id}")
        return ws_id


def import_openapi_in_workspace(swagger_url, workspace_id):
    """
    Gets an OpenAPI specification from a SwaggerHub API URL and creates a corresponding collection under a Postman
    workspace
    :param swagger_url: URL of Swagger API page (api.swaggerhub.com NOT app.swaggerhub.com)
    :param workspace_id: ID of Swagger workspace to attach the new collection to
    """
    response = requests.get(swagger_url)
    swagger_data = response.json()

    api_name = swagger_data["info"]["title"]

    swagger_import = {"input": swagger_data, "type": "json"}

    response = requests.post(f"https://api.getpostman.com/import/openapi?workspace={workspace_id}",
                             json=swagger_import, headers=POSTMAN_AUTH_HEADERS)
    assert response.status_code == 200, f"{response.status_code}: {response.json()}"

    print(f"{api_name} imported in workspace {workspace_id}")


if __name__ == "__main__":

    with open(config["SWAGGER_URLS_FILE"], "r") as outfile:
        swagger_urls: list[str] = outfile.readlines()

    # Validate URLs specified in file and ensure they are API urls (JSON)
    for i, url in enumerate(swagger_urls):
        assert url.startswith("https://app.swaggerhub.com") or url.startswith("https://api.swaggerhub.com"), \
            f"{url} should start with https://app.swaggerhub.com or https://api.swaggerhub.com"

        if url.startswith("https://app.swaggerhub.com"):
            swagger_urls[i] = swagger_urls[i].replace("https://app.swaggerhub.com", "https://api.swaggerhub.com")

    # Get workspace if it exists or create a new one
    workspace_id = get_or_create_workspace(workspace_name=config["WORKSPACE_NAME"])

    # Add all the Swagger API definitions to the workspace as Postman collections
    for api_url in swagger_urls:
        import_openapi_in_workspace(api_url, workspace_id)

    print(f"Workspace Created! Link:\nhttps://web.postman.co/workspace/{workspace_id}")