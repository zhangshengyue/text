import aiomysql
import logging
import asyncio
import pdb

def log (sql,args=()):
	logging.info('SQL:%s' %sql)
	

@asyncio.coroutine
def create_pool(loop, **kw):
	global __pool
	__pool=yield from aiomysql.creat_pool(
	host=kw.get('host','localhost'),
	port=kw.get('port',3306),
	user=kw['user'],
	password=kw['password'],
	db=kw['database'],
	charset=kw.get('charset','utf8'),
	autocommmit=kw.get('autocommmit',True),
	maxsize=kw.get('maxsize',10),
	minsize=kw.get('minsize',1),
	loop=loop
	)


	
@asyncio.coroutine
def select(sql,args,size=None):
	log(sql,args)
	global __pool
	with (yield from __pool)as conn:
		cur =yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?','%s'),args or ())
		if size:
			rs=yield from cur.fetchmany(size)
		else:
			rs=yield from cur.fetchall()
		yield from cur.close()
		logging.info('row returned:%s' % len(rs))
		return rs
		
		
		
@asyncio.coroutine
def execute(sql,args,autocommmit=True):
	log(sql)
	with (yield from __pool) as conn:
		if not autocommmit:
			yield from conn.begin()
		try:
			cur = yield from conn.cursor()			
			yield from cur.execute(sql.replace('?', '%s'), args)
			affected = cur.rowcount
			yield from cur.close
			if not autocommmit:
				yield from conn.commit()
		except BaseException as e:
			if not autocommmit:
				yield from conn.rollback()
			raise e	
		return affected
		

class ModelMetaclass(type):
	def	__new__(cls,name,bases,attrs):
		if name == 'Model':
			return type.__new__(cls,name,bases,attrs)
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table:%s)'%(name,tableName))
		mappings = dict()
		field =[]
		primaryKey = None
		for k,v	in attrs.items():
			if isinstance(v,Field):
				logging.info('found mapping: %s ==> %s ' %(k,v))
				mappings[k] = v 
				if v.primary_Key:
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					field.append(k)
		if not primaryKey:
			raise RuntimeError('primary key not found')
		for k in mappings.key():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: r"`%s`" %f ,fields))
		attrs['__mappings__'] = mappings
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey
		attrs['__fields__'] = fields
		
		attrs['__select__'] = "select `%s`,%s from `%s`" % (
            primaryKey, ','.join(escaped_fields), tableName)		
		attrs['__delete__']	= 'delete from `%s` where `%s` =?' %(
		tableName,','.join(map(lambda f:'`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (
            tableName, primaryKey)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(
            escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		return type.__new__(cls,name,bases,attrs)	
		
		
def create_args_string(num):
	L=[]
	for n in range(num):
		L.append('?')
	return ','.join(L)
	
	
class Model(dict,metaclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model,self).__init__(**kw)
	
	def __getattr__(self,key):
		try:
			return self[key]
		except keyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)
	
	def __setattr__(self,key,value):
		self[key] = value
	
	def getValue(self, key):
		return getattr(self, key, None)
	
	def getValueOrDefault(self,key):
		value = getattr(self,key,none)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default				
				logging.debug('using default value for %s:%s' %
                              (key, str(value)))
				setattr (self,key,value)
		return value
	
	@classmethod
	@asyncio.coroutine
	def findAll(cls, where=None, args=None, **kw):
	#args表示填入sql的选项值，是一个tuple  kw表示关键函数，是一个dict
		sql = [cls.__select__]
        # 我们定义的默认的select语句是通过主键查询的,并不包括where子句
        # 因此若指定有where,需要在select语句中追加关键字
		if where:
			sql.append("where")
		sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get("orderBy", None)
        # 解释同where, 此处orderBy通过关键字参数传入
		if orderBy:
			sql.append("order by")
			sql.append(orderBy)
        # 解释同where
		limit = kw.get("limit", None)
		if limit is not None:
			sql.append("limit")
			if isinstance(limit, int):
				sql.append("?")
				args.append(limit)
			elif isinstance(limint, tuple) and len(limint) == 2:
				sql.append("?, ?")
				args.extend(limit)
			else:
				raise ValueError("Invalid limit value: %s" % str(limit))
		rs = yield from select(' '.join(sql), args) #没有指定size,因此会fetchall
		return [cls(**r) for r in rs]
		
	@classmethod
	@asyncio.coroutine
	def findNumber(cls,selectField,where=None,args=None):#这些是啥，日了吉娃娃了
		sql = ["select %s _num_ from `%s`" % (selectField, cls.__table__)]
		if where:
			sql.append("where")
			sql.append(where)
		rs = yield from select(' '.join(sql), args, 1)
		if len(rs) == 0:
			return None
		return rs[0]["_num_"]
		
	@classmethod
	@asyncio.coroutine
	def find(cls,pk):
		rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs)==0:
			return None
		return cls(**rs[0])
		
		
	@asyncio.coroutine
	def save(self):        
		args = list(map(self.getValueOrDefault, self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
        # pdb.set_trace()
		rows = yield from execute(self.__insert__, args)  
		if rows != 1:
            # 插入失败就是rows!=1
			logging.warn(
				'failed to insert record: affected rows: %s' % rows)
	@asyncio.coroutine
	def update(self):
        # 这里使用getValue说明只能更新那些已经存在的值，因此不能使用getValueOrDefault方法
		args = list(map(self.getValue, self.__fields__))
		args.append(self.getValue(self.__primary_key__))
        # pdb.set_trace()
		rows = yield from execute(self.__update__, args)    # args是属性的list
		if rows != 1:
			logging.warn(
				'failed to update by primary key: affected rows: %s' % rows)
	@asyncio.coroutine
	def remove(self):
		args = [self.getValue(self.__primary_key__)]
        # pdb.set_trace()
		rows = yield from execute(self.__delete__, args)		
		if rows != 1:
			logging.warn("failed to remove by primary key: affected rows %s" % rows)
				
				

class Field(object):  # 属性的基类，给其他具体Model类继承

	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default 			# 如果存在default，在getValueOrDefault中会被用到

	def __str__(self):  # 直接print的时候定制输出信息为类名和列类型和列名
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        # String一般不作为主键，所以默认False,DDL是数据定义语言，为了配合mysql，所以默认设定为100的长度
		super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):

	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)


class IntegerField(Field):

	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'biginit', primary_key, default)


class FloatField(Field):

	def __init__(self, name=None, primary_key=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)


class TextField(Field):

	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)				