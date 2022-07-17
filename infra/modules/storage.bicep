// Parameters
@description('Application name')
param appName string

@description('Environment')
param environment string

@description('Resource location - default value: resourceGroup().location')
param location string = resourceGroup().location

@description('Switch to force creation of a unique name')
@allowed([
  true
  false
])
param unique bool = true

// Variables
var prefix = 'sta'
var tags = resourceGroup().tags
var seed = tags.dateCreated
var uniqueSuffix = take(uniqueString(seed), 5)

// resource name can be made unique if bool param 'unique' is set to true
var name = unique ? '${prefix}${environment}${appName}${uniqueSuffix}' : '${prefix}${environment}${appName}'

// create iot hub resource
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: name
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

output name string = storageAccount.name
output connection_string string = storageAccount.listKeys().keys[0].value

