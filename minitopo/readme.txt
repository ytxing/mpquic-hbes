minitopo文件夹用于替换mininetvm中git目录下的minitopo
minitopoexp文件夹在主机上运行那个唯一的py文件即可，可以在  
mptcpTopos = [{'paths': [{'queuingDelay': '0.048', 'bandwidth': '51.83', 'delay': '10.5', 'jitter': '0'}, {'queuingDelay': '0.063', 'bandwidth': '45.38', 'delay': '13.3', 'jitter': '0'}], 'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]}]进行修改链路设置
netem前两个是链路不要修改
如果想进行多组实验可以在后面加topo
log文件中，主要搜索random（我设置的请求文件是20M，分别叫random，random1和random2） 会有类似https://10.1.0.1:6121/random1: 5.038832229s
后面的时间代表完成用时
文件大小和优先级的调节在/minitopo/mpExperienceQUIC.py 
prepare函数中可以看到由dd命令生成random文件，改变self.random_size为想要的值即可
getQUICClientCmd函数有请求的优先级，原文件里面是200 0 10 5 和40 5
第二个数字是dependency，第一个流是stream 5 ，第二个是stream 7，可以根据这个生成优先级树
原文件是请求三个文件，如果想更多可用在prepare中用dd生成，同时在getQUICClientCmd请求中加入同名的文件

