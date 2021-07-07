# The Azure Batch client template

### When to use Azure Batch for your compute job

1. Does your compute job take longer than you want to wait, or do you want to do more in less time?
2. Can you divide your job into many similar but independent tasks?

If the answer to these two questions is yes, then you may be in luck.
The Azure Batch service is a very accessible way to scale out by parallelizing any application to virtual machines (VMs) in the cloud. 
Using this cient, it allows the user to plug in their own software by simply updating a configuration file.

### Introduction

Azure Batch provides scheduling and management services to orchestrate the scaling of a compute job. To understand exactly what this 
means, we must first get the terminology clear. One must perform a compute job that can be divided into individual tasks. Each task 
makes use of the exact same application software, but may use unique input files, leading to a task-specific output. The first stage 
in running your Batch job therefore consists of defining your application, the division of your job into tasks, and the input for 
each task. In Figure 1 the entire process is shown schematically. 

Batch Service deploys a pool of VMs for you--commonly referred to as compute nodes or simply nodes--in Microsoft data centers and 
handles the division of your tasks over these nodes. When a node has finished a task, Azure Batch sends the next task in the queue to 
that node. If an error occurs on any node, the interrupted task is resumed on another node. This way, Azure Batch makes sure that 
your pool is used as efficiently and robustly possible.


