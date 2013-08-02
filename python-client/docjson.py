# coding: utf-8
import requests
import json
import urlparse


version = '0.2.0'


class DocumentLink(object):
    _errors = {
        'missing_href': "Link missing 'href' key."
    }

    def __init__(self, data, base_url=None):
        assert 'href' in data, self._errors['missing_href']
        self._href = urlparse.urljoin(base_url, data['href'])

    def __call__(self):
        return get(self._href)

    def __repr__(self):
        return _indentprint(self)


class DocumentList(object):
    _errors = {
        'missing_items': "List missing 'items' key.",
        'target_not_list': "Expected a List when following links in paginated list."
    }

    def __init__(self, data):
        assert 'items' in data, self._errors['missing_items']
        self._items = data['items']
        self._next = data.get('next')

    def __getitem__(self, idx):
        if idx < 0:
            raise IndexError('Negative indexing not supported')

        while True:
            # If we've already fetched more items than the requested index,
            # then return the requested index.
            if idx < len(self._items):
                return self._items[idx]

            # If there's no next link then we're at the end of the
            # paginated list.
            if self._next is None:
                raise IndexError

            # Retrieve the DocumentList at the next URL
            doc = get(self._next)
            assert isinstance(doc, DocumentList), self._errors['target_not_list']
            self._items.extend(doc._items)
            self._next = doc._next

    def __repr__(self):
        return _indentprint(self)


class DocumentForm(object):
    _errors = {
        'missing_href': "Form missing 'href' key.",
        'missing_method': "Form missing 'method' key.",
        'fields_not_list': "Form 'fields' was not a list.",
        'field_missing_name': "Form field missing 'name' key."
    }

    def __init__(self, data, base_url=None):
        assert 'href' in data, self._errors['missing_href']
        assert 'method' in data, self._errors['missing_method']
        self._href = urlparse.urljoin(base_url, data['href'])
        self._method = data['method']
        self._fields = data.get('fields', [])
        assert isinstance(self._fields, list), self._errors['fields_not_list']
        assert all(['name' in field for field in self._fields]), self._errors['field_missing_name']

    def __call__(self, **kwargs):
        self.validate(**kwargs)
        if self._method.lower() == 'get':
            request_opts = {
                'params': kwargs
            }
        else:
            request_opts = {
                'data': json.dumps(kwargs),
                'headers': {'content-type': 'application/json'}
            }
        return request(self._method, self._href, **request_opts)

    def __repr__(self):
        return _indentprint(self)

    def validate(self, **kwargs):
        """
        Ensure that arguments passed to the form are correct.
        """
        provided = set(kwargs.keys())

        # Get sets of field names for both required and optional fields.
        required = set([
            field.name for field in self._fields
            if getattr(field, 'required', False)
        ])
        optional = set([
            field.name for field in self._fields
            if not getattr(field, 'required', False)
        ])

        # Determine if any invalid field names supplied.
        unexpected = provided - (optional | required)
        unexpected = ["'" + item + "'" for item in unexpected]
        if unexpected:
            prefix = len(unexpected) > 1 and 'parameters ' or 'parameter '
            raise ValueError('Unknown ' + prefix + ', '.join(unexpected))

        # Determine if any required field names not supplied.
        missing = required - provided
        missing = ["'" + item + "'" for item in missing]
        if missing:
            prefix = len(missing) > 1 and 'parameters ' or 'parameter '
            raise ValueError('Missing required ' + prefix + ', '.join(missing))

    def fields_as_string(self):
        """
        Return the fields as a string containing all the field names,
        indicating which fields are required and which are optional.

        For example: "text, [completed]"
        """
        def field_as_string(field):
            if getattr(field, 'required', False):
                return field.name
            return '[' + field.name + ']'

        return ', '.join([
            field_as_string(field) for field in self._fields
        ])


class Document(object):
    def __init__(self, data):
        self._data = data

    def __getattr__(self, attr):
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError

    def __contains__(self, attr):
        return attr in self._data

    def __dir__(self):
        return self._data.keys()

    def __repr__(self):
        return _indentprint(self)


class _DocJSONDecoder(json.JSONDecoder):
    """
    Custom JSON decoder, for parsing DocJSON documents.
    """
    base_url = None

    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.dict_to_object
        super(_DocJSONDecoder, self).__init__(*args, **kwargs)

    def dict_to_object(self, data):
        identifier = data.get('_type')
        if identifier == 'link':
            return DocumentLink(data, self.base_url)
        elif identifier == 'list':
            return DocumentList(data)
        elif identifier == 'form':
            return DocumentForm(data, self.base_url)
        return Document(data)


def _indentprint(obj, indent=0):
    """
    Returns a nicely formatted string for the given document.
    """
    if isinstance(obj, Document):
        final_idx = len(obj._data) - 1
        ret = '{\n'
        for idx, (key, val) in enumerate(obj._data.items()):
            ret += '    ' * (indent + 1) + key + ': ' + _indentprint(val, indent + 1)
            ret += idx == final_idx and '\n' or ',\n'
        ret += '    ' * indent + '}'
        return ret
    elif isinstance(obj, DocumentList):
        final_idx = len(obj._items) - 1
        ret = '[\n'
        for idx, val in enumerate(obj._items):
            ret += '    ' * (indent + 1) + _indentprint(val, indent + 1)
            ret += idx == final_idx and '\n' or ',\n'
        if obj._next:
            ret += '    ' * (indent + 1) + '...\n'
        ret += '    ' * indent + ']'
        return ret
    elif isinstance(obj, DocumentLink):
        return 'link -> ' + obj._href
    elif isinstance(obj, DocumentForm):
        return 'form(' + obj.fields_as_string() + ')'
    return repr(obj)


def _load_document(content, url=None):
    class _DocJSONDecoderWithBaseURL(_DocJSONDecoder):
        base_url = url
    return json.loads(content, cls=_DocJSONDecoderWithBaseURL)


def request(method, url, *args, **kwargs):
    response = requests.request(method, url, *args, **kwargs)
    return _load_document(response.content, url=response.url)


def get(url, *args, **kwargs):
    response = requests.get(url, *args, **kwargs)
    return _load_document(response.content, url=response.url)
