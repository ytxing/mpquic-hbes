#!/bin/bash
my_ip="192.168.159.145"
my_port="6121"
go run main.go -www /var/www -certpath ~/go/src/github.com/lucas-clemente/pstream/example/ -v -bind ${my_ip}:${my_port}
