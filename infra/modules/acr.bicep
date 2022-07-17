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
var prefix = 'acr'
var tags = resourceGroup().tags
var seed = tags.dateCreated
var uniqueSuffix = take(uniqueString(seed), 5)

// resource name can be made unique if bool param 'unique' is set to true
var name = unique ? '${prefix}${environment}${appName}${uniqueSuffix}' : '${prefix}${environment}${appName}'

// create iot hub resource
resource acr 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// output container registry credentials
// Don't do that in production!
output username string = acr.listCredentials().username
output password string = acr.listCredentials().passwords[0].value
output loginServer string = acr.properties.loginServer
