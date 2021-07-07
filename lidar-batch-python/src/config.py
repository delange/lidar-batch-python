#-------------------------------------------------------------------------
# 

# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, 

# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES 

# OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

#----------------------------------------------------------------------------------

# The example companies, organizations, products, domain names,

# e-mail addresses, logos, people, places, and events depicted

# herein are fictitious. No association with any real company,

# organization, product, domain name, email address, logo, person,

# places, or events is intended or should be inferred.
#--------------------------------------------------------------------------


# Global constant variables (Azure Storage account/Batch details)


# import "config.py" in "batch_python_windows.py"


# Update the Batch and Storage account credential strings below with the values

# unique to your accounts. These are used when constructing connection strings

# for the Batch and Storage client objects.

_BATCH_ACCOUNT_NAME ='' # Your batch account name 
_BATCH_ACCOUNT_KEY = '' # Your batch account key
_BATCH_ACCOUNT_URL = '' # Your batch account URL
_STORAGE_ACCOUNT_NAME = '' # Your storage account name
_STORAGE_URL = ''
_STORAGE_ACCOUNT_KEY = '' # Your storage account key

_POOL_ID = '' # Your Pool ID
_JOB_ID = '' # Job ID
_DEDICATED_POOL_NODE_COUNT = 2	# Number of dedicated VMs in your pool
_LOW_PRIORITY_POOL_NODE_COUNT = 0	# Number of low priority VMs in your pool
_POOL_VM_SIZE = 'standard_d13_v2' #'standard_d2s_v3' # VM Type/Size standard_d2s_v3