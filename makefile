build-image:
	docker build --network=host -t scrob-central .

run-image:
	docker run --rm scrob-central