![alt text](https://github.com/rubeneric/Batch_Client_Template/blob/master/images/batch_overview.png "Azure Batch schematic")

*Figure 1: Schematic functioning of Azure Batch. The batch pool and job are being defined and deployed from the user's personal computer.*


The number of nodes in your pool, and the size of the nodes (i.e. the technical specifications of the VMs that are deployed by Batch), 
are for you to decide. A larger pool gets the job done faster, but may result in a larger number of added compute hours due to the 
overhead time of deploying and decommissioning your nodes. Since you pay per VM, per minute from the time you start your deployment, 
a smaller pool may therefore be cheaper. 

Similarly, choosing large compute nodes with many cores each may prove to be efficient if your application is optimized for 
parallelization on a single machine. In other cases, going with a large number of single-core machines will be advisable. What 
configuration suits the job can typically be estimated from your experience with the application, and when necessary, further optimized 
in a series of small-scale trial runs. More tips and tricks are presented in the section “Optimization and Cost Management” below.

Further sources that this client is based on: 
* The Azure Batch samples at https://github.com/Azure-Samples/azure-batch-samples/tree/master/Python/Batch
* The Azure Batch tutorial at https://github.com/Azure-Samples/batch-dotnet-ffmpeg-tutorial
* The documentation at the Azure Batch Python namespace https://docs.microsoft.com/en-us/python/api/overview/azure/batch?view=azure-python


### Getting started

1.	Setup your Azure services.  If you don’t already have one, you will need to set up an Azure subscription. Within that subscription, create an Azure Batch Service and an Azure Storage account.
    * Create Batch account: https://docs.microsoft.com/en-us/azure/batch/batch-account-create-portal
    * Create Storage account: https://docs.microsoft.com/en-us/azure/storage/common/storage-quickstart-create-account?tabs=portal
    * Optional but recommended - download Azure Storage Explorer: https://azure.microsoft.com/en-us/features/storage-explorer/
    * Optional but recommended - downoad Azure Batch Exmplorer: https://blogs.technet.microsoft.com/windowshpc/2015/01/20/azure-batch-explorer-sample-walkthrough/
2.  Create three containers in your Blob Storage account, named 'application', 'input' and 'output'. 
3. Upload your application files (installers, packages etc) to your application folder. Then create a file named *starttask.cmd* that will be run by Azure Batch each time a node is started up for the first time. This file should contain a batch script that installs everything needed to run tasks on the node. Similarly, create a file named *task.cmd* that contains the script to run each task. You can find an example of these files, along with the *UploadToBlob.exe*, in the 'application' folder in the solution. Upload these two .cmd files and the .exe file to the application folder.
4. Upload all input files to the input container. The output container stays empty: this is where your output files will be uploaded from each node.
5.	Download the Azure Batch Client files from this repository.

![alt text](https://github.com/rubeneric/Batch_Client_Template/blob/master/images/app.config%20(1).png "Config file")

*Figure 2: the contents of the “App.config” configuration file that need to be set up.*

6.	Setup the configuration file. The “app.config” file found in the template folder contains the basic information needed to setup your job. Figure 2 shows which parameters need to be set. We will walk you through them here.
    *	The first five parameters refer to the account properties of your Azure Batch and Storage account
    *	The *PoolID* and *JobID* can be chosen at will to uniquely identify your pool and job, respectively
    *	*FilesPerTask* defines of how many input files a task consists. This number can be chosen to be one, but consider trying to find the right balance between reducing overhead (by not having to restart your application for every single input file), and having a small task size to distribute them evenly over the nodes
    *	The *PoolSizeDedicated* is the number of dedicated nodes Batch will deploy
    *	The *PoolSizeLowPriority* is the number of low priority nodes Batch will deploy. 
        * Documentation: https://docs.microsoft.com/en-us/azure/batch/batch-low-pri-vms
        * Pricing: https://azure.microsoft.com/en-us/pricing/details/batch/
    *	The *NodeSize* is code (id) defining the technical specifications of each node. For an overview of the available options with ids, see https://docs.microsoft.com/en-us/azure/cloud-services/cloud-services-sizes-specs
    *	The *TimeOutLimit* sets a limit in minutes after which time your job is terminated, to prevent it from running indefinitely if it does not finish successfully
7. Run the client, either by building the solution or running the code in debug mode. The client will run locally and monitor the job - make sure the computer that runs the client doesn't shut down or go into sleep mode, or the job will be disrupted.
8. IMPORTANT: After the client has finished running (either after completing the job successfully, or after an errors or interruption), make sure to check that your pool is properly shut down by going to the Azure portal https://ms.portal.azure.com/, checking your Batch Account -> Pools -> Delete. A pool can remain active even after the job is completed, and you will be charged by the minute for this time. The next section explains in more detail how to limit costs.


### Optimization and cost management

The Azure Batch service itself is free of charge – you simply pay, per minute, for the virtual machines that are running in your pool. You are in full control of the number of virtual machines set up and for how long they run.  Therefore, it is critical to understand how to minimize the time they are running, and to understand the risk of unexpected costs should they not be properly shut down after use. Please mind the following best practices to ensure your Batch job runs as efficiently as possible.
1.	__Take the time to optimize your application.__
When you start running many instances of your application, any of bugs or inefficiencies within it will manifest themselves proportionally. Think carefully about how to optimize your application or compute scenario before getting started with Azure Batch.
2.	__Choose the best node and pool size for your job by running several short test scenarios.__
Depending on your application, faster nodes will not always deliver proportional results. If it is unclear how your application handles multiple processor cores, try running a set of small-scale benchmark runs on a range of node and pool sizes. Mark down the time it takes to deploy the nodes, as well as the total run time: that way, it is easy to extrapolate how long your full-scale job will run on each configuration.
[to be added: choosing the right pool size to fit your job]
3.	__Estimate the running costs of your job and set a timeout limit.__
Once you have a good understanding of how your application performs on the chosen nodes, it is easy to estimate the total running time, and with it the costs of your run. If you intend to leave the job running unattended, make sure to set a timeout limit, but do not to make it too tight.
4.	__Monitor your job at set time points__.
While the Azure Batch service is very robust in its distribution and backing up of tasks, mistakes are easily made when setting up your Batch job. It is therefore advisable to closely monitor the first stages of the job where the pool is deployed and the first tasks initiated. Batch Explorer is a good tool for doing so. This minimizes the impact of any errors.
5.	__Check if your pool is correctly decommissioned after job completion.__
Even if all tasks are performed and your job is completed with the desired output, a pool may remain active if not properly decommissioned. The Batch template presented here does this automatically upon job completion, but always check and confirm that the pool was successfully removed or you risk being charged for unnecessary running time.



