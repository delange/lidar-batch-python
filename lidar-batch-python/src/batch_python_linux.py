from __future__ import print_function
import datetime
import io
import os
import sys
import time
import config

from azure.core.exceptions import ResourceExistsError
import azure.storage.blob as azureblob
import azure.batch as azurebatch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels

sys.path.append('.')
sys.path.append('..')

# Update the Batch and Storage account credential strings in config.py with values
# unique to your accounts. These are used when constructing connection strings
# for the Batch and Storage client objects.

def query_yes_no(question, default="yes"):
    """
    Prompts the user for yes/no input, displaying the specified question text.

    :param str question: The text of the prompt for input.
    :param str default: The default if the user hits <ENTER>. Acceptable values
    are 'yes', 'no', and None.
    :rtype: str
    :return: 'yes' or 'no'
    """
    valid = {'y': 'yes', 'n': 'no'}
    if default is None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError("Invalid default answer: '{}'".format(default))

    while 1:
        choice = input(question + prompt).lower()
        if default and not choice:
            return default
        try:
            return valid[choice[0]]
        except (KeyError, IndexError):
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def print_batch_exception(batch_exception):
    """
    Prints the contents of the specified Batch exception.

    :param batch_exception:
    """
    print('-------------------------------------------')
    print('Exception encountered:')
    if batch_exception.error and \
            batch_exception.error.message and \
            batch_exception.error.message.value:
        print(batch_exception.error.message.value)
        if batch_exception.error.values:
            print()
            for mesg in batch_exception.error.values:
                print('{}:\t{}'.format(mesg.key, mesg.value))
    print('-------------------------------------------')


def upload_file_to_container(blob_service_client, account_name, container_name, file_path, blob_permissions):
    """
    Uploads a local file to an Azure Blob storage container.

    :param blob_service_client: A blob service client.
    :type blob_service_client: `azure.storage.blob.BlobServiceClient`
    :param str account_name: The name of the Azure storage account.
    :param str container_name: The name of the Azure Blob storage container.
    :param str file_path: The local path to the file.
    :param blob_permissions: A blob SAS permission object
    :type blob_permissions: blob_permissions: `azure.storage.blob.blobsaspermissions`
    :rtype: `azure.batch.models.ResourceFile`
    :return: An azure.batch.models.ResourceFile initialized with a SAS URL appropriate for Batch
    tasks.
    """
    blob_name = os.path.basename(file_path)

    print('Uploading file {} to container [{}]...'.format(file_path,
                                                          container_name))

    # make first a blob client from the BlobServiceClient
    blob_input_properties = azureblob.BlobProperties(container = container_name, name = blob_name)
    blob_client = blob_service_client.get_blob_client(container_name, blob_input_properties)

    #upload_blob(data, blob_type=<BlobType.BlockBlob: 'BlockBlob'>, length=None, metadata=None, **kwargs)
    with open(file_path, 'rb') as data:
        blob_client.upload_blob(data, blob_type="BlockBlob")
    
    ## Obtain the SAS token for the container.
    sas_token = get_container_sas_token(account_name,
                                        container_name, blob_permissions)
    
    # Construct SAS URL for the blob
    blob_sas_url = "https://{}.blob.core.windows.net/{}/{}?{}".format(account_name, container_name, blob_name, sas_token)   

    return batchmodels.ResourceFile(file_path=blob_name,
                                    http_url=blob_sas_url)


def get_container_sas_token(account_name,
                            container_name, blob_permissions):
    """
    Obtains a shared access signature granting the specified permissions to the
    container.

#    :param block_blob_client: A blob service client.
#    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str account_name: The name of the Azure Blob storage account
    :param str container_name: The name of the Azure Blob storage container.
    :param blob_permissions: A blob SAS permission object
    :type blob_permissions: blob_permissions: `azure.storage.blob.blobsaspermissions`
    :rtype: str
    :return: A SAS token granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container, setting the expiry time and
    # permissions. In this case, no start time is specified, so the shared
    # access signature becomes valid immediately. Expiration is in 2 hours.

    container_sas_token = azureblob.generate_container_sas( \
        account_name,
        container_name,
        account_key=config._STORAGE_ACCOUNT_KEY,
        permission=blob_permissions,
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=24))

    return container_sas_token


def get_container_sas_url(blob_service_client, account_name,
                          container_name, blob_permissions):
    """
    Obtains a shared access signature URL that provides write access to the
    ouput container to which the tasks will upload their output.

    :param blob_service_client: A blob service client.
    :type blob_service_client: `azure.storage.blob.BlobServiceClient`
    :param str account_name: The name fo the Azure Blob storage account
    :param str container_name: The name of the Azure Blob storage container.
    :param blob_permissions: A blob SAS permission object
    :type blob_permissions: blob_permissions: `azure.storage.blob.blobsaspermissions`
    :rtype: str
    :return: A SAS URL granting the specified permissions to the container.
    """
    # Obtain the SAS token for the container.
    sas_token = get_container_sas_token(account_name,
                                        container_name, blob_permissions)

    # Construct SAS URL for the container
    container_sas_url = "https://{}.blob.core.windows.net/{}?{}".format(account_name, container_name,
                                                                        sas_token)

    return container_sas_url


def create_pool(batch_service_client, pool_id, application_files):
    """
    Creates a pool of compute nodes with the specified OS settings.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str pool_id: An ID for the new pool.
    :param application_files: A list of batch.models ResourceFile
    :type application_files: `azure.batch.models.ResourceFile`
