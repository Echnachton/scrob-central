# Community-fixed fork of Spotify's official OpenAPI schema:
# https://developer.spotify.com/reference/web-api/open-api-schema.yaml
SPOTIFY_OPENAPI_URL := https://raw.githubusercontent.com/sonallux/spotify-web-api/main/fixed-spotify-open-api.yml
SPOTIFY_OPENAPI_SCHEMA := schema/spotify-openapi.yaml

.PHONY: fetch-spotify-openapi generate-spotify-schema build-image run-image

fetch-spotify-openapi:
	curl -fsSL "$(SPOTIFY_OPENAPI_URL)" -o "$(SPOTIFY_OPENAPI_SCHEMA)"

generate-spotify-schema: fetch-spotify-openapi
	uv run datamodel-codegen

build-image:
	docker build --network=host -t scrob-central .

run-image:
	docker run --rm --env-file .env scrob-central