// deployment scope (must be susbcription as we are creating a resource group)
targetScope = 'subscription'

// Parameters
@description('Application name')
param appName string

@description('Environnement')
@allowed([
  'demo'
  'prod'
])
param environment string

param tags object = {
  dateCreated: utcNow()
  demo: 'iot'
}

param location string = deployment().location

// variables
var seed = tags.dateCreated // used to create the same unique suffix for all resources deployed by this template
var uniqueSuffix = take(uniqueString(seed), 5)
var resourceGroupName = 'rg-${environment}-${appName}-${uniqueSuffix}'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Create IoT Hub
module iotHub 'modules/iothub.bicep' = {
  scope: rg
  name: 'iothub-deployment-${uniqueSuffix}'
  params: {
    location: location
    appName: appName
    environment: environment
  }
}

// Create Storage Account
module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment-${uniqueSuffix}'
  params: {
    location: location
    appName: appName
    environment: environment
  }
}

// Create container registry
module acr 'modules/acr.bicep' = {
  scope: rg
  name: 'acr-deployment-${uniqueSuffix}'
  params: {
    location: location
    appName: appName
    environment: environment
  }
}

output output_json object = {
  rg_name: rg.name
  storage_name: storage.outputs.name
  storage_connection_string: storage.outputs.connection_string
  acr_login_server: acr.outputs.loginServer
  acr_username: acr.outputs.username
  acr_password: acr.outputs.password
}
