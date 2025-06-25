sync:
	@uv sync \
	--all-extras \
	--all-groups \
	--active \
	--all-packages \
	--upgrade

locked:
	@uv lock --locked

lint: sync
	@uv run ruff check --fix
	@uv run ruff format

test:
	@uv run pytest tests -vv -s

clean:
	@rm -rfv ./dist

build: clean sync
	@uv build --all-packages

publish:
	@uv publish