# Remote-VIIV

## 💥💥 Current Development Progress 💥💥

Login Page: VIIV(backend), index.tsx(frontend)
Main Page: main(backend), room.tsx(frontend) 

## ✨✨ To Collaborate on Our Project ✨✨ 
### Backend
1. Activate Virtual Environment using conda (install conda if you don't have it)
```
conda create -n django_hw python=3.11 -y
conda activate django_hw
```
2. Install required packages
```
cd backend
pip install -r requirements.txt
```

### Frontend
1. Install Node.js

change your working directory to the root directory of the project, and run:
```
mkdir ~/workspace && cd ~/workspace
wget https://nodejs.org/dist/v20.17.0/node-v20.17.0-linux-x64.tar.xz
tar -xf node-v20.17.0-linux-x64.tar.xz
cd node-v20.17.0-linux-x64/bin
```

```
pwd
```
(The Path looks similar to: `export PATH=/your_workspace_absolute_path/node-v20.17.0-linux-x64/bin:$PATH`)
```
export PATH=Path_From_PWD:$PATH
source ~/.bashrc
```

Then re-activate your virtural environment:
```
conda activate django_hw
```

Check if Node.js has successfully installed: `node -v`. 
If it outputs the version number, the installation was successful.

2. Install yarn
(install npm if you haven't install it. `apt install nodejs npm`)
```
npm install -g yarn
```

```
yarn install
```


**You have completed all the installations! Congratulations!**

### Check if backend & frontend can successfully work on your local host
1. Backend
```
cd backend
python manage.py runserver
```
It will start up development server at http://127.0.0.1:8000/.

Access http://localhost:8000/main/1 to check if the server has started successfully. If it is running properly, you will see a webpage containing the message: {"status": "error", "message": "Only POST requests are allowed"}

1. Frontend

Create a new terminal page, and run:
```
cd frontend
yarn dev
```
It will start up development server at http://127.0.0.1:3000/.

Open your browser and enter http://localhost:3000 (replace the port number if the default port is occupied) in the address bar to access the frontend page.


