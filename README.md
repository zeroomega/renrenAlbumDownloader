##人人网相册下载器
鉴于人人网随时都有可能垮掉，然而人人网并不提供数据下载服务，同时一张张自己手动下载照片又太过于繁琐，我动手写了这个下载器。

###使用方法
修改configs.json文件中的用户名和密码为自己的用户名和密码。然后执行:
>python renrenAlbumDownloader.py

即可。相应的照片会自动根据相册名称保存到当前文件夹下。

代码使用python 2.7 测试通过。如果要用python 3 麻烦自己修改一下文件头部的引用部分。

###参数
如果执行过程中遇到问题（请首先检查一下是否存在空的相册），可以使用 -d 参数打印调试信息
>python renrenAlbumDownloader.py -d

然后可以发到Issues 中，我如果有时间也许会看的。

###Note
这份代码没有任何授权协议，欢迎各位自行修改，分发。
