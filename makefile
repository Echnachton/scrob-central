build-image:
	docker build --network=host -t scrob-central .

run-image:
	docker run --rm --env-file .env scrob-central