# Ansible Modules for Viptela vManage API

## Setup Procedure

### Step 1 - Clone Repo
``` 
git clone https://github.com/chrishocker/ansible-viptela.git

cd ansible-viptela
```
### Step 1 - Install virtualenv
``` 
pip2 install virtualenv
```
### Step 2 - Create and activate virtualenv
``` 
virtualenv venv

source venv/bin/activate
```
### Step 3 - Install Ansible and Requests
``` 
pip install ansible
pip install requests
```
### Step 4 - Create secrets.yml file
```
vmanage_ip: "<ip address>"
username: "<username>"
password: "<password>"
```
### Step 5 - Run playbook
```
ansible-playbook playbook.yml
```

