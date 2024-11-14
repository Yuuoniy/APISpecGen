FROM ubuntu:22.04

WORKDIR /root/
ENV TZ=Asia/Dubai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# https://dev.to/grigorkh/fix-tzdata-hangs-during-docker-image-build-4o9m

# RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
# add repo and update
RUN apt-get upgrade
RUN dpkg --add-architecture i386 && apt-get update

# install basic libs and tools
RUN apt-get update && apt-get install -y build-essential gcc-multilib g++-multilib nasm bc fd-find graphviz graphviz-dev python3.10 python3.10-dev openjdk-11-jdk sudo 

# These libs and tools are necessary for Linux 5.x
RUN apt-get install -y flex bison libelf-dev libssl-dev kmod

# install build tools
RUN apt-get install -y ninja-build cmake


# install network tools and "downloaders"
RUN apt-get install -y netcat socat git curl net-tools wget
RUN apt-get update && apt-get install -y python3.10-distutils


# install zshrc with oh-my-zsh
RUN apt-get install -y zsh && git clone --depth=1 https://github.com/robbyrussell/oh-my-zsh.git /tmp/oh-my-zsh && cat /tmp/oh-my-zsh/tools/install.sh | zsh &&\
    sed -i "1,$ s/ZSH_THEME=\"robbyrussell\"/ZSH_THEME=\"ys\"/g" ~/.zshrc && \
    chsh -s /bin/zsh

# install tmux with .tmux
RUN apt-get install -y tmux && \
    git clone https://github.com/gpakosz/.tmux.git && \
    ln -s -f .tmux/.tmux.conf && cp .tmux/.tmux.conf.local .

# locale
RUN apt-get install -y locales && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


RUN git clone https://github.com/Yuuoniy/APISpecGen.git
WORKDIR /root/APISpecGen


RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.10 get-pip.py && pip install -r requirements.txt
RUN mkdir /root/tools
WORKDIR /root/tools

# ENV http_proxy=http://XX.XX.XX.XX:XXX
# ENV https_proxy=http://XX.XX.XX.XX:XXX

RUN apt-get install -y unzip
RUN wget https://github.com/joernio/joern/releases/latest/download/joern-install.sh
RUN chmod +x ./joern-install.sh && ./joern-install.sh --version=v1.1.763


RUN git clone https://github.com/tree-sitter/tree-sitter-c && cd tree-sitter-c && git checkout e348e8ec5efd3aac020020e4af53d2ff18f393a9

WORKDIR /root/tools
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
# RUN cargo install weggli@0.2.2
# Install the weggli with the log-var feature
RUN git clone https://github.com/Yuuoniy/weggli.git
RUN cd weggli && git checkout log-var
WORKDIR /root/tools/weggli
RUN cargo build --release
RUN ln -s /root/tools/weggli/target/release/weggli /usr/bin/weggli


RUN mkdir /root/source && cd /root/source
RUN wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.16.tar.xz
RUN tar -xvf linux-5.16.tar.xz -C /root/source/
RUN mv /root/source/linux-5.16 /root/source/linux

WORKDIR /root/APISpecGen

CMD /bin/bash