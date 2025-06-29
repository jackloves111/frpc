FROM python:3.9-alpine as builder

ENV VERSION 0.60.0
ENV TZ=Asia/Shanghai
WORKDIR /build

# 安装必要的构建依赖
RUN apk add --no-cache wget tzdata

# 下载并解压frpc
RUN if [ "$(uname -m)" = "x86_64" ]; then export PLATFORM=amd64 ; \
    elif [ "$(uname -m)" = "aarch64" ]; then export PLATFORM=arm64 ; \
    elif [ "$(uname -m)" = "armv7" ]; then export PLATFORM=arm ; \
    elif [ "$(uname -m)" = "armv7l" ]; then export PLATFORM=arm ; \
    elif [ "$(uname -m)" = "armhf" ]; then export PLATFORM=arm ; fi \
    && wget --no-check-certificate https://github.com/fatedier/frp/releases/download/v${VERSION}/frp_${VERSION}_linux_${PLATFORM}.tar.gz \
    && tar xzf frp_${VERSION}_linux_${PLATFORM}.tar.gz \
    && cd frp_${VERSION}_linux_${PLATFORM} \
    && mkdir -p /build/frp \
    && mv frpc frpc.toml /build/frp/

# 最终镜像
FROM python:3.9-alpine
LABEL maintainer="Stille <stille@ioiox.com>"

ENV TZ=Asia/Shanghai
ENV FRPC_CONFIG=/frp/frpc.toml
ENV PORT=7070

# 安装必要的包
RUN apk add --no-cache tzdata docker-cli supervisor \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone

# 创建必要的目录
WORKDIR /app

# 复制frpc文件
COPY --from=builder /build/frp /frp

# 复制web管理界面文件
COPY frpc-web-admin .
RUN pip install -r requirements.txt

# 复制配置初始化脚本
COPY init-config.py /app/init-config.py
RUN chmod +x /app/init-config.py

# 复制supervisor配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

VOLUME /frp

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
