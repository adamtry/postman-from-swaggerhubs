# Postman from SwaggerHub Generator

Uses the Postman API to create a workspace and set of collections based on a list of SwaggerHub URLs

### Dependencies:
- Python 3 (current version) with pip package manager [Install from here](https://www.python.org/downloads/)
- Python `requests` library. Install with `python -m pip install -r requirements.txt` or otherwise

### Setup:
1) Visit the [Postman API Key Generation Page](https://web.postman.co/settings/me/api-keys) and generate a new API key (or use an existing one)
2) Save the key in this directory in a file named [postman_api_key.txt](postman_api_key.txt) (gitignored)
3) Create and/or open the [api_urls.txt](api_urls.txt) (gitignored) file and list the SwaggerHub pages to add to the Postman workspace
   - These should all start with `https://app.swaggerhub.com` or `https://api.swaggerhub.com`
   - These should be separated with line breaks only, example:
```
https://app.swaggerhub.com/apis/MyOrganisation/myFirstApiName/1.1.0
https://app.swaggerhub.com/apis/MyOrganisation/mySecondApiName/2.3.0
```
4) Open the [config.json](config.json) file and edit the values as needed

### Run:
1) Run the [index.py](index.py) file with `python index.py` or otherwise
2) Follow the link printed to the console after a successful run (you may need to log in with Web Postman first)
3) The collections may have a SwaggerHub URL set under the Collection Variables for the baseUrl, so you should [edit these for each collection](https://learning.postman.com/docs/sending-requests/variables/#defining-collection-variables)
4) Add any other environment or collection variables as needed
