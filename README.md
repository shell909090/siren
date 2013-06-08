# 简介 #

siren是一套以配置为基础的爬虫系统，他的基本配置和解析系统是yaml。借助yaml的语法，他可以很轻松的定义爬虫，而不需要编写大量代码。

# 背景知识 #

使用siren，你需要了解css或者xpath，能够用css或xpath表述你需要获得的内容。知道正则表达式，能够使用正则处理简单的过滤和替换。

要良好的使用siren，你还可能需要了解robots.txt协议相关的内容。遵循别人的意愿，礼貌的获取数据，做一只绅(bian)士(tai)的爬虫。

# 原理简述 #

siren维护一个爬虫队列。在爬虫工作时，每次从队列中取出一个request。而后开始按照匹配规则进行匹配。

当匹配规则命中某个项目时，爬虫会执行一种action。例如把url下载下来，调用python代码处理。或者解析下载下来的html，再调用python代码。

siren的特殊之处在于，定义了一组预定义的爬虫处理程序。这组程序被称为parsers。通过配置，可以直接处理结果，而不需要编写python代码。

# 范例 #

	name: wenku8
	result: novel:result
	patterns:
	  - name: table of content
		match: http://www.wenku8.cn/novel/[0-9]/[0-9]+/index.htm
		links:
		  - css: a
			attr: href
			is: "[0-9]+\\.htm"
			callto: node
	  - id: node
		name: node
		result:
		  title:
			css: div#title
			text: yes
		  content:
			css: div#content
			html2text: yes

# 配置讲解 #

细节请参考[config](config.md)。

# 入门指引 #

请看[guide](GUIDE.md)。

# TODO #

* 队列防回环：已经爬过的维护一份列表。
* robots.txt解析：支持爬虫协议，限制不允许url和限速。
* cookie在redis中保存：加速存取效率。

# 授权 #

    Copyright (C) 2012 Shell Xu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
