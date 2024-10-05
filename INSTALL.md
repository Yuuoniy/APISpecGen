

## Install 
Get the DockerFile and build the docker.
```shell
wget https://github.com/Yuuoniy/APISpecGen/raw/refs/heads/main/Dockerfile 
docker build -t apispecgen:latest .
docker run -it --name "apispecgen" "apispecgen:latest"
```

If you have network problems that causes tools install to fail, you may add a proxy to the dockerfile as follows: 
```
ENV http_proxy=http://XX.XX.XX.XX:XXX
ENV https_proxy=http://XX.XX.XX.XX:XXX
```