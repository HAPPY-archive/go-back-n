
## frame的组成设计
```
index . data length . data . crc
```
即4字节长度的索引，4字节长度来表示数据长度，数据内容，4字节长度的CRC校验值

## 运行


在`to_send.txt`中写入需要发送的数据。  
服务端最后接受的数据会被保存在`received_result.txt`中

运行服务端
```
python3 receiver.py
```

而后运行客户端
```
python3 sender.py
```

## 参数调整
由于使用了自定义的介质Medium类，故此处可以实现模拟frame在传输时候的损坏，丢失，超时等情况。

### ACK frame损坏概率
在`receiver.py`第59行，初始化Medium类的构造函数中，设置
```
should_emulate_timeout=True
```
而后emulate_timeout_fact为丢失超时的概率，范围从`0-1`的小数。

### frame损坏概率
在`receiver.py`第59行，初始化Medium类的构造函数中，设置emulate_wrong_frame_fact为帧损坏的概率，范围为从`0-1`的小数。

## 运行结果
![result](https://i.imgur.com/mA6KpnV.png)  