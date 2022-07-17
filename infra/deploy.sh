#!/bin/sh
# default values
LOCATION=westeurope

# This script is used to deploy the infra stack.
# It is intended to be run from the workspace root directory of the repository.

# define usage function
usage() {
  echo "Usage: $0 -s|--subscription <subscription name or id> [-l|--location location] [-h]"
  echo "  -s|--subscription <subscription name or id>  : the name or id of the subscription to use"
  echo "  -l|--location: Azure location (default: $LOCATION)"
  echo "  -h: show this help"
  exit 1
}

# parsing script parameters
# - subscription to deploy to
while [ $# -gt 0 ]; do
    case "$1" in
        -s|--subscription)
            SUBSCRIPTION="$2"
            shift
            ;;
        -l|--location)
            LOCATION="$2"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
    shift
done

# check if mandatory parameters are set
if [ -z "$SUBSCRIPTION" ]; then
    usage
    exit 1
fi

# check if azure cli is installed
if ! command -v az > /dev/null; then
    echo "azure cli is not installed. Please install it first."
    exit 1
fi

# check if user is logged in
if ! az account show > /dev/null; then
    echo "Please login to Azure first."
    exit 1
fi

# select subscription
az account set --subscription "$SUBSCRIPTION"

# deploy bicep file to subscription scope
# query output from command to check if deployment was successful
output=$(az deployment sub create --name IoT-infra-deployment --location $LOCATION --template-file "./infra/main.bicep" --parameters "./infra/main.parameters.json" --query properties.outputs.output_json.value)

# extract values from output using jq
rg_name=$(echo "$output" | jq -r '.rg_name')
acr_login_server=$(echo "$output" | jq -r '.acr_login_server')
acr_username=$(echo "$output" | jq -r '.acr_username')
acr_password=$(echo "$output" | jq -r '.acr_password')
storage_name=$(echo "$output" | jq -r '.storage_name')
storage_connection_string=$(echo "$output" | jq -r '.storage_connection_string')

# backuping existing .env file with unique name if it exists
if [ -f .env ]; then
    mv .env .env.bak.$(date +%Y%m%d%H%M%S)
fi

# creating new .env file with values from output
echo "RG_NAME=$rg_name" >> .env
echo "CONTAINER_REGISTRY_NAME=$acr_login_server" >> .env
echo "CONTAINER_REGISTRY_USERNAME=$acr_username" >> .env
echo "CONTAINER_REGISTRY_PASSWORD=$acr_password" >> .env
echo "STORAGE_NAME=$storage_name" >> .env
echo "LOCAL_STORAGE_ACCOUNT_NAME=blob" >> .env
echo "LOCAL_STORAGE_ACCOUNT_KEY=R4WeFb4L8I8rmZfbvNA0og==" >> .env
echo "CLOUD_STORAGE_CONNECTION_STRING=$storage_connection_string" >> .env
echo "PLATFORM=arm32v7" >> .env


