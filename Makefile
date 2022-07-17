
platform := ${PLATFORM} # eg. arm32v7

AZ := az
JQ := jq

# marcros to extract data from module.json file
GetValueFromJson = $(shell cat ./modules/$@/module.json | ${JQ} -r '${1}')
dockerfile = $(shell basename $(call GetValueFromJson, .image.tag.platforms.${platform}))
contextPath = $(call GetValueFromJson, .image.contextPath)
version = $(call GetValueFromJson, .image.tag.version)
repository = $(call GetValueFromJson, .image.repository)
acr_name = $(shell echo ${repository} | sed -E 's/^([^.]*).*.*/\1/')
image_artifact = $(shell echo ${repository} | sed -E 's/^.*\/([^/]*)/\1/'):${version}-${platform}
image_namespace = $(shell echo ${repository} | sed -E 's/^[^/]*\/(.*)\/.*/\1/')

build_platform = $(shell if [ ${platform} = arm32v7 ]; then echo "linux/arm/v7"; elif [ ${platform} = amd64 ]; then echo "amd64"; fi)

all: baseimage camera fastapi-todo

baseimage: devkitbase

fastapi-todo:
	@echo "Building $@"
	@echo "platform: ${platform}"
	@echo "dockerfile: $(dockerfile)"
	@echo "verision: $(version)"
	@echo "contextPath$(contextPath)"
	@echo "repository: $(repository)"
	@echo "acr_name: $(acr_name)"
	@echo "image artifact: $(image_artifact)"
	@echo "image namespace: $(image_namespace)"
	@echo "build platform: $(build_platform)"
	cd ./modules/$@/ && ${AZ} acr build -t ${image_namespace}/${image_artifact} -r ${acr_name} . --platform ${build_platform} --file ${dockerfile}

devkitbase:
	@echo "Building $@"
	@echo "platform: ${platform}"
	@echo "dockerfile: $(dockerfile)"
	@echo "verision: $(version)"
	@echo "contextPath$(contextPath)"
	@echo "repository: $(repository)"
	@echo "acr_name: $(acr_name)"
	@echo "image artifact: $(image_artifact)"
	@echo "image namespace: $(image_namespace)"
	@echo "build platform: $(build_platform)"
	cd ./modules/$@/ && ${AZ} acr build -t ${image_namespace}/${image_artifact} -r ${acr_name} . --platform ${build_platform} --file ${dockerfile}



camera:
	@echo "Building $@"
	cd ./modules/$@/ && ${AZ} acr build -t ${image_namespace}/${image_artifact} -r ${acr_name} . --platform ${build_platform} --file ${dockerfile}



