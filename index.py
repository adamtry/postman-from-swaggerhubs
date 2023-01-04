import os.path
import requests
import json


class SetupIncompleteError(Exception):
    def __init__(self, message):
        super().__init__(message)


def get_or_create_workspace(workspace_name, postman_auth_headers):
    """
    Creates a workspace based on the workspace name in the config, or finds it if it already exists
    """
    response = requests.get("https://api.getpostman.com/workspaces", headers=postman_auth_headers)
    assert response.status_code == 200, f"{response.status_code}: {response.json()}"
    workspaces_data = response.json()["workspaces"]
    for workspace in workspaces_data:
        if workspace["name"] == workspace_name:
            return workspace["id"]
    else:
        payload = {"workspace": {"name": workspace_name, "description": CONFIG["WORKSPACE_DESCRIPTION"],
                                 "type": "personal"}}

        response = requests.post("https://api.getpostman.com/workspaces", json=payload, headers=postman_auth_headers)
        assert response.status_code == 200, f"{response.status_code}: {response.json()}"
        ws_id = response.json()["workspace"]["id"]
        print(f"workspace {ws_id}")
        return ws_id


def update_description_for_collection(collection_id, swagger_url, collection_schema):
    response = requests.get(f"https://api.getpostman.com/collections/{collection_id}", headers=POSTMAN_AUTH_HEADERS)
    collection_details = response.json()["collection"]

    # Remove IDs from item part
    for i, collection_detail in enumerate(collection_details["item"]):
        collection_detail.pop("id")
        collection_details["item"][i] = collection_detail

    body = {
        "collection": {
            "info": {
                "name": collection_details["info"]["name"],
                "description": f"Generated from {swagger_url}",
                "schema": collection_schema,
            },
            "item": collection_details["item"]
        }
    }
    response = requests.put(
        f"https://api.getpostman.com/collections/{collection_id}",
        json=body,
        headers=POSTMAN_AUTH_HEADERS
    )
    assert response.status_code == 200, response.json()
    if response.status_code != 200:
        print(f"Failed to update description for collection {collection_id}")
    else:
        print(f"Updated description for collection {collection_id}")


def import_openapi_as_collection_in_workspace(swagger_url, workspace_id, postman_auth_headers, collection_schema):
    """
    Gets an OpenAPI specification from a SwaggerHub API URL and creates a corresponding collection under a Postman
    workspace
    :param swagger_url: URL of Swagger JSON source
    :param workspace_id: ID of Swagger workspace to attach the new collection to
    """

    # Get Swagger JSON
    response = requests.get(swagger_url)
    swagger_data = response.json()

    api_name = swagger_data["info"]["title"]

    # Get collections already in workspace
    response = requests.get(f"https://api.getpostman.com/collections?workspace={workspace_id}",
                            headers=postman_auth_headers)
    workspace_collections = response.json()["collections"]

    for collection in workspace_collections:
        if api_name == collection["name"]:
            response = requests.delete(f"https://api.getpostman.com/collections/{collection['id']}",
                                       headers=postman_auth_headers)
            assert response.status_code == 200, f"Failed to delete collection {collection['name']} - {collection['id']}"
            break

    swagger_import = {"input": swagger_data, "type": "json"}
    response = requests.post(f"https://api.getpostman.com/import/openapi?workspace={workspace_id}",
                             json=swagger_import, headers=postman_auth_headers)
    assert response.status_code == 200, f"{response.status_code}: {response.json()}"
    created_collection = response.json()["collections"][0]

    update_description_for_collection(created_collection["id"], swagger_url, collection_schema)

    print(f"{api_name} imported in workspace {workspace_id}")


def setup():
    """
    Ensures configuration is complete
    """
    with open("config.json") as outfile:
        cfg = json.load(outfile)

    if not os.path.isfile(cfg["POSTMAN_API_KEY_FILE"]):
        api_key = input("Postman API Key: ")
        with open(cfg["POSTMAN_API_KEY_FILE"], "w") as outfile:
            outfile.write(
                api_key
            )
    else:
        with open(cfg["POSTMAN_API_KEY_FILE"], "r") as outfile:
            # Auth headers to use with every Postman request
            api_key = outfile.read().strip()

    if not os.path.isfile(cfg["SWAGGER_URLS_FILE"]) or os.stat(cfg["SWAGGER_URLS_FILE"]).st_size == 0:
        with open(cfg["SWAGGER_URLS_FILE"], "w") as outfile:
            pass
        raise SetupIncompleteError(f"Open and fill in file: {cfg['SWAGGER_URLS_FILE']}")
    else:
        with open(cfg["SWAGGER_URLS_FILE"], "r") as outfile:
            swaggers: list[str] = outfile.readlines()

    # Validate URLs specified in file and ensure they are API urls (JSON)
    for i, url in enumerate(swaggers):
        url_can_contain = ["https://app.swaggerhub.com", "https://api.swaggerhub.com", "/swagger.json"]
        assert any(url_segment in url for url_segment in url_can_contain), \
            f"{url} in {cfg['SWAGGER_URLS_FILE']} should be for app.swaggerhub.com or api.swaggerhub.com" \
            f" or point to a public swagger.json page"

        if url.startswith("https://app.swaggerhub.com"):
            swaggers[i] = swaggers[i].replace("https://app.swaggerhub.com", "https://api.swaggerhub.com")

    return cfg, api_key, swaggers


if __name__ == "__main__":
    CONFIG, POSTMAN_API_KEY, SWAGGER_URLS = setup()

    POSTMAN_AUTH_HEADERS = {
        "X-API-Key": POSTMAN_API_KEY
    }
    # Get workspace if it exists or create a new one
    workspace_id = get_or_create_workspace(CONFIG["WORKSPACE_NAME"], POSTMAN_AUTH_HEADERS)

    # Add all the Swagger API definitions to the workspace as Postman collections
    for api_url in SWAGGER_URLS:
        import_openapi_as_collection_in_workspace(
            api_url, workspace_id, POSTMAN_AUTH_HEADERS, CONFIG["POSTMAN_COLLECTION_SCHEMA"]
        )

    print(f"Complete! Workspace Link:\nhttps://web.postman.co/workspace/{workspace_id}")
