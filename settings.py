TORTOISE_ORM={
        'connections': {
                # Dict format for connection
            'default': {
                'engine': 'tortoise.backends.mysql',
                'credentials': {
                    'host': '127.0.0.1',
                    'port': '3306',
                    'user': 'root',
                    'password': '',
                    'database': 'philo',
                    'minsize':1,
                    'maxsize':5,
                    'charset':'utf8mb4',
                }
            },
    },
        'apps': {
                'models': {
                    'models': ['models',"aerich.models"],#在根目录下就不用放路径名称前缀
                    'default_connection': 'default',
                }
    },
    }