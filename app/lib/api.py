from flask import current_app
from requests import JSONDecodeError, Timeout, TooManyRedirects, codes, get


class ResourceNotFound(Exception):
    pass


class ResourceForbidden(Exception):
    pass


class JSONAPIClient:
    api_url = ""
    params = {}

    def __init__(self, api_url, params=None):
        self.api_url = api_url
        self.params = params if params is not None else {}

    def add_parameter(self, key, value):
        self.params[key] = value

    def add_parameters(self, params):
        self.params = self.params | params

    def get(self, path="/"):
        url = f"{self.api_url}/{path.lstrip('/')}"
        headers = {
            "Cache-Control": "no-cache",
            "Accept": "application/json",
        }
        try:
            response = get(
                url,
                params=self.params,
                headers=headers,
            )
        except ConnectionError as err:
            current_app.logger.error("JSON API connection error")
            raise Exception("A connection error occured") from err
        except Timeout as err:
            current_app.logger.error("JSON API timeout")
            raise Exception("The request timed out") from err
        except TooManyRedirects as err:
            current_app.logger.error("JSON API had too many redirects")
            raise Exception("Too many redirects") from err
        except Exception as e:
            current_app.logger.error(f"Unknown JSON API exception: {e}")
            raise Exception(str(e)) from e
        current_app.logger.debug(response.url)
        if response.status_code == codes.ok:
            try:
                return response.json()
            except JSONDecodeError as err:
                current_app.logger.error("JSON API provided non-JSON response")
                raise Exception("Non-JSON response provided") from err
        if response.status_code == 400:
            current_app.logger.error(f"Bad request: {response.url}")
            raise Exception("Bad request")
        if response.status_code == 403:
            current_app.logger.warning("Forbidden")
            raise ResourceForbidden("Forbidden")
        if response.status_code == 404:
            current_app.logger.warning("Resource not found")
            raise ResourceNotFound("Resource not found")
        current_app.logger.error(f"JSON API responded with {response.status_code}")
        raise Exception("Request failed")
