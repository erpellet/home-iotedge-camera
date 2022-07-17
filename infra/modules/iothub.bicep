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
var prefix = 'iothub'
var tags = resourceGroup().tags
var seed = tags.dateCreated
var uniqueSuffix = take(uniqueString(seed), 5)

// resource name can be made unique if bool param 'unique' is set to true
var name = unique ? '${prefix}-${environment}-${appName}-${uniqueSuffix}' : '${prefix}-${environment}-${appName}'

// create iot hub resource
resource iotHub 'Microsoft.Devices/IotHubs@2021-07-02' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'S1'
    capacity: 1
  }
}



