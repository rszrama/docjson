import requests
import json


version = '0.1.0'


class DocumentLink(object):
    def __init__(self, data):
        self._href = data['href']

    def get(self):
        response = requests.get(self._href)
        return loads(response.content)

    def __repr__(self):
        return 'link -> %s' % self._href


class DocumentList(object):
    def __init__(self, data):
        self._next = data['next']
        self._items = data['items']

    def __getitem__(self, idx):
        if idx < 0:
            raise IndexError('Negative indexing not supported')

        while self._next is not None:
            data = requests.get(self._next).json()
            self._next = data['next']
            self._items.extend(data['items'])
            if idx < len(self._items):
                return self._items[idx]

        raise KeyError

    def __repr__(self):
        items_repr = ', '.join(repr(item) for item in self._items)
        next_repr = ', ...' if self._next else ''
        return '[' + items_repr + next_repr + ']'


class DocumentForm(object):
    def __init__(self, data):
        self._href = data['href']
        self._method = data['method']
        self._fields = data['fields']

    def __call__(self, **kwargs):
        method = self._method
        href = self._href
        if self._method == 'get':
            response = requests.request(method, href, params=kwargs)
        else:
            payload = json.dumps(kwargs)
            headers = {'content-type': 'application/json'}
            response = requests.request(method, href, data=payload, headers=headers)
        return loads(response.content)

    def __repr__(self):
        fields_repr = ', '.join(self._fields)
        return 'form(' + fields_repr + ')'


class Document(object):
    def __init__(self, data):
        self._data = data

    def __getattr__(self, attr):
        return self._data[attr]

    def __dir__(self):
        return self._data.keys()

    def __repr__(self):
        return repr(self._data)


class DocJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.dict_to_object
        super(DocJSONDecoder, self).__init__(*args, **kwargs)

    def dict_to_object(self, data):
        identifier = data.get('_type')
        if identifier == 'link':
            return DocumentLink(data)
        elif identifier == 'list':
            return DocumentList(data)
        elif identifier == 'form':
            return DocumentForm(data)
        return Document(data)


def loads(content):
    return json.loads(content, cls=DocJSONDecoder)


def get(*args, **kwargs):
    response = requests.get(*args, **kwargs)
    return loads(response.content)
