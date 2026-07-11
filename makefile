build-image:
	docker build --network=host -f dockerfile -t scrob-central .

run-image:
	docker run --rm scrob-central