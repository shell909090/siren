# python函数 #

指定一个python函数时，可以用`file:function_name`的格式指定。或者只指名function_name，file在config中指定。

下载函数的一般性形态有以下几种：

* url(worker, req, m)
* http(worker, res, resp, m)
* lxml(worker, res, doc, m)

resp为下载到的原始内容，doc为lxml解析后的结果。m为匹配时的正则表达式结果（如果是正则的话）。

* result(worker, req, rslt)

# worker对象 #

worker对象是和队列有关的对象，一般包括以下几个方法。

* request(url, headers=None, body=None, method='GET', callto=None)

# reqinfo对象 #

reqinfo是请求有关的内容，一般包括以下几个方法。

* url
* headers
* body
* method
* callto

和request一一对应。
