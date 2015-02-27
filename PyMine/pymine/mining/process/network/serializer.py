import pickle

class Serializer(object):

    def __init__(self):
        pass

    def serialize_as_string(self, obj):
        return pickle.dumps(obj)

    def deserialize_from_string(self, obj):
        return pickle.loads(obj)

    def serialize_as_file(self, obj, filename):
        try:
            with open(filename, 'w') as handle:
                pickle.dump(obj, handle)
            return True
        except Exception, e:
            return False

    def deserialize_from_file(self, filename):
        try:
            with open(filename, 'r') as handle:
                obj = pickle.load(handle)
            return obj
        except Exception, e:
            return False