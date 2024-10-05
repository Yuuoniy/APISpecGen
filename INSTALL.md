

## Install 
Get the DockerFile and build the docker.
```shell
wget https://github.com/Yuuoniy/APISpecGen/raw/refs/heads/main/Dockerfile 
docker build -t apispecgen:latest .
docker run -it --name "apispecgen" "apispecgen:latest"
```

If you have network problems that causes joern install to fail, add a proxy to your dockerfile. -->
```
ENV http_proxy=http://XX.XX.XX.XX:XXX
ENV https_proxy=http://XX.XX.XX.XX:XXX
```