# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from ipaddress import ip_address
from syslog import LOG_SYSLOG
import time
import os
import sys
import asyncio
import glob
from six.moves import input
import threading
import logging
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient, BlobServiceClient

from camera import CameraUtility, take_picture

# global counters
CAMERA_IP = None
TWIN_CALLBACKS = 0
RECEIVED_MESSAGES = 0

camera = CameraUtility()

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def upload_file_to_iotedge_storage(file_path):
    # Get the storage info for the blob
    logger.info("Processing file: %s", file_path)
    blob_name = os.path.basename(file_path)
    logger.info("Extracted blob name from file path: %s", blob_name)
    # create connection string to local blob storage
    try:
        account_name = os.environ["LOCAL_STORAGE_ACCOUNT_NAME"]
        account_key = os.environ["LOCAL_STORAGE_ACCOUNT_KEY"]
    except KeyError as e:
        logger.error("Environment variable is missing %s", e)
        return

    host_device_name = "azureblobstorageoniotedge"
    connection_string = f"DefaultEndpointsProtocol=http;BlobEndpoint=http://{host_device_name}:11002/{account_name};AccountName={account_name};AccountKey={account_key}"
    logger.debug("Connection string: %s", connection_string)

    # Create the BlobServiceClient object which will be used to create a container client
    print("Creating BlobServiceClient object")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string)
    except Exception as ex:
        print(f"Error creating BlobServiceClient object: {ex}")
        return "Error creating BlobServiceClient object"

    container_name = "pictures"
    # Create the container if not exists
    try:
        container_client = blob_service_client.create_container(container_name)
        print(f"Container {container_name} created")
    except AzureError:
        print(f"Container {container_name} already exists")
        container_client = blob_service_client.get_container_client(
            container_name)

    # Create a blob client using the local file name as the name for the blob
    blob_client = container_client.get_blob_client(blob=blob_name)

    print("\nUploading to Azure Storage as blob:\n\t" + blob_name)

    # Upload the file
    try:
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)

            print("Upload succeeded. Result is: \n")
            print()
        result = {
            "status": 200,
            "payload": {
                "message": "File uploaded successfully",
                "file_name": blob_name
            }
        }

    except AzureError as err:
        # If the upload was not successful, the result is the exception object
        print("Upload failed. Exception is: \n")
        print(err)
        print()
        result = {
            "status": 400,
            "payload": {
                "message": "Upload to blob storage failed",
                "file_name": blob_name
            }
        }

    return result


async def main():
    global CAMERA_IP
    try:
        #print("IoT Hub Client for Python")
        logger.info("Now using logger...")
        logger.info("IoT Hub Client for Python")
        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()
        twin = await module_client.get_twin()
        logger.info("Twin: %s", twin)
        CAMERA_IP = twin["desired"].get("camera_ip")
        logger.info("Initial Camera IP: %s", CAMERA_IP)

        # Define behavior for receiving an input message on input1
        # Because this is a filter module, we forward this message to the "output1" queue.
        async def input1_listener(module_client):
            global RECEIVED_MESSAGES
            global TEMPERATURE_THRESHOLD
            while True:
                try:
                    # blocking call
                    input_message = await module_client.receive_message_on_input("input1")
                    message = input_message.data
                    size = len(message)
                    message_text = message.decode('utf-8')
                    print("    Data: <<<%s>>> & Size=%d" %
                          (message_text, size))
                    custom_properties = input_message.custom_properties
                    print("    Properties: %s" % custom_properties)
                    RECEIVED_MESSAGES += 1
                    print("    Total messages received: %d" %
                          RECEIVED_MESSAGES)
                    data = json.loads(message_text)
                    if "machine" in data and "temperature" in data["machine"] and data["machine"]["temperature"] > TEMPERATURE_THRESHOLD:
                        custom_properties["MessageType"] = "Alert"
                        print("Machine temperature %s exceeds threshold %s" % (
                            data["machine"]["temperature"], TEMPERATURE_THRESHOLD))
                        await module_client.send_message_to_output(input_message, "output1")
                except Exception as ex:
                    print("Unexpected error in input1_listener: %s" % ex)

        # twin_patch_listener is invoked when the module twin's desired properties are updated.
        async def twin_patch_listener(module_client):
            global CAMERA_IP
            while True:
                try:
                    data = await module_client.receive_twin_desired_properties_patch()  # blocking call
                    print("The data in the desired properties patch was: %s" % data)
                    if "camera_ip" in data:
                        CAMERA_IP = data["camera_ip"]
                        print("Camera IP is now: %s" % CAMERA_IP)
                except Exception as ex:
                    print("Unexpected error in twin_patch_listener: %s" % ex)

        async def method_request_handler(module_client):
            global CAMERA_IP
            while True:
                method_request = await module_client.receive_method_request()
                logger.info("Method callback called with:methodName = %s - payload = %s",
                            method_request.name, method_request.payload)
                if method_request.name == "snap":
                    logger.info("%s called", method_request.name)                    
                    ip_addr = CAMERA_IP or camera.getWlanIp()
                    logger.info("IP address is: %s", ip_addr)
                    try:
                        result = take_picture(ip_addr)
                    except Exception as ex:
                        logger.info(
                            "Humm... There was a glitch but a picture might have been taken")
                        logger.info("Exception: %s", ex)
                        logger.info(
                            "Trying to continue like nothing happened... ")
                    logger.info("Result is: %s", result)
                    file_name = glob.glob('snapshot_*')[0]
                    logger.info("File is: %s", file_name)
                    local_path = "/app"
                    file_path = os.path.join(
                        local_path, file_name)
                    logger.info("File path is: %s", file_path)
                    try:
                        result = upload_file_to_iotedge_storage(file_path)
                    except Exception as ex:
                        logger.info("Humm... there was a glitch: %s", ex)
                        logger.info(
                            "Trying to continue like nothing happened... ")
                    # set response payload
                    payload = result["payload"]  # set payload
                    status = result["status"]  # set return status code

                    # cleanup
                    logger.info("Doing some cleanup...")

                    for file in glob.glob('snapshot_*'):
                        logger.info("Deleting snapshot file: %s", file)
                        os.remove(file)
                        logger.info("Done deleting snapshot file: %s", file)

                    logger.info("End of execution: %s", method_request.name)

                else:
                    logger.info("%s called but not implemented",
                                method_request.name)
                    # set response payload
                    payload = {"result": False, "data": "unknown method"}
                    status = 400  # set return status code

                # Send the response
                method_response = MethodResponse.create_from_method_request(
                    method_request, status, payload)
                await module_client.send_method_response(method_response)
                print('Message sent!')

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(10)

        # Schedule task for C2D Listener
        listeners = asyncio.gather(input1_listener(module_client), twin_patch_listener(
            module_client), method_request_handler(module_client))

        print("The sample is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop_main = asyncio.get_event_loop()
        user_finished = loop_main.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print("Unexpected error %s " % e)
        raise

if __name__ == "__main__":
    # code valid if python version >= 3.7 ??
    # asyncio.run(main())

    # code for python version < 3.7
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
