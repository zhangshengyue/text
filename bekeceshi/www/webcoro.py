import asyncio, os, inspect, logging, functools
from urllib import parse
#parse 输出一个时间点到1970的时间
from aiohttp import web
from apis import APIError
#端口错误返回

#定义get装饰器；这样，一个函数通过@get()的装饰就附带了URL信息。
def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
	#func表示一个函数，
        @functools.wraps(func)
		#@wraps作用为使函数被装饰后函数名等属性不变
		#args，**kw表示原函数的参数和关键字参数
        def wrapper(*args, **kw):
            return func(*args, **kw)
		#wrapper的方法是get  路径是path	
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator
def post(path):
#post同get
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator
#获取函数传递值中的可变参数或命名关键字参数(不包含设置缺省值的)名称列表：
def get_required_kw_args(fn):
    args = []
    #inspect.signature(fn)：表示fn函数的调用签名及其返回注释，
	#                    为函数提供一个Parameter参数对象存储参数集合。
    #inspect.signature(fn).parameters：参数名与参数对象的有序映射。
    params = inspect.signature(fn).parameters
    for name, param in params.items():  #.items()返回一个由tuple(此处包含name, parameters object)组成的list。
        #inspect.Parameter.kind：描述参数值对应到传参列表
		#             (有固定的5种方式，KEYWORD_ONLY表示值为“可变参数或命名关键字参数”)的方式。
        #inspect.Parameter.default：参数的缺省值，如果没有则属性被设置为 Parameter.empty。
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)
	
	
#获取函数传递值中的可变参数或命名关键字参数(全部的)名称列表：	
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

	
#判断函数传递值中是否存在可变参数或命名关键字参数：
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

#判断函数传递值中是否存在关键字参数：			
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        #VAR_KEYWORD表示值为关键字参数。
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

			
#判断函数传递值中是否包含“request”参数，若有则返回True：
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        #传递值中包含名为'request'的参数则跳出本次循环(不执行本次循环中的后续语句，但还是接着for循环)，found赋值为True：
        if name == 'request':
            found = True
            continue
        #VAR_POSITIONAL表示值为可变参数。
        #传递值中包含参数名为'request'的参数，且参数值对应到传参列表方式不是“可变参数、关键字命名参数、关键字参数”中的任意一种，则抛出异常：
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

	
#aiohttp.web的request handler实例，当url地址请求的时候就会调用。
#封装一个URL处理函数类，由于定义了__call__()方法，因此可以将其实例视为函数：
class RequestHandler(object):
    #不需要手动创建 Request实例 - aiohttp.web 会自动创建。
    #初始化已实例化后的所有父类对象，方便后续使用或扩展父类中的行为：
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)     
		#判断函数传递值中是否包含“request”参数，若有则返回True。
        self._has_var_kw_arg = has_var_kw_arg(fn)      
		#判断函数传递值中是否存在关键字参数。
        self._has_named_kw_args = has_named_kw_args(fn) 
		#判断函数传递值中是否存在可变参数或命名关键字参数。
        self._named_kw_args = get_named_kw_args(fn)     
		#获取函数传递值中的可变参数或命名关键字参数(全部的)名称列表。
        self._required_kw_args = get_required_kw_args(fn)   
		#获取函数传递值中的可变参数或命名关键字参数(不包含设置缺省值的)名称列表。

    #@asyncio.coroutine装饰，变成一个协程:
    @asyncio.coroutine
    def __call__(self, request):    #Request 实例为 aiohttp.web 自动创建的。
        kw = None
        #判断函数是否包含“可变参数、命名关键字参数、关键字参数”，以及是否能获取到参数(不包含缺省)名称列表：
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            #判断HTTP请求方法使用的类型：
            if request.method == 'POST':
                #Contern-Type 标明发送或者接收的实体的MIME类型。例如：Content-Type: text/html
                #判断POST请求的实体MIME类型是否存在：
                if not request.content_type:
                    #MIME类型不存在则返回错误信息：
                    return web.HTTPBadRequest('Missing Content-Type.')
                #将POST请求的实体MIME类型值转换为全小写格式：
                ct = request.content_type.lower()
                #str.startswith(str,[strbeg(int)],[strend(int)]):检查字符串是否是以指定子字符串开头，返回True/False。若参数 beg 和 end 指定值，则在指定范围内检查。
                #检查“content_type”类型是否为“application/json”开头的字符串类型：
                if ct.startswith('application/json'):
                    #以JSON编码读取请求内容：
                    params = yield from request.json()  #request.json() 是个协程。
                    #判断读取的内容是否为“dict”类型；JSON的“object”类型对应的是python中的“dict”类型。
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                #检查“content_type”类型是否为“application/x-www-form-urlencoded”或“multipart/form-data”开头的字符串类型：
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    #读取请求内容的POST参数：
                    params = yield from request.post()  #request.post() 是个协程。
                    #构造POST参数字典：
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            #判断HTTP请求方法使用的类型：
            if request.method == 'GET':
                #获取请求URL中的查询字符串；如：“id=10”。
                qs = request.query_string
                if qs:
                    kw = dict()
                    #urllib.parse.parse_qs(str)：返回解析指定字符串中的查询字符串数据字典；
					#可选参数值“True”表示空白值保留为空白字符串，默认为忽略(False)。
                    #循环出查询字符串数据字典并重组：
                    for k, v in parse.parse_qs(qs, True).items():   #dict.items()返回一个由tuple(包含key,value)组成的list。
                        kw[k] = v[0]
        if kw is None:
            #request.match_info：地址解析的(只读属性和抽象匹配信息实例)结果；确切的类型的属性取决于所使用的地址类型。
            kw = dict(**request.match_info)

        else:
            #若函数不包含“关键字参数”且可变参数或命名关键字参数(全部的)名称列表不为空，则执行以下操作：
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                #循环出参数名称列表并重组成字典：
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            #循环出地址解析的结果字典数据并更新值到kw字典：
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    #打印日志：重复的arg name
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        #判断函数传递值中是否包含“request”参数：若包含则添加至kw字典：
        if self._has_request_arg:
            kw['request'] = request
        # check required kw:
        #获取函数传递值中的可变参数或命名关键字参数(不包含设置缺省值的)名称列表。
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    #传递值的参数不存在于kw字典则返回错误信息：
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        #打印(调用函数的参数字典)日志：
        logging.info('call with args: %s' % str(kw))
        try:
            #使用重构的kw参数字典，执行函数并返回结果：
            r = yield from self._func(**kw)
            return r
        except APIError as e:
            #返回自定义的异常信息分类及处理信息：
            return dict(error=e.error, data=e.data, message=e.message)
			

	

