
FROM alpine:3.21

RUN apk update && apk upgrade --no-cache

CMD ["sh", "-c", "echo Docker security lab image"]