#    :param str publisher: Marketplace image publisher
#    :param str offer: Marketplace image offer
#    :param str sku: Marketplace image sky
    """
    print('Creating pool [{}]...'.format(pool_id))

    # Create a new pool of Windos or Linux compute nodes using an Azure Virtual Machines
    # Marketplace image. For more information about creating pools of Linux
    # nodes, see:
    # https://azure.microsoft.com/documentation/articles/batch-linux-nodes/

    new_pool = azurebatch.models.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(
                publisher="debian",
                offer="debian-10",
                sku="10",
                version="latest"
            ),
            node_agent_sku_id="batch.node.debian 10"),
        vm_size=config._POOL_VM_SIZE,
        target_dedicated_nodes=config._DEDICATED_POOL_NODE_COUNT,
        target_low_priority_nodes=config._LOW_PRIORITY_POOL_NODE_COUNT,
        start_task=batchmodels.StartTask(
            command_line='/bin/bash -c "cp *.* $AZ_BATCH_NODE_SHARED_DIR && starttask.sh"',
            resource_files=application_files,
            wait_for_success=True,
            user_identity=batchmodels.UserIdentity(
                auto_user=batchmodels.AutoUserSpecification(
                    scope=batchmodels.AutoUserScope.pool,
                    elevation_level=batchmodels.ElevationLevel.admin)),
        )
    )

    batch_service_client.pool.add(new_pool)


def create_job(batch_service_client, job_id, pool_id):
    """
    Creates a job with the specified ID, associated with the specified pool.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    print('Creating job [{}]...'.format(job_id))

    job = azurebatch.models.JobAddParameter(
        id=job_id,
        pool_info=azurebatch.models.PoolInformation(pool_id=pool_id))

    batch_service_client.job.add(job)


def add_tasks(batch_service_client, job_id, input_files, output_container_sas_url):
    """
    Adds a task for each input file in the collection to the specified job.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The ID of the job to which to add the tasks.
    :param list input_files: A collection of input files. One task will be
     created for each input file.
    :param output_container_sas_url: A SAS token granting write access to
    the specified Azure Blob storage container.
    """
    
    print('Adding {} tasks to job [{}]...'.format(len(input_files), job_id))

    tasks = list()

    for idx, input_file in enumerate(input_files):
        input_file_path = input_file.file_path
        output_file_path = "OutputFile{}".format(idx)
        command = '/bin/bash -c "task.sh {} {}"'.format(input_file_path, output_file_path)
        tasks.append(azurebatch.models.TaskAddParameter(
            id='Task{}'.format(idx),
            command_line=command,
            resource_files=[input_file],
            output_files=[batchmodels.OutputFile(
                file_pattern=output_file_path,
                destination=batchmodels.OutputFileDestination(
                    container=batchmodels.OutputFileBlobContainerDestination(
                        container_url=output_container_sas_url)),
                upload_options=batchmodels.OutputFileUploadOptions(
                    upload_condition=batchmodels.OutputFileUploadCondition.task_success))]
        )
        )
    batch_service_client.task.add_collection(job_id, tasks)


def wait_for_tasks_to_complete(batch_service_client, job_id, timeout):
    """
    Returns when all tasks in the specified job reach the Completed state.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The id of the job whose tasks should be monitored.
    :param timedelta timeout: The duration to wait for task completion. If all
    tasks in the specified job do not reach Completed state within this time
    period, an exception will be raised.
    """
    timeout_expiration = datetime.datetime.now() + timeout

    print("Monitoring all tasks for 'Completed' state, timeout in {}..."
          .format(timeout), end='')

    while datetime.datetime.now() < timeout_expiration:
        print('.', end='')
        sys.stdout.flush()
        tasks = batch_service_client.task.list(job_id)

        incomplete_tasks = [task for task in tasks if
                            task.state != batchmodels.TaskState.completed]
        if not incomplete_tasks:
            print()
            return True
        else:
            time.sleep(1)

    print()
    raise RuntimeError("ERROR: Tasks did not reach 'Completed' state within "
                       "timeout period of " + str(timeout))


