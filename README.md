# primehub-admin-notebook
[![CircleCI](https://circleci.com/gh/InfuseAI/primehub-admin-notebook.svg?style=svg)](https://circleci.com/gh/InfuseAI/primehub-admin-notebook)

# Kubernetes Management Tasks

This is a notebook for common kubernetes operations against PrimeHub.
These listed operations can be executed independently.

**Note: You should be aware of where and how the jupyter session is running, as kubernetes credentials are sensitive information and leakage posts security risks.**

## Caution: 
Before you execute operations, please check your kubectl and cluster health according to section **1.1 Configure kubectl** and section **1.2 Check version and cluster health** respectively first.


### 1.3 Delete user pvc
You can delete a user pvc by selecting it from `Target`.

### 1.4 Create pv-type dataset
By specifying a `Target` and `Size`, it generates a yaml string which you can apply to create a pv-type dataset.
