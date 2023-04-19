#!/bin/bash
server="192.168.159.145:6121"
file1="test1m"
file2="test2m"
echo "go run client_benchmarker/main.go -v -m -o=/home/mininet/go/src/github.com/lucas-clemente/pstream/example/log-client.txt https://${server}/${file1} 20 0 https://${server}/${file2} 10 0"
go run client_benchmarker/main.go -v -m -o=/home/mininet/go/src/github.com/lucas-clemente/pstream/example/log-client.txt https://${server}/${file1} 20 0 https://${server}/${file2} 10 0
