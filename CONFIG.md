# 文件级配置 #

* file: 用于下面加载python function用。
* download: 指明下载的处理函数。
* downdir: 未指明下载函数时以文件名下载到该目录。注意，同名文件会互相覆盖。
* result: 指明结果数据的处理函数。
* disable_robots: disable robots limitation.
* headers: default headers.
* timeout: timeout setup
* interval: crawl-delay * not support yet

# 匹配模式 #

* name: 使用callto指令，提交一个链接的时候可以同时指明用于处理的配置。
* desc:

# action #

* sitemap: download a sitemap and add all them into queue. txt filter and link filter can be used.
* links: 使用request下载内容，使用lxml.html解析。而后使用parsers进行逐项解析。这个项目的值应该是一个list。
* result: 使用request下载内容，使用lxml.html解析。而后使用parsers进行逐项解析。这个项目的值应该是一个dict。
* lxml: 使用request下载内容，使用lxml.html解析，然后调用后面所指定的python函数。并且将结果一并传递。
* download: 将url下载，使用指定函数处理。如果指定函数为空，使用config中的download函数进行存储。
* http: 使用request下载内容，然后调用后面所指定的python函数。并且将结果一并传递。
* url: 将url直接传递给后面所指定的python函数，没有下载行为。用户可以自行选择下载方式。

有关python函数的指定，请看[api](API.md)。

# html parser #

这是基础parser，用于处理html对象。这里的内容既可以用于link处理也可以用于result处理。但是必须保证对象为html，否则会在lxml解析时出错。

* css: 一个css选择器，选中一组内容。
* xpath: 一个xpath选择器，选中一组内容。
* attr: 获得选中节点的某个属性，例如href。
* text: 获得选中节点的文本内容。
* html: 获得选中节点的html源码。
* html2text: 将选中节点的html源码转换为text。

以上头两个被成为source属性，指名处理哪个节点。后续的称为tostr，将节点转换为字符串。

# txt filter #

这些是文本过滤器，可以辅助处理一些文本。

* is: 一个正则表达式，命中则通过。
* isnot: 一个正则表达式，不命中才通过。
* before: 在执行前调用特定python函数，返回True跳过当前对象。
* after: 在执行后调用特定python函数，返回True退出循环。
* map: 在执行后调用特定python函数，将原始字符串映射为目标字符串。
* dictreplace: 一个列表，里面两个元素。第一个会被按正则解析，并且匹配出一些命名结果。这些结果会被送入第二个做字符串format合成。

# link filter #

* call: 使用callto指定的name执行该link的解析。
* headers: request headers
* method: GET/POST/PUT...
