 kubectl version --client

Client Version: v1.32.3
Kustomize Version: v5.5.0


ishaanagarwal@ishaans-MacBook Helms % az group create \
    --name myAKSResourceGroup \
    --location eastus

{
  "id": "/subscriptions/0da47865-0b6a-4526-b1c5-b0add92f5c1c/resourceGroups/myAKSResourceGroup",
  "location": "eastus",
  "managedBy": null,
  "name": "myAKSResourceGroup",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": null,
  "type": "Microsoft.Resources/resourceGroups"
}