from tortoise import Model,fields

class User(Model):
    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)
    age = fields.IntField(max_length=255)
    avatar = fields.CharField(max_length=255)

