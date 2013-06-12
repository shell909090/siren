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

模式匹配有3种模式，id，base和match。id最优先，其次base，最后match。

* id: 使用callto指令，提交一个链接的时候可以同时指明用于处理的配置。
* base: 使用startswith工作，速度较快。一般用于大型网站的分割组合，复杂度隔离。
* match: 使用正则表达式工作，速度较慢。

id必须有callto才能执行，因此和base/match不冲突。当只有url时，如果base命中任意一条，就不执行match。如果没有base命中，则执行所有命中的match。

# 配置嵌套 #

在一个配置内，可以使用yaml加载另一个同目录下的yaml配置作为处理函数。

因此会引起一些衍生问题。例如，原本有一个yaml配置，声明了function1这么一种action。要调用function1，需要在link中指定callto: function1。但当这个配置被作为另一个配置的子配置加载时，function1就变成了主配置的某个id为function1的action。原本可以执行的callto就无法工作了。

当然，也可以让callto只调用本层的action。但是这就失去了跨配置调用的能力。而且在跨系统上有很大问题。

解决这个问题的方法是使用逐层模型。在第一层中可以指定id和base/match。调用时可以用id1.function1指名具体的action。

目前的callto已经经过调整。当callto的对象不是全局对象（没有.）时，会自动加上本配置的id作为前缀。因此又衍生出两个问题。

* 自动添加前缀只能添加一级。
* 配置如果指定了id，会有多余的东西被添上去。

关于这一问题，理想的方案是只能调用本配置的对应id，而不具备跨配置调用能力。这一目标比较难，目前正在考虑。

另外一个问题是base，当被某个base匹配到时，url会被自动脱去这个前缀。

# action #

* yaml: 指定另一个yaml处理。
* redirect: 自动抓取另一个url，而不抓当前url。
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

* callto: 使用callto指定的id执行该link的解析。
* headers: request headers
* method: GET/POST/PUT...
