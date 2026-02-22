CUR_SHA=$(shell git log -n1 --pretty='%h')
CUR_BRANCH=$(shell git branch --show-current)
VERSION=$(shell git describe --exact-match --tags $(CUR_SHA) 2>/dev/null || echo $(CUR_BRANCH)-$(CUR_SHA))

shell:
	poetry shell

update-dependencies:
	poetry update

docker:
	docker build -t pigeosolutions/ogr2vrt_simple:latest .