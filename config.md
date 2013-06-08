# config #

* file: 用于下面加载python function用。
* download: 指名下载的下载函数。
* downdir: 未指名下载函数时以文件名下载到该目录，注意，同名互相覆盖。
* result: put result to object

# patterns #

模式匹配有3种模式，base和match。base比match优先。

* id: callto id
* base: 使用startswith工作，速度较快。一般用于大型网站的分割组合，复杂度隔离。
* match: 使用正则表达式工作，速度较慢。

# function #

在python代码中可以按名称调用。

# python function #

指定一个python函数时，可以用`file:function_name`的格式指定。或者只指名function_name，file在config中指定。

# action #

* yaml: 指定另一个yaml处理。
* redirect: 自动抓取另一个url，而不抓当前url。
* links: 使用request下载内容，使用lxml.html解析。而后使用parsers进行逐项解析。这个项目的值应该是一个list。
* result: 使用request下载内容，使用lxml.html解析。而后使用parsers进行逐项解析。这个项目的值应该是一个dict。
* lxml: 使用request下载内容，使用lxml.html解析，然后调用后面所指定的python函数。并且将结果一并传递。
* download: 将url下载，使用指定函数处理。如果指定函数为空，使用config中的download函数进行存储。
* http: 使用request下载内容，然后调用后面所指定的python函数。并且将结果一并传递。
* url: 将url直接传递给后面所指定的python函数，没有下载行为。用户可以自行选择下载方式。

# html parser #

* css: 一个css选择器，选中一组内容。
* xpath: 一个xpath选择器，选中一组内容。
* attr: get attr from node.
* text: get text from node.
* html: get html source fron node.
* html2text: render html 2 text.

# txt filter #

* is: re which hit.
* isnot: re which not hit.
* before: 在执行前调用特定python函数，返回True跳过当前对象。
* after: 在执行后调用特定python函数，返回True退出循环。
* map: map source to target

# link filter #

* callto: 使用callto指定的id执行该link的解析。

注：如果callto没有使用绝对id，那么系统会自动增加当前文件的id(如果存在)作为前缀。