if __name__ == '__main__':
    start_time = datetime.datetime.now().replace(microsecond=0)
    print('Sample start: {}'.format(start_time))
    print()

    # Create the blob client, for use in obtaining references to
    # blob storage containers and uploading files to containers.

    blob_service_client = azureblob.BlobServiceClient(
        config._STORAGE_URL, 
        config._STORAGE_ACCOUNT_KEY)

    input_container_name = 'lidarinput'
    application_container_name = 'lidarapplication'
    output_container_name = 'lidaroutput'

    try:
        # Attempt to create container
        blob_service_client.create_container(input_container_name)

    # Catch exception and print error
    except ResourceExistsError as error:
        print(error)

    try:
        # Attempt to create container
        blob_service_client.create_container(application_container_name)

    # Catch exception and print error
    except ResourceExistsError as error:
        print(error)

    try:
        # Attempt to create container
        blob_service_client.create_container(output_container_name)
        
    # Catch exception and print error
    except ResourceExistsError as error:
        print(error)

    sas_permission = azureblob.BlobSasPermissions(read=True, create=True)

    # Create a list of all input files in the InputFiles directory.
    input_file_paths = []

    for folder, subs, files in os.walk(os.path.join(sys.path[1], 'InputFiles')):
        for filename in files:
            # if filename.endswith(".mp4"):
                input_file_paths.append(os.path.abspath(os.path.join(folder, filename)))

    # Upload the input files. This is the collection of files that are to be processed by the tasks. 
    input_files = [
        upload_file_to_container(blob_service_client, config._STORAGE_ACCOUNT_NAME, input_container_name, file_path, sas_permission)
        for file_path in input_file_paths]

    # Create a list of all application files in the ApplicationFiles directory.
    application_file_paths = []

    for folder, subs, files in os.walk(os.path.join(sys.path[1], 'ApplicationFiles')):
        for filename in files:
            application_file_paths.append(os.path.abspath(os.path.join(folder, filename)))

    # Upload the application files. This is the collection of files that are needed to run the application.
    application_files = [
        upload_file_to_container(blob_service_client, config._STORAGE_ACCOUNT_NAME, application_container_name, file_path, sas_permission)
        for file_path in application_file_paths]

    # Obtain a shared access signature URL that provides write access to the output
    # container to which the tasks will upload their output.

    output_container_sas_url = get_container_sas_url(
        blob_service_client,
        config._STORAGE_ACCOUNT_NAME,
        output_container_name,
        sas_permission)

    # Create a Batch service client. We'll now be interacting with the Batch
    # service in addition to Storage
    credentials = batchauth.SharedKeyCredentials(config._BATCH_ACCOUNT_NAME,
                                                 config._BATCH_ACCOUNT_KEY)

    batch_client = azurebatch.BatchServiceClient(
        credentials,
        batch_url=config._BATCH_ACCOUNT_URL)

    try:
        # Create the pool that will contain the compute nodes that will execute the
        # tasks.
        create_pool(batch_client, config._POOL_ID, application_files)

        # Create the job that will run the tasks.
        create_job(batch_client, config._JOB_ID, config._POOL_ID)

        # Add the tasks to the job. Pass the input files and a SAS URL
        # to the storage container for output files.
        add_tasks(batch_client, config._JOB_ID, input_files, output_container_sas_url)

        # Pause execution until tasks reach Completed state.
        wait_for_tasks_to_complete(batch_client,
                                   config._JOB_ID,
                                   datetime.timedelta(minutes=1800))

        print("  Success! All tasks reached the 'Completed' state within the "
              "specified timeout period.")

    except batchmodels.BatchErrorException as err:
        print_batch_exception(err)
        raise


    # Delete input container in storage
    print('Deleting container [{}]...'.format(input_container_name))
    blob_service_client.delete_container(input_container_name)

    # Print out some timing info
    end_time = datetime.datetime.now().replace(microsecond=0)
    print()
    print('Sample end: {}'.format(end_time))
    print('Elapsed time: {}'.format(end_time - start_time))
    print()

    # Clean up Batch resources (if the user so chooses).
    if query_yes_no('Delete job?') == 'yes':
        batch_client.job.delete(config._JOB_ID)

    if query_yes_no('Delete pool?') == 'yes':
        batch_client.pool.delete(config._POOL_ID)

    print()
    input('Press ENTER to exit...')
